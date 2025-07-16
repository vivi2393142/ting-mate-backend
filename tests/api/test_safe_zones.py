import logging

import pytest
from fastapi import status

from app.schemas.user import Role
from tests.conftest import auth_headers

logger = logging.getLogger(__name__)


@pytest.fixture
def register_and_link_users(client, register_user):
    """Register a carereceiver and caregiver, link them, and return their info."""
    cr_email, cr_token, cr_id = register_user(Role.CARERECEIVER)
    cg_email, cg_token, cg_id = register_user(Role.CAREGIVER)
    # caregiver generates invitation
    resp = client.post("/user/invitations/generate", headers=auth_headers(cg_token))
    code = resp.json()["invitation_code"]
    # carereceiver accepts invitation
    client.post(f"/user/invitations/{code}/accept", headers=auth_headers(cr_token))
    return {
        "carereceiver": {"email": cr_email, "token": cr_token, "id": cr_id},
        "caregiver": {"email": cg_email, "token": cg_token, "id": cg_id},
    }


class TestSafeZoneAPI:
    def test_carereceiver_create_safe_zone_success(self, client, register_user):
        """Carereceiver should be able to create safe zone."""
        email, token, _ = register_user(Role.CARERECEIVER)
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        resp = client.post(
            f"/safe-zone/{email}", json=safe_zone_data, headers=auth_headers(token)
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["location"]["name"] == "Home"
        assert data["radius"] == 1000

    def test_caregiver_create_safe_zone_for_linked_carereceiver(
        self, client, register_and_link_users
    ):
        """Caregiver should be able to create safe zone for linked carereceiver."""
        users = register_and_link_users
        caregiver = users["caregiver"]
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        resp = client.post(
            f"/safe-zone/{users['carereceiver']['email']}",
            json=safe_zone_data,
            headers=auth_headers(caregiver["token"]),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["location"]["name"] == "Home"
        assert data["radius"] == 1000

    def test_caregiver_create_safe_zone_no_linked_carereceiver(
        self, client, register_user
    ):
        """Caregiver should not be able to create safe zone without linked carereceiver."""
        _, token, _ = register_user(Role.CAREGIVER)
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        email, _, _ = register_user(Role.CAREGIVER)
        resp = client.post(
            f"/safe-zone/{email}", json=safe_zone_data, headers=auth_headers(token)
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_get_safe_zone_success(self, client, register_and_link_users):
        """Should get safe zone for carereceiver."""
        users = register_and_link_users
        carereceiver = users["carereceiver"]
        # Create safe zone first
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        client.post(
            f"/safe-zone/{carereceiver['email']}",
            json=safe_zone_data,
            headers=auth_headers(carereceiver["token"]),
        )
        # Get safe zone
        resp = client.get(
            f"/safe-zone/{carereceiver['email']}",
            headers=auth_headers(carereceiver["token"]),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["safe_zone"]["location"]["name"] == "Home"
        assert data["safe_zone"]["radius"] == 1000

    def test_caregiver_get_safe_zone_for_linked_carereceiver(
        self, client, register_and_link_users
    ):
        """Caregiver should be able to get safe zone for linked carereceiver."""
        users = register_and_link_users
        carereceiver = users["carereceiver"]
        caregiver = users["caregiver"]
        # Create safe zone first
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        client.post(
            f"/safe-zone/{carereceiver['email']}",
            json=safe_zone_data,
            headers=auth_headers(carereceiver["token"]),
        )
        # Get safe zone as caregiver
        resp = client.get(
            f"/safe-zone/{carereceiver['email']}",
            headers=auth_headers(caregiver["token"]),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["safe_zone"]["location"]["name"] == "Home"
        assert data["safe_zone"]["radius"] == 1000

    def test_update_safe_zone_success(self, client, register_and_link_users):
        """Should update safe zone successfully (using POST for upsert)."""
        users = register_and_link_users
        carereceiver = users["carereceiver"]
        # Create safe zone first
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        client.post(
            f"/safe-zone/{carereceiver['email']}",
            json=safe_zone_data,
            headers=auth_headers(carereceiver["token"]),
        )
        # Update safe zone (should use POST for upsert)
        updated_data = {
            "location": {
                "name": "Updated Home",
                "address": "456 New St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1500,
        }
        resp = client.post(
            f"/safe-zone/{carereceiver['email']}",
            json=updated_data,
            headers=auth_headers(carereceiver["token"]),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["location"]["name"] == "Updated Home"
        assert data["radius"] == 1500

    def test_delete_safe_zone_success(self, client, register_and_link_users):
        """Should delete safe zone successfully."""
        users = register_and_link_users
        carereceiver = users["carereceiver"]
        # Create safe zone first
        safe_zone_data = {
            "location": {
                "name": "Home",
                "address": "123 Main St, Bristol",
                "latitude": 51.4529183,
                "longitude": -2.5994918,
            },
            "radius": 1000,
        }
        client.post(
            f"/safe-zone/{carereceiver['email']}",
            json=safe_zone_data,
            headers=auth_headers(carereceiver["token"]),
        )
        # Delete safe zone
        resp = client.delete(
            f"/safe-zone/{carereceiver['email']}",
            headers=auth_headers(carereceiver["token"]),
        )
        assert resp.status_code == status.HTTP_200_OK
        logger.info("🤖 205, resp: %s", resp.json())
        assert "deleted successfully" in resp.json()["data"]["message"]
        # Verify safe zone is deleted
        resp2 = client.get(
            f"/safe-zone/{carereceiver['email']}",
            headers=auth_headers(carereceiver["token"]),
        )
        assert resp2.status_code == status.HTTP_200_OK
        # Should return safe_zone: None when safe zone is deleted but user has permission
        assert resp2.json()["safe_zone"] is None
