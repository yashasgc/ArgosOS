from fastapi.testclient import TestClient

from app.main import app, get_tool_service


class FakeToolService:
    def email_status(self):
        return {"configured": True, "password_configured": True, "folder": "INBOX"}

    def preview_email(self, **kwargs):
        return {"messages": [{"uid": "42", "subject": "Report"}], "count": 1}

    def sync_email(self, **kwargs):
        return {
            "messages_scanned": 1,
            "imported": [{"id": "doc-1", "title": "Email: Report"}],
            "skipped": [],
            "errors": [],
            "marked_seen": kwargs["mark_seen"],
        }


def client():
    app.dependency_overrides[get_tool_service] = FakeToolService
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.pop(get_tool_service, None)


def test_email_status_hides_credentials():
    response = client().get("/api/email/status")

    assert response.status_code == 200
    assert response.json()["email"]["configured"] is True
    assert "password" not in response.text.replace("password_configured", "")


def test_email_preview_is_available_to_desktop_clients():
    response = client().get("/api/email/preview?limit=5&unread_only=true&since_days=7")

    assert response.status_code == 200
    assert response.json()["email"]["messages"][0]["subject"] == "Report"


def test_email_sync_defaults_to_not_marking_messages_seen():
    response = client().post("/api/email/sync", json={"limit": 5})

    assert response.status_code == 200
    assert response.json()["email"]["marked_seen"] is False
