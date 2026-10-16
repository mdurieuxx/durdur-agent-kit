#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# PreToolUse hook on Bash. Blocks irreversible commands so the decision has to be
# taken explicitly instead of slipping through.
#
# WHY THIS EXISTS. A disk was wiped on this setup while the user was interrupting
# the command: the confirmation had been piped in, removing the only window the
# interrupt could land in. wipefs and sfdisk finish in under a second. Good
# intentions are not a guard; this is.
#
# Exit 0 = allow. Exit 2 = block, and stderr is shown as feedback.
set -uo pipefail

CMD=$(cat | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null)
[ -n "$CMD" ] || exit 0

refuser() {
    printf 'BLOCKED by guard-destructive: %s\n\n' "$1" >&2
    printf 'Matched: %s\n\n' "$2" >&2
    cat >&2 <<'TXT'
This command is irreversible. Per CLAUDE.md §2:
  - look at the target first: mount read-only, list it, size it, say what is there
  - get explicit agreement ON THIS COMMAND, not on the plan
  - or better: hand the user the exact line to run themselves
  - never pipe the confirmation (no `yes |`, no `echo CONFIRM |`, no added --force)
A guard on identity goes immediately before the write, and compares BYTES
(blockdev --getsize64) plus the serial, never the human-readable size.
TXT
    exit 2
}

# Auto-fed confirmations: the exact mistake that cost a disk.
case "$CMD" in
  *"yes |"*|*"yes|"*)                 refuser "a confirmation is being piped in" "yes |" ;;
  *echo*CONFIRM*\|*|*echo*EFFACER*\|*|*echo*DELETE*\|*)
                                      refuser "a confirmation is being piped in" "echo ... |" ;;
esac

# Irreversible writes to block devices and partition tables.
for m in wipefs mkfs sgdisk sfdisk "parted " blkdiscard "shred "; do
  case "$CMD" in *"$m"*) refuser "irreversible write to a block device" "$m" ;; esac
done

# dd and tee onto a device. The operands can come in ANY ORDER, so matching the
# literal "dd of=/dev/" misses "dd if=/dev/zero of=/dev/sdz" — which is exactly
# how this guard let a disk-destroying command through on its first test.
# Match the two parts independently.
case "$CMD" in
  *"dd "*|*"dd"$'\t'*)
      case "$CMD" in *"of=/dev/"*) refuser "dd writing to a block device" "dd ... of=/dev/" ;; esac ;;
esac
case "$CMD" in
  *"tee /dev/sd"*|*"tee /dev/nvme"*|*"tee /dev/vd"*|*"> /dev/sd"*|*"> /dev/nvme"*)
      refuser "writing straight onto a block device" "> /dev/..." ;;
esac

# Destructive git and container operations.
case "$CMD" in
  *"push --force"*|*"push -f "*)      refuser "force-push rewrites published history" "push --force" ;;
  *"git clean -"*[fdx]*)              refuser "git clean removes untracked work" "git clean" ;;
  *"docker system prune"*|*"docker volume prune"*|*"docker volume rm"*)
      refuser "several agents share this Docker; an orphan volume may be a stopped stack's data" "docker prune/rm" ;;
esac

# rm -rf on an absolute path outside the obvious scratch areas.
case "$CMD" in
  *"rm -rf /"*|*"rm -fr /"*|*"rm -r -f /"*)
      case "$CMD" in
        *"rm -rf /tmp/"*|*"rm -rf /var/tmp/"*) : ;;
        *) refuser "recursive delete on an absolute path" "rm -rf /" ;;
      esac ;;
esac

exit 0
