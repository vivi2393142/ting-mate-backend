import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from nanoid import generate

from app.main import app


@pytest.fixture
def client():
    """Fixture for FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def register_user(client):
    def _register(role, email=None, user_id=None):
        if not email:
            email = f"test_{generate(size=8)}@example.com"
        if not user_id:
            user_id = str(uuid.uuid4())
        user_data = {
            "email": email,
            "password": "test123456",
            "id": user_id,
            "role": role,
        }
        reg = client.post("/auth/register", json=user_data)
        assert reg.status_code == status.HTTP_201_CREATED
        login = client.post(
            "/auth/login", json={"email": email, "password": "test123456"}
        )
        assert login.status_code == status.HTTP_200_OK
        token = login.json()["access_token"]
        return email, token, user_id

    return _register
