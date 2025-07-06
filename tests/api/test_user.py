import uuid

from fastapi import status


class TestGetCurrentUser:
    """Test group for getting current user functionality."""

    def test_get_current_user_success(self, client):
        """Test successful retrieval of current user with valid token."""
        # First register a user
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
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
        assert data["anonymous_id"] is None

    def test_get_current_user_no_token(self, client):
        """Test getting current user without authentication token."""
        response = client.get("/user/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"]

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"]

    def test_get_current_user_malformed_token(self, client):
        """Test getting current user with malformed authorization header."""
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/user/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUserByEmail:
    """Test group for getting user by email functionality."""

    def test_get_user_by_email_success(self, client):
        """Test successful retrieval of user by email."""
        # First register a user
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Get user by email
        response = client.get(f"/user/{unique_email}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == unique_email
        assert "id" in data
        assert data["anonymous_id"] is None

    def test_get_user_by_email_not_found(self, client):
        """Test getting user by non-existent email."""
        non_existent_email = f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
        response = client.get(f"/user/{non_existent_email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_invalid_format(self, client):
        """Test getting user with invalid email format."""
        invalid_email = "invalid-email-format"
        response = client.get(f"/user/{invalid_email}")
        # This should still work as the endpoint accepts any string as email parameter
        # The validation happens in the service layer
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_empty_string(self, client):
        """Test getting user with empty email string."""
        response = client.get("/user/")
        # This should return 404 as FastAPI will not match the route
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_by_email_special_characters(self, client):
        """Test getting user with email containing special characters."""
        special_email = "test+special@example.com"
        response = client.get(f"/user/{special_email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_by_email_case_insensitive(self, client):
        """Test getting user with different email case (should be case-insensitive)."""
        # First register a user with lowercase email
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Try to get user with uppercase email
        uppercase_email = unique_email.upper()
        response = client.get(f"/user/{uppercase_email}")

        # This should succeed as email matching is case-insensitive
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == unique_email  # Original email should be preserved
        assert "id" in data
