from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import schemas, models, security
from app.config.database import get_db
from app.config.schemas import UserResponse
from app.config.security import password_hash

router = APIRouter(
    tags=['Authentication']
)

@router.post("/login", response_model=schemas.Token)
async def login(payload: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(models.User)
        .where(models.User.email == payload.email)
    )
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="Incorrect email or password")

    if not password_hash.verify(payload.password, user.password):
        raise HTTPException(status_code=404, detail="Incorrect email or password")

    token = security.create_access_token({"user_id": user.id})

    return {"access_token": token}
