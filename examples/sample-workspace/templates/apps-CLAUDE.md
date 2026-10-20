# apps — repository instructions
This Git root owns: Flutter. It is a child of the sample-bakery workspace (`../`), which owns the agents, the single backlog, requirements, evidence and design sources. Do not duplicate them here.

For coordinated work launch Claude Code from the parent workspace. Read ../CLAUDE.md, ../docs/HANDOFF.md, ../tasks/index.json and ../docs/MULTI-REPO.md; shared paths in those instructions are workspace-relative. If that context is missing, report it before changing shared plans; never create another backlog.

Run build, analyze, format and Git commands with this repository as the working directory. Builds must work independently of the workspace and of sibling repositories. This repository consumes approved versioned design exports copied inside it, never the workspace design folder. Record evidence in ../docs/evidence/ and task status in ../tasks/.

No automated tests (ADR-0001): never create unit, widget, integration, golden or e2e tests, test projects, `test/`/`integration_test/` folders or test dependencies in any repository; delete generated test stubs; never use test project templates. Verification is manual by the manual-tester agent with evidence in docs/evidence/.

## Commands (fill in when verified; never list a command that has not been run here)
- Toolchain and pinned versions:
- Bootstrap / restore:
- Read-only checks (format check, analyze, build):
- Modifying commands (format, generation):
- Run (each app/host):
- Affected-project check:

## Conventions
Owner-mandated coding standards for this repository (or a link to the ADR). Every new or touched line follows them.
