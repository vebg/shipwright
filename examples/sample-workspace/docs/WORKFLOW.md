# Shared task protocol
The planner creates a requirement catalog, scope and architecture proposals, then a dependency graph and individual task files. The main session invokes the developer only for eligible work and the manual-tester for handed-over work. Work is serialized by default. Project-specific rules the owner adds (device rules, local sign-in methods, regression passes, release tagging) are appended below as dated sections.

Index fields: `id`, `title`, `file`, `owner`, `status`, `priority`, `depends_on`; optional `blocker`, `evidence`, `verification` (`pending`, `passed`, `failed`) and `superseded_by`/`note`. The index owns status and dependency data. Do not duplicate those fields in task bodies. Task bodies own specification and verification details.

States:
- planned: scoped or outlined, not yet actionable.
- ready: detailed, decisions settled, every dependency done.
- in_progress: one worker owns the task and has begun work.
- blocked: cannot proceed; blocker field explains why.
- done: acceptance checks passed, evidence recorded. For implementation tasks only the manual-tester (or the owner) sets done, with `verification: "passed"`; design parts and planning tasks are closed by the planner.
- superseded: intentionally replaced or removed by an owner decision, with a traceable note (and follow-up task if any).

## Manual verification flow (ADR-0001)
1. fullstack-developer or frontend-designer: ready → in_progress; implements; runs build/analyze/format and a quick run; writes the Implementation section of docs/evidence/<ID>.md (including how to start, seed and reproduce); sets `verification: "pending"` and keeps status in_progress. A frontend-designer hand-over (static-first) sets the index `note` to "design part done <date>; planner inspection pending" and leaves `verification` unset; the planner inspects the screenshots and evidence, relays them to the owner and closes the design part (done, `verification: "passed"`, note "closed by planner inspection <date>; visual criteria carried into <integration task>"), and the fullstack-developer then builds the linked integration task, which the manual-tester verifies end to end including the visual criteria.
2. The main session (planner) invokes manual-tester for tasks with `verification: "pending"`.
3. manual-tester: verifies every acceptance criterion on the real API/apps/browsers (negative, authorization and concurrency checks included), appends a Manual verification section with steps, observations and screenshots, then sets done + `verification: "passed"`, or ready + `verification: "failed"` with defects. Missing tooling/input keeps the task pending or blocked with the reason.
4. fullstack-developer picks failed tasks first — whoever implemented them; frontend-designer is never re-invoked for defects — fixes them keeping the designer's structure, tokens and copy (a fix that needs a design change is recorded for the planner), and hands over again (step 1).
Planner-owned tasks are verified by focused inspection and the backlog validator, not by manual-tester.

## UI work split (static-first)
The static presentation of every surface is built by `frontend-designer`: markup, styles and theming, screen/widget/theme files, layouts, motion, every UI state as a separate Development-only design route/section with sample values hardcoded in the markup, accessibility attributes, UI strings, design-system runtime exports and screenshots — no application code (no view-models, presentation or fixture sources, services, DI, URL state, providers, clients). `fullstack-developer` builds the backend and the whole integration — view-models, sources, API/realtime clients, authentication, state and navigation wiring, persistence, error/reconnect paths — moving the designer's markup into the real components, binding every hardcoded value it listed and deleting the design routes; plus foundation and scaffolding. The planner names the executing agent(s) in the task body; the index owner stays `fullstack-developer` because it is accountable for every fix after hand-over. Two shapes: (a) linked tasks — `<feature> UI (design part)` with visual-only criteria closed by planner inspection, then `<feature> integration` verified end to end by manual-tester including those visual criteria (default for new screens); (b) one task with the two-stage hand-over of step 1 for small UI. Agents on the same repository run sequentially either way. Look-and-feel changes requested by the owner are new design work for the designer; failed acceptance criteria are defects for the developer. Ad-hoc verification scripts stay outside the code repositories.

Measured rationale (the project this kit comes from): a design part that also built fixture plumbing cost about 10 M tokens / $20 / 46 min, more than the developer batch that integrated three features ($16.7); most of that spend was code the product did not keep. Static-first halved it and removed one tester run per feature.

## Native apps in three stages (optional, for mobile products)
Stage 1: `fullstack-developer` builds the data/domain layers, state providers, clients, session storage, realtime wiring and plugin installs of each app without screens; it hands over with `verification: "pending"` and evidence of real calls against the local API (a scratch harness or a deleted smoke entry) plus analyze/format/builds; the planner closes by inspection. Stage 2: `frontend-designer` delivers the design-system package and one design part per app on the provisional tokens as the final layout and motion (the final brand later swaps colours, logos and fonts only), closed by inspection. Stage 3: feature tasks integrate screens with the stage-1 layer; `manual-tester` verifies them on Android and iOS with the device tools and database queries.

