---
name: doctor
description: Check the machine and the workspace before agents run — Python, Git, Node, Claude Code, the kit files and validator, the code repositories, the Hindsight runtime/server/hooks, context-mode, guard hooks, ignore lines, and the mobile/evidence tools (Xcode, adb, Flutter, .NET, ImageMagick, ffmpeg). Use at the start of a project, after installing companions, or when something "does not work".
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py *)
---
# /shipwright-delivery:doctor

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py` in the workspace (add `--root <path>` when elsewhere). It is read-only and always exits 0; the report is the result.

Then tell the owner, in three lines or a short table: what is MISSING (with the exact fix command from the report), what is a WARN that matters for *this* project (an Android project without `adb`, a wired Hindsight whose server is down), and what is fine. Do not install anything from this skill; installs need the owner's explicit authorization in a later prompt. If the backlog validator failed, that comes first — nothing is planned on an invalid index.
