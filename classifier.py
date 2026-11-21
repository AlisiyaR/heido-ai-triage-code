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
        errors.APIError: on a non-temporary error, or after the last attempt.
    """
    gemini_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Classification,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
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
            wait_seconds = 2**attempt  # 2s, then 4s
            logger.warning(
                "Gemini error %s (attempt %d/%d), retrying in %ds",
                error.code, attempt, MAX_ATTEMPTS, wait_seconds,
            )
            time.sleep(wait_seconds)


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
