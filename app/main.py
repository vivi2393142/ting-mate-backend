from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI

from app.api import (
    assistant,
    auth,
    invitation,
    link,
    places,
    safe_zones,
    shared_notes,
    speech,
    task,
    user,
    user_locations,
)
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
auto_register_routes(router, safe_zones)
auto_register_routes(router, user_locations)
auto_register_routes(router, places)
app.include_router(router)
