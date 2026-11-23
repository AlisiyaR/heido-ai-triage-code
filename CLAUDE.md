# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Heido is a support-email automation pipeline that connects three services:

1. **Gmail**: source of incoming support emails.
2. **Google Gemini**: classifies each email (the LLM step).
3. **monday.com**: where tasks are created from the classified emails.

Data flow: Gmail → Gemini classification → monday.com task.

## Relationship to the no-code version

This repository is the code-based version of Heido. The original no-code version, built on Make.com, lives in the public repo `heido-ai-triage`. Both versions automate the same business process, so the no-code version is the reference for intended behavior.

## Communication

- The user may write in Hebrew. Always reply in English.
- Always write code, comments, commit messages and documentation in English.

## Working rules

### Workflow
Explain everything in simple words. For each task:
1. Explain the plan and wait for my approval before writing code.
2. Write the code. Change only what the task needs and keep changes small.
3. Self-review the new or changed code (see below), then mention briefly what you simplified.
4. Tell me how to run and check that it works.
5. After each feature, update docs/ARCHITECTURE.md (simple English, for a beginner), add a numbered ADR in docs/adr/ (copy 0000-template.md) for each new decision, and add new Python concepts to docs/python-concepts.md.
6. Don't commit or push without my approval. Use short, clear commit messages.

### Code style
- Simple, readable code with clear names. Prefer the shortest solution that fully works.
- Every function gets a short English docstring (what it does, inputs, outputs).
- Add comments only where the code isn't obvious, explaining why.

### Self-review
Before presenting new or changed code, check it and fix:
- repeated code;
- functions that do more than one thing, or are longer than ~40 lines (if one must stay longer, explain why);
- anything I didn't ask for (extra classes, layers or features);
- custom code where the standard library or an already-installed package does the job;
- deep nesting where a simpler structure works (e.g. an early return or a small helper).

These fixes apply only to the code of the current task.

### Ask first
- Before changing, deleting or refactoring other existing code, explain why and wait for my approval.
- Before adding a new package, explain why it's needed.
- If something is unclear, ask me instead of guessing.

### Security
- Never read, print or log secrets (.env, credentials.json, token.json).
- Never hardcode API keys, passwords or tokens. Load them from .env.

## Status

Python 3.13 in `.venv`. Each module has a self-test under `if __name__ == "__main__":`. There is no test framework or linter yet.

- All components are built: `gmail_client.py`, `config.py`, `prompt.txt` + `classifier.py`, `router.py`, `evaluate.py`, `email_reader.py`, `monday_client.py`, `mailer.py`, `main.py`
- `requirements.txt` pins the direct dependencies to the tested versions.
- `README.md`: complete (setup, how to run, evaluation, limitations).
- Docs: `docs/ARCHITECTURE.md` (how the system is built), `docs/adr/` (one file per decision), `docs/python-concepts.md`, `docs/final-check.md` (definition of done, with evidence), `docs/build-brief.md` (requirements)
- All definition-of-done checks in `docs/final-check.md` have passed, including the manual failure and other-folder tests. Optional next step: scheduled runs.

### Setup and run
    py -3.13 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python gmail_client.py   # first run opens a browser sign-in and creates token.json
    python classifier.py     # classifies one sample email
    python evaluate.py       # accuracy on both test CSVs in test-data/ (add --out results.csv to save)
    python email_reader.py   # lists unread INBOX emails; does not mark them as read
    python monday_client.py  # creates one [TEST] item in the configured group and uploads a small file
    python mailer.py         # asks for an address and sends one test confirmation (refuses the support inbox)
    python main.py --dry-run --once   # rehearsal: classify unread emails, change nothing
    python main.py --once             # process unread emails once (exit code 1 if any failed)
    python main.py                    # run every 5 minutes until Ctrl+C (--interval N to change)

### Credentials and config
- `.env` (copied from `.env.example`): `GEMINI_API_KEY`, `MONDAY_API_TOKEN`, `MONDAY_BOARD_ID`, `MONDAY_GROUP_ID`. Loaded by `config.py`.
- Gmail uses OAuth (Desktop app, scope `gmail.modify`): `credentials.json` identifies the app, `token.json` is created on first sign-in.
- All secret files are git-ignored.

### Classification and routing
- The 9 categories are in `config.CATEGORIES` and must match `prompt.txt`. An unknown category becomes `Other / Unclassified`, and an unknown priority becomes `Medium`.
- The assignee comes from a fixed rule, `config.ROUTING`, not from the AI. The default is Emily Carter.
- Gemini calls are limited to `config.GEMINI_REQUESTS_PER_MINUTE` (15, free tier): `classifier.py` spaces calls 4s apart and, on 429/503, retries up to 5 attempts, waiting Google's `retryDelay` (max 60s) or 5/10/20/40s.
- monday.com column IDs are in `config.COLUMNS`.

### Email fetching and running
Polling: `main.py` runs every 5 minutes (`--interval N`) and reads up to 15 unread INBOX emails through the Gmail API. An email is marked as read once its monday item exists, so it is never processed twice. Emails sent by the inbox itself are skipped. Logs go to `logs/heido.log`. With `--once`, the exit code is 1 if any email failed.
