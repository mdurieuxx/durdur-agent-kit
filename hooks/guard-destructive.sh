#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# PreToolUse hook on Bash, shipped by the house-rules plugin. Active by default in
# every project, because the one time it matters is the time nobody expected it.
#
# WHY IT EXISTS. A disk was wiped while the user was interrupting the command: the
# confirmation had been piped in, removing the only window the interrupt could land
# in. wipefs and sfdisk finish in under a second. Good intentions are not a guard.
#
# PER-PROJECT OPT-OUT. Some projects do disk and container work for a living -- a
# NAS admin session legitimately runs wipefs, mkfs and docker prune. A guard that
# obstructs normal work gets switched off wholesale, and then protects nothing. So
# it can be turned off for one project, deliberately and visibly:
#
#     echo "reason" > .claude/destructive-guard.off
#
# When this hook fires, OFFER THE USER THE CHOICE: keep it (they run the command
# themselves, or approve this exact command), or disable it for this project.
#
# Exit 0 = allow. Exit 2 = block, stderr shown as feedback.
set -uo pipefail

ENTREE=$(cat)
CMD=$(printf '%s' "$ENTREE" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null)
[ -n "$CMD" ] || exit 0

# Where are we? CLAUDE_PROJECT_DIR when set, else the cwd the hook was given.
RACINE=${CLAUDE_PROJECT_DIR:-}
[ -n "$RACINE" ] || RACINE=$(printf '%s' "$ENTREE" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$RACINE" ] || RACINE=$PWD

# THREE WAYS TO TURN IT OFF, narrowest first. See the /guard command.
#   1. one command   : DESTRUCTIVE_GUARD=off <command>
#   2. one project    : .claude/destructive-guard.off   (looked up upwards)
#   3. everywhere     : ~/.claude/destructive-guard.off
case "${DESTRUCTIVE_GUARD:-}" in off|OFF|0|false|no) exit 0 ;; esac
[ -f "$HOME/.claude/destructive-guard.off" ] && exit 0
D=$RACINE
while [ "$D" != "/" ] && [ -n "$D" ]; do
    [ -f "$D/.claude/destructive-guard.off" ] && exit 0
    D=$(dirname "$D")
done

refuser() {
    cat >&2 <<TXT
BLOCKED by destructive-guard: $1
Matched: $2

This command is irreversible. Ask the user to choose, do not decide for them:
  KEEP     — they run it themselves, or approve THIS exact command (not the plan)
  DISABLE  — run /guard off  (this project), /guard off --global, or prefix one
             command with DESTRUCTIVE_GUARD=off

Before any irreversible act: look at the target (mount read-only, list it, size
it, say what is there), never pipe the confirmation, and put the identity guard
immediately before the write — serial plus BYTES from blockdev --getsize64, never
the human-readable size.
TXT
    exit 2
}

# What counts as destructive is decided by guard-classify.py, on what is EXECUTED
# in command position -- not on which words appear. The first version matched
# words anywhere, and refused `wipefs /dev/null` plus every commit message,
# heredoc and grep that merely named these tools.
VERDICT=$(printf '%s' "$CMD" | python3 "$(dirname "$0")/guard-classify.py" 2>/dev/null)
STATUS=$?
if [ "$STATUS" = 2 ]; then
    refuser "${VERDICT%%$'\t'*}" "${VERDICT#*$'\t'}"
elif [ "$STATUS" != 0 ]; then
    # Fail open, but VISIBLY: a guard that silently stops guarding is worse than none.
    echo "destructive-guard: classifier failed (status $STATUS) -- command NOT checked" >&2
    exit 1
fi
exit 0
