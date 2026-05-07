from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import schemas, models
from app.config.database import get_db
from app.config.schemas import UserResponse
from app.config.security import password_hash

router = APIRouter(
    tags=['Authentication']
)

@router.post("/login", response_model=UserResponse)
def login():
    pass