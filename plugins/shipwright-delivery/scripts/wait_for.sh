#!/usr/bin/env bash
# wait_for.sh — poll a local URL until it answers, instead of a bare sleep. Nothing is downloaded or executed.
# Usage: wait_for.sh <url> [attempts=30] [delay-seconds=1]
# Exit 0 when the URL returns any HTTP status, 1 when the attempts run out.
set -euo pipefail
url="${1:-}"; attempts="${2:-30}"; delay="${3:-1}"
[ -n "$url" ] || { sed -n 2,4p "$0"; exit 2; }
i=0
while [ "$i" -lt "$attempts" ]; do
  if curl -s -o /dev/null --max-time 2 "$url"; then
    echo "up after $((i + 1)) attempt(s): $url"
    exit 0
  fi
  i=$((i + 1))
  sleep "$delay"
done
echo "not reachable after $attempts attempts: $url" >&2
exit 1
