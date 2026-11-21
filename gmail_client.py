"""Connects to the Gmail API with OAuth (Desktop app flow)."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# gmail.modify lets us read emails, mark them as read and send replies.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = "credentials.json"  # identifies the app (from Google Cloud)
TOKEN_FILE = "token.json"  # the saved login, created after the first sign-in


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


if __name__ == "__main__":
    # Self-test: prints only the account address and the unread count.
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    unread = service.users().labels().get(userId="me", id="INBOX").execute()
    print(f"Connected as: {profile['emailAddress']}")
    print(f"Unread emails in INBOX: {unread['messagesUnread']}")
