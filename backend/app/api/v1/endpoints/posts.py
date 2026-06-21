import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.logging import get_logger
from app.models import Post
from app.schemas import PostCreate, PostResponse, PostUpdate

logger = get_logger("api.posts")

router = APIRouter()


@router.get("/posts", response_model=list[PostResponse])
async def list_posts(
    db: AsyncSession = Depends(get_db),
) -> list[PostResponse]:
    """List all posts, newest first. Public endpoint — no auth required."""
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()
    return [PostResponse.model_validate(p) for p in posts]


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> PostResponse:
    """Create a new post."""
    post = Post(body=body.body)
    db.add(post)
    await db.commit()
    await db.refresh(post)

    logger.info("post_created", post_id=str(post.id))
    return PostResponse.model_validate(post)


@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> PostResponse:
    """Update a post's body."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.body = body.body
    await db.commit()
    await db.refresh(post)

    logger.info("post_updated", post_id=str(post.id))
    return PostResponse.model_validate(post)


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
