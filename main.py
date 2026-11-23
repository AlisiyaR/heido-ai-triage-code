"""Runs the Heido pipeline: unread emails -> Gemini -> routing -> monday task -> confirmation."""

import argparse
import logging
import os
import sys
import time

import classifier
import config
import email_reader
import gmail_client
import mailer
import monday_client
import router

logger = logging.getLogger("heido")

# Next to this file, so it works no matter which folder the program is started from.
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "heido.log")

# Possible results of process_email(), counted in the run summary.
CREATED, SKIPPED, DRY_RUN = "created", "skipped", "dry run"


def setup_logging():
    """Send log lines to the console and to logs/heido.log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )
    # Google and HTTP libraries log every request at INFO; show only their warnings and errors.
    for library in ("googleapiclient", "google_genai", "httpx2"):  # httpx2: the HTTP library google-genai uses
        logging.getLogger(library).setLevel(logging.WARNING)


def process_email(service, email, own_address, dry_run):
    """Handle one email from start to finish.

    Order matters: the email is marked as read right after the monday item is
    created (ADR 0009), so a later failure cannot create a duplicate ticket.

    Args:
        service: a Gmail API service.
        email: an email_reader.Email.
        own_address: the support inbox's own address (for the loop guard).
        dry_run: if True, only classify and log what would be created.

    Returns:
        CREATED, SKIPPED or DRY_RUN.

    Raises:
        Exception: if classification or item creation fails. The email is then
        left unread, so the next run retries it.
    """
    # Loop guard (ADR 0013): never turn the inbox's own emails into tickets.
    if email.from_email.lower() == own_address.lower():
        logger.info("msg=%s skipped: sent by the support inbox itself", email.message_id)
        if not dry_run:
            email_reader.mark_as_read(service, email.message_id)
        return SKIPPED

    classification = classifier.classify(email.subject, email.body)
    assignee = router.assign(classification.category)

    if dry_run:
        logger.info(
            "msg=%s DRY RUN would create: title=%r category=%r priority=%s assignee=%r files=%d",
            email.message_id, classification.title, classification.category,
            classification.priority, assignee, len(email.attachments),
        )
        return DRY_RUN

    item_id = monday_client.create_item(email, classification, assignee)
    email_reader.mark_as_read(service, email.message_id)  # right away (ADR 0009)

    # From here on, failures are logged but not raised: the ticket already exists.
    uploaded = upload_attachments(email, item_id)
    confirmation = try_send_confirmation(service, email, item_id, classification.title)

    logger.info(
        "msg=%s category=%r priority=%s assignee=%r item=%s files=%d/%d confirmation=%s",
        email.message_id, classification.category, classification.priority, assignee,
        item_id, uploaded, len(email.attachments), confirmation,
    )
    return CREATED


def upload_attachments(email, item_id):
    """Upload each attachment to the monday item. A failed file is logged and skipped.

    Args:
        email: an email_reader.Email.
        item_id: the monday item ID.

    Returns:
        The number of files uploaded.
    """
    uploaded = 0
    for attachment in email.attachments:
        try:
            monday_client.upload_file(item_id, attachment)
            uploaded += 1
        except Exception as error:
            logger.error("msg=%s item=%s upload of %r failed: %s",
                         email.message_id, item_id, attachment.filename, error)
    return uploaded


def try_send_confirmation(service, email, item_id, title):
    """Send the confirmation email. A failure is logged instead of raised.

    Args:
        service: a Gmail API service.
        email: an email_reader.Email (the confirmation goes to its sender).
        item_id: the monday item ID (the ticket number).
        title: the ticket topic.

    Returns:
        "sent" or "failed".
    """
    try:
        mailer.send_confirmation(service, email.from_email, item_id, title)
        return "sent"
    except Exception as error:
        logger.error("msg=%s item=%s confirmation failed: %s", email.message_id, item_id, error)
        return "failed"


def run_once(service, own_address, dry_run):
    """Process every unread email once. One failing email does not stop the others.

    Args:
        service: a Gmail API service.
        own_address: the support inbox's own address.
        dry_run: passed on to process_email().

    Returns:
        The number of emails that failed.
    """
    emails = email_reader.fetch_unread(service)
    counts = {CREATED: 0, SKIPPED: 0, DRY_RUN: 0, "failed": 0}
    for email in emails:
        try:
            counts[process_email(service, email, own_address, dry_run)] += 1
        except Exception as error:
            # The email was not marked as read, so the next run tries it again.
            logger.error("msg=%s failed (left unread): %s", email.message_id, error)
            counts["failed"] += 1

    logger.info(
        "Run finished: %d email(s), %d created, %d skipped, %d dry run, %d failed",
        len(emails), counts[CREATED], counts[SKIPPED], counts[DRY_RUN], counts["failed"],
    )
    return counts["failed"]


def main():
    """Read the options and run once or in a loop.

    Returns:
        The exit code: 0 if everything worked, 1 if anything failed (with --once).
    """
    parser = argparse.ArgumentParser(description="Heido support-email pipeline.")
    parser.add_argument("--dry-run", action="store_true",
                        help="classify and show what would be created; change nothing")
    parser.add_argument("--once", action="store_true", help="run one time, then exit")
    parser.add_argument("--interval", type=int, default=5, help="minutes between runs (default 5)")
    args = parser.parse_args()

    setup_logging()
    mode = "DRY RUN" if args.dry_run else "LIVE"
    logger.info("Starting (%s, %s, up to %d emails per run)", mode,
                "once" if args.once else f"every {args.interval} min", config.MAX_EMAILS_PER_RUN)

    try:
        service = gmail_client.get_gmail_service()
        own_address = gmail_client.get_own_address(service)
    except Exception:
        logger.exception("Could not connect to Gmail")
        return 1

    if args.once:
        try:
            failed = run_once(service, own_address, args.dry_run)
        except Exception:
            logger.exception("Run failed")  # e.g. Gmail unreachable
            return 1
        return 1 if failed else 0

    try:
        while True:
            try:
                run_once(service, own_address, args.dry_run)
            except Exception:
                logger.exception("Run failed; trying again at the next interval")
            time.sleep(args.interval * 60)
    except KeyboardInterrupt:  # Ctrl+C
        logger.info("Stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
