# Python concepts – Heido

Python ideas used in this project, explained for a beginner with a Java background. Grouped by the file where each idea first appears. For how the system is built, see [ARCHITECTURE.md](ARCHITECTURE.md).

## `gmail_client.py`

- **`import`**: loads code from libraries, like `import` in Java.
- **`os.path.exists`**: checks whether a file exists.
- **`with open(...) as f:`**: opens a file and closes it automatically at the end of the block, even if an error happens (like try-with-resources in Java).
- **`if __name__ == "__main__":`**: the code in this block runs only when you run the file directly (`python gmail_client.py`), not when another file imports it. We use it for a self-test.
- **f-string** (`f"...{x}..."`): puts a variable's value inside text.


## `config.py`

- **Module**: every `.py` file is a module. `import config` runs the file once and gives access to its variables.
- **UPPER_CASE names**: the Python convention for constants (like `static final` in Java). Python does not enforce it; it is a signal to other programmers.
- **list** `[...]`: an ordered collection, like `ArrayList` in Java. Used for `CATEGORIES`.
- **dict** `{key: value}`: a lookup table, like `HashMap` in Java. Used for `ROUTING` and `COLUMNS`.
- **`raise`**: stops the program with an error, like `throw` in Java.
- **`if not value:`**: true when the value is `None` (missing) or an empty string.
- **Triple-quoted string** `"""..."""`: text that spans several lines. Used for the HTML email.
- **`{item_id}` in a string**: a placeholder, filled in later with `.format(item_id=...)`.


## `classifier.py`

- **Pydantic `BaseModel`**: a class that describes data and checks it. `title: str` means "title must be text". Similar to a Java class with typed fields, plus automatic checking.
- **`try / except`**: like `try / catch` in Java. `except errors.APIError as error:` catches only Gemini API errors.
- **`raise`** with nothing after it (inside `except`): throws the same error again, so the caller sees it.
- **`for attempt in range(1, MAX_ATTEMPTS + 1):`**: loops with attempt = 1, 2, 3, 4, 5. `range` stops *before* the second number.
- **`time.sleep(seconds)`**: pauses the program.
- **`BACKOFF_SECONDS[attempt - 1]`**: picks one wait from a list. Lists count from 0, so attempt 1 gets `BACKOFF_SECONDS[0]` (5 seconds), attempt 2 gets 10 seconds, and so on. A plain list is easier to read and change than a formula.
- **`logging`**: like `print`, but every line has a level (INFO, WARNING, ERROR) and can go to the console and a file. `logger = logging.getLogger(__name__)` creates a logger named after the file.
- **`%r` / `%s` / `%d` in log messages**: placeholders. `%r` shows the value with quotes, so empty or odd values are easy to spot.
- **`os.path.dirname(__file__)`**: the folder of the current file, so `prompt.txt` is found no matter where you run the program from.

### Rate limiting (`wait_for_rate_limit`, `get_retry_delay`)

- **`time.monotonic()`**: a clock that only moves forward, good for measuring how much time passed. (The normal clock can jump, e.g. when the computer syncs its time.)
- **`global last_call_time`**: inside a function, this says "change the variable defined at the top of the file", not a new local one.
- **`"37s".rstrip("s")`**: removes the `s` from the end, giving `"37"`. `float(...)` turns it into the number 37.0.
- **`except (KeyError, TypeError, ValueError):`**: catches several error types in one line. Here: the error has an unexpected format, so we fall back to our own backoff.
- **`pass`**: "do nothing". Python needs at least one line inside a block.


## `router.py`

- **`dict.get(key, default)`**: returns the value for `key`, or `default` if the key is not in the dictionary. Like `getOrDefault()` on a Java `HashMap`. No error is raised for a missing key.
- **`list + list`**: joins two lists into a new one. The self-test uses it to add one made-up category to the real ones.
- **`f"{name:<38}"`**: pads the text to 38 characters, aligned left, so the output lines up in columns.


## `evaluate.py`

