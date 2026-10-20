#!/usr/bin/env bash
# release-tag.example.sh — the proven two-repository release script of the project the Shipwright
# comes from (one shared product version, annotated vX.Y.Z tags in every code repository, a release
# note per version, eight refusal rules). It is a REFERENCE to adapt, not a drop-in: /shipwright-delivery:release
# setup copies it to scripts/release-tag.sh and replaces the two repository names ("platform-repo",
# "apps-repo", RELEASE_PLATFORMS_REPO/RELEASE_APPS_REPO) with the workspace repos. Never pushes.

# release-tag.sh — one shared product version for platform-repo and apps-repo (ADR-0019, TASK-0159).
# Creates the annotated tag vX.Y.Z in both code repositories and writes docs/releases/vX.Y.Z.md in the workspace.
# It never pushes, never changes a branch, never touches a working tree. Run `release-tag.sh --help` for usage.
set -u

usage() {
  cat <<'EOF'
Usage:
  release-tag.sh <patch|minor> TASK-NNNN [--dry-run]       next version for a task that passed verification
  release-tag.sh --set X.Y.Z TASK-NNNN [--dry-run]         an explicit version for a task (the v0.0.1 baseline)
  release-tag.sh --set X.Y.Z --reason "<text>" [--dry-run] an explicit version without a task (the owner's v1.0.0)

Each repository's tag goes on the newest commit whose subject names the task, after the previous v* tag (L).
A repository with no such commit keeps L's commit; the baseline (no v* tag yet) uses HEAD there.
With --reason the tag goes on HEAD. Tags are annotated, local only, never pushed.

Refusals (all checked before the first tag; nothing is tagged or written on a refusal):
  1 a code repository has uncommitted or untracked changes
  2 the task is not done with verification "passed" in tasks/index.json
  3 the repositories disagree on the newest v* tag (or only one has v* tags)
  4 a commit between L and the target names a different task (tag that task first; not applied with --set --reason)
  5 baseline only: a task in tasks/index.json is in_progress
  6 nothing changed since L (allowed only with --set and --reason)
  7 major, or a --set version not greater than L
  8 the tag (or the release note) already exists

Environment (defaults in brackets; used for scratch runs on clones):
  RELEASE_WORKSPACE        planning workspace: tasks/index.json, docs/releases/ [the folder above this script]
  RELEASE_PLATFORMS_REPO   platform-repo Git root [$RELEASE_WORKSPACE/platform-repo]
  RELEASE_APPS_REPO        apps-repo Git root      [$RELEASE_WORKSPACE/apps-repo]
EOF
}

die() {
  printf 'release-tag: refused: %s\n' "$1" >&2
  exit 1
}

usage_error() {
  printf 'release-tag: %s\n\n' "$1" >&2
  usage >&2
  exit 2
}

# ---------- arguments ----------
bump=""
set_version=""
task=""
reason=""
has_reason=0
dry_run=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dry-run) dry_run=1 ;;
    --set)
      [ $# -ge 2 ] || usage_error "--set needs a version X.Y.Z"
      set_version="$2"; shift ;;
    --reason)
      [ $# -ge 2 ] || usage_error "--reason needs a text"
      reason="$2"; has_reason=1; shift ;;
    patch|minor) [ -z "$bump" ] || usage_error "only one bump"; bump="$1" ;;
    major) die "rule 7: major is not used before 1.0.0 (a breaking API change is a minor while 0.x, ADR-0019); after 1.0.0 the planner extends this rule" ;;
    TASK-*) [ -z "$task" ] || usage_error "only one task"; task="$1" ;;
    *) usage_error "unknown argument: $1" ;;
  esac
  shift
done

if [ -n "$set_version" ]; then
  [ -z "$bump" ] || usage_error "give either a bump or --set, not both"
  printf '%s' "$set_version" | grep -Eq '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$' \
    || usage_error "--set needs a version X.Y.Z (digits only), got: $set_version"
  if [ "$has_reason" -eq 1 ]; then
    [ -z "$task" ] || usage_error "--set with --reason takes no task"
    [ -n "$reason" ] || usage_error "--reason must not be empty"
  else
    [ -n "$task" ] || usage_error "--set needs a task or --reason"
  fi
else
  [ -n "$bump" ] || usage_error "give patch, minor or --set"
  [ "$has_reason" -eq 0 ] || usage_error "--reason is used only with --set"
  [ -n "$task" ] || usage_error "a task ID is required"
