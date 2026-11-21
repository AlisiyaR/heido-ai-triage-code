# Learning notes – Heido

## Connecting to Gmail with OAuth (`gmail_client.py`)

### What is OAuth?
Instead of giving the program the Gmail account's password, you sign in once in the browser and click "Allow".
Google then gives the program a saved login, and the program uses it from then on.
Benefit: the real password is never in the code, and you can revoke access at any time from your Google account settings.

### Two important files
| File | What it is | Where it comes from |
|---|---|---|
| `credentials.json` | Identifies the **app** ("who is asking for access") | Downloaded once from Google Cloud Console |
| `token.json` | The **user's** saved login ("who allowed it") | Created automatically after the first browser sign-in |

Both files are secret. They are listed in `.gitignore`, so they never go to GitHub.

### What is a scope?
A scope is the permission the program asks for. We use `gmail.modify`, which allows us to:
- read emails
- mark an email as read
- send a confirmation email to the customer

This scope does **not** allow permanent deletion. We ask only for what we need.

### What `get_gmail_service()` does, step by step
1. If `token.json` exists, load the saved login from it.
2. If there is no login, or it is not valid:
   - if it only expired, renew it quietly (`refresh`), with no browser
   - otherwise, open the browser to sign in (`run_local_server`)
3. Save the login to `token.json` for next time.
4. Return a `service` object, which we use to talk to Gmail.

### Python concepts in this file
- **`import`**: loads code from libraries, like `import` in Java.
- **`os.path.exists`**: checks whether a file exists.
- **`with open(...) as f:`**: opens a file and closes it automatically at the end of the block, even if an error happens (like try-with-resources in Java).
- **`if __name__ == "__main__":`**: the code in this block runs only when you run the file directly (`python gmail_client.py`), not when another file imports it. We use it for a self-test.
- **f-string** (`f"...{x}..."`): puts a variable's value inside text.

### Why we moved from IMAP to the Gmail API
- No App Password is needed.
- The same connection is used both to read emails and to send the confirmation.
- It is the official way Google recommends.

### Important note
While the app in Google Cloud is in **Testing** mode, `token.json` expires after 7 days.
When that happens, delete `token.json` and run the program again. The browser will open so you can sign in again.
