from fastapi import FastAPI
from config import models
from config.database import engine
from routers import books, book_copy

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

app.include_router(books.router)
app.include_router(book_copy.router)
@app.get("/")
async def root():
    return {"message": "Hello World"}
