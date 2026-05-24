import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from backend.config import load_config
from backend.main import app
from backend.persistence.database import init_db, get_engine


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        engine = init_db(db_path)
        config = load_config()
        config.persistence.database.path = db_path
        app.state.config = config
        app.state.db_engine = engine
        yield TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_recommendations_empty(client):
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert data["sections"] == []
