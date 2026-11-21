# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Heido is a support-email automation pipeline that connects three services:

1. **Gmail**: source of incoming support emails.
2. **Google Gemini**: classifies each email (the LLM step).
3. **monday.com**: where tasks are created from the classified emails.

Data flow: Gmail → Gemini classification → monday.com task.

## Relationship to the no-code version

This repository is the code-based version of Heido. The original no-code version, built on Make.com, lives in the public repo `heido-ai-triage`. Both versions automate the same business process, so the no-code version is the reference for intended behavior.

## Communication

- The user may write in Hebrew. Always reply in English.
- Always write code, comments, commit messages and documentation in English.

## Working rules

### Code style
- Write simple, clear, readable code. Prefer the shortest solution that fully works.
- No over-engineering: no extra classes, layers or features I didn't ask for.
- Use clear names for variables and functions.
- Every function gets a short English docstring (what it does, inputs, outputs).
- Add comments only where the code isn't obvious, explaining why.

### Changes
- Before writing code, explain the plan in simple words and wait for my approval.
- Never change, delete or refactor existing code without asking first and explaining why.
- Change only what the task needs. Keep changes small.
- Don't add new packages without asking and explaining why they're needed.

### Security
- Never read, print or log secrets (.env, credentials.json, token.json).
- Never hardcode API keys, passwords or tokens. Load them from .env.

### Testing and Git
- After a change, tell me how to run and check that it works.
- Don't commit or push without my approval. Use short, clear commit messages.

### Learning
- Explain what you're doing in simple words.
- After each feature, update docs/learning-notes.md with a simple explanation in English of what each part does and why, for a beginner.
- If something is unclear, ask me instead of guessing.

## Status

The repository has no code yet. No language, framework, build, lint or test commands have been chosen. Update this file once they exist, covering:

- Build, run, lint and test commands, including how to run a single test
- Where credentials and config for Gmail, Gemini and monday.com are loaded from
- The classification categories and how each one maps to a monday.com board, group or column
- How emails are fetched (polling or push) and how already-processed emails are tracked to avoid duplicate tasks
