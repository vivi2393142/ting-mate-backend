import pytest
from fastapi import status

from app.schemas.user import Role


@pytest.fixture
def register_and_link_users(client, register_user):
    # Create a carereceiver and a caregiver, and link them
    cr_email, cr_token, cr_id = register_user(Role.CARERECEIVER)
    cg_email, cg_token, cg_id = register_user(Role.CAREGIVER)
    # carereceiver enables allow_share_location
    client.put(
        "/user/settings",
        json={"allow_share_location": True},
        headers={"Authorization": f"Bearer {cr_token}"},
    )
    # caregiver enables show_linked_location
    client.put(
        "/user/settings",
        json={"show_linked_location": True},
        headers={"Authorization": f"Bearer {cg_token}"},
    )
    # caregiver generates invitation
    resp = client.post(
        "/user/invitations/generate", headers={"Authorization": f"Bearer {cg_token}"}
    )
    code = resp.json()["invitation_code"]
    # carereceiver accepts invitation
    client.post(
        f"/user/invitations/{code}/accept",
        headers={"Authorization": f"Bearer {cr_token}"},
    )
    return {
        "carereceiver": {"email": cr_email, "token": cr_token, "id": cr_id},
        "caregiver": {"email": cg_email, "token": cg_token, "id": cg_id},
    }


def test_carereceiver_update_location_success(client, register_and_link_users):
    cr = register_and_link_users["carereceiver"]
    location = {"latitude": 25.03, "longitude": 121.56}
    resp = client.post(
        "/user/location",
        json=location,
        headers={"Authorization": f"Bearer {cr['token']}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["latitude"] == location["latitude"]
    assert data["longitude"] == location["longitude"]


def test_carereceiver_update_location_no_permission(client, register_user):
    cr_email, cr_token, _ = register_user(Role.CARERECEIVER)
    # Not enabling allow_share_location
    location = {"latitude": 25.03, "longitude": 121.56}
    resp = client.post(
        "/user/location", json=location, headers={"Authorization": f"Bearer {cr_token}"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_caregiver_get_linked_location_success(client, register_and_link_users):
    cr = register_and_link_users["carereceiver"]
    cg = register_and_link_users["caregiver"]
    # carereceiver uploads location first
    location = {"latitude": 25.03, "longitude": 121.56}
    client.post(
        "/user/location",
        json=location,
        headers={"Authorization": f"Bearer {cr['token']}"},
    )
    # caregiver queries
    resp = client.get(
        f"/user/linked-location/{cr['email']}",
        headers={"Authorization": f"Bearer {cg['token']}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["latitude"] == location["latitude"]
    assert data["longitude"] == location["longitude"]


def test_caregiver_get_linked_location_no_link(client, register_user):
    cr_email, cr_token, _ = register_user(Role.CARERECEIVER)
    cg_email, cg_token, _ = register_user(Role.CAREGIVER)
    # carereceiver enables allow_share_location
    client.put(
        "/user/settings",
        json={"allow_share_location": True},
        headers={"Authorization": f"Bearer {cr_token}"},
    )
    # caregiver enables show_linked_location
    client.put(
        "/user/settings",
        json={"show_linked_location": True},
        headers={"Authorization": f"Bearer {cg_token}"},
    )
    # caregiver queries a carereceiver who is not linked
    resp = client.get(
        f"/user/linked-location/{cr_email}",
        headers={"Authorization": f"Bearer {cg_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_caregiver_get_linked_location_no_permission(client, register_and_link_users):
    cr = register_and_link_users["carereceiver"]
    cg = register_and_link_users["caregiver"]
    # caregiver disables show_linked_location
    client.put(
        "/user/settings",
        json={"show_linked_location": False},
        headers={"Authorization": f"Bearer {cg['token']}"},
    )
    resp = client.get(
        f"/user/linked-location/{cr['email']}",
        headers={"Authorization": f"Bearer {cg['token']}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_caregiver_get_linked_location_cr_no_share(client, register_and_link_users):
    cr = register_and_link_users["carereceiver"]
    cg = register_and_link_users["caregiver"]
    # carereceiver disables allow_share_location
    client.put(
        "/user/settings",
        json={"allow_share_location": False},
        headers={"Authorization": f"Bearer {cr['token']}"},
    )
    resp = client.get(
        f"/user/linked-location/{cr['email']}",
        headers={"Authorization": f"Bearer {cg['token']}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_caregiver_get_linked_location_not_found(client, register_and_link_users):
    cg = register_and_link_users["caregiver"]
    # Query a non-existent email
    resp = client.get(
        "/user/linked-location/notfound@email.com",
        headers={"Authorization": f"Bearer {cg['token']}"},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_carereceiver_cannot_get_linked_location(client, register_and_link_users):
    cr = register_and_link_users["carereceiver"]
    # carereceiver tries to query linked location
    resp = client.get(
        f"/user/linked-location/{cr['email']}",
        headers={"Authorization": f"Bearer {cr['token']}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
