import uuid

from fastapi import status
from nanoid import generate

from app.schemas.user import Role


class TestCaregiverTaskAPI:
    """Test group for caregiver operating carereceiver tasks."""

    def _register_and_login(self, client, user_id=None, role=Role.CARERECEIVER):
        email = f"caregiver_test_{generate(size=8)}@example.com"
        password = "test123456"
        if user_id is None:
            user_id = str(uuid.uuid4())
        user_data = {
            "email": email,
            "password": password,
            "id": user_id,
            "name": "Test User",
            "role": role,
        }
        reg = client.post("/auth/register", json=user_data)
        assert reg.status_code == status.HTTP_201_CREATED
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == status.HTTP_200_OK
        token = login.json()["access_token"]
        return email, token, user_id

    def _auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def _create_task(self, client, token, title="Take medicine", icon="💊"):
        req = {
            "title": title,
            "icon": icon,
            "reminder_time": {"hour": 8, "minute": 0},
            "recurrence": {"interval": 1, "unit": "DAY"},
        }
        resp = client.post("/tasks", json=req, headers=self._auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        return resp.json()

    def _link_users(self, client, caregiver_token, carereceiver_token):
        """Link caregiver and carereceiver"""
        # Generate invitation from caregiver
        resp = client.post(
            "/user/invitations/generate", headers=self._auth_headers(caregiver_token)
        )
        assert resp.status_code == status.HTTP_200_OK
        code = resp.json()["invitation_code"]

        # Accept invitation from carereceiver
        resp = client.post(
            f"/user/invitations/{code}/accept",
            headers=self._auth_headers(carereceiver_token),
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_caregiver_creates_task_for_carereceiver(self, client):
        """Caregiver should be able to create tasks for linked carereceiver"""
        # Register caregiver(be carereceiver before linking) and carereceiver
        caregiver_email, caregiver_token, caregiver_id = self._register_and_login(
            client, role=Role.CARERECEIVER
        )
        carereceiver_email, carereceiver_token, carereceiver_id = (
            self._register_and_login(client, role=Role.CARERECEIVER)
        )

        # Link them
        self._link_users(client, caregiver_token, carereceiver_token)

        # Caregiver creates task
        task_data = self._create_task(client, caregiver_token, "Take medicine", "💊")
        task_id = task_data["task"]["id"]

        # Verify task was created for carereceiver (not caregiver)
        # Get tasks as carereceiver
        resp = client.get("/tasks", headers=self._auth_headers(carereceiver_token))
        assert resp.status_code == status.HTTP_200_OK
        carereceiver_tasks = resp.json()["tasks"]
        assert len(carereceiver_tasks) == 1
        assert carereceiver_tasks[0]["id"] == task_id
        assert carereceiver_tasks[0]["title"] == "Take medicine"

        # Get tasks as caregiver (should see carereceiver's tasks)
        resp = client.get("/tasks", headers=self._auth_headers(caregiver_token))
        assert resp.status_code == status.HTTP_200_OK
        caregiver_tasks = resp.json()["tasks"]
        assert len(caregiver_tasks) == 1
        assert caregiver_tasks[0]["id"] == task_id
        assert caregiver_tasks[0]["title"] == "Take medicine"

    def test_caregiver_updates_task_for_carereceiver(self, client):
        """Caregiver should be able to update tasks for linked carereceiver"""
        # Register caregiver(be carereceiver before linking) and carereceiver
        caregiver_email, caregiver_token, caregiver_id = self._register_and_login(
            client, role=Role.CARERECEIVER
        )
        carereceiver_email, carereceiver_token, carereceiver_id = (
            self._register_and_login(client, role=Role.CARERECEIVER)
        )

        # Link them
        self._link_users(client, caregiver_token, carereceiver_token)

        # Carereceiver creates task
        task_data = self._create_task(client, carereceiver_token, "Take medicine", "💊")
        task_id = task_data["task"]["id"]

        # Caregiver updates the task
        update_req = {
            "title": "Take medicine updated",
            "reminder_time": {"hour": 9, "minute": 30},
        }
        resp = client.put(
            f"/tasks/{task_id}",
            json=update_req,
            headers=self._auth_headers(caregiver_token),
        )
        assert resp.status_code == status.HTTP_200_OK

        # Verify task was updated
        resp = client.get(
            f"/tasks/{task_id}", headers=self._auth_headers(caregiver_token)
        )
        assert resp.status_code == status.HTTP_200_OK
        updated_task = resp.json()["task"]
        assert updated_task["title"] == "Take medicine updated"
        assert updated_task["reminder_time"]["hour"] == 9
        assert updated_task["reminder_time"]["minute"] == 30

    def test_caregiver_deletes_task_for_carereceiver(self, client):
        """Caregiver should be able to delete tasks for linked carereceiver"""
        # Register caregiver(be carereceiver before linking) and carereceiver
        caregiver_email, caregiver_token, caregiver_id = self._register_and_login(
            client, role=Role.CARERECEIVER
        )
        carereceiver_email, carereceiver_token, carereceiver_id = (
            self._register_and_login(client, role=Role.CARERECEIVER)
        )

        # Link them
        self._link_users(client, caregiver_token, carereceiver_token)

        # Carereceiver creates task
        task_data = self._create_task(client, carereceiver_token, "Take medicine", "💊")
        task_id = task_data["task"]["id"]

        # Verify task exists for both users
        resp = client.get("/tasks", headers=self._auth_headers(caregiver_token))
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["tasks"]) == 1

        resp = client.get("/tasks", headers=self._auth_headers(carereceiver_token))
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["tasks"]) == 1

        # Caregiver deletes the task
        resp = client.delete(
            f"/tasks/{task_id}", headers=self._auth_headers(caregiver_token)
        )
        assert resp.status_code == status.HTTP_200_OK

        # Verify task was deleted for both users
        resp = client.get("/tasks", headers=self._auth_headers(caregiver_token))
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["tasks"]) == 0

        resp = client.get("/tasks", headers=self._auth_headers(carereceiver_token))
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["tasks"]) == 0

    def test_caregiver_without_linked_carereceiver_gets_no_tasks(self, client):
        """Caregiver without linked carereceiver should get no tasks"""
        # Register caregiver only
        caregiver_email, caregiver_token, caregiver_id = self._register_and_login(
            client, role=Role.CAREGIVER
        )

        # Try to get tasks
        resp = client.get("/tasks", headers=self._auth_headers(caregiver_token))
        assert resp.status_code == status.HTTP_200_OK
        tasks = resp.json()["tasks"]
        assert len(tasks) == 0

        # Try to create task (should fail)
        req = {
            "title": "Take medicine",
            "icon": "💊",
            "reminder_time": {"hour": 8, "minute": 0},
        }
        resp = client.post(
            "/tasks", json=req, headers=self._auth_headers(caregiver_token)
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "No linked carereceiver found for caregiver" in resp.json()["detail"]

    def test_caregiver_cannot_access_unlinked_carereceiver_tasks(self, client):
        """Caregiver should not be able to access unlinked carereceiver's tasks"""
        # Register caregiver and carereceiver
        caregiver_email, caregiver_token, caregiver_id = self._register_and_login(
            client, role=Role.CAREGIVER
        )
        carereceiver_email, carereceiver_token, carereceiver_id = (
            self._register_and_login(client, role=Role.CARERECEIVER)
        )

        # Carereceiver creates task (without linking)
        task_data = self._create_task(client, carereceiver_token, "Take medicine", "�")
        task_id = task_data["task"]["id"]

        # Caregiver should not see the task
        resp = client.get("/tasks", headers=self._auth_headers(caregiver_token))
        assert resp.status_code == status.HTTP_200_OK
        tasks = resp.json()["tasks"]
        assert len(tasks) == 0

        # Caregiver should not be able to access the task
        resp = client.get(
            f"/tasks/{task_id}", headers=self._auth_headers(caregiver_token)
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
