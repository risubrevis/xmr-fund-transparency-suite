import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.config import settings
from app.crypto import ViewKeyEncryption, validate_monero_address, validate_view_key
from app.database import get_db
from app.logging import get_logger
from app.models import Wallet
from app.rpc_client import WalletRPCError, close_wallet, create_view_only_wallet
from app.schemas import WalletCreate, WalletResponse, WalletUpdate

logger = get_logger("api.wallets")

router = APIRouter()


def _get_encryption() -> ViewKeyEncryption:
    return ViewKeyEncryption(settings.view_key_master_secret)


def _wallet_filename(wallet_uuid: str) -> str:
    """Deterministic RPC filename for a wallet based on its UUID."""
    return f"wallet_{wallet_uuid}"


@router.post("/wallets", response_model=WalletResponse, status_code=201)
async def create_wallet(
    body: WalletCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> WalletResponse:
    """Create a new wallet (view-only wallet tracker).

    Generates a deterministic RPC filename (wallet_{uuid}) so that
    multiple wallets can coexist on the same monero-wallet-rpc instance
    running with --wallet-dir.
    """
    # Validate inputs
    if not validate_monero_address(body.primary_address):
        raise HTTPException(
            status_code=400,
            detail="Invalid Monero address. Must be 95 characters, base58, starting with 4/8/A/B.",
        )
    if not validate_view_key(body.view_key):
        raise HTTPException(
            status_code=400,
            detail="Invalid view key. Must be 64 hexadecimal characters.",
        )

    # Encrypt view key before storing
    cipher = _get_encryption()
    encrypted_view_key = cipher.encrypt(body.view_key)

    # Create DB record first to obtain UUID for the deterministic filename
    wallet = Wallet(
        name=body.name,
        primary_address=body.primary_address,
        view_key=encrypted_view_key,
        start_height=body.start_height,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    # Register view-only wallet on monero-wallet-rpc with deterministic filename
    filename = _wallet_filename(wallet.uuid)
    try:
        await create_view_only_wallet(
            address=body.primary_address,
            view_key=body.view_key,
            start_height=body.start_height,
            filename=filename,
        )
    except WalletRPCError as e:
        logger.error(
            "rpc_wallet_creation_failed", wallet_id=str(wallet.id), error=str(e)
        )
        # Roll back DB creation since RPC failed
        await db.delete(wallet)
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "rpc_wallet_creation_failed", wallet_id=str(wallet.id), error=str(e)
        )
        await db.delete(wallet)
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected error creating wallet: {str(e)}",
        )

    logger.info(
        "wallet_created",
        wallet_id=str(wallet.id),
        uuid=wallet.uuid,
        name=wallet.name,
        start_height=wallet.start_height,
    )

    return WalletResponse.model_validate(wallet)


@router.get("/wallets", response_model=list[WalletResponse])
async def list_wallets(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> list[WalletResponse]:
    """List all wallets."""
    result = await db.execute(select(Wallet).order_by(Wallet.created_at))
    wallets = result.scalars().all()
    return [WalletResponse.model_validate(w) for w in wallets]


@router.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> WalletResponse:
    """Get wallet details."""
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return WalletResponse.model_validate(wallet)


@router.patch("/wallets/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: uuid.UUID,
    body: WalletUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> WalletResponse:
    """Update wallet name or active status."""
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if body.name is not None:
        wallet.name = body.name
    if body.is_active is not None:
        wallet.is_active = body.is_active

    await db.commit()
    await db.refresh(wallet)

    logger.info("wallet_updated", wallet_id=str(wallet.id), name=wallet.name)

    return WalletResponse.model_validate(wallet)


@router.delete("/wallets/{wallet_id}", status_code=204)
async def delete_wallet(
    wallet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> None:
    """Delete a wallet and all its associated funds, transactions, and posts.

    Closes the wallet on monero-wallet-rpc before removing from DB.
    """
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet_uuid = wallet.uuid

    # Close the wallet on monero-wallet-rpc using deterministic filename
    filename = _wallet_filename(wallet_uuid)
    try:
        await close_wallet(filename)
    except Exception as e:
        logger.warning(
            "wallet_close_after_delete_failed", filename=filename, error=str(e)
        )

    # Cascade delete: Wallet -> Funds, Transactions, Posts
    await db.delete(wallet)
    await db.commit()

    logger.info("wallet_deleted", wallet_id=str(wallet_id), filename=filename)
