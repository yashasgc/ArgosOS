"""Local MCP server exposing ArgosOS document and email tools."""

from __future__ import annotations

from mcp.server import MCPServer

from app.tools import ArgosToolService

mcp = MCPServer("ArgosOS")


def _service() -> ArgosToolService:
    return ArgosToolService()


@mcp.tool()
def argos_list_documents(limit: int = 50, offset: int = 0) -> dict:
    """List locally stored ArgosOS documents and their metadata."""
    return _service().list_documents(limit=limit, offset=offset)


@mcp.tool()
def argos_search_documents(query: str, limit: int = 20) -> dict:
    """Search local document titles, summaries, and tags."""
    return _service().search_documents(query=query, limit=limit)


@mcp.tool()
def argos_get_document_text(document_id: str, max_characters: int = 100_000) -> dict:
    """Read extracted text for one local document by its ArgosOS ID."""
    return _service().get_document_text(document_id=document_id, max_characters=max_characters)


@mcp.tool()
def argos_list_tags() -> dict:
    """List all tags in the local ArgosOS library."""
    return _service().list_tags()


@mcp.tool()
def argos_email_status() -> dict:
    """Check whether an IMAP mailbox is configured without revealing its password."""
    return _service().email_status()


@mcp.tool()
def argos_email_preview(limit: int = 20, unread_only: bool = True, since_days: int = 30) -> dict:
    """Preview matching email and attachments without importing or marking messages read."""
    return _service().preview_email(limit=limit, unread_only=unread_only, since_days=since_days)


@mcp.tool()
def argos_email_sync(
    limit: int = 20,
    unread_only: bool = True,
    since_days: int = 30,
    include_bodies: bool = True,
    include_attachments: bool = True,
    mark_seen: bool = False,
) -> dict:
    """Import email bodies and supported attachments into ArgosOS.

    Messages remain unread unless mark_seen is explicitly set to true.
    """
    return _service().sync_email(
        limit=limit,
        unread_only=unread_only,
        since_days=since_days,
        include_bodies=include_bodies,
        include_attachments=include_attachments,
        mark_seen=mark_seen,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
