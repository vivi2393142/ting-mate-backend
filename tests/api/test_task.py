from fastapi import status
from nanoid import generate


class TestTaskAPI:
    """Test group for task API endpoints (CRUD, status, error, edge cases)."""

    def _register_and_login(self, client):
        email = f"task_{generate(size=8)}@example.com"
        password = "test123456"
        user_data = {"email": email, "password": password, "anonymous_id": None}
        reg = client.post("/auth/register", json=user_data)
        assert reg.status_code == status.HTTP_201_CREATED
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == status.HTTP_200_OK
        token = login.json()["access_token"]
        return email, token

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

    def _get_response_data(self, response):
        """Extract data from BaseResponse format"""
        data = response.json()
        if "data" in data and "result" in data["data"]:
            return data["data"]["result"]
        elif "data" in data:
            return data["data"]
        return data

    def test_create_and_get_tasks(self, client):
        """Test creating a task and retrieving it via /tasks."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        # List tasks
        resp = client.get("/tasks", headers=self._auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        response_data = self._get_response_data(resp)
        tasks = response_data["tasks"] if "tasks" in response_data else response_data
        assert any(t["id"] == created["task"]["id"] for t in tasks)

    def test_get_tasks_no_auth(self, client):
        """Test getting tasks without authentication (should fail)."""
        resp = client.get("/tasks")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_task_by_id_success(self, client):
        """Test retrieving a single task by ID."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        resp = client.get(
            f"/tasks/{created['task']['id']}", headers=self._auth_headers(token)
        )
        assert resp.status_code == status.HTTP_200_OK
        task = self._get_response_data(resp)
        assert task["task"]["id"] == created["task"]["id"]
        assert task["task"]["title"] == created["task"]["title"]

    def test_get_task_by_id_not_found(self, client):
        """Test getting a non-existent task by ID."""
        _, token = self._register_and_login(client)
        fake_id = generate()
        resp = client.get(f"/tasks/{fake_id}", headers=self._auth_headers(token))
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in resp.json()["detail"]

    def test_update_task_success(self, client):
        """Test updating a task's fields."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        updates = {"title": "New Title", "icon": "🩺"}
        resp = client.put(
            f"/tasks/{created['task']['id']}",
            json=updates,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        updated = self._get_response_data(resp)
        assert updated["task"]["title"] == "New Title"
        assert updated["task"]["icon"] == "🩺"

    def test_update_task_not_found(self, client):
        """Test updating a non-existent task."""
        _, token = self._register_and_login(client)
        updates = {"title": "Should not work"}
        fake_id = generate()
        resp = client.put(
            f"/tasks/{fake_id}", json=updates, headers=self._auth_headers(token)
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in resp.json()["detail"]

    def test_update_task_status_success(self, client):
        """Test updating a task's completion status."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        status_req = {"completed": True}
        resp = client.put(
            f"/tasks/{created['task']['id']}/status",
            json=status_req,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        updated = self._get_response_data(resp)
        assert updated["task"]["completed"] is True

    def test_update_task_status_not_found(self, client):
        """Test updating status of a non-existent task."""
        _, token = self._register_and_login(client)
        status_req = {"completed": True}
        fake_id = generate()
        resp = client.put(
            f"/tasks/{fake_id}/status",
            json=status_req,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in resp.json()["detail"]

    def test_create_task_invalid_data(self, client):
        """Test creating a task with invalid data (missing required fields)."""
        _, token = self._register_and_login(client)
        # Missing title
        req = {
            "icon": "💊",
            "reminder_time": {"hour": 8, "minute": 0},
            "recurrence": {"interval": 1, "unit": "DAY"},
        }
        resp = client.post("/tasks", json=req, headers=self._auth_headers(token))
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_task_invalid_data(self, client):
        """Test updating a task with invalid data (bad field type)."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        updates = {"title": 12345}  # Should be string
        resp = client.put(
            f"/tasks/{created['task']['id']}",
            json=updates,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_task_is_user_isolated(self, client):
        """Test that tasks are isolated per user (user A cannot see user B's tasks)."""
        # User A
        _, token_a = self._register_and_login(client)
        self._create_task(client, token_a, title="A's task")
        # User B
        _, token_b = self._register_and_login(client)
        self._create_task(client, token_b, title="B's task")
        # User A should only see their own tasks
        resp_a = client.get("/tasks", headers=self._auth_headers(token_a))
        response_data_a = self._get_response_data(resp_a)
        tasks_a = [
            t["title"]
            for t in (
                response_data_a["tasks"]
                if "tasks" in response_data_a
                else response_data_a
            )
        ]
        assert "A's task" in tasks_a
        assert "B's task" not in tasks_a
        # User B can only see their own tasks
        resp_b = client.get("/tasks", headers=self._auth_headers(token_b))
        response_data_b = self._get_response_data(resp_b)
        tasks_b = [
            t["title"]
            for t in (
                response_data_b["tasks"]
                if "tasks" in response_data_b
                else response_data_b
            )
        ]
        assert "B's task" in tasks_b
        assert "A's task" not in tasks_b

    def test_create_task_without_recurrence(self, client):
        """Test creating a task without recurrence (optional field)."""
        _, token = self._register_and_login(client)
        req = {
            "title": "One-time task",
            "icon": "📝",
            "reminder_time": {"hour": 10, "minute": 30},
        }
        resp = client.post("/tasks", json=req, headers=self._auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        task = self._get_response_data(resp)
        assert task["task"]["title"] == "One-time task"
        assert task["task"]["recurrence"] is None

    def test_update_task_partial_fields(self, client):
        """Test updating only some fields of a task."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        # Update only title
        updates = {"title": "Updated Title Only"}
        resp = client.put(
            f"/tasks/{created['task']['id']}",
            json=updates,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        updated = self._get_response_data(resp)
        assert updated["task"]["title"] == "Updated Title Only"
        assert (
            updated["task"]["icon"] == created["task"]["icon"]
        )  # Should remain unchanged

    def test_update_task_status_to_false(self, client):
        """Test updating task status to completed=False."""
        _, token = self._register_and_login(client)
        created = self._create_task(client, token)
        # First complete it
        status_req = {"completed": True}
        resp = client.put(
            f"/tasks/{created['task']['id']}/status",
            json=status_req,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        # Then uncomplete it
        status_req = {"completed": False}
        resp = client.put(
            f"/tasks/{created['task']['id']}/status",
            json=status_req,
            headers=self._auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        updated = self._get_response_data(resp)
        assert updated["task"]["completed"] is False
