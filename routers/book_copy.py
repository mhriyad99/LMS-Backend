from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from config import models, schemas

router = APIRouter(
    prefix="/book_copy",
    tags=["Book Copy"]
)

@router.get("/")
async def add_book_copy(payload, db: AsyncSession = Depends(get_db)):
    pass