"""Classifies a support email with Google Gemini: title, summary, category, priority."""

import logging
import os
import time

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)

# Read the prompt from the file next to this one, so it works from any folder.
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "prompt.txt")
with open(PROMPT_FILE, encoding="utf-8") as prompt_file:
    PROMPT_TEMPLATE = prompt_file.read()

client = genai.Client(api_key=config.GEMINI_API_KEY)

MAX_ATTEMPTS = 3
RETRY_CODES = (429, 503)  # rate limit, overloaded: temporary, worth retrying
MAX_RETRY_WAIT = 60  # seconds; a longer retryDelay usually means the daily quota is used up

# Minimum seconds between two Gemini calls: 60 / 15 = 4.
MIN_SECONDS_BETWEEN_CALLS = 60 / config.GEMINI_REQUESTS_PER_MINUTE
last_call_time = None  # time.monotonic() of the previous call


class Classification(BaseModel):
    """The 4 fields Gemini must return. Also used as the response schema."""

    title: str
    summary: str
    category: str
    priority: str


def classify(subject, body):
    """Classify one email.

    Args:
        subject: the email subject.
        body: the plain-text email body.

    Returns:
        A validated Classification.
    """
    # Only subject and body go to the AI, never the sender address.
    prompt = PROMPT_TEMPLATE.format(subject=subject, body=body)
    return validate(call_gemini(prompt))


def call_gemini(prompt):
    """Send the prompt to Gemini, retrying on temporary errors.

    Args:
        prompt: the full prompt text.

    Returns:
        A Classification parsed from Gemini's JSON answer.

    Raises:
        errors.APIError: on a non-temporary error, after the last attempt, or
        when Google asks to wait longer than MAX_RETRY_WAIT seconds.
    """
    gemini_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Classification,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait_for_rate_limit()  # also before retries: every attempt counts toward the limit
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL, contents=prompt, config=gemini_config
            )
            if response.parsed is None:
                raise ValueError(f"Gemini returned no valid JSON: {response.text!r}")
            return response.parsed
        except errors.APIError as error:
            if error.code not in RETRY_CODES or attempt == MAX_ATTEMPTS:
                raise
            retry_delay = get_retry_delay(error)
            if retry_delay is None:
                wait_seconds, source = 2**attempt, "backoff"  # 2s, then 4s
            else:
                wait_seconds, source = retry_delay + 1, "Google retryDelay"
            if wait_seconds > MAX_RETRY_WAIT:
                raise
            logger.warning(
                "Gemini error %s (attempt %d/%d), waiting %.0fs (%s)",
                error.code, attempt, MAX_ATTEMPTS, wait_seconds, source,
            )
            time.sleep(wait_seconds)


def wait_for_rate_limit():
    """Sleep if needed, so Gemini calls are at least MIN_SECONDS_BETWEEN_CALLS apart.

    This keeps us at or under config.GEMINI_REQUESTS_PER_MINUTE.
    """
    global last_call_time  # we change the module-level variable, not a local copy
    if last_call_time is not None:
        seconds_since_last = time.monotonic() - last_call_time
        if seconds_since_last < MIN_SECONDS_BETWEEN_CALLS:
            time.sleep(MIN_SECONDS_BETWEEN_CALLS - seconds_since_last)
    last_call_time = time.monotonic()


def get_retry_delay(error):
    """Read how long Google asks us to wait from a 429/503 error.

    Args:
        error: an errors.APIError from the Gemini SDK.

    Returns:
        The wait in seconds (e.g. "37s" -> 37.0), or None if Google gave none.
    """
    try:
        for detail in error.details["error"]["details"]:
            if "retryDelay" in detail:
                return float(detail["retryDelay"].rstrip("s"))
    except (KeyError, TypeError, ValueError):
        pass  # unexpected error format: fall back to our own backoff
    return None


def validate(result):
    """Replace a category or priority that is not allowed with a safe default.

    Args:
        result: a Classification from Gemini.

    Returns:
        The same Classification, with category and priority guaranteed valid.
    """
    if result.category not in config.CATEGORIES:
        logger.warning("Unknown category %r, using %r", result.category, config.FALLBACK_CATEGORY)
        result.category = config.FALLBACK_CATEGORY
    if result.priority not in config.PRIORITIES:
        logger.warning("Unknown priority %r, using %r", result.priority, config.DEFAULT_PRIORITY)
        result.priority = config.DEFAULT_PRIORITY
    return result


if __name__ == "__main__":
    # Self-test: classify one sample email.
    logging.basicConfig(level=logging.INFO)
    sample = classify(
        subject="Cannot log in to the CRM",
        body="Hi, since this morning I get 'invalid password' in the CRM, even after "
        "resetting it. The whole sales team is waiting for me. Thanks, Dana",
    )
    print(f"Title:    {sample.title}")
    print(f"Summary:  {sample.summary}")
    print(f"Category: {sample.category}")
    print(f"Priority: {sample.priority}")
