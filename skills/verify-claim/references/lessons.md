# Checks that cannot fail verify nothing

Fourteen recorded cases. Every one returned a plausible answer while measuring
nothing, or measuring something other than what was asked. They are collected
here because the failure shape repeats, and because reading them is cheaper than
re-living them.

The pattern to internalise: **a check that returns "fine" when the check itself
is broken is worse than no check at all** — it converts uncertainty into false
confidence, and nobody looks again.

---

## 1. Writing to a read-only sysfs attribute

```
# in a udev rule
ATTR{ro}="1"
```

`/sys/block/sdX/ro` is `-r--r--r--`. udev cannot write it and **fails without a
word**. Three insertions of foreign disks came up writable while the rule was
believed active.

**Fix:** go through the ioctl.

```
RUN+="/usr/sbin/blockdev --setro $devnode"
```

**Prove it, without plugging anything in:**

```sh
udevadm test /sys/block/sda 2>&1 | grep 'blockdev --setro'   # must appear
udevadm test /sys/block/sdd 2>&1 | grep -c 'blockdev --setro' # whitelisted: 0
lsblk -o NAME,SERIAL,RO                                       # the only real proof
```

## 2. `df` and `findmnt` on a device that is gone

A USB disk was unplugged at 11:12. At 13:43 **and** again at 20:20,
`findmnt /mnt/recup` still listed it and `df -h` still answered
`15T  7.2T used`. Both read the mount table and the **cached** superblock; neither
touches the device. The only copy of 7.2 TB was reported healthy for nine hours
after it left the bus.

**Fix:** interrogate the device.

```sh
lsblk -dno NAME,SERIAL | grep "$SERIAL"
lsusb | grep -i "$VENDOR"
blockdev --getsize64 /dev/disk/by-label/"$LABEL"
ls "$MOUNTPOINT"                     # a real read, not df
dmesg -T | grep -iE 'USB disconnect'
```

## 3. A check whose tool does not exist

`ss`, `lsof` and `synopkg` are **absent from Synology DSM**. Checks built on them
returned empty, which reads exactly like "nothing is listening" — and was used to
conclude a service was not running.

**Fix:** prove the tool before trusting its silence.

```sh
for t in ss lsof netstat; do printf '%-8s %s\n' "$t" "$(command -v $t || echo ABSENT)"; done
```

Then cross-check from **outside** the host, where your own tooling is known good.

## 4. `grep` on a progress log

`rsync --info=progress2` writes everything on **one line** separated by carriage
returns. A 1.6 MB log is one `grep` line. Searching for `rsync error` found a
match inside the progress blob and reported a failure that did not exist; later,
a real error would have been just as invisible.

**Fix:**

```sh
tr '\r' '\n' < log | grep -iE 'rsync error|cannot |No such file|I/O error'
```

The same log became **76 039 lines** once split.

## 5. Human-readable sizes have leading whitespace

```sh
sz=$(lsblk -dno SIZE /dev/sdg)   # " 1,8T"  — note the space
case "$sz" in 1,8T) ;; *) exit 1 ;; esac   # never matches
```

This broke two separate guards. Depending on which way the test was written, it
let everything through or blocked everything.

**Fix:** compare bytes, and strip whitespace from anything `lsblk` returns.

```sh
OCTETS=$(blockdev --getsize64 "$CIBLE")
SERIE=$(lsblk -dno SERIAL "$CIBLE" | tr -d '[:space:]')
[ "$OCTETS" = "2000398934016" ] || exit 1
```

## 6. Bash parameter substitution in a non-bash shell

```sh
r="${f/\/divx_synokrust//volume1/DivX}"   # empty under DSM's shell
test -f "$r" || echo ABSENT
```

Every one of 1295 files was reported absent. **The data was fine; the check was
not.** Use `sed` in anything that may run on a remote or minimal shell:

```sh
r=$(echo "$f" | sed 's#^/old/prefix#/new/prefix#')
```

## 7. A guard that checked the table, not the column

A database backup guard verified `CREATE TABLE public.participant_accounts` was
present. It passed every night — and on the night it mattered it passed a dump
whose 533 accounts had **`password_hash` empty on every row**.