- **`argparse`**: reads options from the command line (`--out results.csv`). `nargs="*"` means "zero or more file names". If none are given, `default` is used.
- **`csv.DictReader`**: reads a CSV where each row becomes a dict, e.g. `row["subject"]`.
- **`csv.DictWriter`**: the opposite: writes a list of dicts to a CSV.
- **`encoding="utf-8-sig"`**: the test files start with a hidden BOM character. This encoding skips it; without it, the first column name would be wrong.
- **List comprehension** `[x for x in items if ...]`: builds a new list in one line. Like a short `for` loop that collects values.
- **Dict comprehension** `{path: evaluate_file(path) for path in files}`: the same, but builds a dict.
- **`sum(1 for ... if ...)`**: counts how many items match a condition.
- **`except Exception as error`**: catches any error, so one bad row does not stop the whole run.
- **`f"{value:.0%}"`**: formats a number like 0.933 as `93%`.


## `email_reader.py`

- **`@dataclass`**: put above a class, it writes the constructor (`__init__`) and a readable print-out for you, from the field list. Like a Java class with only fields, a constructor and `toString()`, but in a few lines. Similar to a Java `record`.
- **Type hints** (`subject: str`, `attachments: list[Attachment]`): say what type a field should hold. Python does not enforce them at runtime; they help readers and editors.
- **`field(default_factory=list)`**: gives each new object its own empty list. Writing `= []` directly would make every object share the same list.
- **`bytes`**: raw binary data (e.g. a PDF file), not text. `.decode("utf-8")` turns bytes into text.
- **`base64.urlsafe_b64decode`**: Gmail sends the raw email encoded as base64url (only letters, digits, `-` and `_`). This turns it back into bytes. The `"=" * (-len(data) % 4)` adds the padding that base64 needs.
- **`email.message_from_bytes(raw, policy=policy.default)`**: Python's built-in email parser. It turns the raw email bytes into an `EmailMessage` object. `policy.default` gives the modern behavior: headers like the subject come back already decoded (Hebrew included).
- **`msg.get_body(preferencelist=("plain", "html"))`**: finds the email's main text, preferring plain text, and skips attached files. Returns `None` if there is no text.
- **`part.get_content()`**: returns the text of a part, decoded from base64 and from its charset (e.g. `windows-1255`). One call replaces hand-written decoding.
- **`msg.walk()`**: goes through every part of the email at every level (an email is a tree: a part can contain parts). Before, we wrote this tree walk ourselves with recursion; the standard library already does it.
- **`part.get_filename()`, `part.get_content_type()`, `part.get_payload(decode=True)`**: the file name (or `None`), the type (e.g. `image/png`), and the file's bytes.
- **Shadowing a module name**: after `import email`, a variable named `email` would replace the module. That is why the self-test loop uses `message` as the variable name.
- **`datetime.fromtimestamp(seconds, tz=timezone.utc)`**: turns "seconds since 1970" into a date and time, in UTC. Gmail gives milliseconds, so we divide by 1000.
- **`email.utils.parseaddr`**: splits `"Dana Cohen <dana@x.com>"` into `("Dana Cohen", "dana@x.com")`.
- **Tuple unpacking** (`from_name, from_email = parseaddr(...)`): puts each value of a pair into its own variable in one line.
- **`re.sub(pattern, replacement, text)`**: replaces every match of a regular expression. `(?i)` means ignore upper/lower case; `(?s)` lets `.` match line breaks too.
- **`f"{message.received_at:%Y-%m-%d %H:%M}"`**: formats a date inside an f-string.
- **Import inside `if __name__ == "__main__":`**: `gmail_client` is only needed by the self-test, so it is imported there and not when another file imports `email_reader`.


## `monday_client.py`

- **`requests.post(url, ...)`**: sends an HTTP POST request and returns a response object. `json=` sends a dict as JSON; `data=` sends form fields; `files=` uploads files; `headers=` adds headers like `Authorization`; `timeout=` stops waiting after N seconds instead of hanging forever.
- **`response.json()`**: turns the answer's JSON text into a Python dict. It raises `ValueError` if the answer is not JSON.
- **`response.raise_for_status()`**: raises an error if the HTTP status is 400 or higher (e.g. 401 Unauthorized, 500 Server Error).
- **`json.dumps(obj)`**: turns a dict into a JSON string. monday wants `column_values` as a JSON *string*, not as a nested object.
- **GraphQL**: a query language for APIs. You send one request with a "query" (or "mutation", for changes) that says exactly what to do and which fields to return, e.g. `create_item(...) { id }` returns only the new item's ID.
- **GraphQL variables** (`$itemName`): placeholders in the query, with the real values sent separately. Like a `PreparedStatement` with `?` in Java JDBC: user text can never break the query.
- **Multipart upload**: the format browsers use to upload files in a form. `requests` builds it when you pass `files={"field": (filename, bytes, mime_type)}`.
- **`f"{{ }}"` in f-strings**: double braces produce a literal `{` or `}`, because single braces mean "insert a value here".
- **`datetime.strftime("%Y-%m-%d")`**: formats a date as text, e.g. `2026-11-22`. `%H:%M:%S` gives the time.
- **`a or b` as a fallback**: returns `a` if it is not empty, otherwise `b`. Used for `email.from_name or email.from_email`.
- **`int("123")`**: turns text into a whole number; it raises `ValueError` for text like `"12; drop"`. Used as a safety check before putting the item ID into a query.
- **Duck typing**: `build_column_values` does not import the `Email` or `Classification` classes; it only uses their attributes (`email.body`, `classification.title`). Any object with those attributes works, which also makes testing easy.


