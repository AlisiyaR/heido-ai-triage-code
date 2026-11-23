# 0011. Email parsing rules: which body, which files, which order

- **Status:** Accepted
- **Date:** 2026-11-22 (implementation changed by [0015](0015-raw-format-and-python-email-package.md); the rules below are unchanged)

## Context
Real emails come in many shapes: plain text only, HTML only, both (multipart/alternative), with attached files, with images pasted into the body, and in different character sets (Hebrew emails are often `windows-1255`).
The rest of the pipeline needs one body text, a list of files, and a predictable order.
The Make version took the plain-text body (`fullTextBody`), uploaded files when the email had attachments **or** media, and processed up to 11 emails per run.

## Decision
In `email_reader.py`:
- **Body:** the first `text/plain` part that is not an attached file. If there is none, the first `text/html` part with the tags removed. Text is decoded with the charset in its `Content-Type`, falling back to UTF-8.
- **Files:** every leaf MIME part that has content and is not body text. This includes real attachments, images pasted into the body, and attached `.txt` files (a text part *with* a filename is a file, not the body). A file with no name gets `inline_N.<ext>`.
- **Order and limit:** ask Gmail for up to `MAX_EMAILS_PER_RUN` (20) unread INBOX emails, then process them **oldest first**.
- Reading never marks an email as read; that is a separate call ([0009](0009-mark-as-read-after-item-created.md)).

## Alternatives
- **Use the HTML body when both exist:** keeps formatting, but monday's "Original Message" is a plain long-text column, and HTML would add noise. Plain text matches Make.
- **Real attachments only, skip pasted images:** simpler, but customers often paste screenshots of errors, and Make included media too.
- **Page through every unread email to find the true oldest 20:** fairer with a big backlog, but more API calls and code. At support-inbox volume, a backlog over 20 is unlikely.
- **A full HTML-to-text library:** better output for complex HTML, but one more package for the rare HTML-only email.

## Consequences
- The body is always plain text, and Hebrew emails decode correctly.
- Screenshots pasted into an email reach the monday task.
- Email signatures with logo images will also be uploaded as files (same as Make).
- **Known limitation:** with more than 20 unread emails, Gmail returns the 20 *newest*, so older ones wait until the backlog shrinks.
- HTML stripping is basic (tags removed, line breaks kept); complex layouts may look untidy.
