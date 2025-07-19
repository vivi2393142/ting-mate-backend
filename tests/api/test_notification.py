from tests.conftest import auth_headers


def test_notification_after_create_task(client, register_and_link_users):
    """Test notification is sent to group members when creating a task."""
    # Create linked users (caregiver and carereceiver)
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create task as caregiver
    task_payload = {
        "title": "Test Notification Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_task_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_task_resp.status_code == 200

    # Check that carereceiver receives notification
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("created a new task" in n["message"] for n in notif_list)


def test_notification_after_update_task(client, register_and_link_users):
    """Test notification is sent to group members when updating a task."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create task as caregiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["task"]["id"]

    # Update task as caregiver
    update_payload = {"title": "Updated Task Title"}
    update_resp = client.put(
        f"/tasks/{task_id}", json=update_payload, headers=auth_headers(caregiver_token)
    )
    assert update_resp.status_code == 200

    # Check that carereceiver receives update notification
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("updated task" in n["message"] for n in notif_list)


def test_notification_after_complete_task(client, register_and_link_users):
    """Test notification is sent to group members when completing a task."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create task as caregiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["task"]["id"]

    # Complete task as caregiver
    complete_payload = {"completed": True}
    complete_resp = client.put(
        f"/tasks/{task_id}/status",
        json=complete_payload,
        headers=auth_headers(caregiver_token),
    )
    assert complete_resp.status_code == 200

    # Check that carereceiver receives completion notification
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("marked" in n["message"] and "done" in n["message"] for n in notif_list)


def test_notification_after_delete_task(client, register_and_link_users):
    """Test notification is sent to group members when deleting a task."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create task as caregiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["task"]["id"]

    # Delete task as caregiver
    delete_resp = client.delete(
        f"/tasks/{task_id}", headers=auth_headers(caregiver_token)
    )
    assert delete_resp.status_code == 200

    # Check that carereceiver receives deletion notification
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("deleted task" in n["message"] for n in notif_list)


def test_notification_after_accept_invitation(client, register_user):
    """Test notification is sent when accepting an invitation."""
    # Register users without linking them
    cr_email, cr_token, cr_id = register_user("CARERECEIVER")
    cg_email, cg_token, cg_id = register_user("CAREGIVER")

    # Generate invitation as caregiver
    invite_resp = client.post(
        "/user/invitations/generate", headers=auth_headers(cg_token)
    )
    assert invite_resp.status_code == 200
    invitation_code = invite_resp.json()["invitation_code"]

    # Accept invitation as carereceiver
    accept_resp = client.post(
        f"/user/invitations/{invitation_code}/accept",
        headers=auth_headers(cr_token),
    )
    assert accept_resp.status_code == 200

    # Check that caregiver receives notification
    response = client.get("/notifications", headers=auth_headers(cg_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("linked with you" in n["message"] for n in notif_list)


def test_notification_after_safe_zone_violation(client, register_and_link_users):
    """Test notification is sent when carereceiver leaves safe zone."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]
    carereceiver_email = users["carereceiver"]["email"]

    # Create safe zone for carereceiver
    safe_zone_data = {
        "location": {
            "name": "Home",
            "address": "123 Main St, Bristol",
            "latitude": 51.4529183,
            "longitude": -2.5994918,
        },
        "radius": 1000,  # 1km radius
    }
    safe_zone_resp = client.post(
        f"/safe-zone/{carereceiver_email}",
        json=safe_zone_data,
        headers=auth_headers(caregiver_token),
    )
    assert safe_zone_resp.status_code == 200

    # Update carereceiver location to outside safe zone (far away)
    location_payload = {
        "latitude": 51.5000,  # Far from safe zone center
        "longitude": -2.6000,
    }
    location_resp = client.post(
        "/user/location",
        json=location_payload,
        headers=auth_headers(carereceiver_token),
    )
    assert location_resp.status_code == 200

    # Check that caregiver receives safe zone warning notification
    response = client.get("/notifications", headers=auth_headers(caregiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert any("has left the safe zone" in n["message"] for n in notif_list)


def test_no_notification_when_within_safe_zone(client, register_and_link_users):
    """Test no notification is sent when carereceiver is within safe zone."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]
    carereceiver_email = users["carereceiver"]["email"]

    # Create safe zone for carereceiver
    safe_zone_data = {
        "location": {
            "name": "Home",
            "address": "123 Main St, Bristol",
            "latitude": 51.4529183,
            "longitude": -2.5994918,
        },
        "radius": 1000,  # 1km radius
    }
    safe_zone_resp = client.post(
        f"/safe-zone/{carereceiver_email}",
        json=safe_zone_data,
        headers=auth_headers(caregiver_token),
    )
    assert safe_zone_resp.status_code == 200

    # Update carereceiver location to within safe zone
    location_payload = {
        "latitude": 51.4529183,  # Same as safe zone center
        "longitude": -2.5994918,
    }
    location_resp = client.post(
        "/user/location",
        json=location_payload,
        headers=auth_headers(carereceiver_token),
    )
    assert location_resp.status_code == 200

    # Check that caregiver does not receive safe zone warning notification
    response = client.get("/notifications", headers=auth_headers(caregiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert not any("has left the safe zone" in n["message"] for n in notif_list)


def test_mark_notifications_as_read(client, register_and_link_users):
    """Test marking notifications as read."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create a task to generate notification
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200

    # Get notifications for carereceiver
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert len(notif_list) > 0

    # Get notification IDs to mark as read
    notification_ids = [notif["id"] for notif in notif_list]

    # Mark notifications as read
    mark_read_resp = client.put(
        "/notifications/mark-read",
        json=notification_ids,
        headers=auth_headers(carereceiver_token),
    )
    assert mark_read_resp.status_code == 200
    mark_read_data = mark_read_resp.json()
    assert mark_read_data["success"] is True
    assert "data" in mark_read_data
    data = mark_read_data["data"]
    assert data["marked_count"] == len(notification_ids)
    assert data["total_count"] == len(notification_ids)

    # Verify notifications are marked as read
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    for notif in notif_list:
        if notif["id"] in notification_ids:
            assert notif["is_read"] is True


def test_mark_notifications_as_read_empty_list(client, register_and_link_users):
    """Test marking notifications as read with empty list."""
    # Create linked users
    users = register_and_link_users
    carereceiver_token = users["carereceiver"]["token"]

    # Try to mark empty list as read
    mark_read_resp = client.put(
        "/notifications/mark-read",
        json=[],
        headers=auth_headers(carereceiver_token),
    )
    assert mark_read_resp.status_code == 400
    assert "empty" in mark_read_resp.json()["detail"]


def test_mark_notifications_as_read_invalid_id(client, register_and_link_users):
    """Test marking notifications as read with invalid notification ID."""
    # Create linked users
    users = register_and_link_users
    carereceiver_token = users["carereceiver"]["token"]

    # Try to mark non-existent notification as read
    mark_read_resp = client.put(
        "/notifications/mark-read",
        json=["invalid-notification-id"],
        headers=auth_headers(carereceiver_token),
    )
    assert mark_read_resp.status_code == 404
    assert "not found" in mark_read_resp.json()["detail"]


def test_mark_notifications_as_read_unauthorized(client, register_and_link_users):
    """Test marking notifications as read for notifications that don't belong to user."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create a task to generate notification for carereceiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200

    # Get notifications for carereceiver
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert len(notif_list) > 0

    # Try to mark carereceiver's notification as read using caregiver token
    notification_ids = [notif["id"] for notif in notif_list]
    mark_read_resp = client.put(
        "/notifications/mark-read",
        json=notification_ids,
        headers=auth_headers(caregiver_token),
    )
    assert mark_read_resp.status_code == 403
    assert "does not belong to current user" in mark_read_resp.json()["detail"]


def test_notification_disabled_by_reminder_settings(client, register_and_link_users):
    """Test that notifications are not sent when disabled in reminder settings."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Disable task notifications for carereceiver
    reminder_settings = {
        "task_reminder": False,
        "task_change_notification": False,
        "task_completion_notification": False,
        "safe_zone_exit_reminder": False,
        "overdue_reminder": {"enabled": False, "delay_minutes": 30, "repeat": False},
    }

    settings_resp = client.put(
        "/user/settings",
        json={"reminder": reminder_settings},
        headers=auth_headers(carereceiver_token),
    )
    assert settings_resp.status_code == 200

    # Create task as caregiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200

    # Check that carereceiver does NOT receive notification (disabled)
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert not any("created a new task" in n["message"] for n in notif_list)


def test_safe_zone_notification_disabled_by_reminder_settings(
    client, register_and_link_users
):
    """Test that safe zone notifications are not sent when disabled in reminder settings."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]
    carereceiver_email = users["carereceiver"]["email"]

    # Disable safe zone notifications for caregiver
    reminder_settings = {
        "task_reminder": True,
        "task_change_notification": True,
        "task_completion_notification": True,
        "safe_zone_exit_reminder": False,  # Disable safe zone notifications
        "overdue_reminder": {"enabled": True, "delay_minutes": 30, "repeat": True},
    }

    settings_resp = client.put(
        "/user/settings",
        json={"reminder": reminder_settings},
        headers=auth_headers(caregiver_token),
    )
    assert settings_resp.status_code == 200

    # Create safe zone for carereceiver
    safe_zone_data = {
        "location": {
            "name": "Home",
            "address": "123 Main St, Bristol",
            "latitude": 51.4529183,
            "longitude": -2.5994918,
        },
        "radius": 1000,  # 1km radius
    }
    safe_zone_resp = client.post(
        f"/safe-zone/{carereceiver_email}",
        json=safe_zone_data,
        headers=auth_headers(caregiver_token),
    )
    assert safe_zone_resp.status_code == 200

    # Update carereceiver location to outside safe zone
    location_payload = {
        "latitude": 51.5000,  # Far from safe zone center
        "longitude": -2.6000,
    }
    location_resp = client.post(
        "/user/location",
        json=location_payload,
        headers=auth_headers(carereceiver_token),
    )
    assert location_resp.status_code == 200

    # Check that caregiver does NOT receive safe zone notification (disabled)
    response = client.get("/notifications", headers=auth_headers(caregiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    assert not any("has left the safe zone" in n["message"] for n in notif_list)


def test_get_notifications_with_total_count(client, register_and_link_users):
    """Test that notifications API returns total count in response."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create multiple tasks to generate notifications
    for i in range(3):
        task_payload = {
            "title": f"Test Task {i+1}",
            "icon": "check",
            "reminder_time": {"hour": 9, "minute": 0},
            "recurrence": None,
        }
        create_resp = client.post(
            "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
        )
        assert create_resp.status_code == 200

    # Get notifications for carereceiver
    response = client.get("/notifications", headers=auth_headers(carereceiver_token))
    assert response.status_code == 200
    response_data = response.json()

    # Check response structure
    assert "notifications" in response_data
    assert "total" in response_data
    assert "limit" in response_data
    assert "offset" in response_data

    # Check that total count is correct
    assert response_data["total"] >= 3  # Should have at least 3 notifications
    assert (
        len(response_data["notifications"]) <= response_data["limit"]
    )  # Should respect limit

    # Check pagination info
    assert response_data["limit"] == 50  # Default limit
    assert response_data["offset"] == 0  # Default offset


def test_get_notifications_pagination(client, register_and_link_users):
    """Test notifications API pagination with limit and offset."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]
    carereceiver_token = users["carereceiver"]["token"]

    # Create multiple tasks to generate notifications
    for i in range(5):
        task_payload = {
            "title": f"Test Task {i+1}",
            "icon": "check",
            "reminder_time": {"hour": 9, "minute": 0},
            "recurrence": None,
        }
        create_resp = client.post(
            "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
        )
        assert create_resp.status_code == 200

    # Get first page with limit 2
    response = client.get(
        "/notifications?limit=2&offset=0", headers=auth_headers(carereceiver_token)
    )
    assert response.status_code == 200
    response_data = response.json()

    assert response_data["total"] >= 5
    assert len(response_data["notifications"]) == 2
    assert response_data["limit"] == 2
    assert response_data["offset"] == 0

    # Get second page
    response2 = client.get(
        "/notifications?limit=2&offset=2", headers=auth_headers(carereceiver_token)
    )
    assert response2.status_code == 200
    response_data2 = response2.json()

    assert response_data2["total"] >= 5
    assert len(response_data2["notifications"]) == 2
    assert response_data2["limit"] == 2
    assert response_data2["offset"] == 2

    # Verify different notifications (should not overlap)
    first_page_ids = {n["id"] for n in response_data["notifications"]}
    second_page_ids = {n["id"] for n in response_data2["notifications"]}
    assert first_page_ids.isdisjoint(second_page_ids)  # No overlap


def test_no_self_notification(client, register_and_link_users):
    """Test that users don't receive notifications for their own actions."""
    # Create linked users
    users = register_and_link_users
    caregiver_token = users["caregiver"]["token"]

    # Create task as caregiver
    task_payload = {
        "title": "Test Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_resp = client.post(
        "/tasks", json=task_payload, headers=auth_headers(caregiver_token)
    )
    assert create_resp.status_code == 200

    # Check that caregiver doesn't receive notification for their own action
    response = client.get("/notifications", headers=auth_headers(caregiver_token))
    assert response.status_code == 200
    response_data = response.json()
    assert "notifications" in response_data
    notif_list = response_data["notifications"]
    # Should not have any notifications for own actions
    assert not any("created a new task" in n["message"] for n in notif_list)
