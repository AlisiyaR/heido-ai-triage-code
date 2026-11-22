"""Reads unread support emails from Gmail and marks them as read."""

import base64
import html
import mimetypes
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
        message = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(parse_message(service, message))
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


def parse_message(service, message):
    """Turn a Gmail API message (format="full") into an Email.

    Args:
        service: a Gmail API service, used to download large attachments.
        message: the message dict returned by messages().get().

    Returns:
        An Email object.
    """
    payload = message["payload"]
    headers = {header["name"].lower(): header["value"] for header in payload.get("headers", [])}
    from_name, from_email = parseaddr(headers.get("from", ""))
    # internalDate is the time Gmail received the email, in milliseconds since 1970.
    received_at = datetime.fromtimestamp(int(message["internalDate"]) / 1000, tz=timezone.utc)

    return Email(
        message_id=message["id"],
        subject=headers.get("subject", ""),
        body=find_body(payload),
        from_name=from_name,
        from_email=from_email,
        received_at=received_at,
        attachments=collect_attachments(service, message["id"], payload),
    )


def find_body(payload):
    """Return the email's text: the plain-text part, or the HTML part without tags.

    Args:
        payload: the message payload (the top MIME part).

    Returns:
        The body as a string ("" if the email has no text).
    """
    plain_part = find_text_part(payload, "text/plain")
    if plain_part:
        return decode_text(plain_part)
    html_part = find_text_part(payload, "text/html")
    if html_part:
        return strip_html(decode_text(html_part))
    return ""


def find_text_part(part, mime_type):
    """Search the MIME tree for the first body part of a type (not an attached file).

    Args:
        part: a MIME part dict; it may contain sub-parts under "parts".
        mime_type: e.g. "text/plain".

    Returns:
        The matching part dict, or None.
    """
    if part.get("mimeType") == mime_type and not part.get("filename"):
        return part
    for sub_part in part.get("parts", []):  # recursion: search inside each sub-part
        found = find_text_part(sub_part, mime_type)
        if found:
            return found
    return None


def collect_attachments(service, message_id, part, attachments=None):
    """Collect every file in the email, including images pasted into the body.

    Args:
        service: a Gmail API service.
        message_id: the Gmail message ID.
        part: a MIME part dict (start with the payload).
        attachments: the list being filled; leave empty when calling.

    Returns:
        A list of Attachment objects.
    """
    if attachments is None:
        attachments = []
    for sub_part in part.get("parts", []):
        collect_attachments(service, message_id, sub_part, attachments)

    is_leaf = not part.get("parts")
    is_body_text = part.get("mimeType", "").startswith("text/") and not part.get("filename")
    has_content = part.get("body", {}).get("attachmentId") or part.get("body", {}).get("data")
    if is_leaf and not is_body_text and has_content:
        attachments.append(Attachment(
            filename=part.get("filename") or default_filename(part["mimeType"], len(attachments) + 1),
            mime_type=part["mimeType"],
            data=download_part(service, message_id, part),
        ))
    return attachments


def download_part(service, message_id, part):
    """Return a part's file content as bytes.

    Small files come inside the message; larger ones must be downloaded separately.
    """
    body = part["body"]
    if "data" in body:
        return decode_base64url(body["data"])
    attachment = service.users().messages().attachments().get(
        userId="me", messageId=message_id, id=body["attachmentId"]
    ).execute()
    return decode_base64url(attachment["data"])


def default_filename(mime_type, number):
    """Make a name for a file that has none, e.g. "inline_1.png"."""
    extension = mimetypes.guess_extension(mime_type) or ""
    return f"inline_{number}{extension}"


def decode_text(part):
    """Decode a text part to a string, using the charset from its Content-Type."""
    data = part.get("body", {}).get("data", "")
    content_type = next(
        (h["value"] for h in part.get("headers", []) if h["name"].lower() == "content-type"), ""
    )
    match = re.search(r'charset="?([\w-]+)', content_type, re.IGNORECASE)
    charset = match.group(1) if match else "utf-8"
    try:
        return decode_base64url(data).decode(charset, errors="replace")
    except LookupError:  # unknown charset name
        return decode_base64url(data).decode("utf-8", errors="replace")


def decode_base64url(data):
    """Decode Gmail's base64url text to bytes (adds missing "=" padding)."""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


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
    for email in unread:
        print(f"\n- {email.received_at:%Y-%m-%d %H:%M} UTC  {email.subject!r}")
        print(f"  From: {email.from_name} <{email.from_email}>")
        print(f"  Body: {len(email.body)} characters")
        for attachment in email.attachments:
            print(f"  Attachment: {attachment.filename} ({attachment.mime_type}, {len(attachment.data):,} bytes)")
