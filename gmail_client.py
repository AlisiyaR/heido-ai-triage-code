"""Connects to the Gmail API with OAuth (Desktop app flow)."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# gmail.modify lets us read emails, mark them as read and send replies.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")  # identifies the app
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")  # saved login, created on first sign-in


def get_gmail_service():
    """Return a Gmail API service that is signed in.

    Uses the saved login in token.json. If it is missing or no longer valid,
    refreshes it or opens the browser to sign in, then saves token.json.

    Returns:
        A Gmail API service object, used like service.users().messages()...
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # The short-lived access token expired; get a new one without the browser.
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)  # port=0 picks any free port
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_own_address(service):
    """Return the email address of the signed-in inbox (the support inbox)."""
    return service.users().getProfile(userId="me").execute()["emailAddress"]


if __name__ == "__main__":
    # Self-test: prints only the account address and the unread count.
    service = get_gmail_service()
    unread = service.users().labels().get(userId="me", id="INBOX").execute()
    print(f"Connected as: {get_own_address(service)}")
    print(f"Unread emails in INBOX: {unread['messagesUnread']}")
