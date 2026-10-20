---
name: start
description: Guided entry point of the Shipwright. Runs the discovery interview (product, users, surfaces, inspiration links/videos/apps, technologies already decided, constraints, brand, working agreement), collects the few decisions the kit needs, scaffolds the workspace (optionally with Hindsight memory and context-mode wiring) and explains the next step. Also adopts an existing repository, resumes a workspace, or sets up memory, context-mode or device tools. Use when a directory has no Shipwright workspace yet or the user asks how to begin.
disable-model-invocation: true
argument-hint: "[new|adopt|resume|memory|context|devices]"
allowed-tools: AskUserQuestion, Read, Glob, Grep, Write, Edit, WebFetch, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/scaffold.py *)
---
# /shipwright-delivery:start

You are running the Shipwright intake. Ask, decide, scaffold, explain — in that order. Never scaffold before the user has answered. Argument given: `$ARGUMENTS` (empty means ask). Speak to the user in the language they write in; the files you write are in English.

## 1. What does the user want to do?
If no argument was given, ask with AskUserQuestion (single select):
- **New product workspace** — discovery interview, then plan and build a new product from requirements with the planner, designer, developer and tester agents.
- **Adopt an existing repository** — a shorter interview, then add the workflow (backlog, evidence, decisions) to code that already exists in this directory.
- **Resume a workspace** — continue work in a Shipwright workspace (read its handoff and backlog).
- **Set up memory (Hindsight), context-mode or device tools** — wire the optional companions into an existing workspace.

For **Resume**: if the current directory is a workspace (`shipwright.json` or `tasks/index.json` + `docs/HANDOFF.md`), run `/shipwright-delivery:resume`; otherwise ask for the workspace path and tell the user to start Claude Code there.

For **memory / context / devices** in an existing workspace go to §5.

## 2. Discovery interview (new product; abbreviated for adopt)
Goal: understand the product well enough that the planner's first `/shipwright-delivery:plan` has real material, and capture every link, video, app or file the user wants the team to look at. Run it in **rounds** with AskUserQuestion — at most four questions per call, each with 2–4 concrete options plus the automatic "Other" for free text — and keep the rounds short (five to six calls for a new product, two to three for adopt). Acknowledge each round in one line and move on; never lecture. When the user gives a URL, fetch it with WebFetch only if it is public and the user wants you to read it; otherwise record it as a reference. Never ask for credentials, keys or production data.

Round A — the product: what it is in one paragraph (free text); who the users are and their technical comfort (options: general public / staff / both / developers); the problem and how it is handled today; the single result that would make version 1 a success.
Round B — surfaces and reach: surfaces in scope (multi-select: public web, web admin, mobile iOS/Android, tablet, display/TV, API/integrations); end-user language(s); countries/time zones/currencies; offline, realtime or notification needs.
Round C — inspiration and references: products, apps, sites, videos, screenshots or competitors to look at (free text, one per line, with "what to take / what not to take"); whether files will be dropped in `design/inbox/` or `requirements/inbox/`.
Round D — technology and constraints: decisions already made (stack, frameworks, libraries, hosting, repositories, CI, stores — "undecided, propose" is a valid answer and the planner then proposes in `docs/ARCHITECTURE.md`); existing systems/data/APIs to integrate; legal, privacy, payments, accessibility constraints; hard limits (budget, dates, devices, team).
Round E — brand and design: brand status (nothing / drafts / final assets, and where); tone in three words; known no-gos.
Round F — working agreement: **automated tests policy** — ask it explicitly and explain the trade-off in two sentences before the options: *"Shipwright ships with manual verification: the tester runs the real API, browsers and devices against every acceptance criterion and records evidence, so you review deliverables instead of test code. Automated tests are possible, but every test file is written, run and maintained by agents — roughly a third more tokens per task and more time before anything ships; most owners who want to ship choose to review the deliverables instead."* Options: *None — manual verification with evidence (recommended, proven, cheaper)* / *Allowed — tests permitted, manual verification still gates done (more tokens, slower)*; record the answer and the reason in the discovery file; repository layout (*Single repository* / *Multi-repository workspace* — then name, folder and one-line stack per child); how the owner wants updates (terminal only / chat plugin) and in which language; what is explicitly out of scope for version 1; memory, context-mode and device tools (§5 options, each yes/no); a cost budget in USD for `/shipwright-delivery:balance` (optional); whether updates also go to a chat plugin (then `--chat-updates yes` copies docs/CHAT-UPDATES.md).

For **adopt**: rounds A (short), D (what exists: stack, folders, commands that work), F; the rest only if the user volunteers it.

