# 0008. Secrets in `.env`, all settings in `config.py`, fail fast

- **Status:** Accepted
- **Date:** 2026-11-18

## Context
The system needs secrets (Gemini API key, monday token) and many fixed settings (board and group IDs, 10 column IDs, 9 categories, the routing table, the confirmation email).
Secrets must never reach GitHub. Settings are used by several files and must not be repeated.
A missing secret should be noticed immediately, not deep inside a run.

## Decision
- Secrets live only in `.env` (git-ignored). A committed `.env.example` lists the keys with empty values.
- `config.py` loads `.env` with `python-dotenv` and holds every other setting as an UPPER_CASE constant. Other files use `import config`.
- `require_env(name)` raises `RuntimeError("Missing NAME in .env")` when a value is missing or empty, so the program stops at start-up with a clear message.
- Gmail credentials are not in `.env`: they are the OAuth files `credentials.json` and `token.json`, also git-ignored (see [0001](0001-gmail-api-with-oauth.md)).

## Alternatives
- **Hard-code values in each file:** fast to start, but secrets could be committed and settings would be duplicated.
- **Read environment variables directly wherever needed:** works, but a missing value would cause a confusing error later.
- **A YAML/JSON settings file or a settings library:** more structure than this project needs.

## Consequences
- No secrets in the repository; a full scan of the git history confirmed it.
- Changing a column ID or an employee name means editing one line.
- All four `.env` values are required at import, even by `evaluate.py`, which only needs the Gemini key. Simple, but strict; it can be relaxed later if needed.
