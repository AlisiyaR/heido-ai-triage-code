"""All settings for Heido: secrets from .env and fixed constants from the Make scenario."""

import os

from dotenv import load_dotenv

load_dotenv()


def require_env(name):
    """Return the value of an environment variable from .env.

    Args:
        name: the variable name, e.g. "GEMINI_API_KEY".

    Returns:
        The value as a string.

    Raises:
        RuntimeError: if the variable is missing or empty, so the program stops
        early with a clear message instead of failing later.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name} in .env")
    return value


# ── Secrets (from .env) ───────────────────────────────────────
GEMINI_API_KEY = require_env("GEMINI_API_KEY")
MONDAY_API_TOKEN = require_env("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = require_env("MONDAY_BOARD_ID")
MONDAY_GROUP_ID = require_env("MONDAY_GROUP_ID")

# ── Gemini and Gmail ──────────────────────────────────────────
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_REQUESTS_PER_MINUTE = 15  # free-tier limit
MAX_EMAILS_PER_RUN = 15  # one run fits into GEMINI_REQUESTS_PER_MINUTE

# ── Classification ────────────────────────────────────────────
# Must match the names in prompt.txt exactly.
CATEGORIES = [
    "Login & Access Issues",
    "Software & System Issues",
    "Performance Issues",
    "Network & Connectivity Issues",
    "Hardware Issues",
    "Installation & Configuration",
    "Data & Information Issues",
    "Service Requests & General Support",
    "Other / Unclassified",
]
FALLBACK_CATEGORY = "Other / Unclassified"

PRIORITIES = ["High", "Medium", "Low"]
DEFAULT_PRIORITY = "Medium"

# ── Routing: category → employee (a fixed rule, not the AI) ───
ROUTING = {
    "Login & Access Issues": "Daniel Anderson",
    "Software & System Issues": "Daniel Anderson",
    "Performance Issues": "Daniel Anderson",
    "Network & Connectivity Issues": "Ryan Mitchell",
    "Hardware Issues": "Ryan Mitchell",
    "Installation & Configuration": "Ryan Mitchell",
}
DEFAULT_ASSIGNEE = "Emily Carter"  # every other category

# ── monday.com column IDs on the "Customer Support" board ─────
COLUMNS = {
    "category": "color_mm91tmat",
    "priority": "priority",
    "original_message": "long_text_mm91q00k",
    "assigned_to": "dropdown_mm91ncnc",
    "customer_email": "email_mm91b42r",
    "received_at": "date_mm91b4bh",
    "status": "project_status",
    "summary": "text_mm94sk4j",
    "customer_name": "text_mm94v9bp",
    "files": "file",
}

# ── Confirmation email to the customer ────────────────────────
CONFIRMATION_SUBJECT = "We received your request – Ticket {item_id}"
CONFIRMATION_HTML = """<p>Hi,</p>
<p>Thank you for contacting <strong>Heido Support</strong>.</p>
<p>We have received your request and opened a support ticket:</p>
<p><strong>Ticket number:</strong> {item_id}<br>
<strong>Topic:</strong> {title}</p>
<p>Our team is reviewing your request and will get back to you as soon as possible.<br>
Please keep this ticket number for future reference.</p>
<p>Best regards,<br>Heido Support Team</p>"""
