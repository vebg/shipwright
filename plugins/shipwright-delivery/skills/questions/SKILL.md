---
name: questions
description: The open-questions table for the owner — every question in docs/QUESTIONS.md §1 and every awaited input in §3 with its default in force, what it blocks and a one-line way to answer. Use when the owner asks "what do you need from me?" or before a planning session.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
---
# /shipwright-delivery:questions

Read `docs/QUESTIONS.md` (sections 1 "Open questions" and 3 "Inputs awaited") and the `blocked` tasks in `tasks/index.json`. Produce one table: ID — question in one line — default in force — what it blocks (task ids) — how to answer ("reply 1/2/3", "paste the link", "send the file to design/inbox/"). Group by urgency: blocking a ready task first, then blocking planned work, then nice-to-know. Keep it under one screen; when the owner answers, record the answer in `requirements/inbox/USER-DECISIONS-<date>.md` and move the question to the resolved section — never re-ask a resolved one.
