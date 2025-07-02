from dotenv import load_dotenv
from fastapi import FastAPI
from app.api import auth

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth.router)
