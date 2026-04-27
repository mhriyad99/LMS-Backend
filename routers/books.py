from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
def update_book(_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == _id).first()

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    return book

@router.post("/", response_model=schemas.BookResponse)
def add_book(payload: schemas.Book,db: Session = Depends(get_db)):
    new_book = models.Book(**payload.model_dump())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.put("/{_id}", response_model=schemas.BookResponse)
def update_book(_id: int, payload: schemas.Book, db: Session = Depends(get_db)):
    book_query = db.query(models.Book).filter(models.Book.id == _id)
    book = book_query.first()

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    book_query.update(payload.model_dump(), synchronize_session=False)
    db.commit()
    return book_query.first()

@router.delete("/{_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(_id: int, db: Session = Depends(get_db)):
    book_query = db.query(models.Book).filter(models.Book.id == _id)
    book = book_query.first()

    if not book:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail="Book not found")

    book_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)