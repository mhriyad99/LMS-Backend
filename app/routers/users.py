from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import schemas, models
from app.config.database import get_db
from app.config.security import password_hash

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.post("/register", response_model=schemas.UserResponse)
async def register_user(payload: schemas.UserRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalars(
        select(models.User)
        .where(models.User.email == payload.email)
    )

    if user.first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = password_hash.hash(payload.password)
    new_user = models.User(
        email=payload.email,
        username = payload.username,
        password = hashed_password
    )

    db.add(new_user)
    await db.commit()

    return new_user