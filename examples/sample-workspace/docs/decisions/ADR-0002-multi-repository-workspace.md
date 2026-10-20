# ADR-0002 — Coordination workspace with separate application Git roots
Status: Accepted — owner answer at workspace creation (2026-10-19, `/shipwright:start`).

## Context
The product has several deployables with different toolchains and release cycles. One backlog, one set of requirements, one evidence folder and one design hub must coordinate them without forcing one repository, one CI or one atomic commit.

## Decision
- This directory is the **coordination workspace**: agents, CLAUDE.md, docs/, tasks/, requirements/, design/, scripts/ and templates/. Its Git repository tracks coordination only and ignores the child folders.
- Each child folder listed in shipwright.json `repos` is an **independent Git repository** with its own CLAUDE.md (technology-specific commands and conventions), contracts, CI and releases. No submodules.
| Git repository | Folder | Stack |
|---|---|---|
| platform | `bakery-platform/` | undecided |
| apps | `bakery-apps/` | Flutter |
- Rules: no duplicate backlog or agents; no cross-repository source path dependency (sharing goes through versioned contracts, generated clients or published packages); every task names its repositories and paths; cross-repository features are provider/consumer task pairs with recorded revisions and rollout order; Git status is checked separately in every affected repository; commits are never described as atomic across repositories. Details: docs/MULTI-REPO.md.

## Consequences
Independent deployment and rollback per repository; slightly more bookkeeping per task (repository-qualified paths, paired revisions); the parent must have its .gitignore in place before staging anything.
