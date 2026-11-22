# Heido AI Inquiry Triage – Python version

> **🚧 Work in progress.** All building blocks work: reading emails, classification, monday.com task creation, the confirmation email and evaluation. The full pipeline (`main.py`) is still being built.

An automation pipeline that turns customer support emails into tasks for **Heido**, a fictional IT services company:

**Gmail** → **Google Gemini** (classifies the email) → **fixed routing rule** (picks the employee) → **monday.com** task → confirmation email to the customer.

This is a code rebuild of the no-code version built on Make.com: **[heido-ai-triage](https://github.com/AlisiyaR/heido-ai-triage)**.
Both versions automate the same business process. The Python version adds retries, a rate limit, AI output validation and an automated evaluation script.

## Status

| Component | What it does | Status |
|---|---|---|
| `config.py` | Settings and constants; secrets loaded from `.env` | ✅ Done |
| `gmail_client.py` | Gmail API sign-in with OAuth | ✅ Done |
| `prompt.txt` + `classifier.py` | Gemini classification with validation, retry and rate limit | ✅ Done |
| `router.py` | Category → employee (fixed rule, not the AI) | ✅ Done |
| `evaluate.py` | Accuracy test on 30 test emails | ✅ Done |
| `email_reader.py` | Read unread emails and attachments | ✅ Done |
| `monday_client.py` | Create the monday.com task and upload files | ✅ Done |
| `mailer.py` | Send the confirmation email | ✅ Done |
| `main.py` | Run the full pipeline (with dry-run mode) | ⏳ Planned |

## Evaluation results so far

Classification accuracy on the same 30 test emails used for the Make version:

| Set | Category | Priority | Assignee |
|---|---|---|---|
| Development (15) | 93% | 100% | 93% |
| Holdout (15) | 100% | 93% | 100% |
| **Combined (30)** | **97%** | **97%** | **97%** |

Same results as the Make version. Run it yourself with `python evaluate.py`.

## Tech stack

Python 3.13 · Gmail API (OAuth) · Google Gemini (`google-genai`) · monday.com GraphQL API · Pydantic · python-dotenv

## Documentation

- [Architecture](docs/ARCHITECTURE.md): components, data flow, error handling
- [Architecture Decision Records](docs/adr/): why each design choice was made
- [Build brief](docs/build-brief.md): the original requirements

Full setup and run instructions will be added when the pipeline is complete.

## License

[MIT](LICENSE) © 2026 Alisiya Rabinovich
