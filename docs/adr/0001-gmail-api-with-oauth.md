# 0001. Gmail API with OAuth instead of IMAP/SMTP with an App Password

- **Status:** Accepted
- **Date:** 2026-11-21

## Context
The system must read unread emails from the support inbox, mark them as read, read attachments and send a confirmation email.
The brief first suggested the built-in `imaplib` and `smtplib` with a Gmail App Password.
An App Password is a long-lived secret that gives full mailbox access, needs 2-Step Verification, and must be stored by the program.

## Decision
Use the **Gmail API** with **OAuth (Desktop app flow)** and the `gmail.modify` scope.
`credentials.json` identifies the app; `token.json` is created after a one-time browser sign-in and refreshed automatically. Both are git-ignored.
One connection (`gmail_client.get_gmail_service()`) is used for reading, marking as read and sending.

## Alternatives
- **IMAP + SMTP with an App Password:** no extra packages, but the password gives broad access, must be stored in `.env`, and needs two different protocols for reading and sending.
- **A wider scope such as full mail access:** would also allow permanent deletion, which we never need.

## Consequences
- No password in the project; access can be revoked any time from the Google account.
- `gmail.modify` covers everything Heido needs and nothing more (no permanent delete).
- Two new packages: `google-api-python-client` and `google-auth-oauthlib`.
- One-time setup in Google Cloud Console: enable the Gmail API, create a Desktop OAuth client, add the inbox as a test user.
- While the app is in "Testing" mode, `token.json` expires after 7 days and the user must sign in again.
- `email_reader.py` and `mailer.py` will use the Gmail API instead of `imaplib`/`smtplib`.
