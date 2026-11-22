# 0012. monday.com: labels by text, GraphQL variables, no retries

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
Each email becomes an item on the monday.com board "Customer Support" with 10 columns (brief §3, module 13).
- The Make version set the Priority status by **label index** (Low = 7, Medium = 109, High = 110). Those numbers are invisible on the board and differ between boards. The brief asked to use label text if the API allows it.
- The Category column must accept any of the 9 categories, even if a label does not exist yet.
- Item values come from customer emails and the AI, so they can contain quotes, braces and other characters that have meaning in a query.
- monday calls can fail (wrong token, invalid value, monday down). The Make version had no retries for monday.

## Decision
In `monday_client.py`:
- Set status columns with `{"label": "<text>"}` and the dropdown with `{"labels": ["<name>"]}`, and call `create_item` with `create_labels_if_missing: true`.
- Send all values as **GraphQL variables** (`$itemName`, `$columnValues`, ...), never by pasting them into the query string. The only value placed in a query string is the item ID in the file upload, and it is converted to an integer first.
- On any monday error, raise a `RuntimeError` with monday's message. **No automatic retries**; `main.py` logs the error for that email.

## Alternatives
- **Label indexes, as in Make:** works, but the code would contain magic numbers that only make sense after looking them up on the board.
- **Build the query by pasting values into the text:** shorter, but a quote in an email could break the request (a classic injection problem).
- **Retry monday errors like Gemini errors:** helps with short outages, but most monday errors here (bad token, bad value) would fail again. A retry after a timeout could also create the item twice, which ADR 0009 tries to avoid.

## Consequences
- The code reads like the board: `{"label": "High"}`.
- A new or renamed category creates a new label automatically instead of failing. A typo would also create a label, but `classifier.validate()` only lets the 9 known categories through.
- Customer text cannot break the GraphQL query.
- A monday outage means the item is not created; under ADR 0009 the email stays unread and is retried on the next run, so nothing is lost.
- A failed file upload is logged but not retried; the item exists without that file.
