from app.schemas.user import Role
from tests.conftest import auth_headers


def test_get_notification_after_create_task(client, register_user):
    _, token, _ = register_user(Role.CARERECEIVER)

    headers = auth_headers(token)

    # Create a task
    task_payload = {
        "title": "Test Notification Task",
        "icon": "check",
        "reminder_time": {"hour": 9, "minute": 0},
        "recurrence": None,
    }
    create_task_resp = client.post("/tasks", json=task_payload, headers=headers)
    assert create_task_resp.status_code == 200

    # Call /notifications and check notification exists
    response = client.get("/notifications", headers=headers)
    assert response.status_code == 200
    notif_list = response.json()
    assert any("created a new task" in n["message"] for n in notif_list)
