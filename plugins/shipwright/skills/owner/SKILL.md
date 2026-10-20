---
name: owner
description: The owner's checklist — everything the owner must do that agents never do: versions to release since the last deployed one, environment/configuration lines, migrations, store steps, "For the owner" sections from evidence, open questions with their defaults, and HANDOFF's "waiting on the owner" items. Use before a release, when the owner asks "what do I need to do?", or at the end of a milestone.
disable-model-invocation: true
argument-hint: "[--since vX.Y.Z]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(python3:*)
---
# /shipwright:owner

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/owner_checklist.py" $ARGUMENTS` in the workspace. Without `--since` it uses `shipwright.json` → `project.deployed_version` (keep that field current when the owner reports a deployment); with neither it lists every release note.
2. Edit the generated Markdown into the final checklist: keep only what the owner must do, in the order he must do it (hosts before clients; migrations with the backup step the project uses; configuration lines before the restart; store builds and listing texts; "glance on your phone" checks for criteria that were owner-pending). Quote environment lines exactly as the evidence states them; never invent a key or a value. Credentials and server addresses never appear.
3. Write it to `docs/OWNER-CHECKLIST.md` (overwrite; it is a generated view, the release notes and evidence stay authoritative) and relay it to the owner in the agreed language and channel (terminal, or the chat plugin when the project uses one — docs/CHAT-UPDATES.md).
4. Open questions (docs/QUESTIONS.md §1) go at the end with the default in force for each, so the owner can answer in one message.