fi
if [ -n "$task" ]; then
  printf '%s' "$task" | grep -Eq '^TASK-[0-9]{4}$' || usage_error "task IDs look like TASK-0159, got: $task"
fi

# ---------- locations ----------
script_dir="$(cd "$(dirname "$0")" && pwd)"
workspace="${RELEASE_WORKSPACE:-$(cd "$script_dir/.." && pwd)}"
platforms="${RELEASE_PLATFORMS_REPO:-$workspace/platform-repo}"
apps="${RELEASE_APPS_REPO:-$workspace/apps-repo}"
index="$workspace/tasks/index.json"
notes_dir="$workspace/docs/releases"

[ -f "$index" ] || die "no task index at $index"
for repo in "$platforms" "$apps"; do
  git -C "$repo" rev-parse --show-toplevel >/dev/null 2>&1 || die "not a Git repository: $repo"
done

repo_label() {
  if [ "$1" = "$platforms" ]; then echo "platform-repo"; else echo "apps-repo"; fi
}

# ---------- rule 1: clean working trees ----------
for repo in "$platforms" "$apps"; do
  dirty="$(git -C "$repo" status --porcelain)"
  if [ -n "$dirty" ]; then
    die "rule 1: $(repo_label "$repo") has uncommitted or untracked changes:
$dirty"
  fi
done

# ---------- index reads ----------
index_field() { # <task> <field>  prints the field or nothing
  python3 - "$index" "$1" "$2" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for t in data["tasks"]:
    if t["id"] == sys.argv[2]:
        value = t.get(sys.argv[3])
        if value is not None:
            print(value)
        break
PY
}

in_progress_tasks() {
  python3 - "$index" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
print(" ".join(t["id"] for t in data["tasks"] if t.get("status") == "in_progress"))
PY
}

title=""
if [ -n "$task" ]; then
  status="$(index_field "$task" status)" || die "could not read $index"
  [ -n "$status" ] || die "rule 2: $task is not in tasks/index.json"
  verification="$(index_field "$task" verification)"
  title="$(index_field "$task" title)"
  if [ "$status" != "done" ] || [ "$verification" != "passed" ]; then
    die "rule 2: $task is '$status' with verification '${verification:-unset}'; it must be done with verification passed"
  fi
fi

# ---------- versions ----------
newest_tag() { # newest vX.Y.Z tag by SemVer order, or nothing
  git -C "$1" tag -l 'v*' --sort=-v:refname | grep -E '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$' | head -n 1
}

semver_gt() { # 0 when $1 > $2 (X.Y.Z each)
  local a1 a2 a3 b1 b2 b3
  IFS=. read -r a1 a2 a3 <<EOF
$1
EOF
  IFS=. read -r b1 b2 b3 <<EOF
$2
EOF
  if [ "$a1" -ne "$b1" ]; then [ "$a1" -gt "$b1" ]; return; fi
  if [ "$a2" -ne "$b2" ]; then [ "$a2" -gt "$b2" ]; return; fi
  [ "$a3" -gt "$b3" ]
}

last_platforms="$(newest_tag "$platforms")"
last_apps="$(newest_tag "$apps")"
if [ "$last_platforms" != "$last_apps" ]; then
  die "rule 3: the newest v* tags differ: platform-repo '${last_platforms:-none}', apps-repo '${last_apps:-none}'"
fi
last="$last_platforms"
last_version="${last#v}"

baseline=0
if [ -z "$last" ]; then
  baseline=1
  [ -n "$set_version" ] || die "no v* tag exists yet; create the baseline first with --set X.Y.Z TASK-NNNN"
fi

if [ -n "$set_version" ]; then
  version="$set_version"
  if [ "$baseline" -eq 0 ] && ! semver_gt "$version" "$last_version"; then
    die "rule 7: --set $version is not greater than the newest tag $last"
  fi
else
  IFS=. read -r major minor patch <<EOF
$last_version
EOF
  if [ "$bump" = "patch" ]; then
    version="$major.$minor.$((patch + 1))"
  else
    version="$major.$((minor + 1)).0"
  fi
fi
tag="v$version"

# ---------- rule 5: baseline with unverified work ----------
if [ "$baseline" -eq 1 ]; then
  open_tasks="$(in_progress_tasks)"
  [ -z "$open_tasks" ] || die "rule 5: the baseline needs no task in_progress, but these are: $open_tasks"
fi

# ---------- rule 8: existing tag or note ----------
for repo in "$platforms" "$apps"; do
  if git -C "$repo" rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    die "rule 8: tag $tag already exists in $(repo_label "$repo")"
  fi
