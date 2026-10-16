---
name: readable-code
description: Write clean, readable, maintainable code: naming, function size, comments that carry the why, and the terse idioms that silently break. Use while writing or reviewing code, and whenever a line needs a second read.
---

# Readable code

> **Ten descriptive lines beat one line nobody can read.**
>
> **Code says what it does; a comment says why it exists.**

## Terseness that hides a precondition is the expensive kind

Not style — these each cost real time:

| The clever line | What it actually did |
| --- | --- |
| `n=$(grep -c X f \|\| echo 0)` | `grep -c` **already prints 0** then exits 1, so `n` became `0\n0` and every comparison after it died or was skipped. **Three times in one session** — `verify-claim` case 12. |
| `r="${f/old/new}"` | empty string under a non-bash shell — then every file reported missing. The data was fine; the line was not. |
| `case "$sz" in 1,8T)` | never matched: the formatted size carried a leading space. Two guards disabled by it. |
| `*"dd of=/dev/"*` | missed `dd if=/dev/zero of=/dev/sdz`, because operands come in any order. |
| `awk '{print $(NF-4)}'` | broke the moment the line gained a parenthesis. |

**The shape:** a short form that is correct only under a condition you cannot see
at the call site. Write the long form, or make the condition explicit.

```sh
# clever, and wrong
n=$(grep -c X "$f" || echo 0)

# longer, and says what it assumes
n=$(grep -c X "$f") || true     # grep exits 1 when it matches nothing
n=${n:-0}
```

## Modular — while writing

Boundaries are `modular-design`'s subject. Two habits belong here, at the
keyboard:

- **A function needing "and" in its name is two functions.** The name is the
  test, not a line count.
- **Nothing reads the clock or the real environment** outside one boundary named
  as such. Already paid for: a test green on a variable present in the deployed
  process and absent from the runner.

## Robust

- **Fail loudly, never silently default.** `|| true` and `?? 0` turn an error
  into a plausible number, which is worse than a crash because nobody looks
  again.
- **Assert the precondition instead of assuming it.** An empty variable in
  arithmetic becomes `0` and `0` looks like an answer.
- **Bound anything from outside** — size, count, depth, rate.
- **One way to express a state**, not two that can disagree. Two sources of the
  same truth will diverge; it is only a question of when.

## Comments

**Self-documenting first**: a name that says it needs no comment. But
self-documenting code cannot express *why*, and why is what a maintainer lacks.

| Write | Skip |
| --- | --- |
| the incident that produced the line | what the line does |
| why the obvious approach was rejected | a restatement of the name |
| the precondition a reader cannot see | a changelog — git has that |
| what must change together elsewhere | a decorative banner |

The comment headers on this kit's own hooks are the model: each names the failure
that caused it to exist. Those are the lines a later reader needs first — and
the reason **a hook or a script is never compressed to save tokens**: they never
enter the context, so the incident costs nothing to keep.
