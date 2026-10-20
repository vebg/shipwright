---
name: release
description: Set up or run the kit's release bookkeeping — one shared product version tagged in every code repository per verified task, a release note per version, compatibility rules after the first public release. Use when the owner wants versioning/tagging or a release note, or when the planner needs to record the "Release bump" of a task.
disable-model-invocation: true
argument-hint: "[setup|note vX.Y.Z|bump TASK-NNNN|store-notes]"
---
# /shipwright:release

Argument: `$ARGUMENTS`.

## The rules this skill implements (adopt them with an ADR before the first tag)
- **One shared product version** across every code repository; the workspace records it in `docs/releases/vX.Y.Z.md` and is not tagged itself.
- **One version per verified task** from the baseline on: a fix is a patch, a feature a minor, a breaking contract change a minor before 1.0.0 and a major after it. The planner writes the bump in the task's "Release bump" line; the manual-tester tags as the last step of a passed verification.
- **Annotated tags `vX.Y.Z`** on the newest commit naming the task in each repository (a repository without a commit for the task keeps the previous tag's commit), local only — pushing is the owner's. Commit subjects carry `(TASK-NNNN)`.
- **Refusals**: dirty repository; task not done/passed; repositories disagreeing on the newest tag; an earlier untagged task's commit in between (tag that first, or release the batch as one explicit `--set X.Y.Z --reason` version); nothing changed since the last tag; an existing tag or note.
- **v1.0.0 only on the owner's word**; after it, changes are additive by default and each API release is checked against the last published client build before tagging; a breaking change is an owner-approved event with an "Impact on installed clients" summary.
- **Build versions** come from the checked-out tag (development builds show `0.0.0`); no version-bump commits.

## `setup`
Write `docs/decisions/ADR-NNNN-product-versioning-and-release-tags.md` from the rules above (status Proposed until the owner accepts), add the "Release bump" line to templates/TASK.md if missing, add a "Release tagging" section to docs/WORKFLOW.md, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/release_setup.py"` (renders `scripts/release-tag.sh` for a two-repository workspace from the reference script with the repository names of `shipwright.json`; explains the single-repository case; never overwrites), and create `docs/STORE-RELEASE-NOTES.md` from `${CLAUDE_PLUGIN_ROOT}/skills/release/assets/STORE-RELEASE-NOTES.md.tmpl` when the project publishes to app stores. Record `project.deployed_version` in `shipwright.json` whenever the owner reports a deployment (the owner checklist starts from it).

## `note vX.Y.Z`
Write `docs/releases/vX.Y.Z.md`: version, date with offset, task(s), bump, each repository's target commit and the commit subjects since the previous tag, the contract version if the workspace pins one, the workspace HEAD. Never invent commits: read them with `git log` in each repository.

## `bump TASK-NNNN`
Read the task and its requirement links; propose patch/minor/major with the reason; write the "Release bump" line into the task body. Do not tag.

## `store-notes`
Update `docs/STORE-RELEASE-NOTES.md`: for every verified task since the last published build, decide whether it earns a user-facing sentence (user-visible behaviour yes; backend, legal dates, configuration no) and draft it in the product language, in the user's words, without task ids; keep the Play 500-character limit in view. The owner approves the text; the planner never submits to a store.
