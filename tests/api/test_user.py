import uuid

from fastapi import status
from nanoid import generate


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
            "role": "CARERECEIVER",
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
        assert "id" in data
        assert data["id"] is not None

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
        assert data["id"] == anon_id
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
        assert data["id"] == anon_id
        assert data["email"] is None

    def test_get_current_user_registered_id_with_id_fail(self, client):
        """Fail: registered id cannot use id to get current user (must use token)."""
        user_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id,
            "role": "CARERECEIVER",
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
            "role": "CARERECEIVER",
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
        assert data["id"] == user_id

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
            "role": "CARERECEIVER",
        }
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/user/me", params={"id": user_id}, headers=headers)
        assert resp.status_code == 400 or resp.status_code == 401
