from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.security import create_access_token, verify_password
from app.services.user import create_user, get_user

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=RegisterResponse,
    summary="Register a new user",
    response_description="User registered successfully",
)
def register(request: RegisterRequest):
    """
    Register a new user. If anonymous_id is provided, upgrade to a registered user.
    """
    try:
        user = create_user(request)
        return RegisterResponse(message="User registered successfully", user=user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/auth/login", response_model=LoginResponse, summary="Login and get access token"
)
def login(request: LoginRequest):
    """
    Login with email and password to get an access token.
    """
    userdb = get_user(request.email, by="email")
    if not userdb or not verify_password(request.password, userdb.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = create_access_token({"sub": userdb.id})
    return LoginResponse(access_token=access_token)
