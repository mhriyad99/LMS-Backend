from fastapi import FastAPI
from config import models
from config.database import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
@app.get("/")
async def root():
    return {"message": "Hello World"}
