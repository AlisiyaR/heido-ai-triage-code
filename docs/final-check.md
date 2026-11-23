# Final check – definition of done

The project checked against the definition of done in the [build brief](build-brief.md) (§8).
Checked on 2026-11-23, with prompt v2. Later the prompt was updated to v3 (English task title) and re-evaluated: 100% / 97% / 100% combined; see [ADR 0016](adr/0016-prompt-v3-english-title.md).

## Definition of done

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | A real email sent to the support inbox produces the same result as the Make version: correct task on the board, attachments uploaded, confirmation email received | ✅ Done | Live run on 2026-11-22: 2 real emails, each created a monday item with its attachment uploaded and a confirmation sent (see the log below). A second run found 0 emails, so nothing was processed twice. |
| 2 | `evaluate.py` on both test sets gives results comparable to the Make version | ✅ Done | 97% / 97% / 97% combined, the same as Make on every set (see below). 0 errors. |
| 3 | No secrets in the repository | ✅ Done | Full scan of all 20 commits and the current files (see below). |
| 4 | README explains the architecture, setup steps, how to run, the evaluation results, and links to the Make version | ✅ Done | [README.md](../README.md): how it works, improvements, setup, how to run, evaluation, structure, limitations, link to the Make repo. |
| 5 | I can explain every file | Author's part | Supported by [ARCHITECTURE.md](ARCHITECTURE.md), 14 [ADRs](adr/) and [python-concepts.md](python-concepts.md); every function has a docstring. |

## 1. Live end-to-end run

`python main.py --once`, then `echo $LASTEXITCODE`:

```
2026-11-22 22:47:37 INFO Starting (LIVE, once, up to 20 emails per run)
2026-11-22 22:47:40 WARNING Gemini error 503 (attempt 1/3), waiting 2s (backoff)
2026-11-22 22:47:48 INFO msg=1a1e8d01fbac3589 category='Login & Access Issues' priority=High assignee='Daniel Anderson' item=3375882756 files=1/1 confirmation=sent
2026-11-22 22:47:55 INFO msg=1a204f6a24610035 category='Hardware Issues' priority=High assignee='Ryan Mitchell' item=3375899766 files=1/1 confirmation=sent
2026-11-22 22:47:55 INFO Run finished: 2 email(s), 2 created, 0 skipped, 0 dry run, 0 failed
0
```

What this shows:
- **Full flow works:** classification → routing → monday item → attachment upload → confirmation, for both emails.
- **Retry works in real use:** Gemini answered 503 (overloaded) once; the classifier waited and the retry succeeded ([ADR 0004](adr/0004-retry-only-temporary-errors.md)). The Make version would have lost this email.
- **No duplicates:** a second `--once` run reported `0 email(s)`, because each email was marked as read after its item was created ([ADR 0009](adr/0009-mark-as-read-after-item-created.md)).
- **Exit code** `0` for a run without failures.

Also tested before the live run:
- Each module on its own: `gmail_client.py` (sign-in), `classifier.py`, `router.py`, `email_reader.py`, `monday_client.py` (test item with all columns and a file appeared on the board), `mailer.py` (confirmation received; HTML escaping confirmed).
- Offline tests of `main.py` with fake services: step order, a failed upload, a failed confirmation, the email-loop guard, Gemini and monday failures leaving the email unread, dry run with no writes, and all exit codes.

## 2. Evaluation

`python evaluate.py --out results.csv` (prompt v2, `gemini-3.5-flash-lite`):

| Set | Category | Priority | Assignee | Errors | Make version |
|---|---|---|---|---|---|
| Development (T01–T15) | 93% | 100% | 93% | 0 | 93% / 100% / 93% |
| Holdout (H01–H15) | 100% | 93% | 100% | 0 | 100% / 93% / 100% |
| **Combined (30)** | **97%** | **97%** | **97%** | **0** | 97% / 97% / 97% |

## 3. Secrets and personal data

Scan of every file in all 20 commits, plus the current files:

| Check | Result |
|---|---|
| Google API keys, OAuth client secrets, access/refresh tokens, JWTs (monday tokens), private keys, JSON secret fields | 0 hits |
| `.env`-style assignments with a real value | 0 (all are `require_env(...)` calls in `config.py`) |
| `.env`, `credentials.json` or `token.json` ever committed | Never |
| Personal email as commit author or committer | 0 (all commits use the GitHub noreply address) |
| Personal email addresses in files | 0 (only the project inbox, heido.support@gmail.com) |
| Git-ignored now | `.env`, `credentials.json`, `token.json`, `logs/`, `results*.csv` |

## Requirements beyond the definition of done (brief §6)

| Requirement | Result |
|---|---|
| Same behavior as the Make scenario | ✅ Same modules, columns, routing table, prompt and confirmation text |
| Validate the AI output | ✅ `classifier.validate()` ([ADR 0003](adr/0003-structured-output-and-validation.md)) |
| One failing email does not stop the others | ✅ per-email `try/except` in `main.py` ([ADR 0014](adr/0014-polling-loop-and-per-email-isolation.md)) |
| Mark as read only after successful processing | ✅ right after the monday item exists ([ADR 0009](adr/0009-mark-as-read-after-item-created.md)) |
| Retry with backoff on 503/429 | ✅ seen working in the live run |
| One log line per email, console and file | ✅ `logs/heido.log` |
| `evaluate.py` without Gmail or monday | ✅ |
| Dry-run mode | ✅ `--dry-run` |
| Secrets only in `.env`, `.env.example` committed | ✅ (Gmail uses OAuth files instead of a password, [ADR 0001](adr/0001-gmail-api-with-oauth.md)) |

## Manual checks

Both checks from the `main.py` test plan passed (confirmed 2026-11-23):

- [x] **Failure test:** sent an email, ran `$env:GEMINI_API_KEY = "invalid"; python main.py --once; echo $LASTEXITCODE; Remove-Item Env:GEMINI_API_KEY`. Result: the run failed for that email with exit code `1`, the email stayed unread and no item was created. A follow-up normal run was not done as part of this test; normal processing of unread emails is covered by the live run in section 1.
- [x] **Start from another folder:** `cd ..`, `python Heido\main.py --dry-run --once`, `cd Heido`. Result: worked the same as from the project folder (credentials, token, `.env` and the log file were all found).

## Optional next steps (not required)

- Scheduled runs with Windows Task Scheduler (`python main.py --once` every few minutes), or GitHub Actions (needs the OAuth app in "Production" because of the 7-day token).
