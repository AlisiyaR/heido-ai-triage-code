# 0009. Mark an email as read once its monday item exists

- **Status:** Accepted (to be implemented in `main.py`)
- **Date:** 2026-11-18

## Context
"Unread" in the inbox is how the system knows which emails still need processing. The brief says: mark an email as read only after it was processed successfully, so a failed email is retried next run.
But processing has several steps: classify → create monday item → upload files → send confirmation.
If the email stays unread whenever *any* step fails, a failure after the item was created (e.g. a failed upload) would create a **second ticket** on the next run.

## Decision
- An email is marked as read **as soon as its monday item exists**.
- If classification or item creation fails, the email stays unread and is retried on the next run.
- If a file upload or the confirmation email fails, the error is logged, but the email is not retried, because retrying would create a duplicate ticket.
- In dry-run mode nothing is written and nothing is marked as read.

## Alternatives
- **Mark as read only after every step succeeds:** follows the brief literally, but risks duplicate tickets.
- **Mark as read before processing:** no duplicates, but a failed email would be lost silently.
- **Keep a local list of processed message IDs:** more robust, but adds a state file to manage; the inbox's read flag is enough at this scale.

## Consequences
- No duplicate tickets.
- An email whose item was created but whose attachments or confirmation failed needs a manual follow-up; the log line shows which one.
- The rule must be implemented carefully in `main.py`: the mark-as-read call goes right after item creation, not at the end.
