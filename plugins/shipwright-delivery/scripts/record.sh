#!/usr/bin/env bash
# record.sh — record a short MP4 of a local simulator/emulator or a screen region for evidence.
# Usage:
#   record.sh ios  <TASK-ID> <name> [seconds=20] [udid]     # xcrun simctl io recordVideo (booted simulator by default)
#   record.sh android <TASK-ID> <name> [seconds=20] [serial] # adb screenrecord, pulled to the evidence folder
#   record.sh screen <TASK-ID> <name> [seconds=20]          # macOS screen via ffmpeg avfoundation (whole display 1)
# Output: docs/evidence/screenshots/<TASK-ID>/<name>.mp4 (H.264, playable in chat apps). Never uploads anything.
set -euo pipefail
kind="${1:-}"; task="${2:-}"; name="${3:-}"; secs="${4:-20}"; dev="${5:-}"
[ -n "$kind" ] && [ -n "$task" ] && [ -n "$name" ] || { sed -n 2,7p "$0"; exit 2; }
root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
while [ "$root" != "/" ] && [ ! -f "$root/tasks/index.json" ]; do root="$(dirname "$root")"; done
[ -f "$root/tasks/index.json" ] || { echo "not inside a Shipwright workspace" >&2; exit 1; }
out_dir="$root/docs/evidence/screenshots/$task"; mkdir -p "$out_dir"; out="$out_dir/$name.mp4"
case "$kind" in
  ios)
    command -v xcrun >/dev/null || { echo "xcrun missing (Xcode)"; exit 1; }
    target="${dev:-booted}"
    echo "recording iOS simulator ($target) for ${secs}s → $out"
    xcrun simctl io "$target" recordVideo --codec h264 --force "$out" & pid=$!
    sleep "$secs"; kill -INT "$pid"; wait "$pid" || true ;;
  android)
    command -v adb >/dev/null || { echo "adb missing (platform-tools)"; exit 1; }
    s=(); [ -n "$dev" ] && s=(-s "$dev")
    echo "recording Android (${dev:-default}) for ${secs}s → $out"
    adb "${s[@]}" shell screenrecord --time-limit "$secs" --bit-rate 4000000 /sdcard/shipwright-rec.mp4
    adb "${s[@]}" pull /sdcard/shipwright-rec.mp4 "$out" >/dev/null; adb "${s[@]}" shell rm /sdcard/shipwright-rec.mp4 ;;
  screen)
    command -v ffmpeg >/dev/null || { echo "ffmpeg missing (brew install ffmpeg)"; exit 1; }
    echo "recording the screen for ${secs}s → $out (grant screen-recording permission to the terminal once)"
    ffmpeg -y -loglevel error -f avfoundation -framerate 30 -i "1:none" -t "$secs" -pix_fmt yuv420p -vcodec libx264 -preset veryfast "$out" ;;
  *) echo "unknown kind: $kind (ios|android|screen)"; exit 2 ;;
esac
ls -la "$out"
