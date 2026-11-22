# 0014. Polling loop, per-email isolation, logging and scheduler readiness

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
`main.py` connects all the building blocks. Several questions had to be answered:
- **How is the program triggered?** Make watched the inbox on Make's servers. The brief suggests running `main.py` in a loop every N minutes, and perhaps a scheduler later.
- **What if one email fails?** The brief requires that one failing email must not stop the others.
- **How do we know what happened?** The brief requires one log line per email, to the console and a file.
- **Future automation:** a scheduler (Windows Task Scheduler, GitHub Actions) runs the program unattended, often from a different folder, and needs a way to see whether a run failed.

## Decision
- **Polling inside the program:** `python main.py` runs, then sleeps `--interval` minutes (default 5), until Ctrl+C. `--once` runs a single time. `--dry-run` classifies and logs without changing anything.
- **Each email in its own `try/except`:** a failure before the monday item exists leaves the email unread (retried next run); failures after it (file upload, confirmation) are logged and do not stop the email or the run (ADR 0009). A failure of the whole run is logged and the loop continues.
- **Logging:** Python's `logging`, to the console and `logs/heido.log` (git-ignored). One summary line per email with message ID, category, priority, assignee, item ID, files uploaded and confirmation result, or the error. No customer email text in the log.
- **Loop guard:** emails sent by the support inbox itself are skipped and marked as read (ADR 0013).
- **Scheduler readiness:**
  - With `--once`, the exit code is `0` if no email failed and `1` otherwise (an email left unread, or a failed run).
  - All files are found next to the code (`os.path.dirname(__file__)`): `credentials.json` and `token.json` in `gmail_client.py`, `prompt.txt`, `logs/`; `.env` is found by `load_dotenv()` from the code's folder.

## Alternatives
- **Gmail push notifications (Pub/Sub):** near-instant, but needs a public web endpoint and a Google Cloud Pub/Sub setup; far more than a support inbox needs.
- **Only an external scheduler, no loop:** fine for 24/7 use, but needs setup before the program is useful. The loop works out of the box, and `--once` keeps the scheduler option open.
- **Stop the run at the first failing email:** simpler, but one bad email would block all others.
- **Exit code 1 also for a failed upload or confirmation:** stricter, but those emails were processed and will not be retried; they are visible as `ERROR` lines in the log.

## Consequences
- The pipeline runs with one command and survives single-email and whole-run failures.
- New emails wait up to `--interval` minutes (default 5) before they are processed.
- It only runs while the program is running: closing the terminal or turning off the computer stops it, unlike Make.
- A scheduler can run `python main.py --once` from any folder and mark failed runs by the exit code.
- **Known limitation for unattended use:** while the Google Cloud app is in "Testing" mode, `token.json` expires after 7 days, and signing in again needs a browser. Running unattended for longer requires publishing the OAuth app to "Production" (a later decision).
- `logs/heido.log` grows over time; rotation is not needed at this volume.
