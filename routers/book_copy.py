from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.database import get_db
from config import models, schemas
from config.schemas import AddCopiesRequest

router = APIRouter(
    prefix="/copies",
    tags=["Book Copy"]
)

@router.post("/books/{book_id}/copies")
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
        models.BookCopy(
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

@router.get("/books/{book_id}/copies", response_model=List[schemas.CopyResponse])
async def get_copies(book_id: int, db: AsyncSession = Depends(get_db)):
    book = await db.get(models.Book, book_id)

    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    copies = await db.scalars(
        select(models.BookCopy)
        .where(models.BookCopy.book_id == book_id)
    )

    return copies.all()

@router.get("/{copy_id}", response_model=schemas.CopyResponse)
async def get_copy(copy_id: int, db: AsyncSession = Depends(get_db)):
    copy = await db.get(models.BookCopy, copy_id)
    if not copy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Copy not found")

    return copy

@router.delete("/{copy_id}", response_model=schemas.CopyResponse)
async def delete_copy(copy_id: int, db: AsyncSession = Depends(get_db)):
    copy = await db.get(models.BookCopy, copy_id)
    if not copy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Copy not found")

    if not copy.availability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Copy is currently borrowed")

    await db.delete(copy)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
