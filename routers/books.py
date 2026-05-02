from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from config.database import get_db
from config import models, schemas

router = APIRouter(
    prefix="/books",
    tags=["Books"]
)

@router.get("/", response_model=List[schemas.BookResponse])
async def get_book(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Book))
    books = result.scalars().all()

    return books

@router.get("/{_id}", response_model=schemas.BookResponse)
async def update_book(_id: int, db: AsyncSession = Depends(get_db)):
    book = await db.get(models.Book, _id)

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    return book

@router.post("/", response_model=schemas.BookResponse)
async def add_book(payload: schemas.Book,db: AsyncSession = Depends(get_db)):
    new_book = models.Book(**payload.model_dump())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

@router.put("/{_id}", response_model=schemas.BookResponse)
async def update_book(_id: int, payload: schemas.Book, db: AsyncSession = Depends(get_db)):
    book = await db.get(models.Book, _id)

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    await db.execute(
        update(models.Book)
        .where(models.Book.id == _id)
        .values(**payload.model_dump())
    )
    await db.commit()
    await db.refresh(book)
    return book

@router.delete("/{_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(_id: int, db: AsyncSession = Depends(get_db)):
    book = await db.get(models.Book, _id)

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")


    await db.delete(book)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)