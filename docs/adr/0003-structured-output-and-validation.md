# 0003. Structured AI output with a response schema, plus validation

- **Status:** Accepted
- **Date:** 2026-11-18

## Context
The rest of the pipeline needs four exact fields from the AI: `title`, `summary`, `category` and `priority`.
Category and priority must be one of a fixed set of values, because they map to monday labels and to the routing rule.
AI models can return text in an unexpected format or invent a value that is not on the list.

## Decision
- Pass a Pydantic model, `Classification`, to Gemini as the **response schema**, with JSON output. Gemini must answer in exactly that shape, and the SDK returns a `Classification` object.
- After every call, `validate()` checks the values:
  - a category not in `config.CATEGORIES` becomes `Other / Unclassified`;
  - a priority not in `High / Medium / Low` becomes `Medium`;
  - each fix is logged as a warning.

## Alternatives
- **Ask for plain text and parse it ourselves:** fragile; small wording changes would break the parser.
- **Trust the schema only, no validation:** the schema guarantees the fields exist, but not that their values are on our list.
- **Reject the email when a value is invalid:** the email would never become a ticket; a safe default keeps the process moving and the warning makes the problem visible.

## Consequences
- The code works with a typed object instead of raw text.
- Downstream code (router, monday) can rely on valid values.
- A bad AI answer still creates a ticket, with a safe default that a person can correct on the board.
- Requires `pydantic` (already a dependency of the Gemini SDK).
