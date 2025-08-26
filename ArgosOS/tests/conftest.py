import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def app_settings():
    """App settings fixture"""
    return app.state.settings if hasattr(app.state, 'settings') else None

