from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from config import models, schemas
from config.schemas import AddCopiesRequest

router = APIRouter(
    prefix="/book_copies",
    tags=["Book Copy"]
)

@router.post("/{_id}")
async def add_copies(book_id: int, payload: AddCopiesRequest,
                     db: AsyncSession = Depends(get_db)):
    book = await db.get(models.Book, book_id)

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    if payload.quantity < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Quantity must be at least 1")

    copies = [
        BookCopy(
            book_id=book_id,
            availability=True
        )
        for _ in range(payload.quantity)
    ]

    db.add_all(copies)
    await db.commit()

    return {
        "message": f"{payload.quantity} copies added",
        "book_id": book_id
    }