⚠️ **And the first reading of that was wrong too.** The conclusion drawn was
"533 accounts with no credential", which would have been a disaster. The
credentials had simply **moved column**: a schema change had added `code_key` and
`code_sealed`, and all 533 rows carried both. Nothing was lost.

So there were two failures stacked. The guard could not tell a credential-bearing
dump from a credential-less one — a real defect. And the human reading of its
silence invented a loss that had not happened — the worse of the two, because it
nearly triggered a restore over good data.

**Fix:** count what matters, and resolve column positions from the header so a
schema change cannot silently invalidate the guard.

```sh
awk -F'\t' '
  /^COPY public\.accounts \(/ {
     h=$0; sub(/.*\(/,"",h); sub(/\).*/,"",h); n=split(h,c,/, */)
     for (i=1;i<=n;i++) { if (c[i]=="password_hash") ph=i; if (c[i]=="code_sealed") cs=i }
     inside=1; next }
  inside && /^\\\.$/ { inside=0 }
  inside { rows++; if ((ph && $ph!="\\N") || (cs && $cs!="\\N")) creds++ }
  END { printf "%d rows, %d with a credential\n", rows, creds }'
```

And **prove it** by blanking those columns in a real dump: the guard must fire.

## 8. An empty variable that became a valid-looking zero

A read-throughput test sampled five positions of a disk and printed five
plausible, consistent figures. But `blockdev --getsize64` had failed with
*Permission denied*, leaving the size variable **empty** — so every computed
offset was `0`, and all five samples re-read the same start of the disk.

**The regularity was the tell.** Results that are too consistent deserve
suspicion.

**Fix:** assert non-empty before computing.

```sh
S=$(blockdev --getsize64 "$D") || exit 1
[ -n "$S" ] && [ "$S" -gt 0 ] || { echo "size unreadable"; exit 1; }
```

## 9. `pgrep` matching its own invocation

```sh
pgrep -af 'btrfs rescue' >/dev/null && echo ALIVE || echo DEAD
```

The shell running the check contains the string `btrfs rescue` in its own command
line, so `pgrep` matched **itself**. A scan that had died hours earlier was
reported alive, and its progress was narrated from a stale log.

**Fix:** exclude the checker, and confirm by PID.

```sh
ps -eo pid,etimes,args | grep -E 'btrfs (rescue|check)' | grep -vE 'grep|zsh|eval'
ps -p "$PID" >/dev/null || echo "process $PID is gone"
```

Also check the log's **mtime**: a file that stopped growing is the cheapest
liveness signal there is.

## 10. `systemctl is-active` on a oneshot unit

A unit with `Type=oneshot` and `RemainAfterExit=yes` reports **`active`
indefinitely**, including long after the process it launched has died. systemd is
not watching anything.

**Fix:** judge by the thing itself.

```sh
tmux ls | grep -E '^session:'            # does it exist
tmux capture-pane -p -t session | tail   # is it alive inside
```

---

## The common fix

Before trusting any check, ask the three questions:

1. **Could this command have failed and still produced this output?**
2. **Is it measuring the thing, or a cache of the thing?**
3. **Have I ever seen it fail?**

If the answer to the third is no, break something on purpose and watch.

---

## 11. A pattern that required two tokens to be adjacent

Found while writing `guard-destructive.sh` for this very template — on the
guard's first test run.

```sh
for m in wipefs mkfs "dd of=/dev/"; do
  case "$CMD" in *"$m"*) refuser ;; esac
done
```

It blocked `wipefs` and `mkfs`. It **let through**:

```
dd if=/dev/zero of=/dev/sdz bs=1M
```

because `if=/dev/zero ` sits between `dd` and `of=`, so the literal substring
`dd of=/dev/` never appears. Command operands come in **any order**; a pattern
that assumes adjacency is a pattern with a hole.

**Fix:** match the parts independently.

```sh
case "$CMD" in *"dd "*)
  case "$CMD" in *"of=/dev/"*) refuser "dd writing to a block device" ;; esac ;;
esac
```

