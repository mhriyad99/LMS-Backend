from fastapi import FastAPI
from app.routers import books, book_copy, users, auth

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

app.include_router(books.router)
app.include_router(book_copy.router)
app.include_router(users.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
