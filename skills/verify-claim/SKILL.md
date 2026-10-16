---
name: verify-claim
description: Re-measure a claim before stating it, when being wrong would change what the user does. Use before announcing a backup, copy, deployment or recovery succeeded, before saying a service is running or a disk is present, and whenever a check returned a reassuring answer you have never seen fail.
---

# Verify before claiming

Being wrong here is expensive in a specific way: it does not look like an error,
it looks like good news. Twelve recorded cases are in `references/lessons.md` -- read it when a check
looks suspicious. Every one returned a plausible number while measuring nothing.

## The three questions

Ask them of the check itself, before trusting its output.

1. **Could this command have failed and still produced this output?**
   A missing tool, a permission error, an empty variable — all return something
   that reads like a negative result.
2. **Is it measuring the thing, or a cache of the thing?**
   `df` and `findmnt` answered for a disk that had left the bus nine hours
   earlier. Query the device, not the bookkeeping.
3. **Have I ever seen this check fail?**
   If not, break the thing on purpose and watch. A guard never seen to fire is a
   decoration.

## Mechanical habits that remove whole classes of error

```sh
# assert non-empty before computing — an empty var becomes a convincing 0
S=$(blockdev --getsize64 "$D") || exit 1
[ -n "$S" ] && [ "$S" -gt 0 ] || { echo "unreadable"; exit 1; }

# strip whitespace from human-readable output, and prefer bytes
SERIE=$(lsblk -dno SERIAL "$D" | tr -d '[:space:]')

# never let a matcher match itself
ps -eo pid,etimes,args | grep -E 'mypattern' | grep -vE 'grep|zsh|eval'

# split carriage-return progress logs before searching them
tr '\r' '\n' < log | grep -iE 'error|cannot|No such file'

# prove the tool exists before trusting its silence
command -v ss >/dev/null || echo "ss ABSENT — this check proves nothing"
```

## Signals that something is wrong even when output looks right

- **Results too regular.** Five throughput samples within 1 % of each other meant
  all five read the same sector, not that the disk was consistent.
- **A guard that has always passed.** Especially a nightly one.
- **A number that did not move when the underlying thing changed.**
- **A unit reported `active` by systemd** when its type is `oneshot` with
  `RemainAfterExit` — systemd is watching nothing.

## When the claim is already out

Correct it in one sentence, plainly, and continue. Do not defend it, do not
re-litigate how it happened, do not tally. If it changes nothing for the user,
just fix it silently and move on.
