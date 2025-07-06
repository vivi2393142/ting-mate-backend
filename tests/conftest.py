import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Fixture for FastAPI test client."""
    with TestClient(app) as c:
        yield c