Write the answers to `requirements/inbox/DISCOVERY-<YYYY-MM-DD>.md` using `${CLAUDE_PLUGIN_ROOT}/skills/start/assets/discovery/DISCOVERY.md.tmpl` (after the scaffold, so the folder exists; one file per interview, never overwrite an earlier one). References with files go to `design/inbox/RESOURCE-LIST.md` (visual) or `requirements/CATALOG.md` rows (functional) when the files arrive. Put every unanswered consequential question into `docs/QUESTIONS.md` with a default in force.

## 3. Decisions the scaffold needs
From the interview (ask only what is still missing, in one AskUserQuestion call): project name (kebab-case suggestion from the directory name), repository layout and child repos, automated tests policy, stack summary (one line per deployable), product language, mobile/tablet in scope, web UI in scope, memory (Hindsight) yes/no — and if yes, self-hosted URL (default `http://127.0.0.1:8888`) or cloud —, context-mode yes/no.

Routine choices (folder names, templates) are not asked; the kit's defaults apply and can be edited later.

## 4. Scaffold
Run the scaffold with the answers (quote values; repeat `--repo` per child):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/scaffold.py --target "<directory>" --name "<project>" --mode <new|adopt> --tests <forbidden|allowed> --language <code> --stack "<summary>" [--mobile yes|no] [--web yes|no] [--repo "<name>=<folder>:<stack>" ...] [--memory hindsight [--hindsight-url URL] [--hindsight-mode self-hosted|cloud]] [--context-mode yes]
```

The script never overwrites existing files (it lists what it skipped), creates the kit folders, renders `CLAUDE.md`, `shipwright.json`, the docs, templates, design hub, `.claude/settings.json`, `tasks/index.json`, the first ADRs and copies the validator, the token report and the protocol references. With `--memory hindsight` it also writes the tracked `.hindsight/coding-agent.json`, merges the Hindsight hooks, `env` and MCP servers into `.claude/settings.json` and `.mcp.json` (adds missing entries only), ignores `/.hindsight/logs/`, and copies the runtime's companion skill from `~/.hindsight/coding-agents/skill/` when present. With `--context-mode yes` it writes `CONTEXT_MODE_DIR` and ignores `/.context-mode/`. `--budget-usd N` stores the budget for `/shipwright-delivery:balance`; `--chat-updates yes` copies docs/CHAT-UPDATES.md. Then write the discovery file (§2), run `python3 scripts/validate_backlog.py` in the target and show the result.

## 5. Memory, context-mode and device tools
Explain, confirm, and only then act. Nothing here installs software without the user's explicit yes; the kit bundles none of these tools.
- **Hindsight memory** (long-term project memory, one bank per workspace). Prerequisites the user installs: a Hindsight server (self-hosted in Docker, API on `127.0.0.1:8888` by default, or the cloud service) and the runtime `npx @vectorize-io/hindsight-coding-agents install claude-code` (stages `~/.hindsight/coding-agents`). Then, in the workspace: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/scaffold.py --target . --name "<project>" --mode adopt --memory hindsight [--hindsight-url URL]` — it adds only the memory files and entries (everything else is skipped as existing). Restart Claude Code; the 🧠 banner and the `mcp__hindsight` tools confirm the wiring. Edit `.hindsight/coding-agent.json` `customPages` to the project's own questions.
- **context-mode** (sandboxed command output and document indexing): `claude plugin marketplace add mksglu/context-mode` then `claude plugin install context-mode@context-mode` (user scope) or enable it in the project's `enabledPlugins`; then `scaffold.py --target . --name "<project>" --mode adopt --context-mode yes` writes `CONTEXT_MODE_DIR` and the ignore line. `/context-mode:ctx-doctor` checks the install.
- **Device tools**: `claude plugin install shipwright-devices@shipwright`; the designer and the tester then drive local simulators/emulators; remote devices are never allocated without the user's approval.

## 6. Explain the next step (short)
- Put the software requirements (any format) in `requirements/inbox/` next to the discovery file and complete `requirements/INTAKE.md`; physical or commercial background notes go in `requirements/context/`.
- Brand files, references, videos and screenshots go in `design/inbox/` (read `design/README.md`); the kit treats branding as pending until approved values exist.
- For a multi-repository workspace: create or move each child Git root into its folder, commit the parent `.gitignore` first, and place the generated `templates/<repo>-CLAUDE.md` as `<repo>/CLAUDE.md` with the repository's real commands.
- Restart Claude Code in the workspace: the plugin makes `planner` the main-session agent (`/agents` shows planner, frontend-designer, fullstack-developer, manual-tester, store-compliance-reviewer). Then run `/shipwright-delivery:plan`.
- Optional: the companions of §5; the design skills the designer uses (`frontend-design@claude-plugins-official`, `impeccable@impeccable`, the Emil Kowalski motion skills) — see the plugin README §Design tooling.

Finish by listing the files created, the files skipped, the discovery file path and the exact next command.
