from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI

from app.api import assistant, auth, invitation, link, shared_notes, speech, task, user
from app.core.api_decorator import auto_register_routes

load_dotenv()

app = FastAPI()

router = APIRouter()
auto_register_routes(router, auth)
auto_register_routes(router, user)
auto_register_routes(router, task)
auto_register_routes(router, assistant)
auto_register_routes(router, speech)
auto_register_routes(router, invitation)
auto_register_routes(router, link)
auto_register_routes(router, shared_notes)
app.include_router(router)
