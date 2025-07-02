from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.user import create_user, get_user
from app.services.security import verify_password
from app.services.jwt import create_access_token
from app.schemas.auth import TokenPayload

router = APIRouter()


@router.post("/register")
def register(register_request: RegisterRequest):
    try:
        crated_user = create_user(register_request)
        return RegisterResponse(email=crated_user.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(login_request: LoginRequest):
    user = get_user(login_request.email)
    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token = create_access_token(TokenPayload(sub=user.email))
    return LoginResponse(access_token=token)
