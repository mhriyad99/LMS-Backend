from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select, func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import column_property, relationship
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


class BookCopy(Base):
    __tablename__ = "book_copies"
    id = Column(Integer, primary_key=True, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    availability = Column(Boolean, nullable=False, server_default=text('false'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    book = relationship("Book", back_populates="copies_list")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    description = Column(String(1000))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    copies = column_property(select(func.count(BookCopy.id))
                             .where(BookCopy.book_id == id)
                             .correlate_except(BookCopy)
                             .scalar_subquery())

    copies_list = relationship("BookCopy",
                               back_populates="book",
                               cascade="all, delete-orphan")

class BorrowRecord(Base):
    __tablename__ = "borrow_records"
    id = Column(Integer, primary_key=True, nullable=False)
    book_copy_id = Column(Integer, ForeignKey('book_copies.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    borrow_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    due_date = Column(TIMESTAMP(timezone=True), nullable=False)
    return_date = Column(TIMESTAMP(timezone=True), nullable=True)




