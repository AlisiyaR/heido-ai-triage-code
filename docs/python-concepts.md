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
- **`for attempt in range(1, MAX_ATTEMPTS + 1):`**: loops with attempt = 1, 2, 3. `range` stops *before* the second number.
- **`time.sleep(seconds)`**: pauses the program.
- **`2**attempt`**: "2 to the power of attempt" (2, 4).
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
- **`base64.urlsafe_b64decode`**: Gmail sends file and text content encoded as base64url (only letters, digits, `-` and `_`). This turns it back into bytes. The `"=" * (-len(data) % 4)` adds the padding that base64 needs.
- **Recursion**: a function that calls itself. An email is a tree of parts (a part can contain parts), so `find_text_part` and `collect_attachments` call themselves on each sub-part.
- **`datetime.fromtimestamp(seconds, tz=timezone.utc)`**: turns "seconds since 1970" into a date and time, in UTC. Gmail gives milliseconds, so we divide by 1000.
- **`email.utils.parseaddr`**: splits `"Dana Cohen <dana@x.com>"` into `("Dana Cohen", "dana@x.com")`.
- **Tuple unpacking** (`from_name, from_email = parseaddr(...)`): puts each value of a pair into its own variable in one line.
- **`dict.get(key, default)` on nested data**: `part.get("body", {}).get("data")` reads a value two levels deep without crashing if a level is missing.
- **`next((... for ... if ...), "")`**: returns the first item that matches, or `""` if none does.
- **`re.sub(pattern, replacement, text)`**: replaces every match of a regular expression. `(?i)` means ignore upper/lower case; `(?s)` lets `.` match line breaks too.
- **`f"{email.received_at:%Y-%m-%d %H:%M}"`**: formats a date inside an f-string.
- **Import inside `if __name__ == "__main__":`**: `gmail_client` is only needed by the self-test, so it is imported there and not when another file imports `email_reader`.
