"""Reads unread support emails from Gmail and marks them as read."""

import base64
import email
import html
import mimetypes
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email import policy
from email.utils import parseaddr

import config


@dataclass
class Attachment:
    """One file from an email: a real attachment or an image pasted into the body."""

    filename: str
    mime_type: str
    data: bytes


@dataclass
class Email:
    """The parts of an email the pipeline needs."""

    message_id: str
    subject: str
    body: str
    from_name: str
    from_email: str
    received_at: datetime
    attachments: list[Attachment] = field(default_factory=list)


def fetch_unread(service, limit=config.MAX_EMAILS_PER_RUN):
    """Return unread INBOX emails, oldest first. Does not mark them as read.

    Args:
        service: a Gmail API service from gmail_client.get_gmail_service().
        limit: the maximum number of emails to return.

    Returns:
        A list of Email objects.
    """
    response = service.users().messages().list(
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=limit
    ).execute()
    message_refs = response.get("messages", [])  # the key is missing when there are none
    message_refs.reverse()  # Gmail returns newest first; handle the oldest first

    emails = []
    for ref in message_refs:
        # "raw" gives the whole email (files included) in one piece, for Python's email package.
        message = service.users().messages().get(userId="me", id=ref["id"], format="raw").execute()
        emails.append(parse_message(message))
    return emails


def mark_as_read(service, message_id):
    """Remove the UNREAD label from one email.

    Args:
        service: a Gmail API service.
        message_id: the Gmail message ID (Email.message_id).
    """
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def parse_message(message):
    """Turn a Gmail API message (format="raw") into an Email.

    Args:
        message: the message dict returned by messages().get(format="raw").

    Returns:
        An Email object.
    """
    raw_bytes = base64.urlsafe_b64decode(message["raw"] + "=" * (-len(message["raw"]) % 4))
    mime = email.message_from_bytes(raw_bytes, policy=policy.default)
    from_name, from_email = parseaddr(str(mime["from"] or ""))
    # internalDate is the time Gmail received the email, in milliseconds since 1970.
    received_at = datetime.fromtimestamp(int(message["internalDate"]) / 1000, tz=timezone.utc)

    return Email(
        message_id=message["id"],
        subject=str(mime["subject"] or ""),
        body=find_body(mime),
        from_name=from_name,
        from_email=from_email,
        received_at=received_at,
        attachments=collect_attachments(mime),
    )


def find_body(mime):
    """Return the email's text: the plain-text part, or the HTML part without tags.

    Args:
        mime: the parsed email (an email.message.EmailMessage).

    Returns:
        The body as a string ("" if the email has no text).
    """
    part = mime.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        text = part.get_content()  # decodes base64 and the charset (e.g. Hebrew windows-1255)
    except LookupError:  # unknown charset name
        text = part.get_payload(decode=True).decode("utf-8", errors="replace")
    return strip_html(text) if part.get_content_subtype() == "html" else text


def collect_attachments(mime):
    """Collect every file in the email, including images pasted into the body.

    Body text (a text part without a filename) is skipped; everything else
    with content counts as a file (ADR 0011).

    Args:
        mime: the parsed email (an email.message.EmailMessage).

    Returns:
        A list of Attachment objects.
    """
    attachments = []
    for part in mime.walk():  # every part, at every level
        filename = part.get_filename()
        is_body_text = part.get_content_maintype() == "text" and not filename
        if part.is_multipart() or is_body_text:
            continue
        data = part.get_payload(decode=True)
        if data:
            attachments.append(Attachment(
                filename=filename or default_filename(part.get_content_type(), len(attachments) + 1),
                mime_type=part.get_content_type(),
                data=data,
            ))
    return attachments


def default_filename(mime_type, number):
    """Make a name for a file that has none, e.g. "inline_1.png"."""
    extension = mimetypes.guess_extension(mime_type) or ""
    return f"inline_{number}{extension}"


def strip_html(html_text):
    """Turn HTML into readable plain text."""
    text = re.sub(r"(?is)<(style|script).*?</\1>", "", html_text)  # drop CSS and scripts
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", text)  # keep line breaks
    text = re.sub(r"<[^>]+>", "", text)  # remove all other tags
    text = html.unescape(text)  # &amp; -> &
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


if __name__ == "__main__":
    # Self-test: list unread emails. Nothing is marked as read.
    import gmail_client

    gmail = gmail_client.get_gmail_service()
    unread = fetch_unread(gmail)
    print(f"Fetched {len(unread)} unread email(s) from INBOX (limit {config.MAX_EMAILS_PER_RUN})")
    for message in unread:
        print(f"\n- {message.received_at:%Y-%m-%d %H:%M} UTC  {message.subject!r}")
        print(f"  From: {message.from_name} <{message.from_email}>")
        print(f"  Body: {len(message.body)} characters")
        for attachment in message.attachments:
            print(f"  Attachment: {attachment.filename} ({attachment.mime_type}, {len(attachment.data):,} bytes)")
