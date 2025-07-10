from fastapi import HTTPException

from app.core.api_decorator import post_route
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.security import create_access_token, verify_password
from app.services.user import create_user, get_user


@post_route(
    path="/auth/register",
    summary="User Registration",
    description="Register a new user and return access token. The id, email, and role must be provided by frontend and be valid.",
    response_model=RegisterResponse,
    tags=["authentication"],
    status_code=201,
)
def register(request: RegisterRequest):
    user = create_user(request)
    # Create access token immediately after registration
    access_token = create_access_token({"sub": user.id})
    return RegisterResponse(
        message="User registered successfully",
        user=user,
        access_token=access_token,
        anonymous_id=user.id,
    )


@post_route(
    path="/auth/login",
    summary="User Login",
    description="Login with email and password to get access token.",
    response_model=LoginResponse,
    tags=["authentication"],
)
def login(request: LoginRequest):
    userdb = get_user(request.email, by="email")
    if not userdb or not verify_password(request.password, userdb.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": userdb.id})
    return LoginResponse(access_token=access_token, anonymous_id=userdb.id)
