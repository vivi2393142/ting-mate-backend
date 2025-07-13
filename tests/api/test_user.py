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
        # New fields
        assert "emergency_contacts" in settings
        assert settings["emergency_contacts"] is None or isinstance(
            settings["emergency_contacts"], list
        )
        assert "safe_zone" in settings
        assert settings["safe_zone"] is None or isinstance(settings["safe_zone"], dict)
        assert "allow_share_location" in settings
        assert isinstance(settings["allow_share_location"], bool)
        assert "show_linked_location" in settings
        assert isinstance(settings["show_linked_location"], bool)

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
        # New fields with default values
        assert settings["emergency_contacts"] is None
        assert settings["safe_zone"] is None
        assert settings["allow_share_location"] is False
        assert settings["show_linked_location"] is False

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
        """Fail: no id and no token should fail."""
        resp = client.get("/user/me")
        assert resp.status_code == 400

    def test_get_current_user_both_id_and_token_fail(self, client):
        """Fail: both id and token should fail."""
        anon_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer invalid_token"}
        resp = client.get("/user/me", params={"id": anon_id}, headers=headers)
        assert resp.status_code == 400


class TestUpdateUserSettings:
    """Test group for updating user settings functionality."""

    def test_update_user_settings_success(self, client, register_user):
        """Success: update user settings with valid data."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # Update settings
        update_data = {
            "name": "Test User",
            "textSize": UserTextSize.LARGE,
            "displayMode": UserDisplayMode.SIMPLE,
            "reminder": {
                "taskTimeReminder": True,
                "overdueReminder": {
                    "enabled": True,
                    "delayMinutes": 10,
                    "repeat": False,
                },
                "safeZoneReminder": False,
            },
        }

        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["email"] == email
        assert data["role"] == "CARERECEIVER"

        settings = data["settings"]
        assert settings["name"] == "Test User"
        assert settings["textSize"] == UserTextSize.LARGE
        assert settings["displayMode"] == UserDisplayMode.SIMPLE
        assert settings["reminder"] == {
            "taskTimeReminder": True,
            "overdueReminder": {"enabled": True, "delayMinutes": 10, "repeat": False},
            "safeZoneReminder": False,
        }

    def test_update_user_settings_partial_update(self, client, register_user):
        """Success: update only some settings fields."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # Update only name
        update_data = {"name": "New Name"}

        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["name"] == "New Name"
        # Other fields should remain unchanged
        assert settings["textSize"] == UserTextSize.STANDARD
        assert settings["displayMode"] == UserDisplayMode.FULL
        assert settings["reminder"] is None

    def test_update_user_settings_no_authentication(self, client):
        """Fail: update settings without authentication."""
        update_data = {"name": "Test User"}
        response = client.put("/user/settings", json=update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_user_settings_invalid_token(self, client):
        """Fail: update settings with invalid token."""
        update_data = {"name": "Test User"}
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.put("/user/settings", json=update_data, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_user_settings_invalid_text_size(self, client, register_user):
        """Fail: update settings with invalid text size."""
        _, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"textSize": "INVALID_SIZE"}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_user_settings_invalid_display_mode(self, client, register_user):
        """Fail: update settings with invalid display mode."""
        _, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"displayMode": "INVALID_MODE"}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_user_settings_empty_request(self, client, register_user):
        """Success: update settings with empty request (no changes)."""
        email, token, _ = register_user(Role.CARERECEIVER)

        # Get initial settings
        initial_response = client.get("/user/me", headers=auth_headers(token))
        initial_data = initial_response.json()

        # Update with empty request
        response = client.put("/user/settings", json={}, headers=auth_headers(token))
        assert response.status_code == status.HTTP_200_OK

        # Settings should remain the same
        data = response.json()
        assert data["settings"] == initial_data["settings"]

    def test_update_user_settings_complex_reminder(self, client, register_user):
        """Success: update settings with complex reminder object."""
        email, token, _ = register_user(Role.CARERECEIVER)

        complex_reminder = {
            "taskTimeReminder": False,
            "overdueReminder": {"enabled": True, "delayMinutes": 5, "repeat": True},
            "safeZoneReminder": True,
        }

        update_data = {"reminder": complex_reminder}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["reminder"] == complex_reminder

    def test_update_user_settings_null_reminder(self, client, register_user):
        """Success: set reminder to null."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"reminder": None}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["reminder"] is None

    def test_update_user_settings_all_fields(self, client, register_user):
        """Success: update all settings fields at once."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {
            "name": "Complete Test User",
            "textSize": UserTextSize.LARGE,
            "displayMode": UserDisplayMode.SIMPLE,
            "reminder": {
                "taskTimeReminder": False,
                "overdueReminder": {
                    "enabled": False,
                    "delayMinutes": 15,
                    "repeat": True,
                },
                "safeZoneReminder": True,
            },
        }

        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["name"] == "Complete Test User"
        assert settings["textSize"] == UserTextSize.LARGE
        assert settings["displayMode"] == UserDisplayMode.SIMPLE
        assert settings["reminder"] == {
            "taskTimeReminder": False,
            "overdueReminder": {"enabled": False, "delayMinutes": 15, "repeat": True},
            "safeZoneReminder": True,
        }

    def test_update_user_settings_anonymous_user(self, client):
        """Success: update settings for anonymous user."""
        anon_id = str(uuid.uuid4())

        # First create anonymous user
        client.get("/user/me", params={"id": anon_id})

        # Update settings
        update_data = {"name": "Anonymous User"}
        response = client.put(
            "/user/settings", json=update_data, params={"id": anon_id}
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["name"] == "Anonymous User"

    def test_update_user_settings_emergency_contacts(self, client, register_user):
        """Success: update emergency contacts."""
        email, token, _ = register_user(Role.CARERECEIVER)

        emergency_contacts = [
            {
                "id": "contact-1",
                "name": "Emergency Contact 1",
                "phone": "+1234567890",
                "methods": ["PHONE", "WHATSAPP"],
            },
            {
                "id": "contact-2",
                "name": "Emergency Contact 2",
                "phone": "+0987654321",
                "methods": ["PHONE"],
            },
        ]

        update_data = {"emergency_contacts": emergency_contacts}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )

        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["emergency_contacts"] == emergency_contacts

    def test_update_user_settings_safe_zone(self, client, register_user):
        """Success: update safe zone."""
        email, token, _ = register_user(Role.CARERECEIVER)

        safe_zone = {"latitude": 51.4529183, "longitude": -2.5994918, "radius": 1000}

        update_data = {"safe_zone": safe_zone}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["safe_zone"] == safe_zone

    def test_update_user_settings_location_sharing(self, client, register_user):
        """Success: update location sharing settings."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"allow_share_location": True, "show_linked_location": False}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["allow_share_location"] is True
        assert settings["show_linked_location"] is False

    def test_update_user_settings_all_new_fields(self, client, register_user):
        """Success: update all new fields at once."""
        email, token, _ = register_user(Role.CARERECEIVER)

        emergency_contacts = [
            {
                "id": "contact-1",
                "name": "Emergency Contact",
                "phone": "+1234567890",
                "methods": ["PHONE"],
            }
        ]

        safe_zone = {"latitude": 51.4529183, "longitude": -2.5994918, "radius": 500}

        update_data = {
            "name": "Test User",
            "emergency_contacts": emergency_contacts,
            "safe_zone": safe_zone,
            "allow_share_location": True,
            "show_linked_location": True,
        }

        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["name"] == "Test User"
        assert settings["emergency_contacts"] == emergency_contacts
        assert settings["safe_zone"] == safe_zone
        assert settings["allow_share_location"] is True
        assert settings["show_linked_location"] is True

    def test_update_user_settings_null_emergency_contacts(self, client, register_user):
        """Success: set emergency_contacts to null."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"emergency_contacts": None}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["emergency_contacts"] is None

    def test_update_user_settings_null_safe_zone(self, client, register_user):
        """Success: set safe_zone to null."""
        email, token, _ = register_user(Role.CARERECEIVER)

        update_data = {"safe_zone": None}
        response = client.put(
            "/user/settings", json=update_data, headers=auth_headers(token)
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        settings = data["settings"]
        assert settings["safe_zone"] is None
