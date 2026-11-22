# 0013. Confirmation email: format, escaping and the email-loop guard

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
After the monday item is created, the customer gets a confirmation with the ticket number (brief §3, module 24). The brief gives the exact subject and HTML body.
- The topic in the email is the AI's title, which is based on the customer's own email text. If it contained HTML such as `<script>` or `<a href=...>`, it could change how the email looks or behaves.
- Some email apps show only plain text.
- The confirmation is sent **from** the support inbox. If it were ever sent **to** the support inbox (for example, a test, or an email the inbox sent to itself), it would arrive as a new unread email, become a ticket, trigger another confirmation, and so on.

## Decision
In `mailer.py`:
- Build the email with Python's `EmailMessage`: the brief's HTML body plus a **plain-text version** made from it with `email_reader.strip_html()`.
- **HTML-escape the title** (`html.escape`) before putting it in the HTML. The ticket number comes from monday and is a number.
- Send it through the **Gmail API** (`messages.send`) as a **new email**, not a reply, as Make did. Gmail sets the "From" address.
- Do not retry a failed send; `main.py` logs it (ADR 0009: the item already exists).
- **Loop guard:** the self-test refuses the inbox's own address (read from the Gmail profile, not hard-coded), and `main.py` will skip unread emails sent by the inbox itself.

## Alternatives
- **HTML only:** matches the brief, but some apps and spam filters treat HTML-only emails worse.
- **Write a separate plain-text template:** more control, but two templates to keep in sync.
- **Reply in the customer's thread:** nicer for the customer, but needs extra headers and thread IDs, and differs from Make. Can be added later.
- **No escaping:** simpler, but trusts AI output built from customer text.

## Consequences
- The email matches the brief and shows correctly in HTML and plain-text apps.
- Customer or AI text cannot inject HTML into the confirmation.
- The confirmation starts a new thread, so the customer sees two threads (their request and our confirmation).
- A failed confirmation means the customer gets no email for that ticket; the log line shows which one.
- The loop guard depends on `main.py` comparing each sender with the inbox's address; that check must be in the `main.py` step.
