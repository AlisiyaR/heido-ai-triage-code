# Learning notes – Heido


###### Connecting to Gmail with OAuth (`gmail_client.py`) ######

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


###### Settings in one place (`config.py`) ######

### What is it for?
All settings live in one file. Other files write `import config` and use values like `config.CATEGORIES`.
If a monday column ID or an employee name changes, you fix it in one place only.

### Two kinds of settings
- **Secrets** (API key, token, board and group IDs): loaded from `.env`, never written in the code.
- **Fixed constants** (categories, routing table, column IDs, confirmation email): copied from the Make scenario.

### How secrets are loaded
1. `load_dotenv()` reads `.env` and puts each line into the program's environment variables.
2. `require_env(name)` reads one variable with `os.getenv(name)`.
3. If it is missing or empty, `require_env` raises an error with a clear message, e.g. `Missing MONDAY_GROUP_ID in .env`.
   It is better to stop at the start with a clear message than to fail later with a confusing one.

### Python concepts in this file
- **Module**: every `.py` file is a module. `import config` runs the file once and gives access to its variables.
- **UPPER_CASE names**: the Python convention for constants (like `static final` in Java). Python does not enforce it; it is a signal to other programmers.
- **list** `[...]`: an ordered collection, like `ArrayList` in Java. Used for `CATEGORIES`.
- **dict** `{key: value}`: a lookup table, like `HashMap` in Java. Used for `ROUTING` and `COLUMNS`.
- **`raise`**: stops the program with an error, like `throw` in Java.
- **`if not value:`**: true when the value is `None` (missing) or an empty string.
- **Triple-quoted string** `"""..."""`: text that spans several lines. Used for the HTML email.
- **`{item_id}` in a string**: a placeholder, filled in later with `.format(item_id=...)`.


###### The AI step (`prompt.txt` + `classifier.py`) ######

### What is it for?
Gemini reads an email's subject and body and returns 4 fields: `title`, `summary`, `category`, `priority`.
Only the subject and body are sent, never the sender's email address (data minimization: send only what is needed).

### Why the prompt is in its own file
`prompt.txt` holds the prompt text, with two placeholders: `{subject}` and `{body}`.
You can improve the prompt without touching any Python code.
`PROMPT_TEMPLATE.format(subject=..., body=...)` puts the real email into the placeholders.

### The three functions
1. **`classify(subject, body)`**: the only function other files use. It builds the prompt, calls Gemini, then validates the answer.
2. **`call_gemini(prompt)`**: sends the prompt to Gemini.
   - If Gemini says "too many requests" (429) or "overloaded" (503), it waits 2 seconds, tries again, then waits 4 seconds and tries a third time. This is called **retry with backoff**: each wait is longer than the last.
   - Any other error (for example a wrong API key) stops right away, because trying again would not help.
3. **`validate(result)`**: the AI can make mistakes, so we check its answer.
   - A category that is not one of the 9 becomes "Other / Unclassified".
   - A priority that is not High, Medium or Low becomes "Medium".
   - Each fix writes a warning to the log.

### What is a response schema?
We give Gemini the `Classification` model as a "schema", which is the exact shape of the answer we want.
Gemini must then return JSON with exactly those 4 fields, and the SDK turns it into a `Classification` object (`response.parsed`).
This is more reliable than asking for text and trying to cut it into pieces ourselves.

### Python concepts in this file
- **Pydantic `BaseModel`**: a class that describes data and checks it. `title: str` means "title must be text". Similar to a Java class with typed fields, plus automatic checking.
- **`try / except`**: like `try / catch` in Java. `except errors.APIError as error:` catches only Gemini API errors.
- **`raise`** with nothing after it (inside `except`): throws the same error again, so the caller sees it.
- **`for attempt in range(1, MAX_ATTEMPTS + 1):`**: loops with attempt = 1, 2, 3. `range` stops *before* the second number.
- **`time.sleep(seconds)`**: pauses the program.
- **`2**attempt`**: "2 to the power of attempt" (2, 4).
- **`logging`**: like `print`, but every line has a level (INFO, WARNING, ERROR) and can go to the console and a file. `logger = logging.getLogger(__name__)` creates a logger named after the file.
- **`%r` / `%s` / `%d` in log messages**: placeholders. `%r` shows the value with quotes, so empty or odd values are easy to spot.
- **`os.path.dirname(__file__)`**: the folder of the current file, so `prompt.txt` is found no matter where you run the program from.
