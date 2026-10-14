# ArgosOS MCP and email tools

ArgosOS includes a local Model Context Protocol server so an MCP host can list,
search, and read the user's document library. The same tool service also imports
email through generic IMAP.

## Available MCP tools

| Tool | Purpose | Changes data? |
|---|---|---|
| `argos_list_documents` | List local document metadata | No |
| `argos_search_documents` | Search titles, summaries, and tags | No |
| `argos_get_document_text` | Extract text from one document | No |
| `argos_list_tags` | List the local tag vocabulary | No |
| `argos_email_status` | Check IMAP configuration without exposing the password | No |
| `argos_email_preview` | Preview messages and attachments using `BODY.PEEK` | No |
| `argos_email_sync` | Import selected email bodies and supported attachments | Yes, local import only |

No MCP delete tool is exposed.

## Configure email

Copy the email variables from `config.env.example` into `.env`:

```dotenv
EMAIL_IMAP_HOST=imap.example.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=you@example.com
EMAIL_IMAP_PASSWORD=replace_with_an_app_password
EMAIL_IMAP_FOLDER=INBOX
EMAIL_IMAP_USE_SSL=true
```

For Gmail, use `imap.gmail.com` and a Google app password. Do not commit `.env`
or a real password. Future OAuth adapters can implement the same connector
interface without changing the MCP tools.

By default, previews and syncs:

- look at unread messages from the last 30 days;
- process at most 20 messages;
- leave messages unread;
- import the email body as a text document;
- import supported attachments; and
- rely on ArgosOS content hashes to avoid duplicates.

The caller must explicitly set `mark_seen=true` to mark imported messages read.

## Run the server

Install dependencies and start the stdio MCP server:

```bash
poetry install
poetry run argos-mcp
```

Example MCP host configuration:

```json
{
  "mcpServers": {
    "argos": {
      "command": "poetry",
      "args": ["run", "argos-mcp"],
      "cwd": "/absolute/path/to/ArgosOS"
    }
  }
}
```

The server uses stdio, so standard output is reserved for MCP protocol traffic.
Application diagnostics should use Python logging, which writes to standard
error.

## Desktop and HTTP integration

The FastAPI backend exposes the same email service for the desktop application:

- `GET /api/email/status`
- `GET /api/email/preview`
- `POST /api/email/sync`

Both MCP and HTTP therefore share the same validation, MIME parsing,
deduplication, and read-only defaults. A future Settings screen can call these
endpoints without adding a second email implementation.

## Tool architecture

`app/tools/service.py` is intentionally independent of MCP. The desktop UI,
FastAPI endpoints, scheduled import jobs, and other automation adapters can call
the same service. This provides one place for validation, deduplication, and
safe file access.

The next useful tool additions are:

1. cited question answering over selected document IDs;
2. semantic search backed by local embeddings;
3. an OAuth Gmail adapter and a Microsoft Graph adapter;
4. saved import rules for sender, subject, folder, and attachment type; and
5. explicit approval tools for outbound actions such as drafting a reply.
