from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import auth, task, user

load_dotenv()

app = FastAPI()

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(task.router)
