import os
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from nanoid import generate

from app.main import app
from app.schemas.user import Role


@pytest.fixture(autouse=True)
def setup_testing_environment():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)


@pytest.fixture
def client():
    """Fixture for FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def register_user(client):
    """Register a user and return (email, token, user_id)."""

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


def auth_headers(token):
    """Return authorization headers for a given token."""
    return {"Authorization": f"Bearer {token}"}


def create_link_by_invitation(client, inviter_token, invitee_token):
    """Create a user link by invitation code."""
    resp = client.post(
        "/user/invitations/generate", headers=auth_headers(inviter_token)
    )
    assert resp.status_code == 200
    code = resp.json()["invitation_code"]
    resp2 = client.post(
        f"/user/invitations/{code}/accept", headers=auth_headers(invitee_token)
    )
    assert resp2.status_code == 200


@pytest.fixture
def register_and_link_users(client, register_user):
    """Register a carereceiver and caregiver, link them, and return their info."""
    cr_email, cr_token, cr_id = register_user(Role.CARERECEIVER)
    # register as carereceiver, but will be updated to caregiver when accepting invitation
    cg_email, cg_token, cg_id = register_user(Role.CARERECEIVER)

    # carereceiver generates invitation
    resp = client.post("/user/invitations/generate", headers=auth_headers(cr_token))
    code = resp.json()["invitation_code"]

    # caregiver accepts invitation
    resp = client.post(
        f"/user/invitations/{code}/accept", headers=auth_headers(cg_token)
    )

    # carereceiver enables allow_share_location
    client.put(
        "/user/settings",
        json={"allow_share_location": True},
        headers=auth_headers(cr_token),
    )

    return {
        "carereceiver": {"email": cr_email, "token": cr_token, "id": cr_id},
        "caregiver": {"email": cg_email, "token": cg_token, "id": cg_id},
    }
