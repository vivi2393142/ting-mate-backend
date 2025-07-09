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
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        resp = client.get("/user/me", params={"id": user_id})
        assert resp.status_code == 401
        assert "token" in resp.json()["detail"].lower()

    def test_get_current_user_registered_id_with_token_success(self, client):
        """Success: registered id can use token to get current user."""
        user_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
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
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/user/me", params={"id": user_id}, headers=headers)
        assert resp.status_code == 400 or resp.status_code == 401


class TestGetUserByEmail:
    """Test group for getting user by email functionality."""

    def test_get_user_by_email_success(self, client):
        """Success: get user by email."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": str(uuid.uuid4()),
        }
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query user by email with token
        response = client.get(f"/user/{unique_email}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == unique_email

    def test_get_user_by_email_not_found(self, client):
        """Fail: get user by non-existent email (with token)."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query non-existent email
        non_existent_email = f"nonexistent_{generate(size=8)}@example.com"
        response = client.get(f"/user/{non_existent_email}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_invalid_format(self, client):
        """Fail: get user with invalid email format (with token)."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query invalid email format
        invalid_email = "invalid-email-format"
        response = client.get(f"/user/{invalid_email}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_empty_string(self, client):
        """Fail: get user with empty email string (with token)."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query with empty string (should return 404)
        response = client.get("/user/", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_by_email_special_characters(self, client):
        """Fail: get user with email containing special characters (with token)."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query with special character email
        special_email = "test+special@example.com"
        response = client.get(f"/user/{special_email}", headers=headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_case_insensitive(self, client):
        """Success: get user with different email case (should be case-insensitive, with token)."""
        # Register and login to get token
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": str(uuid.uuid4()),
        }
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Query with uppercase email
        uppercase_email = unique_email.upper()
        response = client.get(f"/user/{uppercase_email}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert (
            data["data"]["email"] == unique_email
        )  # Original email should be preserved

    def test_get_user_by_email_anonymous_id_fail(self, client):
        """Fail: anonymous id cannot get user by email (should fail)."""
        anon_id = str(uuid.uuid4())
        unique_email = f"test_{generate(size=8)}@example.com"
        # Try to get user by email with id param (anonymous)
        resp = client.get(f"/user/{unique_email}", params={"id": anon_id})
        assert resp.status_code == 401 or resp.status_code == 404

    def test_get_user_by_email_after_register_id_fail(self, client):
        """Fail: cannot use id to get user by email after registration (should fail)."""
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        # Query with id param (should fail, no token)
        resp = client.get(f"/user/{unique_email}", params={"id": user_id})
        assert resp.status_code == 401 or resp.status_code == 404

    def test_get_user_by_email_anonymous_to_registered_transition(self, client):
        """Success: user not found before registration, found after registration (with token)."""
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        # Before registration (no token)
        resp = client.get(f"/user/{unique_email}")
        assert resp.status_code == 401
        # Register and login to get token
        user_data = {"email": unique_email, "password": "test123456", "id": user_id}
        client.post("/auth/register", json=user_data)
        login_data = {"email": unique_email, "password": "test123456"}
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # After registration (with token)
        resp = client.get(f"/user/{unique_email}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["email"] == unique_email
