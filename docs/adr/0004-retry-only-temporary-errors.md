# 0004. Retry only temporary AI errors, waiting as long as Google asks

- **Status:** Accepted
- **Date:** 2026-11-18 (updated 2026-11-22: honour `retryDelay`, 60-second cap; updated 2026-11-23: 5 attempts, backoff 5/10/20/40s)

## Context
The Make README listed a known limitation: when Gemini was overloaded, the email failed with no retry.
Some API errors are temporary (429 "too many requests", 503 "overloaded") and succeed if we wait. Others (wrong API key, bad request) will fail again however often we retry.
In the first evaluation run, a fixed 2s/4s wait was shorter than the time Google asked for, so two 429 errors still failed.
In the prompt-v3 evaluation, Gemini answered 503 "high demand" **without** a `retryDelay` during a busy period. The 2s/4s backoff (3 attempts) gave up after about 6 seconds, and 4 of 30 emails failed.

## Decision
In `classifier.call_gemini()`:
- Retry **only** on 429 and 503, with up to **5 attempts**.
- Wait **Google's `retryDelay` + 1 second** when the error includes it (read by `get_retry_delay()`), otherwise our own backoff from `BACKOFF_SECONDS`: **5s, 10s, 20s, 40s** (about 75 seconds of patience in total).
- If Google asks for more than **60 seconds**, fail instead of waiting (this usually means the daily quota is used up).
- Any other error fails immediately.
- Each retry is logged with the wait time and its source (Google or backoff).

## Alternatives
- **No retries (as in Make):** a short overload loses the email for this run.
- **Retry every error:** wastes time and quota on errors that can never succeed, and hides real problems such as a wrong key.
- **Always use a fixed backoff:** simpler, but too short for rate-limit errors, as the first evaluation run showed.
- **Keep 3 attempts with 2s/4s:** fast, but too short for Gemini's busy spikes, as the v3 evaluation showed.
- **Even more attempts or longer waits:** more chance to succeed, but one email could block the run for minutes.
- **Wait as long as Google asks, with no cap:** a daily-quota error could block the program for hours.

## Consequences
- Short overloads and rate-limit spikes no longer lose emails.
- Permanent errors surface right away with a clear message.
- One email can wait up to about 75 seconds in the worst case (plus the 4-second spacing per attempt). During a long outage, a run of 15 emails can take several minutes; runs never overlap, because the next one starts only after the previous one ends.
- Retries also count toward the rate limit (see [0005](0005-client-side-gemini-rate-limit.md)).
