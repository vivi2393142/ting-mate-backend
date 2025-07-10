import uuid

import pytest
from fastapi import status
from nanoid import generate

from app.schemas.user import Role, UserDisplayMode, UserTextSize


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


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestUserMeAPI:
    def test_user_me_response_fields(self, client, register_user):
        """Should return correct user info and settings fields."""
        email, token, _ = register_user(Role.CAREGIVER)
        resp = client.get("/user/me", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email
        assert data["role"] == "CAREGIVER"
        settings = data["settings"]
        assert "name" in settings
        assert "linked" in settings
        assert isinstance(settings["linked"], list)
        assert "textSize" in settings
        assert settings["textSize"] in [UserTextSize.STANDARD, UserTextSize.LARGE]
        assert "displayMode" in settings
        assert settings["displayMode"] in [UserDisplayMode.FULL, UserDisplayMode.SIMPLE]
        assert "reminder" in settings
        # reminder can be None or dict
        assert settings["reminder"] is None or isinstance(settings["reminder"], dict)

    def test_user_me_no_settings(self, client):
        """Should return default values if user_settings does not exist."""
        anon_id = str(uuid.uuid4())
        resp = client.get("/user/me", params={"id": anon_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] is None
        assert data["role"] == "CARERECEIVER"
        settings = data["settings"]
        assert settings["name"] == ""
        assert settings["linked"] == []
        assert settings["textSize"] == UserTextSize.STANDARD
        assert settings["displayMode"] == UserDisplayMode.FULL
        assert settings["reminder"] is None

    def test_user_me_linked_content(self, client, register_user):
        """Should return correct linked user info after linking."""
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)
        # Link them
        resp = client.post(
            "/user/invitations/generate", headers=auth_headers(caregiver_token)
        )
        code = resp.json()["invitation_code"]
        client.post(
            f"/user/invitations/{code}/accept", headers=auth_headers(carereceiver_token)
        )
        # Check caregiver's linked
        resp2 = client.get("/user/me", headers=auth_headers(caregiver_token))
        linked = resp2.json()["settings"]["linked"]
        assert any(u["email"] == carereceiver_email for u in linked)
        assert all("name" in u for u in linked)


class TestGetCurrentUser:
    """Test group for getting current user functionality."""

    def test_get_current_user_success(self, client):
        """Success: get current user with valid token."""
        # First register a user
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": str(uuid.uuid4()),
            "role": Role.CARERECEIVER,
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Login to get access token
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        access_token = login_response.json()["access_token"]

        # Get current user with token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/user/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == unique_email
        assert "role" in data
        assert data["role"] is not None

    def test_get_current_user_no_token(self, client):
        """Fail: get current user without authentication token."""
        response = client.get("/user/me")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_current_user_invalid_token(self, client):
        """Fail: get current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"]

    def test_get_current_user_malformed_token(self, client):
        """Fail: get current user with malformed authorization header."""
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/user/me", headers=headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_current_user_new_anonymous_id(self, client):
        """Success: new anonymous id creates user and returns user info."""
        anon_id = str(uuid.uuid4())
        resp = client.get("/user/me", params={"id": anon_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] is None

    def test_get_current_user_existing_anonymous_id(self, client):
        """Success: existing anonymous id (not registered) returns user info."""
        anon_id = str(uuid.uuid4())
        # First call to create user
        client.get("/user/me", params={"id": anon_id})
        # Second call should return same user
        resp = client.get("/user/me", params={"id": anon_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] is None

    def test_get_current_user_registered_id_with_id_fail(self, client):
        """Fail: registered id cannot use id to get current user (must use token)."""
        user_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id,
            "role": Role.CARERECEIVER,
        }
        client.post("/auth/register", json=user_data)
        resp = client.get("/user/me", params={"id": user_id})
        assert resp.status_code == 401
        assert "token" in resp.json()["detail"].lower()

    def test_get_current_user_registered_id_with_token_success(self, client):
        """Success: registered id can use token to get current user."""
        user_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id,
            "role": Role.CARERECEIVER,
        }
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/user/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == unique_email

    def test_get_current_user_no_id_no_token_fail(self, client):
        """Fail: get current user with no id and no token should fail."""
        resp = client.get("/user/me")
        assert resp.status_code == 400 or resp.status_code == 401

    def test_get_current_user_both_id_and_token_fail(self, client):
        """Fail: get current user with both id and token should fail."""
        user_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id,
            "role": Role.CARERECEIVER,
        }
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/user/me", params={"id": user_id}, headers=headers)
        assert resp.status_code == 400 or resp.status_code == 401
