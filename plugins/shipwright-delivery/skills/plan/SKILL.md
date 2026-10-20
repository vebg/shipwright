---
name: plan
description: Run a planning pass as the planner — ingest new or changed requirement sources, update the spec, scope, architecture, decisions, diagrams, traceability and the dependency-ordered backlog, record open questions and validate the index. Use after requirements arrive or change, or when the owner asks to plan the next milestone.
disable-model-invocation: true
argument-hint: "[focus, e.g. 'next milestone' or a source file]"
---
# /shipwright-delivery:plan

Focus given: `$ARGUMENTS` (empty = ingest everything new and detail the next milestone).

1. Read `CLAUDE.md`, `docs/HANDOFF.md`, `tasks/index.json`, `requirements/INTAKE.md`, `requirements/CATALOG.md`. Compare the checksums in the catalog with `requirements/inbox/` and read only new or changed sources (and, on the first run, everything). Files in `requirements/context/` are background, not requirements.
2. Update `requirements/SPEC.md` (stable REQ IDs, actor, behaviour, constraints, source, confirmation state), `requirements/CATALOG.md` (ingestion log, sources with checksum prefix, contradictions and decisions), `docs/SCOPE.md`, `docs/QUESTIONS.md` (only questions that materially block a decision, each with a proposed default in force) and `docs/decisions/` for consequential trade-offs (templates/ADR.md; proposed vs accepted).
3. Update `docs/ARCHITECTURE.md`, `docs/STRUCTURE.md` and the affected `docs/diagrams/` (Mermaid; validate with a renderer when available, else record "source reviewed; rendering not checked"). Label unconfirmed stack choices as proposals; never reselect what docs/STACK.md settles.
4. Build or update the backlog: `tasks/TASK-NNNN.md` from `templates/TASK.md` with stable IDs and dependency edges; foundation before features; vertical slices with manual acceptance checks; UI work split into design part + integration (docs/WORKFLOW.md §UI work split); repository and impact filled for every implementation task; `docs/TRACEABILITY.md` covering every in-scope REQ. Detail the next milestone fully; keep later tasks small and `planned`. Promote to `ready` only what meets the definition of ready.
5. Write `docs/evidence/<planning task ID>.md` when the pass is a planning task, update `docs/HANDOFF.md`, run `python3 scripts/validate_backlog.py` and repair structural failures.
6. Report: sources ingested, REQ/ADR/task counts (created, amended, superseded), open questions for the owner, the ready task IDs in order and what the first batch would be. Start no agent in this skill.
