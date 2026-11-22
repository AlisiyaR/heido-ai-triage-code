"""Sends the customer a confirmation email with the ticket number."""

import base64
import html
from email.message import EmailMessage

import config
from email_reader import strip_html


def send_confirmation(service, to_address, item_id, title):
    """Send the confirmation email through the Gmail API.

    Args:
        service: a Gmail API service from gmail_client.get_gmail_service().
        to_address: the customer's email address.
        item_id: the monday item ID (the ticket number).
        title: the ticket topic (the AI's title).

    Returns:
        The Gmail message ID of the sent email.

    Raises:
        googleapiclient.errors.HttpError: if Gmail refuses to send.
    """
    # The title is AI text based on the customer's email, so escape it:
    # "<script>" must appear as text in the email, not run as HTML.
    html_body = config.CONFIRMATION_HTML.format(item_id=item_id, title=html.escape(title))

    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = config.CONFIRMATION_SUBJECT.format(item_id=item_id)
    message.set_content(strip_html(html_body))  # plain-text version for apps without HTML
    message.add_alternative(html_body, subtype="html")
    # No "From": Gmail uses the signed-in inbox.

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"]


if __name__ == "__main__":
    # Self-test: send one test confirmation to an address you type in.
    import gmail_client

    gmail = gmail_client.get_gmail_service()
    own_address = gmail.users().getProfile(userId="me").execute()["emailAddress"]

    recipient = input("Send a test confirmation to which address? ").strip()
    if recipient.lower() == own_address.lower():
        # It would land in the support inbox as a new unread email and become a ticket.
        print(f"Refused: {own_address} is the support inbox itself. Use a different address.")
    else:
        message_id = send_confirmation(gmail, recipient, "TEST-0001", "Test ticket <b>escaped</b>")
        print(f"Sent confirmation to {recipient}, Gmail message ID {message_id}")
