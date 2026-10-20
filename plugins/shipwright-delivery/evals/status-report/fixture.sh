#!/usr/bin/env bash
# Minimal Shipwright workspace: three tasks, one handoff, policies.
set -e
mkdir -p tasks docs/evidence scripts
cat > shipwright.json <<'J'
{"schema_version":1,"project":{"name":"sample","product_language":"en"},"policies":{"automated_tests":"forbidden"},"repos":[]}
J
cat > tasks/index.json <<'J'
{"schema_version":1,"tasks":[
 {"id":"TASK-0001","title":"Workspace and toolchain setup","file":"tasks/TASK-0001.md","owner":"fullstack-developer","status":"done","priority":0,"depends_on":[],"verification":"passed"},
 {"id":"TASK-0002","title":"Order list API","file":"tasks/TASK-0002.md","owner":"fullstack-developer","status":"ready","priority":10,"depends_on":["TASK-0001"]},
 {"id":"TASK-0003","title":"Order list screen (design part)","file":"tasks/TASK-0003.md","owner":"fullstack-developer","status":"planned","priority":11,"depends_on":["TASK-0002"]}
]}
J
printf '# Handoff\n## State\n- TASK-0001 done; TASK-0002 ready; TASK-0003 planned.\n' > docs/HANDOFF.md
printf '# Questions\n## 1. Open questions\n| ID | Question | Default | Tasks |\n|---|---|---|---|\n| Q-1 | Pickup time slots: 15 or 30 minutes? | 30 | TASK-0002 |\n' > docs/QUESTIONS.md
printf '# CLAUDE.md\nRead docs/HANDOFF.md and tasks/index.json first.\n' > CLAUDE.md
