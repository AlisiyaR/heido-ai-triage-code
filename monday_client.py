"""Creates the support task on the monday.com board and uploads the email's files."""

import json

import requests

import config

API_URL = "https://api.monday.com/v2"
FILE_URL = "https://api.monday.com/v2/file"
TIMEOUT = 30  # seconds to wait for monday before giving up

CREATE_ITEM_QUERY = """
mutation ($boardId: ID!, $groupId: String!, $itemName: String!, $columnValues: JSON!) {
  create_item(board_id: $boardId, group_id: $groupId, item_name: $itemName,
              column_values: $columnValues, create_labels_if_missing: true) {
    id
  }
}
"""


def build_column_values(email, classification, assignee):
    """Build the monday column values for one email.

    Args:
        email: an email_reader.Email.
        classification: a classifier.Classification.
        assignee: the employee name from router.assign().

    Returns:
        A dict of column ID -> value, in the format monday expects.
    """
    columns = config.COLUMNS
    return {
        # Status and dropdown columns are set by label text, not by index.
        columns["category"]: {"label": classification.category},
        columns["priority"]: {"label": classification.priority},
        columns["status"]: {"label": "Not Started"},
        columns["assigned_to"]: {"labels": [assignee]},
        columns["original_message"]: {"text": email.body},
        columns["customer_email"]: {"email": email.from_email, "text": email.from_email},
        columns["received_at"]: {
            "date": email.received_at.strftime("%Y-%m-%d"),
            "time": email.received_at.strftime("%H:%M:%S"),  # monday expects UTC
        },
        columns["summary"]: classification.summary,
        columns["customer_name"]: email.from_name or email.from_email,
    }


def create_item(email, classification, assignee):
    """Create the task (item) in the configured board and group.

    Args:
        email: an email_reader.Email.
        classification: a classifier.Classification (its title becomes the item name).
        assignee: the employee name from router.assign().

    Returns:
        The new item ID as a string (this is the ticket number).

    Raises:
        RuntimeError: if monday rejects the request.
    """
    # Values go in "variables", not pasted into the query text, so quotes or
    # special characters in a customer's email cannot break the query.
    variables = {
        "boardId": config.MONDAY_BOARD_ID,
        "groupId": config.MONDAY_GROUP_ID,
        "itemName": classification.title,
        "columnValues": json.dumps(build_column_values(email, classification, assignee)),
    }
    response = requests.post(
        API_URL,
        json={"query": CREATE_ITEM_QUERY, "variables": variables},
        headers={"Authorization": config.MONDAY_API_TOKEN},
        timeout=TIMEOUT,
    )
    data = check_response(response)
    return data["create_item"]["id"]


def upload_file(item_id, attachment):
    """Upload one file to the item's Files column.

    Args:
        item_id: the item ID from create_item().
        attachment: an email_reader.Attachment.

    Raises:
        RuntimeError: if monday rejects the upload.
    """
    item_id = int(item_id)  # always a number; makes it safe to put in the query text
    query = (
        f'mutation ($file: File!) {{ add_file_to_column(item_id: {item_id}, '
        f'column_id: "{config.COLUMNS["files"]}", file: $file) {{ id }} }}'
    )
    response = requests.post(
        FILE_URL,
        data={"query": query},
        files={"variables[file]": (attachment.filename, attachment.data, attachment.mime_type)},
        headers={"Authorization": config.MONDAY_API_TOKEN},
        timeout=TIMEOUT,
    )
    check_response(response)


def check_response(response):
    """Return the "data" part of a monday answer, or raise if monday reported an error.

    Args:
        response: a requests.Response from the monday API.

    Returns:
        The "data" dict from the JSON answer.

    Raises:
        RuntimeError: with monday's own error message.
    """
    try:
        body = response.json()
    except ValueError:  # not JSON at all, e.g. an HTML error page
        response.raise_for_status()
        raise RuntimeError(f"monday returned a non-JSON answer: {response.text[:200]}")

    # monday often answers HTTP 200 even for errors, so check the body first.
    if body.get("errors"):
        messages = "; ".join(error.get("message", str(error)) for error in body["errors"])
        raise RuntimeError(f"monday error: {messages}")
    if body.get("error_message"):
        raise RuntimeError(f"monday error: {body['error_message']}")
    response.raise_for_status()
    return body["data"]


if __name__ == "__main__":
    # Self-test: create one test item with sample data and upload a small file.
    # No Gmail, no Gemini.
    from datetime import datetime, timezone

    from classifier import Classification
    from email_reader import Attachment, Email

    sample_email = Email(
        message_id="test",
        subject="VPN keeps disconnecting",
        body="Hi, since this morning the VPN drops every few minutes and I can't reach the file server.\n"
             "This is a test item created by monday_client.py.",
        from_name="Test Customer",
        from_email="test.customer@example.com",
        received_at=datetime.now(timezone.utc),
    )
    sample_classification = Classification(
        title="[TEST] VPN keeps disconnecting",
        summary="The customer's VPN drops every few minutes, blocking access to the file server.",
        category="Network & Connectivity Issues",
        priority="High",
    )
    item_id = create_item(sample_email, sample_classification, assignee="Ryan Mitchell")
    print(f"Created item {item_id} in group {config.MONDAY_GROUP_ID}")

    upload_file(item_id, Attachment("heido-test.txt", "text/plain", b"Test file from monday_client.py\n"))
    print("Uploaded heido-test.txt")
