#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# SessionStart hook: one line on this project's cumulative token consumption.
#
# WHY SessionStart AND NOT UserPromptSubmit. A counter that spends tokens every
# turn to tell you about tokens is self-defeating. Once per session is enough to
# notice a trend; the /tokens command is there when you want the detail.
#
# Silent on any failure: a reporting hook must never be the reason a session
# fails to start.
set -uo pipefail

L=$(python3 "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/scripts/token-usage.py" 2>/dev/null \
    | awk '/^  TOTAL/{print}') || exit 0
[ -n "$L" ] || exit 0

printf '%s\n' "$L" | sed 's/[()]//g' | awk '{
  printf "[tokens] this project: out %s, cache read %s, %s messages over %s sessions. /tokens for detail.\n",
         $(NF-4), $(NF-3), $NF, $2
}' 2>/dev/null || true
exit 0
