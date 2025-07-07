from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI

from app.api import auth, task, user, voice
from app.core.api_decorator import auto_register_routes

load_dotenv()

app = FastAPI()

router = APIRouter()
auto_register_routes(router, auth)
auto_register_routes(router, user)
auto_register_routes(router, task)
auto_register_routes(router, voice)
app.include_router(router)
