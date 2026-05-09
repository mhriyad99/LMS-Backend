from pydantic import BaseModel, EmailStr

class Book(BaseModel):
    title: str
    author: str
    description: str

class BookResponse(Book):
    copies: int

class AddCopiesRequest(BaseModel):
    quantity: int = 1

class CopyResponse(BaseModel):
    id: int
    book_id: int
    availability: bool

    class Config:
        from_attributes = True

class UserRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    email: EmailStr
    username: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    id : Optional[str] = None