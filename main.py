from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.routers import books, book_copy, users, auth, chat
from app.config.embedding import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(books.router)
app.include_router(book_copy.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return FileResponse("static/index.html")