## General rules
A task cannot use a superseded dependency as satisfied. Replan its dependency explicitly. Newly unblocked tasks still need a definition-of-ready review. If a done task regresses, record follow-up work and reassess dependent tasks rather than silently changing history.

Use stable IDs and dependency edges for order, not filenames alone. Maintain requirement-to-task coverage in docs/TRACEABILITY.md. Detail the next milestone and keep future tasks small in the index until needed. No arbitrary target task count.

Evidence belongs in docs/evidence/<ID>.md. Include each acceptance criterion and result, commands and outcomes, relevant manual/browser checks and unresolved limitations. A validator can check file existence; it cannot establish that the claims are truthful or the product works.

At each boundary update docs/HANDOFF.md. Keep it short and link to detail. After a session ends, use the handoff to resume; no always-on scheduler or usage-limit bypass is included.

## Repository-aware execution
Canonical task files/index and evidence live in the workspace. Repository and impact metadata belongs in each task body, not duplicated status fields. Cross-repository dependencies remain ordinary task-ID edges in this one graph. Record the relevant Git revision and dirty state for each checkout in evidence and HANDOFF. Git status/build/run commands must execute in the intended repository.

## Scope and evidence discipline
Before substantial work, connect scope/assumptions to observable outcomes. Before hand-over, inspect changed files in each affected repository for unrelated edits; the manual tester checks that each observation actually demonstrates the promised behavior. Evidence distinguishes baseline failures, new failures, passing checks and checks not run. Keep optional unrelated improvements out of the active task. The batch limit, blocker handling and authorization boundaries remain in force.

## Session sizing, captures and local verification
- Cost grows with session length (measured: a 322-turn design session cost $186; the same work as two ~80-tool-call parts cost $20). A large design task runs as parts — one short designer session, one commit and one planner inspection per part, the task `in_progress` between parts with the index note "part X done <date>; planner inspection pending". Developer invocations are sized the same way: one large task alone, or up to three small ones.
- Design captures: every state once on the default device at text scale 1.0; larger text scale and the second platform only for the states the task names; a gallery capture only for a shared widget that changed. Captures come from the final build of the part.
- Every state that must be captured is reachable by a route option (query parameters, preview entries), so a state never depends on a tap walk. Device tools (shipwright-devices plugin) tap, type and read the screen on local simulators and emulators; remote devices are never allocated without the owner's explicit approval. Simulators have limits (no own time zone or airplane mode on the iPhone simulator; spoken screen-reader output cannot be observed by an agent — record the accessibility tree and say so).
- Each agent works in its own subfolder of the session scratch directory so that one run does not overwrite another's scripts.
- `Monitor` may be unavailable: start a server or emulator in the background and poll with a command that does work (the plugin's `scripts/wait_for.sh <url>`, `adb wait-for-device`), never a bare `sleep`.
- Production behaviour of a web host is checked on the published build, not the development server.
- Reading discipline (every agent, the planner included): search (`grep -n`) before reading; read a file with offset and limit around the lines needed; read a whole file only when it is the task file, a brief, or short; never read the same file twice in a session unless it changed; evidence files are read by section.
- Screenshots are the most expensive reads. A design hand-over includes contact sheets — one image per screen group with the captures side by side, saved as `contact-<group>.png` beside the captures — and the planner inspects those, opening a single capture only where a sheet shows a doubt.
- The planner's session is cleared at a task boundary once it is long: state lives in docs/HANDOFF.md, tasks/index.json and docs/evidence.

## Agent starts need the owner's go
The planner plans, documents and runs read-only checks on its own, but starts a developer, designer or tester run only after the owner says go for that task or batch (a go given for a batch covers its developer → tester sequence).

## Commits land on the agreed branch
The developer commits on the branch named in each repository's CLAUDE.md (default `main`), never on a checked-out tag or detached HEAD; before handing over it runs `git branch --show-current`. Every code commit names its task as `(TASK-NNNN)` in the subject. No push: remotes and pushing stay the owner's.

## Language
Communication with the owner — terminal replies, chat updates, questions, handoff summaries — is in English unless the owner says otherwise. The product language (shipwright.json) applies only to end-user texts.
