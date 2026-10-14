"""Email ingestion adapters for ArgosOS."""

from .imap_connector import EmailAttachment, EmailMessage, IMAPEmailConnector

__all__ = ["EmailAttachment", "EmailMessage", "IMAPEmailConnector"]
