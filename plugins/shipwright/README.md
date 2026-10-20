# Shipwright

A planner-led, evidence-driven delivery workflow for Claude Code, extracted from a real product that went from requirements to store-ready mobile apps, web hosts and an API with four agents and one traceable backlog. Install it, run `/shipwright:start`, answer a handful of questions, drop your requirements in a folder and the planner takes it from there.

## What it does
- **Planner as the main session.** While the plugin is enabled, `planner` is the default main-thread agent (plugin `settings.json`; override with `claude --agent <other>` or your own `agent` setting). It turns requirements into stable `REQ-` IDs, scope, architecture, ADRs, Mermaid diagrams, a dependency-ordered backlog with `TASK-` files and a traceability table, and keeps `docs/HANDOFF.md` current so any fresh session resumes.
- **Four delivery agents, one at a time.** `frontend-designer` (static-first UI: markup, styles, every state as a design route, real screenshots), `fullstack-developer` (backend, foundation, all integration, every fix), `manual-tester` (verifies on the real API, browsers and devices and records evidence), and the optional `store-compliance-reviewer`. The planner closes design parts by inspection; nothing is `done` without `verification: "passed"`.
- **Guard hooks** that enforce what a plugin cannot ship as permissions: design skills and design helper agents are designer-only; test runners and test templates are denied while the workspace forbids automated tests; force pushes, hard resets and database drops are always denied for agents.
- **Session context and cost.** A `SessionStart` hook injects the backlog state and the resume order; `Stop`/`SubagentStop` hooks regenerate `docs/TOKEN-COSTS.md`, attributing every agent run to its `Task: TASK-XXXX` line.
- **Discovery first.** On the first message in a folder that is not yet a workspace, the main session opens the intake; `/shipwright:start` interviews you in short rounds — the product and its users, surfaces, inspiration links/videos/apps, technologies already decided, constraints, brand, working agreement — writes `requirements/inbox/DISCOVERY-<date>.md` for the planner, and only then scaffolds.
- **Skills (slash commands):** `/shipwright:start`, `:resume`, `:plan`, `:design`, `:develop`, `:verify`, `:status`, `:balance` (cost per task/group with totals, statistics, forecast and budget), `:doctor` (machine and workspace checks), `:owner` (the owner's release checklist), `:questions` (open questions with defaults), `:release` (tags, notes, store brief), and `:workflow` (the protocol reference).
- **Evidence helpers:** `scripts/contact_sheet.py` (labelled contact sheet per task, ImageMagick or ffmpeg) and `scripts/record.sh` (short MP4 from an iOS simulator, Android emulator or the screen).
- **Evals:** `evals/` holds `claude plugin eval` cases (intake opens the interview, status report, tests policy); see `evals/README.md`.

## Install
```bash
claude plugin marketplace add vebg/shipwright
claude plugin install shipwright@shipwright
```
Then, in the directory where the product's workspace should live:
```text
/shipwright:start
```
Requirements: Claude Code 2.1.281 or later, Python 3 on the PATH (hooks and scripts use only the standard library), Git. The agents default to the `fable` (planner, designer), `opus` (developer, compliance) and `sonnet` (tester) model aliases; copy an agent file into your project's `.claude/agents/` to change its model or effort (project agents take precedence over plugin agents).

## How a project runs
1. `/shipwright:start` scaffolds the workspace: `CLAUDE.md`, `shipwright.json` (policies the hooks read), `docs/` (handoff, questions, stack, scope, architecture, structure, traceability, decisions, diagrams, evidence, protocol references), `requirements/` (inbox, context, catalog, spec), `tasks/index.json`, `templates/`, `design/` hub, `scripts/` (backlog validator, token report) and `.claude/settings.json` (read-only allow list, deny list, `acceptEdits`); optionally the Hindsight memory and context-mode wiring (§Companions).
2. Put requirements in `requirements/inbox/` and run `/shipwright:plan`. The planner ingests them once, records every source with a checksum, asks only blocking questions (`docs/QUESTIONS.md`, each with a default in force) and builds the backlog.
3. Say go. `/shipwright:design` → `/shipwright:develop` → `/shipwright:verify`, three tasks per batch, one agent and one repository at a time. Every batch ends with evidence, an updated handoff and its cost.
4. `/shipwright:resume` in any later session; `/shipwright:status` any time; `/shipwright:release` when you want one shared product version tagged per verified task.

## Policies you choose at start
- **Automated tests:** `forbidden` (the proven default — the tester verifies the real software and records evidence, so you review deliverables instead of test code) or `allowed` (tests permitted; manual verification still gates `done`). The intake explains the trade-off before asking: agent-written tests cost roughly a third more tokens per task and delay the first shippable build.
- **Budget (optional):** `budget.total_usd`, `per_task_usd`, `warn_at` in `shipwright.json` — `/shipwright:balance` and the session-start line report against it; nothing blocks on its own.
- **Repository layout:** single repository, or a coordination workspace whose child folders are independent Git roots (the layout used for a .NET platform repo plus a Flutter apps repo); the kit never puts several deployables in one toolchain workspace unless you say so.
- **Stack:** whatever you name is settled and never reselected by an agent; what you leave open the planner proposes in `docs/ARCHITECTURE.md` with the label *proposal*.

## Design tooling (optional, recommended for UI work)
The designer uses, when installed: `frontend-design@claude-plugins-official`, `impeccable@impeccable` (adds the four `impeccable-*` helper agents the guard allows the designer to start), the Emil Kowalski motion/craft skills and the taste skills (install with the `skills` CLI or copy them under `.claude/skills/`). None is bundled here — each has its own licence. The guard list in `shipwright.json` → `policies.designer_only_skills` is editable.

## Companions (optional)
- `shipwright-devices@shipwright` — pinned `mobile-mcp` server for driving local iOS simulators and Android emulators (designer and tester).
- **Hindsight project memory** (`@vectorize-io/hindsight-coding-agents`, a self-hosted server in Docker or the cloud service; not bundled). `/shipwright:start memory` wires it **at project level** the way the proven workspace does: a tracked `.hindsight/coding-agent.json` (one bank per workspace, git-message ingest, codebase survey, reflect injection, cron knowledge pages, a `toolGuideExtra` that says memory is a past record), the three hooks and the `HINDSIGHT_*` env in `.claude/settings.json`, the `hindsight` stdio + `hindsight-bank` HTTP MCP servers in `.mcp.json`, `/.hindsight/logs/` ignored, the runtime's companion skill copied to `.claude/skills/`. Every agent carries `mcp__hindsight` and a "Project memory" section: search before re-deriving decisions, credit what you used, correct stale memory with `Correction: <topic>`; `docs/HANDOFF.md`, `tasks/index.json`, task bodies and evidence stay authoritative. Without the runtime the tools are simply absent and the agents skip the section.
- **context-mode** (`context-mode@context-mode`, marketplace `mksglu/context-mode`; not bundled). Every agent carries `mcp__plugin_context-mode_context-mode` and a "Context budget" section (builds, analyzers, logs, curl bodies, big files through `ctx_execute`/`ctx_batch_execute`/`ctx_execute_file`; long documents through `ctx_index`/`ctx_search`; evidence files keep the full output). `/shipwright:start` writes `CONTEXT_MODE_DIR=<workspace>/.context-mode` and the ignore line when you say yes.

## What this plugin runs, sends and stores
Hooks run Python scripts bundled in the plugin (`scripts/`): they read the hook payload from stdin, read `shipwright.json` and `tasks/index.json` in your workspace, and write only `docs/TOKEN-COSTS.md` (from your local `~/.claude/projects/` transcripts). No network calls, no telemetry, no credentials read. The scaffold writes files only into the directory you name and never overwrites existing files, with one documented exception: with `--memory hindsight` or `--context-mode yes` it **merges** the needed `env`, `hooks`, `enabledMcpjsonServers` and `mcpServers` entries into an existing `.claude/settings.json` / `.mcp.json` (adds missing keys only, never removes or replaces yours). The Hindsight hooks it writes call the runtime you installed under `~/.hindsight/coding-agents` (nothing of Hindsight is bundled); they talk to the server URL in your `.hindsight/coding-agent.json`. Agents and skills are Markdown instructions; what they do with your repositories follows your permission settings and the authorizations you give in each prompt.

## Licence
Apache License 2.0 — see LICENSE.
