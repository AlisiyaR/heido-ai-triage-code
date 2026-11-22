# 0002. Fixed routing rule instead of the AI choosing the employee

- **Status:** Accepted
- **Date:** 2026-11-18

## Context
Each ticket must be assigned to one of three employees. The Make version used a Switch module: a fixed table from category to employee.
The AI already returns a category, so it could also be asked to pick the employee.

## Decision
The AI picks only the **category**. A fixed rule in code picks the **employee**: `router.assign(category)` looks the category up in `config.ROUTING`.
Daniel Anderson and Ryan Mitchell each own three categories; every other value, including unexpected ones, goes to **Emily Carter** (the default).

## Alternatives
- **Let the AI choose the employee:** one fewer step, but the result could change from run to run, could return a name that does not exist, and would be hard to explain or audit.
- **Put the routing table inside `router.py`:** works, but `config.py` is the single place for business settings, so the table lives there.

## Consequences
- Assignment is predictable, testable and easy to explain: same category, same person, always.
- Changing who owns a category means editing one dictionary in `config.py`.
- Assignment accuracy depends fully on category accuracy (in evaluation, a wrong category is the only way to get a wrong assignee).
- An unexpected category never crashes the program; it goes to the default employee.