## `mailer.py`

- **`EmailMessage`** (from `email.message`): Python's built-in way to build an email. You set headers like a dict (`message["To"] = ...`), then the content.
- **`set_content(text)` + `add_alternative(html, subtype="html")`**: creates one email with two versions of the same text, plain and HTML ("multipart/alternative"). The email app shows the best one it supports.
- **`message.as_bytes()`**: turns the finished email into the raw bytes that mail servers send. Non-English characters (like the "–" in the subject) are encoded automatically.
- **`base64.urlsafe_b64encode(bytes)`**: the reverse of what `email_reader.py` does: turns bytes into base64url text, because the Gmail API wants the raw email in that form. `.decode("ascii")` turns the result into a normal string.
- **`html.escape(text)`**: replaces `<`, `>`, `&` and quotes with safe codes (`&lt;`, `&gt;` ...), so text is shown as text and never treated as HTML.
- **`str.format(name=value)`**: fills named placeholders like `{item_id}` in a template string. Extra placeholders that are not in the template are an error, so the template and the code must match.
- **`input("question ")`**: shows a question in the terminal and waits for the user to type an answer. Used only in the self-test.
- **`.strip()` and `.lower()`**: remove spaces at both ends, and make text lower case. Used to compare two email addresses safely ("Heido.Support@Gmail.com" and "heido.support@gmail.com" are the same address).
- **Importing a function from another module** (`from email_reader import strip_html`): reuses code instead of writing it twice.


## `main.py`

- **`argparse` flags**: `action="store_true"` makes an on/off switch (`--once` present means `True`); `type=int` turns `--interval 10` into the number 10. `--dry-run` becomes `args.dry_run` (the dash becomes an underscore).
- **`logging.basicConfig(...)`**: sets up logging once for the whole program: the level (INFO and above), the line format (`%(asctime)s %(levelname)s %(message)s`) and the **handlers**, which decide where lines go. Here: `StreamHandler` (the console) and `FileHandler` (a file).
- **Loggers in other files**: `classifier.py` uses `logging.getLogger(__name__)`. Because `main.py` configured logging, those warnings also appear on screen and in the log file, with no extra code.
- **Logger names and `setLevel`**: loggers are arranged by name like folders. `logging.getLogger("google_genai").setLevel(logging.WARNING)` hides that library's INFO lines, and also those of `google_genai.models` and every other "child" logger under that name. Our own loggers are not affected.
- **`logger.exception("...")`**: like `logger.error`, but also writes the full error details (the traceback). Use it inside `except`.
- **`os.makedirs(path, exist_ok=True)`**: creates a folder (and its parents); `exist_ok=True` means "no error if it already exists".
- **`while True:` + `time.sleep(seconds)`**: an endless loop that pauses between rounds. It ends only by `return`, `break` or an exception.
- **`KeyboardInterrupt`**: the exception Python raises when you press Ctrl+C. Catching it lets the program stop cleanly with a log line instead of a long error.
- **Nested `try/except`**: the inner one (around each email) keeps the loop going when one email fails; the outer one (around the whole loop) catches Ctrl+C.
- **`sys.exit(code)`**: ends the program with an exit code. `0` means success, anything else means failure. In PowerShell, `echo $LASTEXITCODE` shows the code of the last command.
- **Module-level constants as named results** (`CREATED`, `SKIPPED`): names instead of repeated strings, so a typo becomes an error instead of a silent bug.
- **`counts[result] += 1`**: uses the returned value as a dictionary key to count each kind of result.
