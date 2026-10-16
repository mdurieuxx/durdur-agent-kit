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

# Auto-fed confirmations: the exact mistake that cost a disk.
case "$CMD" in
  *"yes |"*|*"yes|"*)  refuser "a confirmation is being piped in" "yes |" ;;
  *echo*CONFIRM*\|*|*echo*EFFACER*\|*|*echo*DELETE*\|*)
                       refuser "a confirmation is being piped in" "echo ... |" ;;
esac

# Irreversible writes to block devices and partition tables.
for m in wipefs mkfs sgdisk sfdisk "parted " blkdiscard "shred "; do
  case "$CMD" in *"$m"*) refuser "irreversible write to a block device" "$m" ;; esac
done

# dd and tee onto a device. Operands come in ANY ORDER, so matching the literal
# "dd of=/dev/" misses "dd if=/dev/zero of=/dev/sdz" -- which is exactly how this
# guard let a disk-destroying command through on its first test (lesson 11).
case "$CMD" in *"dd "*)
  case "$CMD" in *"of=/dev/"*) refuser "dd writing to a block device" "dd ... of=/dev/" ;; esac ;;
esac
case "$CMD" in
  *"tee /dev/sd"*|*"tee /dev/nvme"*|*"tee /dev/vd"*|*"> /dev/sd"*|*"> /dev/nvme"*)
      refuser "writing straight onto a block device" "> /dev/..." ;;
esac

# Destructive git and container operations.
case "$CMD" in
  *"push --force"*|*"push -f "*)  refuser "force-push rewrites published history" "push --force" ;;
  *"git clean -"*[fdx]*)          refuser "git clean removes untracked work" "git clean" ;;
  *"docker system prune"*|*"docker volume prune"*|*"docker volume rm"*)
      refuser "several agents may share this Docker; an orphan volume can be a stopped stack's data" "docker prune/rm" ;;
esac

# rm -rf on an absolute path, outside the obvious scratch areas.
case "$CMD" in
  *"rm -rf /"*|*"rm -fr /"*|*"rm -r -f /"*)
      case "$CMD" in
        *"rm -rf /tmp/"*|*"rm -rf /var/tmp/"*) : ;;
        *) refuser "recursive delete on an absolute path" "rm -rf /" ;;
      esac ;;
esac

exit 0
