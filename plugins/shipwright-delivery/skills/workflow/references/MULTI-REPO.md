# Coordination workspace with separate application Git roots
The repository split is an owner decision recorded in ADR-0002. Folder names below are starter conventions; change them only with a documented reason.

## Ownership and setup
The workspace parent owns `.claude/` (project settings), CLAUDE.md, docs/, tasks/, requirements/, design/, scripts/ and templates/; each child folder listed in shipwright.json `repos` is an independent Git repository with its own CLAUDE.md (technology-specific commands and conventions only, pointing to ../CLAUDE.md and ../docs/ for coordination), CI and releases. Launch Claude Code from the parent. Do not duplicate the backlog or agents.

Track the parent as a small coordination repository with every child folder excluded by its .gitignore before anything is staged. No submodules unless explicitly requested. Check and commit each affected repository separately; a parent commit never captures child changes. Keep the workspace handoff with the child commit IDs.

## Structure rules
- Apps consume shared packages/libraries; packages never depend on apps; no imports between apps; no circular references; shared UI contains no networking (it takes data and callbacks).
- Create packages/projects as needed for a current consumer; avoid empty packages, giant "common" modules or microservices that only match folders. Backend rules stay authoritative even when clients validate inputs for usability.
- Pin toolchains (SDK versions, workspace tooling, central package versions) in each repository and record them in its CLAUDE.md and docs/STACK.md; never silently upgrade all dependencies during a feature task. Verify versions during setup; do not claim scaffolding examples were executed.
- Each repository supplies root commands for bootstrap, format check, analysis, per-app run and generation, distinguishing read-only checks from modifying commands. An affected-project check computes changes relative to the merge base and falls back to all projects for root toolchain/lockfile/CI changes or uncertain impact; shared changes also check transitive dependents.

## Contracts across repositories
The provider repository owns the authoritative API contract (for example OpenAPI) and separately defined realtime event schemas; an API document alone does not describe hub behavior. Export a versioned contract artifact, pin its release/commit and checksum in each consumer, and generate clients reproducibly with a pinned generator. Never generate from an arbitrary live endpoint, hand-edit generated clients or use sibling source files as runtime dependencies. Document nullable fields, serialization, dates/time zones, enums, errors and auth semantics. Contract artifacts contain no credentials or customer records.

Each compatible API expansion lands before its consumer. Keep old fields/events available for deployed clients during an explicit support window; mobile updates are not simultaneous with backend deployment. Breaking changes require versioning or a staged migration and, after the first public release, the owner's approval with an "Impact on installed clients" summary. Verify realtime authentication, reconnect and refresh from authoritative state with the selected client adapter.

## Cross-repository tasks
Link producer/consumer task IDs. Record both commits (and uncommitted changes), artifact version, integration outcome and rollout/rollback order. Two Git roots cannot share an atomic commit. Do not mark a feature complete on a passing provider build while the required consumers remain unverified.

## Completion gates
Planner: document structures, dependency boundaries, toolchain choices, contract flow, the affected-check policy and the ordered foundation tasks. Developer: check each Git root; implement scoped tasks; build/analyze affected consumers; hand over. Manual tester: verify acceptance criteria on real devices/browsers; record evidence and real screenshots with repository/app/revision in the workspace docs/evidence/. Read manifests, task links and affected code rather than loading repositories wholesale.
