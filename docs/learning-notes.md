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

### Rate limits (staying under 15 requests per minute)
The Gemini free tier allows **15 requests per minute**. Above that, Google answers with error **429** ("too many requests").
We handle this in two ways:

1. **Prevent it: space out the calls.** `wait_for_rate_limit()` runs before every Gemini call, retries included.
   It remembers when the last call happened and, if needed, sleeps until **4 seconds** have passed (60 seconds / 15 = 4).
   So we can never send more than 15 calls in a minute. Both `evaluate.py` and the real pipeline go through `classify()`, so both are protected.
   The price: 20 emails take at least about 80 seconds.
2. **If it still happens: wait as long as Google asks.** A 429 error includes `retryDelay`, e.g. `"37s"`.
   `get_retry_delay(error)` reads it, and we wait that long plus 1 second. If Google gives no time, we use our own backoff (2s, then 4s).
   If Google asks for more than 60 seconds, the **daily** quota is probably used up. Waiting would not help, so we stop with an error.

Limitation: the spacing works inside one running program. Two programs using the same key at the same time could still go over the limit together.

More Python concepts used here:
- **`time.monotonic()`**: a clock that only moves forward, good for measuring how much time passed. (The normal clock can jump, e.g. when the computer syncs its time.)
- **`global last_call_time`**: inside a function, this says "change the variable defined at the top of the file", not a new local one.
- **`"37s".rstrip("s")`**: removes the `s` from the end, giving `"37"`. `float(...)` turns it into the number 37.0.
- **`except (KeyError, TypeError, ValueError):`**: catches several error types in one line. Here: the error has an unexpected format, so we fall back to our own backoff.
- **`pass`**: "do nothing". Python needs at least one line inside a block.


###### Picking the employee (`router.py`) ######

### What is it for?
It decides which employee gets the ticket, based on the category.
This is a **fixed rule, not the AI**, like the Switch module in Make.
The AI only picks the category; our code picks the person. That way the assignment is always predictable and easy to check.

### How it works
`assign(category)` looks the category up in `config.ROUTING`:
- Daniel Anderson: Login & Access, Software & System, Performance
- Ryan Mitchell: Network & Connectivity, Hardware, Installation & Configuration
- Anything else (including an unexpected value): Emily Carter, the default

The table lives in `config.py`. `router.py` only uses it, so the rule is written in one place.

### Python concepts in this file
- **`dict.get(key, default)`**: returns the value for `key`, or `default` if the key is not in the dictionary. Like `getOrDefault()` on a Java `HashMap`. No error is raised for a missing key.
- **`list + list`**: joins two lists into a new one. The self-test uses it to add one made-up category to the real ones.
- **`f"{name:<38}"`**: pads the text to 38 characters, aligned left, so the output lines up in columns.


###### Measuring accuracy (`evaluate.py`) ######

### What is it for?
It tests how accurate the AI is, without Gmail or monday.
It runs our classifier and router on the 30 test emails from the Make version (`test-data/`), compares each answer to the expected one, and prints the accuracy.
This proves, with numbers, that the Python version works as well as the Make version.

### How to run it
- `python evaluate.py`: runs both test files.
- `python evaluate.py test-data/heido_test_cases.csv`: runs one file.
- `python evaluate.py --out results.csv`: also saves all results to a CSV you can open in Excel.

### What it prints
1. One progress line per email, e.g. `T01  category OK  priority OK  assignee OK`.
2. A report for each file: the accuracy for category, priority and assignee, the errors, and a list of mismatches.
3. A **Combined** report for all emails together.

### Errors vs. wrong answers
These are two different things, so they are reported separately:
- **Wrong answer (mismatch)**: the AI answered, but not what we expected. This tells us about the AI's quality.
- **Error**: there was no answer at all, e.g. a 429 rate-limit error. This tells us nothing about the AI.

So the accuracy is calculated **only on emails that got an answer**. For example, `Category 13/13 100%` with `Errors: 2` means 13 emails were answered and all 13 were correct; 2 emails failed and are listed under "Error details".

### The functions
- **`evaluate_row(row, file_name)`**: classifies one test email with the existing `classify()` and `assign()`, and stores expected vs. actual values. If the API fails, it saves the error so the run continues.
- **`evaluate_file(path)`**: reads one CSV and calls `evaluate_row` for each row.
- **`is_match(result, field)`**: True if actual equals expected.
- **`print_report(title, results)`**: prints the accuracy (answered emails only), the errors and the mismatches. Called once per file and once for the combined list, so the printing code is written only once.
- **`save_results(results, path)`**: writes all results to a CSV.
- **`main()`**: reads the command-line options and runs everything.

### How accuracy is calculated
accuracy = correct answers / number of answered emails (errors left out). For example, 14 correct out of 15 = 93%.
One email is about 7% of a 15-email file, so a single difference changes the number a lot.
The AI is not 100% repeatable, so a run can differ from the Make results by one email.

### Python concepts in this file
- **`argparse`**: reads options from the command line (`--out results.csv`). `nargs="*"` means "zero or more file names". If none are given, `default` is used.
- **`csv.DictReader`**: reads a CSV where each row becomes a dict, e.g. `row["subject"]`.
- **`csv.DictWriter`**: the opposite: writes a list of dicts to a CSV.
- **`encoding="utf-8-sig"`**: the test files start with a hidden BOM character. This encoding skips it; without it, the first column name would be wrong.
- **List comprehension** `[x for x in items if ...]`: builds a new list in one line. Like a short `for` loop that collects values.
- **Dict comprehension** `{path: evaluate_file(path) for path in files}`: the same, but builds a dict.
- **`sum(1 for ... if ...)`**: counts how many items match a condition.
- **`except Exception as error`**: catches any error, so one bad row does not stop the whole run.
- **`f"{value:.0%}"`**: formats a number like 0.933 as `93%`.
