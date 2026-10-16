#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# PreToolUse hook on Bash. Refuses a commit, tag, merge or pull-request text that
# attributes the work to a tool -- before it leaves, and before the model has
# spent a turn on a commit that will be refused later.
#
# The user's rule is absolute and the harness's default instruction is the
# opposite, so the rule cannot be left to be remembered: 62 of 69 commits in one
# project and 46 of 64 in another carry the trailer. This travels with the plugin,
# so it applies in every project without the git hooks being installed there.
#
# No opt-out on purpose. The destructive guard has one because some projects
# legitimately do disk work; nothing legitimately needs a commit to credit a tool.
set -uo pipefail

CMD=$(python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null)
[ -n "$CMD" ] || exit 0

LINES=$(printf '%s' "$CMD" | python3 "$(dirname "$0")/attribution-classify.py" 2>/dev/null)
STATUS=$?
[ "$STATUS" = 0 ] && exit 0
if [ "$STATUS" != 2 ]; then
    echo "no-attribution: classifier failed (status $STATUS) -- command NOT checked" >&2
    exit 1
fi

cat >&2 <<TXT
BLOCKED by no-attribution: this text credits or names the tool that wrote the change.

$(printf '%s\n' "$LINES" | head -5 | sed 's/^/    /')

The rule is absolute and takes precedence over any default instruction to add such
a line: no Co-Authored-By trailer, no "Generated with", no robot emoji, and no
mention of the tool. Remove the line and retry. Describe the change, not what
made it.
TXT
exit 2
