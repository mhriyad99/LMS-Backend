from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_db
from app.config import models, schemas

router = APIRouter(
    prefix="/genre",
    tags=["Genre"],
)

@router.get("/books")
def get_books():
    pass

@router.get("/", response_model=List[schemas.GenresOut])
async def get_genres(db: AsyncSession = Depends(get_db())):
    result = await db.scalars(
        select(models.Genre)
    )

    genres = result.all()

    return [
        schemas.GenresOut(
            id=genre.id,
            title=genre.genre
        )
        for genre in genres
    ]

@router.post("/", response_model=schemas.GenresOut)
async def create_genre(payload: schemas.GenreCreate, db: AsyncSession = Depends(get_db)):
    genre = await db.scalar(
        select(models.Genre)
        .where(models.Genre.genre == payload.title)
    )

    if genre:
        raise HTTPException(status_code=400, detail="Genre already exists")

    new_genre = models.Genre(
        genre=payload.title,
    )
    db.add(new_genre)
    await db.commit()
    await db.refresh(new_genre)
    return new_genre

@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await db.get(models.Genre, genre_id)

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    await db.delete(genre)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)