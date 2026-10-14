"""Application service shared by HTTP, MCP, and future automation adapters."""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

from app.agents.ingest_agent import IngestAgent
from app.config import settings
from app.db.crud import DocumentCRUD, TagCRUD
from app.db.engine import SessionLocal, init_database
from app.email_ingest import EmailMessage, IMAPEmailConnector
from app.files.text_extractor import TextExtractor
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import DisabledLLMProvider
from app.utils.validation import FileValidator


class ArgosToolService:
    """Safe tool surface for documents and email ingestion.

    This service intentionally exposes no delete operation. It can be reused by
    MCP, HTTP endpoints, a CLI, or scheduled jobs without duplicating business
    logic.
    """

    def __init__(
        self,
        session_factory=SessionLocal,
        email_connector_factory: Callable[[], IMAPEmailConnector] = IMAPEmailConnector,
        ingest_agent_factory: Optional[Callable[[], IngestAgent]] = None,
    ) -> None:
        self.session_factory = session_factory
        self.email_connector_factory = email_connector_factory
        self.ingest_agent_factory = ingest_agent_factory or self._default_ingest_agent
        init_database()

    @contextmanager
    def _session(self):
        db = self.session_factory()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def _default_ingest_agent() -> IngestAgent:
        provider = OpenAIProvider()
        if not provider.is_available():
            provider = DisabledLLMProvider()
        return IngestAgent(provider)

    @staticmethod
    def _document_dict(document) -> dict:
        try:
            tags = json.loads(document.tags) if document.tags else []
        except (TypeError, json.JSONDecodeError):
            tags = []
        return {
            "id": document.id,
            "title": document.title,
            "summary": document.summary,
            "mime_type": document.mime_type,
            "size_bytes": document.size_bytes,
            "created_at": document.created_at,
            "imported_at": document.imported_at,
            "tags": tags,
        }

    def list_documents(self, limit: int = 50, offset: int = 0) -> dict:
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        with self._session() as db:
            documents = DocumentCRUD.get_all(db, skip=offset, limit=limit)
            return {"documents": [self._document_dict(doc) for doc in documents], "count": len(documents)}

    def search_documents(self, query: str, limit: int = 20) -> dict:
        query = query.strip()
        if not query:
            raise ValueError("query cannot be empty")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        with self._session() as db:
            documents = DocumentCRUD.search(db, query, 0, limit)
            return {
                "query": query,
                "documents": [self._document_dict(doc) for doc in documents],
                "count": len(documents),
                "search_mode": "local metadata",
            }

    def list_tags(self) -> dict:
        with self._session() as db:
            tags = TagCRUD.get_all(db)
            return {"tags": [tag.tag for tag in tags], "count": len(tags)}

    def get_document_text(self, document_id: str, max_characters: int = 100_000) -> dict:
        if max_characters < 1 or max_characters > 1_000_000:
            raise ValueError("max_characters must be between 1 and 1000000")
        with self._session() as db:
            document = DocumentCRUD.get_by_id(db, document_id)
            if not document:
                raise ValueError("document not found")
            blob_path = Path(document.storage_path).resolve()
            blobs_root = settings.blobs_dir.resolve()
            if not blob_path.is_relative_to(blobs_root) or not blob_path.is_file():
                raise ValueError("document file is unavailable")
            file_data = blob_path.read_bytes()
            extractor = TextExtractor(DisabledLLMProvider())
            text = extractor.extract_text(file_data, document.mime_type, document.title) or ""
            truncated = len(text) > max_characters
            return {
                "document": self._document_dict(document),
                "text": text[:max_characters],
                "truncated": truncated,
            }

    def email_status(self) -> dict:
        return self.email_connector_factory().status()

    def preview_email(self, limit: int = 20, unread_only: bool = True, since_days: int = 30) -> dict:
        messages = self.email_connector_factory().fetch_messages(
            limit=limit,
            unread_only=unread_only,
            since_days=since_days,
            mark_seen=False,
        )
        return {"messages": [message.preview() for message in messages], "count": len(messages)}

    def sync_email(
        self,
        limit: int = 20,
        unread_only: bool = True,
        since_days: int = 30,
        include_bodies: bool = True,
        include_attachments: bool = True,
        mark_seen: bool = False,
    ) -> dict:
        if not include_bodies and not include_attachments:
            raise ValueError("include_bodies or include_attachments must be enabled")
        messages = self.email_connector_factory().fetch_messages(
            limit=limit,
            unread_only=unread_only,
            since_days=since_days,
            mark_seen=mark_seen,
        )
        agent = self.ingest_agent_factory()
        imported: list[dict] = []
        skipped: list[dict] = []
        errors: list[dict] = []

        with self._session() as db:
            for message in messages:
                if include_bodies and message.body.strip():
                    self._ingest_email_body(agent, db, message, imported, skipped, errors)
                if include_attachments:
                    for attachment in message.attachments:
                        if not agent.is_supported(attachment.mime_type):
                            skipped.append({
                                "source": "attachment",
                                "filename": attachment.filename,
                                "reason": f"unsupported MIME type: {attachment.mime_type}",
                            })
                            continue
                        self._ingest_item(
                            agent,
                            db,
                            attachment.content,
                            FileValidator.sanitize_filename(attachment.filename),
                            attachment.mime_type,
                            f"Email attachment: {attachment.filename}",
                            imported,
                            skipped,
                            errors,
                        )

        return {
            "messages_scanned": len(messages),
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "marked_seen": mark_seen,
        }

    def _ingest_email_body(self, agent, db, message: EmailMessage, imported, skipped, errors) -> None:
        metadata = "\n".join([
            f"Subject: {message.subject}",
            f"From: {message.sender}",
            f"To: {message.recipients}",
            f"Date: {message.sent_at or ''}",
            f"Message-ID: {message.message_id}",
            "",
            message.body,
        ])
        safe_subject = re.sub(r"[^A-Za-z0-9._-]+", "-", message.subject).strip("-.") or "message"
        filename = FileValidator.sanitize_filename(f"email-{message.uid}-{safe_subject[:80]}.txt")
        self._ingest_item(
            agent,
            db,
            metadata.encode("utf-8"),
            filename,
            "text/plain",
            f"Email: {message.subject}",
            imported,
            skipped,
            errors,
        )

    @staticmethod
    def _ingest_item(agent, db, content, filename, mime_type, title, imported, skipped, errors) -> None:
        document, item_errors = agent.ingest_file(content, filename, mime_type, db, title=title)
        duplicate = bool(item_errors and any("already exists" in error for error in item_errors))
        if document and not duplicate:
            imported.append({"id": document.id, "title": document.title, "mime_type": document.mime_type})
        elif document and duplicate:
            skipped.append({"source": filename, "reason": "already imported", "document_id": document.id})
        else:
            errors.append({"source": filename, "errors": item_errors or ["ingestion failed"]})
