import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.logging import get_logger
from app.models import Fund, Post, Wallet
from app.schemas import PostCreate, PostResponse, PostUpdate

logger = get_logger("api.posts")

router = APIRouter()


async def _enrich_post(post: Post, db: AsyncSession) -> PostResponse:
    """Add fund_label and wallet_name to a post response."""
    fund_label = None
    wallet_name = None

    result = await db.execute(select(Fund.label).where(Fund.id == post.fund_id))
    row = result.scalar_one_or_none()
    if row:
        fund_label = row

    result = await db.execute(select(Wallet.name).where(Wallet.id == post.wallet_id))
    row = result.scalar_one_or_none()
    if row:
        wallet_name = row

    return PostResponse(
        id=post.id,
        fund_id=post.fund_id,
        wallet_id=post.wallet_id,
        body=post.body,
        fund_label=fund_label,
        wallet_name=wallet_name,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/posts", response_model=list[PostResponse])
async def list_posts(
    fund_id: uuid.UUID | None = Query(None, description="Filter posts by fund ID"),
    wallet_id: uuid.UUID | None = Query(None, description="Filter posts by wallet ID"),
    start_date: datetime | None = Query(
        None, description="Filter posts created after this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter posts created before this date"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """List posts, optionally filtered by fund, wallet, or date range. Public endpoint."""
    query = select(Post).order_by(Post.created_at.desc())
    if fund_id is not None:
        query = query.where(Post.fund_id == fund_id)
    elif wallet_id is not None:
        query = query.where(Post.wallet_id == wallet_id)
    if start_date is not None:
        query = query.where(Post.created_at >= start_date)
    if end_date is not None:
        query = query.where(Post.created_at <= end_date)

    result = await db.execute(query)
    posts = result.scalars().all()

    responses = []
    for post in posts:
        responses.append(await _enrich_post(post, db))
    return responses


@router.get("/wallets/{wallet_id}/posts", response_model=list[PostResponse])
async def list_wallet_posts(
    wallet_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """List all posts for a wallet across all its funds. Public endpoint."""
    result = await db.execute(
        select(Post).where(Post.wallet_id == wallet_id).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()

    responses = []
    for post in posts:
        responses.append(await _enrich_post(post, db))
    return responses


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    body: PostCreate,
    fund_id: uuid.UUID | None = Query(
        None, description="Fund ID (legacy, prefer body field)"
    ),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> PostResponse:
    """Create a new post linked to a fund."""
    # Use fund_id from body if provided, otherwise fall back to query param
    effective_fund_id = body.fund_id or fund_id
    if not effective_fund_id:
        raise HTTPException(
            status_code=422,
            detail="fund_id is required (provide in request body or as query parameter)",
        )

    # Verify fund exists and get wallet_id
    result = await db.execute(select(Fund).where(Fund.id == effective_fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    post = Post(body=body.body, fund_id=fund.id, wallet_id=fund.wallet_id)
    db.add(post)
    await db.commit()
    await db.refresh(post)

    logger.info("post_created", post_id=str(post.id), fund_id=str(fund.id))
    return await _enrich_post(post, db)


@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> PostResponse:
    """Update a post's body and/or move it to a different fund."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if body.body is not None:
        post.body = body.body

    if body.fund_id is not None:
        # Verify the new fund exists and get its wallet_id
        fund_result = await db.execute(select(Fund).where(Fund.id == body.fund_id))
        new_fund = fund_result.scalar_one_or_none()
        if not new_fund:
            raise HTTPException(status_code=404, detail="Fund not found")
        post.fund_id = new_fund.id
        post.wallet_id = new_fund.wallet_id

    await db.commit()
    await db.refresh(post)

    logger.info("post_updated", post_id=str(post.id))
    return await _enrich_post(post, db)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> None:
    """Delete a post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()

    logger.info("post_deleted", post_id=str(post_id))
