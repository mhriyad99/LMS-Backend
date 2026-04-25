from pydantic import BaseModel

class Book(BaseModel):
    title: str
    author: str
    description: str

class BookResponse(Book):
    copies: int