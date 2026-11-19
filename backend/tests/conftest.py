import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(database_url="sqlite://", seed_demo_data=False))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def demo_client():
    app = create_app(Settings(database_url="sqlite://", seed_demo_data=True))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def student_id(client) -> int:
    return client.post("/api/students", json={"name": "Test Student"}).json()["id"]
