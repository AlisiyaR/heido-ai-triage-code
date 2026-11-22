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

### Code style
- Write simple, clear, readable code. Prefer the shortest solution that fully works.
- No over-engineering: no extra classes, layers or features I didn't ask for.
- Use clear names for variables and functions.
- Every function gets a short English docstring (what it does, inputs, outputs).
- Add comments only where the code isn't obvious, explaining why.

### Changes
- Before writing code, explain the plan in simple words and wait for my approval.
- Never change, delete or refactor existing code without asking first and explaining why.
- Change only what the task needs. Keep changes small.
- Don't add new packages without asking and explaining why they're needed.

### Security
- Never read, print or log secrets (.env, credentials.json, token.json).
- Never hardcode API keys, passwords or tokens. Load them from .env.

### Testing and Git
- After a change, tell me how to run and check that it works.
- Don't commit or push without my approval. Use short, clear commit messages.

### Learning
- Explain what you're doing in simple words.
- After each feature, update docs/ARCHITECTURE.md (simple English, for a beginner) and add a numbered ADR in docs/adr/ (copy 0000-template.md) for each new decision. Add new Python concepts to docs/python-concepts.md.
- If something is unclear, ask me instead of guessing.

## Status

Python 3.13 in `.venv`. Each module has a self-test under `if __name__ == "__main__":`. There is no test framework or linter yet.

- Built: `gmail_client.py`, `config.py`, `prompt.txt` + `classifier.py`, `router.py`, `evaluate.py`, `email_reader.py`, `monday_client.py`, `mailer.py`
- Not built yet: `main.py`
- `README.md`: short overview with a work-in-progress status; full setup and run instructions come in the final step
- Docs: `docs/ARCHITECTURE.md` (how the system is built), `docs/adr/` (one file per decision), `docs/python-concepts.md`, `docs/build-brief.md` (requirements)

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

### Credentials and config
- `.env` (copied from `.env.example`): `GEMINI_API_KEY`, `MONDAY_API_TOKEN`, `MONDAY_BOARD_ID`, `MONDAY_GROUP_ID`. Loaded by `config.py`.
- Gmail uses OAuth (Desktop app, scope `gmail.modify`): `credentials.json` identifies the app, `token.json` is created on first sign-in.
- All secret files are git-ignored.

### Classification and routing
- The 9 categories are in `config.CATEGORIES` and must match `prompt.txt`. An unknown category becomes `Other / Unclassified`, and an unknown priority becomes `Medium`.
- The assignee comes from a fixed rule, `config.ROUTING`, not from the AI. The default is Emily Carter.
- Gemini calls are limited to `config.GEMINI_REQUESTS_PER_MINUTE` (15, free tier): `classifier.py` spaces calls 4s apart and, on 429/503, waits Google's `retryDelay` (max 60s).
- monday.com column IDs are in `config.COLUMNS`.

### Email fetching (planned)
Polling: `main.py` runs every few minutes and reads up to 20 unread INBOX emails through the Gmail API. An email is marked as read once its monday item exists, so it is never processed twice.
