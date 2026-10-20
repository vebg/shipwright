# Why these rules
Shipwright's rules come from one product shipped end to end (mobile apps in two stores, three web hosts, an API) with Claude Code agents. Each rule exists because its absence cost a release.

- **Planner as the main session.** A single thread that owns requirements, scope and the backlog keeps every decision written down (`requirements/inbox/USER-DECISIONS-*`, ADRs, task bodies). Agents started ad hoc re-litigated settled choices; the planner's "read the index, the task and its linked context" rule keeps context small and decisions stable.
- **Evidence gates done.** A passing build proved nothing about booking races, authorization or time zones. A separate manual-tester that runs real requests, concurrent requests, database queries, devices and browsers — and writes what it saw — caught the defects builds did not.
- **Manual verification by default, tests optional.** Agents writing and maintaining test suites spent tokens and time without the confidence a real run gives; owners who want to ship review deliverables instead. The policy is a choice at intake, not a dogma.
- **Static-first design, integration by the developer.** Designers produce markup, styles and every state as a design route with real screenshots; the developer binds data and owns every fix. Re-invoking the designer for defects produced redesigns instead of fixes.
- **One agent per repository at a time, three tasks per batch.** Parallel agents on one repository collided on files and Git state; small batches keep the owner's go meaningful and the cost visible.
- **Task line in every agent prompt.** `Task: TASK-XXXX` makes every token attributable; `/shipwright-delivery:balance` turns that into a per-feature cost and a forecast.
- **Memory is a past record.** Long-term memory (Hindsight) answers "why" quickly, but a remembered decision is never confirmation of new work; the handoff, index, task bodies and evidence stay authoritative.
- **Nothing pushed, deployed or purchased by an agent.** Releases are tagged locally per verified task; deployment, stores and credentials are the owner's, with a generated checklist (`/shipwright-delivery:owner`) instead of improvisation.
