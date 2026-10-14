from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.ingest_agent import IngestAgent
from app.config import settings
from app.db.models import Base
from app.email_ingest import EmailAttachment, EmailMessage
from app.llm.provider import DisabledLLMProvider
from app.tools import ArgosToolService


class FakeConnector:
    def status(self):
        return {"configured": True, "password_configured": True}

    def fetch_messages(self, **kwargs):
        return [
            EmailMessage(
                uid="42",
                message_id="<42@example.com>",
                subject="Launch notes",
                sender="team@example.com",
                recipients="owner@example.com",
                sent_at="2026-10-13T09:30:00-05:00",
                body="The launch risk is supplier delay.",
                attachments=[
                    EmailAttachment(
                        filename="risk-register.txt",
                        mime_type="text/plain",
                        content=b"Supplier delay is the primary launch risk.",
                    )
                ],
            )
        ]


def make_service(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(settings, "blobs_dir", tmp_path / "blobs")
    return ArgosToolService(
        session_factory=sessions,
        email_connector_factory=FakeConnector,
        ingest_agent_factory=lambda: IngestAgent(DisabledLLMProvider()),
    )


def test_email_sync_imports_body_and_supported_attachment(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)

    result = service.sync_email(limit=1)

    assert result["messages_scanned"] == 1
    assert len(result["imported"]) == 2
    assert result["marked_seen"] is False

    documents = service.list_documents()
    assert documents["count"] == 2
    assert {doc["title"] for doc in documents["documents"]} == {
        "Email: Launch notes",
        "Email attachment: risk-register.txt",
    }


def test_email_sync_is_idempotent(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)

    first = service.sync_email(limit=1)
    second = service.sync_email(limit=1)

    assert len(first["imported"]) == 2
    assert len(second["imported"]) == 0
    assert len(second["skipped"]) == 2
    assert service.list_documents()["count"] == 2


def test_local_search_finds_imported_email(tmp_path, monkeypatch):
    service = make_service(tmp_path, monkeypatch)
    service.sync_email(limit=1)

    result = service.search_documents("Launch notes")

    assert result["count"] == 1
    assert result["documents"][0]["title"] == "Email: Launch notes"
