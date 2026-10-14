import pytest
from mcp import Client

from app.mcp.server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_server_exposes_expected_tools():
    async with Client(mcp) as client:
        result = await client.list_tools()

    names = {tool.name for tool in result.tools}
    assert names == {
        "argos_list_documents",
        "argos_search_documents",
        "argos_get_document_text",
        "argos_list_tags",
        "argos_email_status",
        "argos_email_preview",
        "argos_email_sync",
    }
