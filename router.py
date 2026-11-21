"""Picks the responsible employee for a category (a fixed rule, not the AI)."""

import config


def assign(category):
    """Return the employee responsible for a category.

    Args:
        category: a category name, e.g. "Hardware Issues".

    Returns:
        The employee's name. Categories not in config.ROUTING (including
        unexpected values) go to config.DEFAULT_ASSIGNEE.
    """
    return config.ROUTING.get(category, config.DEFAULT_ASSIGNEE)


if __name__ == "__main__":
    # Self-test: every category, plus one unexpected value.
    for name in config.CATEGORIES + ["Made-up Category"]:
        print(f"{name:<38} -> {assign(name)}")
