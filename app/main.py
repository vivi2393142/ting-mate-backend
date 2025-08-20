from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI

from app.api import (
    activity_log,
    assistant,
    auth,
    invitation,
    link,
    notification,
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

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或填你的前端 IP，如 "http://10.136.75.21:8000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
auto_register_routes(router, activity_log)
auto_register_routes(router, notification)
app.include_router(router)

# Include SSE router in
app.include_router(notification.router)
