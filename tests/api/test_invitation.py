import uuid

import pytest
from fastapi import status
from nanoid import generate

from app.schemas.user import Role


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


def create_invitation(client, token):
    resp = client.post("/user/invitations/generate", headers=auth_headers(token))
    assert resp.status_code == 200
    return resp.json()["invitation_code"]


def get_invitation_info(client, code, token):
    return client.get(f"/user/invitations/{code}", headers=auth_headers(token))


def accept_invitation(client, code, token):
    return client.post(f"/user/invitations/{code}/accept", headers=auth_headers(token))


def cancel_invitation(client, code, token):
    return client.delete(f"/user/invitations/{code}", headers=auth_headers(token))


class TestInvitationAPI:
    def test_generate_and_get_invitation(self, client, register_user):
        """Should generate and fetch invitation info successfully."""
        _, token, _ = register_user(Role.CAREGIVER)
        code = create_invitation(client, token)
        resp = get_invitation_info(client, code, token)
        assert resp.status_code == 200
        data = resp.json()
        assert "inviter_name" in data
        assert "inviter_role" in data
        assert "expires_at" in data

    def test_get_invitation_not_found(self, client, register_user):
        _, token, _ = register_user(Role.CAREGIVER)
        resp = get_invitation_info(client, "NONEXIST", token)
        assert resp.status_code == 404

    def test_accept_invitation_role_check(self, client, register_user):
        """Caregiver can only link carereceiver and vice versa."""
        # Caregiver invites, carereceiver accepts (should succeed)
        _, caregiver_token, _ = register_user(Role.CAREGIVER)
        code = create_invitation(client, caregiver_token)
        _, carereceiver_token, _ = register_user(Role.CARERECEIVER)
        resp = accept_invitation(client, code, carereceiver_token)
        assert resp.status_code == 200
        # Carereceiver invites, caregiver accepts (should succeed)
        _, carereceiver_token2, _ = register_user(Role.CARERECEIVER)
        code2 = create_invitation(client, carereceiver_token2)
        _, caregiver_token2, _ = register_user(Role.CAREGIVER)
        resp2 = accept_invitation(client, code2, caregiver_token2)
        assert resp2.status_code == 200
        # Caregiver invites, caregiver accepts (should fail)
        _, caregiver_token3, _ = register_user(Role.CAREGIVER)
        code3 = create_invitation(client, caregiver_token3)
        _, caregiver_token4, _ = register_user(Role.CAREGIVER)
        resp3 = accept_invitation(client, code3, caregiver_token4)
        assert resp3.status_code == 400
        # Carereceiver invites, carereceiver accepts (should fail)
        _, carereceiver_token3, _ = register_user(Role.CARERECEIVER)
        code4 = create_invitation(client, carereceiver_token3)
        _, carereceiver_token4, _ = register_user(Role.CARERECEIVER)
        resp4 = accept_invitation(client, code4, carereceiver_token4)
        assert resp4.status_code == 400

    def test_accept_invitation_not_found(self, client, register_user):
        _, token, _ = register_user(Role.CAREGIVER)
        resp = accept_invitation(client, "NONEXIST", token)
        assert resp.status_code == 404

    def test_cancel_invitation_by_inviter(self, client, register_user):
        _, token, _ = register_user(Role.CAREGIVER)
        code = create_invitation(client, token)
        resp = cancel_invitation(client, code, token)
        assert resp.status_code == 200
        assert "Invitation cancelled successfully" in resp.json()["data"]["message"]

    def test_cancel_invitation_by_non_inviter(self, client, register_user):
        _, token, _ = register_user(Role.CAREGIVER)
        code = create_invitation(client, token)
        _, other_token, _ = register_user(Role.CAREGIVER)
        resp = cancel_invitation(client, code, other_token)
        assert resp.status_code == 403

    def test_cancel_invitation_not_found(self, client, register_user):
        _, token, _ = register_user(Role.CAREGIVER)
        resp = cancel_invitation(client, "NONEXIST", token)
        assert resp.status_code == 404
