import json
from dataclasses import dataclass

from pydantic_ai import RunContext
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.embedding import embed
from app.config.models import Book, BookCopy, BorrowRecord, ActionType
from app.chat.schemas import (
    BookSearchResult, AvailabilityResult,
    BorrowIntentPayload, ReturnIntentPayload, ActiveBorrow
)


@dataclass
class AgentDeps:
    db: AsyncSession
    user_id: int | None


async def search_books(ctx: RunContext[AgentDeps], query: str) -> list[BookSearchResult]:
    """Search books by semantic similarity, with ILIKE fallback."""
    db = ctx.deps.db

    query_embedding = await embed(query)

    result = await db.execute(
        select(Book)
        .order_by(Book.embedding.cosine_distance(query_embedding))
        .limit(5)
    )
    books = result.scalars().all()

    if not books:
        pattern = f"%{query}%"
        result = await db.execute(
            select(Book).where(
                Book.title.ilike(pattern) | Book.author.ilike(pattern)
            ).limit(5)
        )
        books = result.scalars().all()

    return [
        BookSearchResult(
            id=b.id,
            title=b.title,
            author=b.author,
            description=b.description,
            copies_available=b.copies,
        )
        for b in books
    ]


async def check_availability(ctx: RunContext[AgentDeps], book_id: int) -> AvailabilityResult:
    """Return available copy count and next available copy_id for a book."""
    db = ctx.deps.db

    result = await db.execute(
        select(Book).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise ValueError(f"Book with id {book_id} not found.")

    result = await db.execute(
        select(BookCopy)
        .where(and_(BookCopy.book_id == book_id, BookCopy.availability == True))
        .limit(1)
    )
    available_copy = result.scalar_one_or_none()

    result = await db.execute(
        select(BookCopy).where(
            and_(BookCopy.book_id == book_id, BookCopy.availability == True)
        )
    )
    all_available = result.scalars().all()

    return AvailabilityResult(
        book_id=book_id,
        title=book.title,
        copies_available=len(all_available),
        next_copy_id=available_copy.id if available_copy else None,
    )


async def stage_borrow_intent(ctx: RunContext[AgentDeps], book_id: int) -> BorrowIntentPayload:
    """Validate and stage a borrow — does NOT write a BorrowRecord."""
    db = ctx.deps.db
    user_id = ctx.deps.user_id

    if user_id is None:
        raise ValueError("You must be logged in to borrow books.")

    availability = await check_availability(ctx, book_id)
    if availability.copies_available == 0 or availability.next_copy_id is None:
        raise ValueError(f'No available copies of "{availability.title}".')

    # Check user doesn't already have this book borrowed
    result = await db.execute(
        select(BorrowRecord)
        .join(BookCopy, BorrowRecord.book_copy_id == BookCopy.id)
        .where(
            and_(
                BookCopy.book_id == book_id,
                BorrowRecord.user_id == user_id,
                BorrowRecord.return_date == None,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError(f'You already have a copy of "{availability.title}" borrowed.')

    return BorrowIntentPayload(
        book_id=book_id,
        book_copy_id=availability.next_copy_id,
        title=availability.title,
    )


async def stage_return_intent(ctx: RunContext[AgentDeps], borrow_record_id: int) -> ReturnIntentPayload:
    """Validate and stage a return — does NOT update the BorrowRecord."""
    db = ctx.deps.db
    user_id = ctx.deps.user_id

    if user_id is None:
        raise ValueError("You must be logged in to return books.")

    result = await db.execute(
        select(BorrowRecord)
        .join(BookCopy, BorrowRecord.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                BorrowRecord.id == borrow_record_id,
                BorrowRecord.user_id == user_id,
                BorrowRecord.return_date == None,
            )
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise ValueError("Active borrow record not found for your account.")

    result = await db.execute(select(Book).join(BookCopy, Book.id == BookCopy.book_id)
                              .where(BookCopy.id == record.book_copy_id))
    book = result.scalar_one_or_none()

    return ReturnIntentPayload(
        borrow_record_id=record.id,
        book_copy_id=record.book_copy_id,
        title=book.title if book else "Unknown",
    )


async def get_active_borrows(ctx: RunContext[AgentDeps]) -> list[ActiveBorrow]:
    """Return all unreturned borrow records for the current user."""
    db = ctx.deps.db
    user_id = ctx.deps.user_id

    if user_id is None:
        raise ValueError("You must be logged in to view your borrows.")

    result = await db.execute(
        select(BorrowRecord, Book.title)
        .join(BookCopy, BorrowRecord.book_copy_id == BookCopy.id)
        .join(Book, BookCopy.book_id == Book.id)
        .where(
            and_(
                BorrowRecord.user_id == user_id,
                BorrowRecord.return_date == None,
            )
        )
    )
    rows = result.all()

    return [
        ActiveBorrow(
            borrow_record_id=row.BorrowRecord.id,
            book_copy_id=row.BorrowRecord.book_copy_id,
            title=row.title,
            borrow_date=row.BorrowRecord.borrow_date.isoformat(),
            due_date=row.BorrowRecord.due_date.isoformat(),
        )
        for row in rows
    ]