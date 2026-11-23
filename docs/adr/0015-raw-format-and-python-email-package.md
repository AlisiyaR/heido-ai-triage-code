# 0015. Parse emails with Python's `email` package (Gmail raw format)

- **Status:** Accepted (on branch `refactor/stdlib-email-parser`, pending a re-test with real emails)
- **Date:** 2026-11-23

## Context
`email_reader.py` first asked Gmail for each email in the **full** format: a JSON tree of MIME parts. The code then walked that tree itself, with hand-written recursion, base64 decoding, charset handling, and a separate API call to download each larger attachment (about 100 lines).
The self-review of the code found that Python's standard library already does all of this. The working rule says: no custom code where the standard library does the job.

## Decision
- Fetch each email in Gmail's **raw** format (`messages.get(format="raw")`): the whole email, files included, in one download.
- Parse it with Python's built-in `email` package (`email.message_from_bytes(..., policy=policy.default)`):
  - subject and sender are decoded automatically;
  - `get_body(("plain", "html"))` picks the body, `get_content()` decodes its charset;
  - `walk()` goes through every part to collect the files.
- Keep the **rules of [ADR 0011](0011-email-parsing-rules.md) unchanged**: plain text first with an HTML fallback (still `strip_html()`), every file counts including pasted images, nameless files get `inline_N.<ext>`, up to 20 unread emails, oldest first.
- Develop it on a separate branch; merge into `main` only after a re-test with real emails.

## Alternatives
- **Keep the full format and the hand-written parser:** it works and was tested live, but it is about 50 lines of code the standard library already provides, and harder to explain.
- **Use `iter_attachments()` instead of `walk()`:** shorter, but it decides by itself which parts count as attachments, which could change ADR 0011's rules (e.g. for pasted images).
- **A third-party email parsing package:** one more dependency for something the standard library does.

## Consequences
- `email_reader.py` is about 50 lines shorter (224 → 174); `find_text_part`, `download_part` and `decode_text` are gone, and there is no hand-written recursion.
- One API call per email instead of one plus one per large attachment.
- The behavior was checked side by side: the old and new readers gave identical results for a Hebrew email with a PDF and an attached `.txt`, a pasted image, an HTML-only email, an email with only an attachment, and an unknown charset.
- An email's full size (up to Gmail's 25 MB limit) is downloaded in one response; at support-inbox volume this is fine.
- Nothing changes for `main.py`, `mailer.py` or `monday_client.py`.
- **Re-tested with real emails (2026-11-23):** a Hebrew subject and body, a PDF with a Hebrew file name, a Swedish subject and a pasted image were all read correctly by `email_reader.py`. A live `main.py --once` run created 4 monday tasks with all columns filled and the PDF and image uploaded, sent 4 confirmations and marked the emails as read.
