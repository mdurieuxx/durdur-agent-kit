#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# SessionStart hook: puts the plugin's few standing rules in the session context.
#
# A plugin has no rules/ directory (0 of the 315 official plugins use one), but a
# SessionStart hook's output enters the context, so a short rule CAN travel with it.
# The price is its tokens for the whole session, so this is reserved for rules that
# are judgment (not hook-checkable) or that the harness's own defaults contradict.
#
# Rule 1 is enforced by no-attribution regardless. It is also stated here because the
# harness's default instruction is to add the trailer: without this line, every first
# commit attempt is refused and retried -- a wasted round trip each time.
#
# Silent on failure: a hook that informs must never be why a session fails to start.
set -uo pipefail
cat "$(dirname "$0")/session-rules.txt" 2>/dev/null || true
exit 0
