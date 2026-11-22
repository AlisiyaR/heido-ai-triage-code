# 0010. Evaluation accuracy counts only answered emails

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
`evaluate.py` measures how well the AI classifies the 30 test emails. In the first full run, two emails failed with 429 rate-limit errors.
They were counted as wrong answers, which made the AI look less accurate than it was: the problem was the API limit, not the AI's judgment.

## Decision
- Keep two separate outcomes:
  - **Mismatch:** the AI answered, but differently than expected. This measures AI quality.
  - **Error:** no answer at all (e.g. 429). This says nothing about AI quality.
- Accuracy = correct answers / **answered** emails. Each report also shows `Errors: N (excluded from accuracy)` and an "Error details" list.
- If every row in a report failed, it prints "No successful rows" instead of dividing by zero.

## Alternatives
- **Count errors as wrong answers:** simpler, but mixes infrastructure problems with AI quality.
- **Stop the whole run on the first error:** clear, but one temporary error would waste the whole run.

## Consequences
- The accuracy numbers reflect only the AI and can be compared fairly with the Make results.
- Errors are still visible, so a run with many errors is not mistaken for a good result: always check the error count next to the accuracy.
- With the rate limit in place ([0005](0005-client-side-gemini-rate-limit.md)), the rerun had 0 errors and matched Make: 97% / 97% / 97% combined.
