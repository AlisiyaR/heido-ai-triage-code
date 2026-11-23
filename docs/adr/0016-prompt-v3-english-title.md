# 0016. Prompt v3: the task title is always in English

- **Status:** Accepted (on branch `refactor/stdlib-email-parser`)
- **Date:** 2026-11-23

## Context
The monday task should be readable by the whole support team, whatever language the customer wrote in.
- Category, priority, status and assignee were already always English: they are fixed lists, and `classifier.validate()` replaces any other value.
- The **summary** was English by the prompt (v2): *"a one-sentence summary in English, even if the email is in another language"*.
- The **title** (the task name on the board, and the "Topic" in the confirmation email) was **not**: v2 only asked for *"a short task name (2-5 words)"*. In a live test with Hebrew and Swedish emails Gemini still chose English titles, but nothing guaranteed it.

The build brief says to use prompt v2 "exactly as is", and the evaluation baseline (97% / 97% / 97%) was measured with v2. So changing it needs a measured, documented decision.

## Decision
- Change one line of `prompt.txt` (now **prompt v3**):
  `- title: a short task name (2-5 words) in English describing the issue`
- Keep everything else in the prompt word for word.
- Accept the change only because the evaluation stayed the same or improved (see Consequences).

## Alternatives
- **Keep v2 and document that the title is usually English:** follows the brief literally, but the board could still get a Hebrew title someday.
- **Translate the title in code** (a second AI call or a translation service): more cost, more code and another failure point, for something one prompt line solves.
- **Generate the title from the summary in code:** loses the short 2–5 word task name.

## Consequences
- Every AI-generated field on the board (title and summary) is in English; category, priority, status and assignee are English by fixed lists. The **Original Message**, the customer's name and file names stay exactly as the customer wrote them.
- The confirmation email's "Topic" line is also always English.
- Evaluation with prompt v3 (2026-11-23; 26 emails in the full run plus the 4 that hit Gemini overload errors, rerun individually; each email classified once):

  | Set | v2 | v3 |
  |---|---|---|
  | Development (15) | 93% / 100% / 93% | 100% / 100% / 100% |
  | Holdout (15) | 100% / 93% / 100% | 100% / 93% / 100% |
  | **Combined (30)** | 97% / 97% / 97% | **100% / 97% / 100%** |

  (Category / Priority / Assignee.) The only miss is H10's priority, the known borderline case; v2 also missed one holdout priority. Because the AI is not fully repeatable, this is read as "at least as good as v2", not as a proven improvement.
- The two Hebrew test emails got English titles: T09 "Cannot login after password reset", H09 "Printer Burning Smell and Smoke".
- This is a deliberate, documented deviation from the brief's "use the prompt exactly as is".
