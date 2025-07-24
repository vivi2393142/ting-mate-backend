from app.schemas.user import Role
from tests.conftest import auth_headers


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
