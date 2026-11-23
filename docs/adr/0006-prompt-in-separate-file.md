# 0006. Keep the AI prompt in `prompt.txt`, not in the code

- **Status:** Accepted
- **Date:** 2026-11-18 (the prompt is now v3: [ADR 0016](0016-prompt-v3-english-title.md))

## Context
The prompt (v2) is long (about 40 lines of categories, decision rules and priority rules) and was tuned through several versions in the Make project.
It is likely to change again, and changes should be easy to review on their own.

## Decision
Store the prompt word for word in `prompt.txt`, with two placeholders: `{subject}` and `{body}`.
`classifier.py` reads the file once at start-up (path relative to `classifier.py`, so it works from any folder) and fills the placeholders with `.format(subject=..., body=...)`.

## Alternatives
- **A long string inside `classifier.py`:** mixes text and logic; prompt edits would show up as code changes.
- **A template engine (e.g. Jinja):** more power than two placeholders need, and one more package.

## Consequences
- The prompt can be improved without touching Python code, and its history is easy to follow in git.
- `evaluate.py` can measure the effect of every prompt change with one command.
- The prompt must contain no other `{` or `}` characters, or `.format()` will fail. (Checked: it contains only the two placeholders.) Curly braces inside an email body are safe, because only the template is formatted.
