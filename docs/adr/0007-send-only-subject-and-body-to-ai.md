# 0007. Send only the subject and body to the AI (data minimization)

- **Status:** Accepted
- **Date:** 2026-11-18

## Context
Each email contains personal data: the sender's name and email address, and sometimes more in the body.
The classification (category, priority, title, summary) depends on what the problem is, not on who sent it.
Sending data to an external AI service should be limited to what the task needs.

## Decision
`classifier.classify()` takes only `subject` and `body`. The sender's name and email address are **never** sent to Gemini.
They go directly from the email to monday.com (Customer Name and Customer Email columns), without passing through the AI.
The function's signature enforces this: there is no parameter for the sender.

## Alternatives
- **Send the whole email, including headers:** might give the AI a little more context (e.g. a known customer), but shares personal data the task does not need.
- **Also mask names or numbers inside the body:** stronger privacy, but complex to do well and could remove details the AI needs to judge the problem.

## Consequences
- Less personal data leaves the system; this matches the Make version's design.
- Classification cannot use the sender's identity (e.g. VIP customers). If that is ever needed, it should be a fixed rule in code, like routing ([0002](0002-fixed-routing-not-ai.md)).
- Personal data written inside the email body is still sent. This is a known limitation.
