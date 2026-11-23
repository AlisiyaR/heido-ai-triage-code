# Heido AI Inquiry Triage – Python version

An automation pipeline that turns customer support emails into tasks for **Heido**, a fictional IT services company.

**Gmail** → **Google Gemini** (classifies the email) → **fixed routing rule** (picks the employee) → **monday.com** task (with attachments) → **confirmation email** to the customer.

This is a code rebuild of the no-code version built on Make.com: **[heido-ai-triage](https://github.com/AlisiyaR/heido-ai-triage)**. Both versions automate the same business process and give the same classification results.

## How it works

For every unread email in the support inbox, `main.py`:

1. reads the email and its attachments (`email_reader.py`);
2. sends **only the subject and body** to Gemini, which returns a title, a one-sentence summary, a category (one of 9) and a priority (High / Medium / Low) (`classifier.py`);
3. picks the responsible employee from the category with a **fixed rule, not the AI** (`router.py`);
4. creates an item on the monday.com board with all 10 columns and uploads the attachments (`monday_client.py`);
5. marks the email as read, so it is never processed twice;
6. sends the customer a confirmation with the ticket number (`mailer.py`).

Details, diagrams and the reasons behind each design choice are in the [documentation](#documentation).

## Improvements over the Make version

| | Make version | Python version |
|---|---|---|
| Gemini overloaded (503) or rate-limited (429) | email fails | retried, waiting the time Google asks for |
| Gemini free-tier limit (15 requests/min) | can be exceeded | calls spaced 4 seconds apart |
| Invalid AI answer (unknown category/priority) | passed through | replaced with a safe default and logged |
| One email fails | – | the others continue; the failed one is retried next run |
| Logging | Make run history | one line per email, in the console and `logs/heido.log` |
| Accuracy testing | by hand | `python evaluate.py` |
| Try without changing anything | – | `--dry-run` |

## Evaluation results

Classification accuracy on the same 30 test emails used for the Make version (prompt v2, `gemini-3.5-flash-lite`):

| Set | Category | Priority | Assignee |
|---|---|---|---|
| Development (15) | 93% | 100% | 93% |
| Holdout (15) | 100% | 93% | 100% |
| **Combined (30)** | **97%** | **97%** | **97%** |

Same results as the Make version, with 0 errors. The test set includes vague emails and prompt-injection attempts. Rerun it with `python evaluate.py` (see below).

## Tech stack

Python 3.13 · Gmail API (OAuth) · Google Gemini (`google-genai`) · monday.com GraphQL API · Pydantic · python-dotenv

## Setup

### Prerequisites
- **Python 3.13**
- A **Gmail** account for the support inbox
- A **Google Cloud** project with:
  - the **Gmail API** enabled;
  - an **OAuth client** of type **Desktop app** (download its JSON);
  - the support inbox added as a **test user** on the OAuth consent screen.
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/)
- A **monday.com** account with:
  - a personal **API token** (avatar → Developers → My access tokens);
  - a board with the columns listed in [ARCHITECTURE.md](docs/ARCHITECTURE.md) (section 4.7), and the board ID and group ID to write to.

### Install
```powershell
git clone https://github.com/AlisiyaR/heido-ai-triage-code.git
cd heido-ai-triage-code
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Configure
1. Copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`, `MONDAY_API_TOKEN`, `MONDAY_BOARD_ID` and `MONDAY_GROUP_ID`.
2. Save the downloaded OAuth client JSON as `credentials.json` in the project folder.
3. Sign in to Gmail once:
   ```powershell
   python gmail_client.py
   ```
   A browser opens; sign in as the support inbox and allow access. This creates `token.json`, and the script prints the address and the unread count.

`.env`, `credentials.json` and `token.json` are secret and git-ignored. While the Google Cloud app is in "Testing" mode, `token.json` expires after 7 days: delete it and run `python gmail_client.py` again.

## How to run

| Command | What it does |
|---|---|
| `python main.py --dry-run --once` | Rehearsal: reads and classifies unread emails and logs what *would* be created. Changes nothing. |
| `python main.py --once` | Processes all unread emails (up to 20) once, then exits. |
| `python main.py` | Checks the inbox every 5 minutes until Ctrl+C. |
| `python main.py --interval 10` | Same, every 10 minutes. |

Example log from a real run (also saved in `logs/heido.log`):
```
2026-11-22 22:47:37 INFO Starting (LIVE, once, up to 20 emails per run)
2026-11-22 22:47:40 WARNING Gemini error 503 (attempt 1/3), waiting 2s (backoff)
2026-11-22 22:47:48 INFO msg=1a1e8d01fbac3589 category='Login & Access Issues' priority=High assignee='Daniel Anderson' item=3375882756 files=1/1 confirmation=sent
2026-11-22 22:47:55 INFO msg=1a204f6a24610035 category='Hardware Issues' priority=High assignee='Ryan Mitchell' item=3375899766 files=1/1 confirmation=sent
2026-11-22 22:47:55 INFO Run finished: 2 email(s), 2 created, 0 skipped, 0 dry run, 0 failed
```

With `--once`, the exit code is `0` if no email failed and `1` otherwise, so a scheduler can detect failed runs. The program works when started from any folder.

### Accuracy test
```powershell
python evaluate.py                      # both test sets, plus a combined total
python evaluate.py --out results.csv    # also save every row to a CSV
```
No Gmail or monday is used. It takes about 2 minutes because of the rate limit.

### Testing one part at a time
Each module has a self-test:

| Command | Checks |
|---|---|
| `python gmail_client.py` | Gmail sign-in; prints the address and unread count |
| `python classifier.py` | classifies one sample email |
| `python router.py` | prints the employee for every category |
| `python email_reader.py` | lists unread emails and attachments (does not mark them as read) |
| `python monday_client.py` | creates one `[TEST]` item and uploads a small file |
| `python mailer.py` | sends one test confirmation to an address you type in |

## Project structure

```
├── main.py              # runs the full pipeline
├── config.py            # settings and constants; secrets from .env
├── gmail_client.py      # Gmail API sign-in (OAuth)
├── email_reader.py      # read unread emails and attachments
├── prompt.txt           # the AI prompt (v2)
├── classifier.py        # Gemini call, validation, retry, rate limit
├── router.py            # category → employee
├── monday_client.py     # create the monday item, upload files
├── mailer.py            # confirmation email
├── evaluate.py          # accuracy test
├── test-data/           # 30 test emails (from the Make version)
├── docs/                # architecture, decisions, final check, brief
├── requirements.txt
└── .env.example
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md): components, data flow diagrams, error handling, limits
- [Architecture Decision Records](docs/adr/): why each design choice was made (14 decisions)
- [Final check](docs/final-check.md): the project checked against its definition of done
- [Python concepts](docs/python-concepts.md): the Python ideas used in the code, explained
- [Build brief](docs/build-brief.md): the original requirements

## Known limitations

- **Runs only while the program runs.** Closing the terminal stops it (Make runs on Make's servers). `main.py --once` is ready for a scheduler such as Windows Task Scheduler.
- **Gmail token in "Testing" mode** expires after 7 days; running unattended for longer needs the OAuth app published to "Production".
- **More than 20 unread emails:** Gmail returns the 20 newest; the rest are processed in later runs.
- **Rate limit:** at most 15 Gemini calls per minute, so 20 emails take at least about 80 seconds.

## License

[MIT](LICENSE) © 2026 Alisiya Rabinovich
