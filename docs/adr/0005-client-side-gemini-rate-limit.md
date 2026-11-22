# 0005. Client-side rate limit: at most 15 Gemini calls per minute

- **Status:** Accepted
- **Date:** 2026-11-22

## Context
The Gemini free tier allows 15 requests per minute. `evaluate.py` sends 30 requests in a row, and the pipeline may process up to 20 emails per run (`MAX_EMAILS_PER_RUN`).
The first full evaluation run went over the limit, and two emails failed with 429 errors.
Retrying after the error ([0004](0004-retry-only-temporary-errors.md)) helps, but it is better not to hit the limit at all.

## Decision
- Add `GEMINI_REQUESTS_PER_MINUTE = 15` to `config.py`.
- In `classifier.py`, `wait_for_rate_limit()` runs before **every** Gemini attempt, retries included. It remembers the time of the last call (`time.monotonic()`) and sleeps until at least 60 / 15 = **4 seconds** have passed.
- The limit lives in the classifier, because both `evaluate.py` and the pipeline call Gemini only through `classify()`.

## Alternatives
- **Lower `MAX_EMAILS_PER_RUN` to 15:** limits one run, but not retries, and not a second run that starts soon after.
- **A sliding-window counter (allow bursts of 15, then wait):** faster for small batches, but more code to explain for little gain at this volume.
- **Rely on retries alone:** works, but every limit hit costs a long wait and log noise.
- **A paid tier:** removes the problem, but adds cost to a portfolio project.

## Consequences
- The program never sends more than 15 Gemini calls per minute. The rerun had 0 errors.
- Every caller is protected automatically, including future ones.
- Runs are slower: 20 emails take at least about 80 seconds; the 30 test emails take about 2 minutes.
- The limit works inside one running program only. Running `evaluate.py` and `main.py` at the same time with the same key could still exceed it.
