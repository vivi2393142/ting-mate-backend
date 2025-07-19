from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

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


@post_route(
    path="/auth/token",
    summary="OAuth2 Token",
    description="OAuth2 compatible token endpoint for Swagger UI. Use username field for email.",
    response_model=LoginResponse,
    tags=["authentication"],
)
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    The 'username' field should contain the email address.
    """
    # Use username field as email
    email = form_data.username
    password = form_data.password

    userdb = get_user(email, by="email")
    if not userdb or not verify_password(password, userdb.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": userdb.id})
    return LoginResponse(access_token=access_token, anonymous_id=userdb.id)