done
note="$notes_dir/$tag.md"
[ ! -e "$note" ] || die "rule 8: the release note $note already exists"

# ---------- targets and rule 4 ----------
subject_tasks() { # task IDs named in a subject, one per line
  printf '%s\n' "$1" | grep -Eo 'TASK-[0-9]{4}' | sort -u
}

# compute_target <repo>: sets target (full SHA) and target_note
compute_target() {
  local repo="$1" range sha subject
  target=""
  target_note=""
  if [ "$baseline" -eq 1 ]; then range="HEAD"; else range="$last..HEAD"; fi
  if [ -n "$task" ]; then
    while IFS="$(printf '\t')" read -r sha subject; do
      [ -n "$sha" ] || continue
      if subject_tasks "$subject" | grep -qx "$task"; then
        target="$sha"
        target_note="newest commit naming $task"
        break
      fi
    done <<EOF
$(git -C "$repo" log --topo-order --format='%H%x09%s' "$range")
EOF
  else
    target="$(git -C "$repo" rev-parse HEAD)"
    target_note="HEAD (--reason)"
  fi
  if [ -z "$target" ]; then
    if [ "$baseline" -eq 1 ]; then
      target="$(git -C "$repo" rev-parse HEAD)"
      target_note="HEAD (no commit names $task)"
    else
      target="$(git -C "$repo" rev-parse "$last^{commit}")"
      target_note="stays at $last (no commit names $task since $last)"
    fi
  fi
}

# check_between <repo> <target>: rule 4 on the commits in L..target, oldest first
check_between() {
  local repo="$1" tgt="$2" sha subject named other
  [ "$baseline" -eq 0 ] || return 0
  # --set X.Y.Z --reason tags HEAD on the owner's/planner's explicit word (ADR-0019, 2026-10-07):
  # rule 4 is not applied; the release note lists every carried commit, with or without a task.
  [ "$has_reason" -eq 0 ] || return 0
  while IFS="$(printf '\t')" read -r sha subject; do
    [ -n "$sha" ] || continue
    # A merge commit's subject echoes the merged tasks' ids but carries no change of its own
    # (2026-10-14: the planner's main reconciliation merges); rule 4 reads the merged commits instead.
    if [ "$(git -C "$repo" rev-list --parents -n 1 "$sha" | wc -w)" -gt 2 ]; then
      continue
    fi
    named="$(subject_tasks "$subject")"
    [ -n "$named" ] || continue
    if [ -n "$task" ] && printf '%s\n' "$named" | grep -qx "$task"; then
      continue
    fi
    other="$(printf '%s\n' "$named" | head -n 1)"
    die "rule 4: in $(repo_label "$repo"), commit ${sha:0:7} \"$subject\" names $other and lies between $last and the target; tag $other first (a tag never carries another task's unreleased change)"
  done <<EOF
$(git -C "$repo" log --reverse --topo-order --format='%H%x09%s' "$last..$tgt")
EOF
}

compute_target "$platforms"; target_platforms="$target"; note_platforms="$target_note"
compute_target "$apps"; target_apps="$target"; note_apps="$target_note"
check_between "$platforms" "$target_platforms"
check_between "$apps" "$target_apps"

# ---------- rule 6: nothing changed ----------
if [ "$baseline" -eq 0 ]; then
  last_platforms_commit="$(git -C "$platforms" rev-parse "$last^{commit}")"
  last_apps_commit="$(git -C "$apps" rev-parse "$last^{commit}")"
  if [ "$target_platforms" = "$last_platforms_commit" ] && [ "$target_apps" = "$last_apps_commit" ]; then
    if [ -z "$set_version" ] || [ "$has_reason" -eq 0 ]; then
      die "rule 6: nothing changed since $last in either repository${task:+ (no commit names $task)}; only --set X.Y.Z --reason may tag unchanged commits"
    fi
  fi
fi

# ---------- release note ----------
if [ -n "$task" ]; then
  message="$tag — $task $title"
else
  message="$tag — $reason"
fi
if [ -n "$set_version" ] && [ "$baseline" -eq 1 ]; then
  bump_text="set $version (baseline, no previous tag)"
elif [ -n "$set_version" ]; then
  bump_text="set $version (previous $last)"
else
  bump_text="$bump (from $last)"
