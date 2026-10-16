#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# PreToolUse hook on Bash. Refuses to commit, push, merge, tag or open a pull request or
# issue on a repository whose owner is not in the user's list.
#
# The user's rule: nothing is committed on a repository that does not belong to them.
# Ownership is read from the remote, not assumed -- the repository that prompted this
# was thought to be theirs and sat under another person's account, where they had WRITE.
#
# The list is ~/.claude/owned-owners. THE AGENT MUST NEVER EDIT IT TO UNBLOCK ITSELF: that
# is the exact act the rule forbids. Only the user adds an owner.
#
# No opt-out in the environment, deliberately; a variable is one `export` away from being
# used to get past the rule.
set -uo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input", {}).get("command", ""), end="")
except Exception: pass' 2>/dev/null)
CWD=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd", ""), end="")
except Exception: pass' 2>/dev/null)
[ -n "$COMMAND" ] || exit 0

VERDICT=$(printf '%s' "$COMMAND" | OWNERSHIP_CWD="${CWD:-$PWD}" python3 "$(dirname "$0")/ownership-classify.py" 2>/dev/null)
STATUS=$?
[ "$STATUS" = 0 ] && exit 0
if [ "$STATUS" != 2 ]; then
    echo "no-foreign-commit: classifier failed (status $STATUS) -- command NOT checked" >&2
    exit 1
fi

OWNER=${VERDICT%%$'\t'*}; WHAT=${VERDICT#*$'\t'}
LIST="${HOUSE_RULES_OWNED:-$HOME/.claude/owned-owners}"
{
    echo "BLOCKED by no-foreign-commit: '$WHAT' would write to a repository owned by '$OWNER'."
    echo
    if [ -f "$LIST" ]; then
        echo "That owner is not in $LIST."
    else
        echo "$LIST does not exist, so no owner is known to be the user's."
    fi
    cat <<'TXT'

The rule: nothing is committed, pushed or opened on a repository that does not belong
to the user. Write access is not ownership.

Do NOT edit the list to get past this -- that is exactly what the rule forbids. Tell the
user which owner and repository, and let them decide. If it is theirs, they add one line:
    github.com/<owner>
TXT
} >&2
exit 2
