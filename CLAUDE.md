# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Heido is a support-email automation pipeline that connects three services:

1. **Gmail**: source of incoming support emails.
2. **Google Gemini**: classifies each email (the LLM step).
3. **monday.com**: where tasks are created from the classified emails.

Data flow: Gmail → Gemini classification → monday.com task.

## Status

The repository has no code yet. No language, framework, build, lint or test commands have been chosen. Update this file once they exist, covering:

- Build, run, lint and test commands, including how to run a single test
- Where credentials and config for Gmail, Gemini and monday.com are loaded from
- The classification categories and how each one maps to a monday.com board, group or column
- How emails are fetched (polling or push) and how already-processed emails are tracked to avoid duplicate tasks
