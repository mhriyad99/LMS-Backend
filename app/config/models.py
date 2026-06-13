import enum
import datetime as dt
from datetime import datetime, timedelta
from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey,
                        select, func, Enum, Table)
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import column_property, relationship
from pgvector.sqlalchemy import Vector

from app.config.database import Base
from app.config.enums import UserRole
from app.config.settings import settings

DEFAULT_DUE_DATE = 15


def default_due_date():
    return datetime.now(dt.UTC) + timedelta(days=DEFAULT_DUE_DATE)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, server_default="member")

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


class BookCopy(Base):
    __tablename__ = "book_copies"
    id = Column(Integer, primary_key=True, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    availability = Column(Boolean, nullable=False, server_default=text('false'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    book = relationship("Book", back_populates="copies_list")


book_genres = Table(
    "book_genres",
    Base.metadata,
    Column("book_id", Integer,ForeignKey('books.id'), primary_key=True),
    Column("genre_id", Integer,ForeignKey('genres.id'), primary_key=True),
)

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, nullable=False)
    genre = Column(String(255), nullable=False)

    books = relationship("Book", secondary=book_genres, back_populates="genres")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    description = Column(String(1000))
    embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    copies = column_property(select(func.count(BookCopy.id))
                             .where(BookCopy.book_id == id)
                             .correlate_except(BookCopy)
                             .scalar_subquery())

    copies_list = relationship("BookCopy",
                               back_populates="book",
                               cascade="all, delete-orphan")

    genres = relationship("Genre", secondary=book_genres, back_populates="books")


class BorrowRecord(Base):
    __tablename__ = "borrow_records"
    id = Column(Integer, primary_key=True, nullable=False)
    book_copy_id = Column(Integer, ForeignKey('book_copies.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    borrow_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    due_date = Column(TIMESTAMP(timezone=True), nullable=False, default=default_due_date)
    return_date = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User")
    book_copy = relationship("BookCopy")


# --- Chat enums ---

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ActionType(str, enum.Enum):
    borrow = "borrow"
    return_ = "return"


class ActionStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    executed = "executed"


# --- Chat models ---

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, nullable=False)
    session_token = Column(String(36), unique=True, nullable=False)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    pending_actions = relationship("PendingAction", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(String, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    metadata_ = Column("metadata", String, nullable=True)  # stored as JSON string
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    session = relationship("ChatSession", back_populates="messages")


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(Enum(ActionType), nullable=False)
    status = Column(Enum(ActionStatus), nullable=False, server_default="pending")
    action_payload = Column(String, nullable=False)  # stored as JSON string
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    session = relationship("ChatSession", back_populates="pending_actions")

