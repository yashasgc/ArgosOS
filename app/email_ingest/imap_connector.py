"""Read-only-by-default IMAP connector used by ArgosOS tools and MCP."""

from __future__ import annotations

import imaplib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return "\n".join(self.parts)


@dataclass(frozen=True)
class EmailAttachment:
    filename: str
    mime_type: str
    content: bytes


@dataclass(frozen=True)
class EmailMessage:
    uid: str
    message_id: str
    subject: str
    sender: str
    recipients: str
    sent_at: Optional[str]
    body: str
    attachments: list[EmailAttachment] = field(default_factory=list)

    def preview(self) -> dict:
        return {
            "uid": self.uid,
            "message_id": self.message_id,
            "subject": self.subject,
            "sender": self.sender,
            "sent_at": self.sent_at,
            "attachment_count": len(self.attachments),
            "attachments": [
                {"filename": item.filename, "mime_type": item.mime_type, "size_bytes": len(item.content)}
                for item in self.attachments
            ],
            "body_preview": self.body[:240],
        }


class IMAPEmailConnector:
    """Fetch messages from a configured IMAP mailbox without changing them by default."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        folder: Optional[str] = None,
        use_ssl: Optional[bool] = None,
        client_factory: Optional[Callable[..., imaplib.IMAP4]] = None,
    ) -> None:
        self.host = host or settings.email_imap_host
        self.port = port or settings.email_imap_port
        self.username = username or settings.email_imap_username
        self.password = password or settings.email_imap_password
        self.folder = folder or settings.email_imap_folder
        self.use_ssl = settings.email_imap_use_ssl if use_ssl is None else use_ssl
        self.client_factory = client_factory

    def status(self) -> dict:
        configured = bool(self.host and self.username and self.password)
        return {
            "configured": configured,
            "host": self.host if configured else None,
            "port": self.port,
            "username": self.username if configured else None,
            "folder": self.folder,
            "use_ssl": self.use_ssl,
            "password_configured": bool(self.password),
        }

    def fetch_messages(
        self,
        limit: int = 20,
        unread_only: bool = True,
        since_days: int = 30,
        mark_seen: bool = False,
    ) -> list[EmailMessage]:
        if not self.status()["configured"]:
            raise ValueError(
                "Email is not configured. Set EMAIL_IMAP_HOST, EMAIL_IMAP_USERNAME, "
                "and EMAIL_IMAP_PASSWORD."
            )
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if since_days < 1 or since_days > 3650:
            raise ValueError("since_days must be between 1 and 3650")

        client = self._connect()
        try:
            client.login(self.username, self.password)
            status, _ = client.select(self.folder, readonly=not mark_seen)
            if status != "OK":
                raise RuntimeError(f"Could not open IMAP folder: {self.folder}")

            since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%d-%b-%Y")
            criteria = ["SINCE", since]
            if unread_only:
                criteria.insert(0, "UNSEEN")
            status, data = client.uid("search", None, *criteria)
            if status != "OK":
                raise RuntimeError("IMAP search failed")

            raw_uids = data[0].split() if data and data[0] else []
            selected_uids = list(reversed(raw_uids[-limit:]))
            messages: list[EmailMessage] = []
            fetch_item = "(RFC822)" if mark_seen else "(BODY.PEEK[])"

            for raw_uid in selected_uids:
                uid = raw_uid.decode("ascii", errors="ignore")
                status, payload = client.uid("fetch", raw_uid, fetch_item)
                if status != "OK":
                    logger.warning("Could not fetch IMAP message UID %s", uid)
                    continue
                raw_message = self._extract_raw_message(payload)
                if raw_message is not None:
                    messages.append(self._parse_message(uid, raw_message))
            return messages
        finally:
            try:
                client.logout()
            except Exception:
                logger.debug("IMAP logout failed", exc_info=True)

    def _connect(self) -> imaplib.IMAP4:
        if self.client_factory:
            return self.client_factory(self.host, self.port)
        if self.use_ssl:
            return imaplib.IMAP4_SSL(self.host, self.port)
        return imaplib.IMAP4(self.host, self.port)

    @staticmethod
    def _extract_raw_message(payload) -> Optional[bytes]:
        for item in payload or []:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        return None

    @staticmethod
    def _decode_header(value: Optional[str]) -> str:
        if not value:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except Exception:
            return value

    @classmethod
    def _parse_message(cls, uid: str, raw_message: bytes) -> EmailMessage:
        message = BytesParser(policy=policy.default).parsebytes(raw_message)
        subject = cls._decode_header(message.get("Subject")) or "Untitled email"
        sent_at = None
        if message.get("Date"):
            try:
                sent_at = parsedate_to_datetime(message.get("Date")).isoformat()
            except (TypeError, ValueError, OverflowError):
                sent_at = message.get("Date")

        body = cls._extract_body(message)
        attachments: list[EmailAttachment] = []
        for part in message.walk():
            if part.is_multipart():
                continue
            filename = part.get_filename()
            disposition = part.get_content_disposition()
            if not filename and disposition != "attachment":
                continue
            content = part.get_payload(decode=True) or b""
            if not content:
                continue
            attachments.append(
                EmailAttachment(
                    filename=cls._decode_header(filename) or "attachment.bin",
                    mime_type=part.get_content_type() or "application/octet-stream",
                    content=content,
                )
            )

        return EmailMessage(
            uid=uid,
            message_id=message.get("Message-ID", ""),
            subject=subject,
            sender=cls._decode_header(message.get("From")),
            recipients=cls._decode_header(message.get("To")),
            sent_at=sent_at,
            body=body,
            attachments=attachments,
        )

    @staticmethod
    def _extract_body(message) -> str:
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in message.walk():
            if part.is_multipart() or part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type not in {"text/plain", "text/html"}:
                continue
            try:
                text = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True) or b""
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            if content_type == "text/plain":
                plain_parts.append(text.strip())
            else:
                html_parts.append(text)
        if plain_parts:
            return "\n\n".join(part for part in plain_parts if part)
        if html_parts:
            parser = _HTMLTextExtractor()
            parser.feed("\n".join(html_parts))
            return parser.text()
        return ""
