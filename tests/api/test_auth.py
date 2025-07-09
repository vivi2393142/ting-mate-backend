import uuid

from fastapi import status
from nanoid import generate

from app.schemas.user import Role


class TestRegister:
    """Test group for user registration functionality."""

    def test_register_missing_id(self, client):
        """Fail: registration fails if id is missing."""
        user_data = {
            "email": "a@b.com",
            "password": "test123456",
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_upgrade_anonymous(self, client):
        """Success: register upgrades anonymous user if id exists without email."""
        anon_id = str(uuid.uuid4())
        from app.services.user import create_anonymous_user

        create_anonymous_user(anon_id)
        unique_email = f"test_{generate(size=8)}@example.com"
        user_data = {
            "email": unique_email,
            "password": "test123456",
            "id": anon_id,
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user"]["email"] == unique_email
        assert data["user"]["id"] == anon_id
        assert data["user"]["role"] == Role.CARERECEIVER

    def test_register_duplicate_id(self, client):
        """Fail: registration fails if id is already registered."""
        unique_email1 = f"test_{generate(size=8)}@example.com"
        unique_email2 = f"test_{generate(size=8)}@example.com"
        user_id = str(uuid.uuid4())
        user_data1 = {
            "email": unique_email1,
            "password": "test123456",
            "id": user_id,
            "role": Role.CARERECEIVER,
        }
        user_data2 = {
            "email": unique_email2,
            "password": "test123456",
            "id": user_id,
            "role": Role.CARERECEIVER,
        }
        response1 = client.post("/auth/register", json=user_data1)
        assert response1.status_code == 201
        response2 = client.post("/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "User id already registered" in response2.json()["detail"]

    def test_register_missing_password(self, client):
        """Fail: registration fails if password is missing."""
        user_data = {
            "email": f"test_{generate(size=8)}@example.com",
            "id": str(uuid.uuid4()),
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_missing_email(self, client):
        """Fail: registration fails if email is missing."""
        user_data = {
            "password": "test123456",
            "id": str(uuid.uuid4()),
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_invalid_id_format(self, client):
        """Fail: registration fails if id is not a valid UUID."""
        user_data = {
            "email": f"test_{generate(size=8)}@example.com",
            "password": "test123456",
            "id": "not-a-uuid",
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Invalid UUID format" in response.json()["detail"]

    def test_register_invalid_email_format(self, client):
        """Fail: registration fails if email is not valid."""
        user_data = {
            "email": "not-an-email",
            "password": "test123456",
            "id": str(uuid.uuid4()),
            "role": Role.CARERECEIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_duplicate_email(self, client):
        """Fail: registration fails if email is already registered."""
        unique_email = f"test_{generate(size=8)}@example.com"
        user_id1 = str(uuid.uuid4())
        user_id2 = str(uuid.uuid4())
        user_data1 = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id1,
            "role": Role.CARERECEIVER,
        }
        user_data2 = {
            "email": unique_email,
            "password": "test123456",
            "id": user_id2,
            "role": Role.CARERECEIVER,
        }
        response1 = client.post("/auth/register", json=user_data1)
        assert response1.status_code == 201
        response2 = client.post("/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_register_fail_missing_role(self, client):
        """Fail: registration fails if role is missing."""
        user_data = {
            "email": f"test_{generate(size=8)}@example.com",
            "password": "test123456",
            "id": str(uuid.uuid4()),
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

    def test_register_fail_invalid_role(self, client):
        """Fail: registration fails if role is not a valid value."""
        user_data = {
            "email": f"test_{generate(size=8)}@example.com",
            "password": "test123456",
            "id": str(uuid.uuid4()),
            "role": "INVALID_ROLE",
        }
        response = client.post("/auth/register", json=user_data)
        # 422 if schema validation, 400 if backend validation
        assert response.status_code in (400, 422)

    def test_register_success_caregiver_role(self, client):
        """Success: registration succeeds if role is CAREGIVER."""
        user_data = {
            "email": f"test_{generate(size=8)}@example.com",
            "password": "test123456",
            "id": str(uuid.uuid4()),
            "role": Role.CAREGIVER,
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201 or response.status_code == 201
        data = response.json()
        assert data["user"]["role"] == Role.CAREGIVER


class TestLogin:
    """Test group for user login functionality."""

    def test_login_success(self, client):
        """Success: login with correct credentials."""
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

        # Then login
        login_data = {"email": unique_email, "password": "test123456"}
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None

    def test_login_fail_invalid_credentials(self, client):
        """Fail: login with invalid credentials."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_fail_wrong_password(self, client):
        """Fail: login with existing user but wrong password."""
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

        # Try to login with wrong password
        login_data = {"email": unique_email, "password": "wrongpassword"}
        response = client.post("/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
