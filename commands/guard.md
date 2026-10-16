---
description: Turn the destructive-command guard off or on, for one command, one project or everywhere, and show which scope is in force.
---

# /guard — the destructive guard's switch

The guard (`hooks/guard-destructive.sh`) is **on by default** in every project.
This command is how it gets turned off deliberately instead of worked around.

Argument given by the user: `$ARGUMENTS` — expect `status`, `off`, `on`,
optionally with `--global`, and optionally a reason after `off`.

## What to do

**`status`** (also the answer when no argument is given) — report which scope is
in force, checking all three, narrowest first:

```sh
echo "env      : ${DESTRUCTIVE_GUARD:-unset}"
ls -l ~/.claude/destructive-guard.off 2>/dev/null && cat ~/.claude/destructive-guard.off
D=$PWD; while [ "$D" != "/" ]; do
  [ -f "$D/.claude/destructive-guard.off" ] && { echo "project: $D"; cat "$D/.claude/destructive-guard.off"; }
  D=$(dirname "$D"); done
```

Then **prove it** rather than reading the files — run the guard on a command you
know it should block and report the exit code:

```sh
printf '%s' '{"tool_input":{"command":"wipefs -a /dev/sdz"},"cwd":"'"$PWD"'"}' \
  | "$CLAUDE_PLUGIN_ROOT/hooks/guard-destructive.sh" >/dev/null 2>&1
echo "exit=$?   # 2 = guard active, 0 = disabled"
```

**`off [reason]`** — this project only. Ask for a reason if none was given; a
marker without one is a marker nobody dares remove later.

```sh
mkdir -p .claude
echo "<reason> — <date>" > .claude/destructive-guard.off
```

Say that it should be **committed**: it is a recorded decision, not local noise.

**`off --global [reason]`** — everywhere, `~/.claude/destructive-guard.off`.
⚠️ Before writing it, say plainly what is being given up: this removes the guard
from **every** project, including ones created later. Prefer per-project unless
the user means it. Ask for confirmation on this one.

**`on`** — remove the marker for the scope asked (project by default,
`--global` for the user-level one), and report which ones remain.

## For one command only

No marker needed, nothing to clean up afterwards:

```sh
DESTRUCTIVE_GUARD=off sudo wipefs -a /dev/sdX    # the command, inline
```

Prefer this when a project needs the guard off **once**. A permanent marker for a
one-off need is how guards quietly disappear.
