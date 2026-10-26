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
# Seed the ownership list once, from what GitHub says. Quiet, and never overwrites.
[ -e "$HOME/.claude/owned-owners" ] || "$(dirname "$0")/../scripts/seed-owned-owners.sh" >/dev/null 2>&1 || true
cat "$(dirname "$0")/session-rules.txt" 2>/dev/null || true
# Plugin option cost_before_clear (default on). Witnessed: a clear proposed without the
# cost of a message, after the owner had asked for it every time; the skill alone was not enough.
if [ "${CLAUDE_PLUGIN_OPTION_COST_BEFORE_CLEAR:-true}" != "false" ]; then
  echo "3. Every clear proposal, and the first reply after a clear, starts with the cost of a message: context size (tokens re-read each turn), session total, window fill. A proposal or resume without it is incomplete."
fi
exit 0