And keep the legitimate case working — `dd if=/dev/sda of=image.img` reads a disk
into a file and must pass. A guard that blocks the safe form gets disabled, and
then it protects nothing.

**The general shape:** when guarding a command line, enumerate what an attacker
*or a tired operator* could reorder, abbreviate or space differently — then test
each form. This hole existed for four minutes because the guard was tested
immediately. Untested, it would have read as protection for months.

---

## 12. `grep -c` with a fallback that adds a second number

Made **three times in a single session**, which is why it gets its own entry
rather than hiding inside case 8.

```sh
n=$(grep -c PATTERN "$f" 2>/dev/null || echo 0)
[ "$n" -gt 2 ] && echo "found"
```

`grep -c` **already prints `0`** when it matches nothing — and exits `1`. So the
`|| echo 0` appends a second zero, `$n` becomes `0\n0`, and every comparison
dies with *integer expression expected*. Under `set -e` the script stops; without
it, the test is skipped and **the loop reports a clean result having evaluated
nothing**.

The first time, it declared two repositories free of French without checking a
single file. The second, it printed a coupling table whose verdict column was
wrong throughout.

**Fix:** `grep -c` needs no fallback at all, only permission to exit non-zero.

```sh
n=$(grep -c PATTERN "$f" 2>/dev/null) || true
n=${n:-0}
```

And the same trap wears other clothes: `echo -` prints an empty line in zsh, not
a dash — which silently emptied a variable in the same table and sent whole rows
down the wrong branch.

**The habit that catches all of them:** before trusting a scan that reports
"nothing found", run it against a **witness** you built to be found. If the
witness is not detected, the scan proves nothing.

---

## 13. A guard tested only on synthetic input

The destructive-command guard passed a 74-case test written by its author. Run
as an installed plugin in a real session, it refused `wipefs /dev/null`, a
read-only listing.

It matched **words anywhere in the command line**. Replayed over one session's
300 real commands, it would have blocked **26** — of which about four were
genuinely destructive. The other twenty-odd were commit messages, heredocs and
greps that merely *named* the tools while documenting them: most of what writing
this very kit involved. A guard that obstructs normal work gets switched off
wholesale, and then protects nothing.

The same replay exposed three holes in the other direction: `git push -f` with
nothing after it passed (the pattern wanted a trailing space), `mkswap` was not
covered, and `printf CONFIRM |` slipped past a rule written for `echo`.

**Fix:** decide on what is *executed*, in command position, and let the read-only
forms through — a parser, not a substring match.

**The habit that catches it:** before trusting a guard, **replay your own real
history through it**. Synthetic cases are written by the person who already
knows what the guard does, so they confirm the design; real commands contradict
it. Keep both lists, blocked and allowed — a guard tested only on what it must
block drifts toward blocking everything.

And when a case fails, decide **which side is wrong** before touching either.
One of the failures here was the *test* (`yes | head`, listed as allowed on a
guess); rewriting the code to satisfy it would have been the mistake.

---

## 14. A rule that depends on being remembered

The rule "nothing published credits the tool that wrote it" lived in a memory
file and in the instructions of one project. The harness's default instruction
says the opposite, and wins in every session that does not load the rule.

Nobody noticed, because each commit looked fine. Counting did: over 14
repositories, **108 of 867 commits carried the trailer** — 62 of 69 in one
project, 46 of 64 in another, none in the rest. Two projects, driven by sessions
that simply followed their defaults, and no failure anywhere to point at.

**Fix, in two layers.** Inject the rule at session start, so the model does not
attempt it. Enforce it where the text leaves, so a commit carrying it is refused
before it exists. Verified live in a project with no commit hooks installed: the
first session added the trailer; with the plugin, a session asked to commit as
usual produced a clean message and quoted the rule back; one *ordered* to add it
was blocked and created no commit.

```sh
git log --format=%B | grep -ciE 'co-authored-by:.*(claude|anthropic|copilot)'
```

**The habit:** for any rule the harness's defaults contradict, **count the leak in
history before assuming the rule holds**. A rule stated in one place protects
only the sessions that read that place.
