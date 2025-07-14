from app.schemas.user import Role
from tests.conftest import auth_headers


def get_links(client, token):
    return client.get("/user/links", headers=auth_headers(token))


def remove_link(client, token, user_email):
    return client.delete(f"/user/links/{user_email}", headers=auth_headers(token))


def create_link_by_invitation(client, inviter_token, invitee_token):
    resp = client.post(
        "/user/invitations/generate", headers=auth_headers(inviter_token)
    )
    assert resp.status_code == 200
    code = resp.json()["invitation_code"]
    resp2 = client.post(
        f"/user/invitations/{code}/accept", headers=auth_headers(invitee_token)
    )
    assert resp2.status_code == 200


class TestLinkAPI:
    def test_get_links_empty(self, client, register_user):
        """Should return empty list if no links exist."""
        _, token, _ = register_user(Role.CAREGIVER)
        resp = get_links(client, token)
        assert resp.status_code == 200
        assert resp.json()["data"]["links"] == []

    def test_get_links_after_link(self, client, register_user):
        """Should return linked user's email and name after linking."""
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)
        create_link_by_invitation(client, caregiver_token, carereceiver_token)
        resp = get_links(client, caregiver_token)
        assert resp.status_code == 200
        links = resp.json()["data"]["links"]
        assert any(link["email"] == carereceiver_email for link in links)
        assert all("name" in link for link in links)

    def test_remove_link_success(self, client, register_user):
        """Should remove link by email successfully."""
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)
        carereceiver_email, carereceiver_token, _ = register_user(Role.CARERECEIVER)
        create_link_by_invitation(client, caregiver_token, carereceiver_token)
        # Remove link from caregiver side
        resp = remove_link(client, caregiver_token, carereceiver_email)
        assert resp.status_code == 200
        assert "Link removed successfully" in resp.json()["data"]["message"]
        # After removal, links should be empty
        resp2 = get_links(client, caregiver_token)
        assert resp2.status_code == 200
        assert resp2.json()["data"]["links"] == []

    def test_remove_link_not_found(self, client, register_user):
        """Should return 404 if trying to remove a non-existent link."""
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)
        resp = remove_link(client, caregiver_token, "notfound@example.com")
        assert resp.status_code == 404

    def test_remove_link_user_not_found(self, client, register_user):
        """Should return 404 if email does not exist."""
        caregiver_email, caregiver_token, _ = register_user(Role.CAREGIVER)
        # Try to remove a link with a non-existent user
        resp = remove_link(client, caregiver_token, "noone@notfound.com")
        assert resp.status_code == 404
