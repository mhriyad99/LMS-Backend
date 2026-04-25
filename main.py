from fastapi import FastAPI
from config import models
from config.database import engine
from routers import books

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

app.include_router(books.router)
@app.get("/")
async def root():
    return {"message": "Hello World"}
