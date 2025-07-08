from fastapi import status
from nanoid import generate


class TestRegister:
    """Test group for user registration functionality."""

    def test_register_success(self, client):
        """Test successful user registration with unique email."""
        # Generate unique email to avoid conflicts
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == unique_email
        assert "id" in data["user"]
        assert data["user"]["anonymous_id"] is None

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        # First registration
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to register with same email
        response2 = client.post("/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response2.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        user_data = {
            "email": "invalid-email",
            "password": "test123456",
            "anonymous_id": None,
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Test registration with password too short."""
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {"email": unique_email, "password": "123", "anonymous_id": None}

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test group for user login functionality."""

    def test_login_success(self, client):
        """Test successful login."""
        # First register a user
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Then login
        login_data = {"email": unique_email, "password": "test123456"}
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_wrong_password(self, client):
        """Test login with existing user but wrong password."""
        # First register a user
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "anonymous_id": None,
        }

        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Try to login with wrong password
        login_data = {"email": unique_email, "password": "wrongpassword"}
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
