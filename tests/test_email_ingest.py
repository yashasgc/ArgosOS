from email.message import EmailMessage as MIMEEmailMessage

from app.email_ingest.imap_connector import IMAPEmailConnector


class FakeIMAP:
    def __init__(self, raw_message: bytes):
        self.raw_message = raw_message
        self.fetch_item = None
        self.readonly = None

    def login(self, username, password):
        return "OK", []

    def select(self, folder, readonly=True):
        self.readonly = readonly
        return "OK", [b"1"]

    def uid(self, command, *args):
        if command == "search":
            return "OK", [b"42"]
        if command == "fetch":
            self.fetch_item = args[-1]
            return "OK", [(b"42 (BODY[] {100})", self.raw_message)]
        raise AssertionError(f"Unexpected IMAP command: {command}")

    def logout(self):
        return "BYE", []


def build_message() -> bytes:
    message = MIMEEmailMessage()
    message["Subject"] = "Quarterly report"
    message["From"] = "Finance <finance@example.com>"
    message["To"] = "Owner <owner@example.com>"
    message["Date"] = "Tue, 13 Oct 2026 09:30:00 -0500"
    message["Message-ID"] = "<report-42@example.com>"
    message.set_content("Revenue increased by twelve percent.")
    message.add_attachment(
        b"launch risks and revenue details",
        maintype="text",
        subtype="plain",
        filename="report.txt",
    )
    return message.as_bytes()


def test_fetch_messages_is_read_only_by_default():
    fake = FakeIMAP(build_message())
    connector = IMAPEmailConnector(
        host="imap.example.com",
        username="owner@example.com",
        password="app-password",
        client_factory=lambda host, port: fake,
    )

    messages = connector.fetch_messages(limit=1)

    assert fake.readonly is True
    assert fake.fetch_item == "(BODY.PEEK[])"
    assert len(messages) == 1
    assert messages[0].subject == "Quarterly report"
    assert "twelve percent" in messages[0].body
    assert messages[0].attachments[0].filename == "report.txt"
    assert messages[0].attachments[0].content == b"launch risks and revenue details"


def test_status_never_exposes_password():
    connector = IMAPEmailConnector(
        host="imap.example.com",
        username="owner@example.com",
        password="do-not-return-this",
    )

    status = connector.status()

    assert status["configured"] is True
    assert status["password_configured"] is True
    assert "password" not in status
    assert "do-not-return-this" not in str(status)