fi
now="$(date '+%Y-%m-%d %H:%M:%S %z')"
api_contract="$(git -C "$platforms" describe --tags --abbrev=0 --match 'contracts-v*' "$target_platforms" 2>/dev/null)"
apps_contract="$(git -C "$apps" show "$target_apps:packages/api_client/contract.lock" 2>/dev/null | sed -n 's/^tag=//p' | head -n 1)"
if git -C "$workspace" rev-parse --verify -q HEAD >/dev/null 2>&1; then
  workspace_head="$(git -C "$workspace" rev-parse HEAD)"
  if [ -n "$(git -C "$workspace" status --porcelain 2>/dev/null)" ]; then
    workspace_head="$workspace_head (with uncommitted changes)"
  fi
else
  workspace_head="not a Git repository ($workspace)"
fi

repo_section() { # <label> <repo> <target> <target note>
  local label="$1" repo="$2" tgt="$3" tnote="$4" line sha subject with_task="" without_task="" count
  printf '## %s\n' "$label"
  printf -- '- Target: `%s` (`%s`), %s.\n' "$(git -C "$repo" rev-parse --short "$tgt")" "$tgt" "$tnote"
  if [ "$baseline" -eq 1 ]; then
    count="$(git -C "$repo" rev-list --count "$tgt")"
    printf -- '- Baseline: no earlier v* tag; the tag covers the whole history up to the target (%s commits).\n\n' "$count"
    return
  fi
  while IFS="$(printf '\t')" read -r sha subject; do
    [ -n "$sha" ] || continue
    line="  - \`$sha\` $subject"
    if [ -n "$(subject_tasks "$subject")" ]; then
      with_task="$with_task$line"$'\n'
    else
      without_task="$without_task$line"$'\n'
    fi
  done <<EOF
$(git -C "$repo" log --topo-order --format='%h%x09%s' "$last..$tgt")
EOF
  if [ -z "$with_task$without_task" ]; then
    printf -- '- Commits since %s: none (the tag stays on %s'"'"'s commit).\n\n' "$last" "$last"
    return
  fi
  printf -- '- Commits since %s:\n' "$last"
  [ -z "$with_task" ] || printf '%s' "$with_task"
  if [ -n "$without_task" ]; then
    printf -- '- Commits without a task:\n%s' "$without_task"
  fi
  printf '\n'
}

note_text="$(
  printf '# %s\n\n' "$tag"
  printf -- '- Version: %s\n' "$version"
  printf -- '- Tagged: %s\n' "$now"
  if [ -n "$task" ]; then
    printf -- '- Task: %s — %s\n' "$task" "$title"
  else
    printf -- '- Reason: %s\n' "$reason"
  fi
  printf -- '- Bump: %s\n' "$bump_text"
  printf -- '- Tag message: %s\n' "$message"
  printf -- '- API contract (platform-repo at the target): %s\n' "${api_contract:-none}"
  printf -- '- Apps pinned contract (packages/api_client/contract.lock at the target): %s\n' "${apps_contract:-none}"
  printf -- '- Planning workspace HEAD: %s\n\n' "$workspace_head"
  repo_section "platform-repo" "$platforms" "$target_platforms" "$note_platforms"
  repo_section "apps-repo" "$apps" "$target_apps" "$note_apps"
)"

# ---------- summary / effects ----------
printf 'release-tag: %s — %s — %s\n' "$tag" "$bump_text" "${task:+$task \"$title\"}${reason:+reason \"$reason\"}"
printf '  platform-repo: %s — %s\n' "$(git -C "$platforms" rev-parse --short "$target_platforms")" "$note_platforms"
printf '  apps-repo:      %s — %s\n' "$(git -C "$apps" rev-parse --short "$target_apps")" "$note_apps"
printf '  release note:     %s\n' "$note"

if [ "$dry_run" -eq 1 ]; then
  printf '\n--- release note (not written) ---\n%s\n---\ndry run: nothing tagged or written.\n' "$note_text"
  exit 0
fi

git -C "$platforms" tag -a "$tag" -m "$message" "$target_platforms" || die "could not create $tag in platform-repo"
if ! git -C "$apps" tag -a "$tag" -m "$message" "$target_apps"; then
  git -C "$platforms" tag -d "$tag" >/dev/null
  die "could not create $tag in apps-repo; the platform-repo tag was removed again"
fi
if ! { mkdir -p "$notes_dir" && printf '%s\n' "$note_text" > "$note"; }; then
  git -C "$platforms" tag -d "$tag" >/dev/null
  git -C "$apps" tag -d "$tag" >/dev/null
  rm -f "$note"
  die "could not write $note; both tags were removed again"
fi
printf 'tagged %s in both repositories (local only, not pushed); wrote %s\n' "$tag" "$note"
