---
name: machine-first
description: Do the work on the machine instead of in the context, and turn any repeatable action into an idempotent script. Use before reading a large file, counting or comparing across many files, or when an action may be needed a second time.
---

# Machine first

> **A replayable action is a script, not a transcript.**
>
> **Compute on the machine; bring back the answer, not the data.**

## Before reading a file, ask what question it answers

Then ask a command instead. Measured on real cases:

| Question | On the machine | Loaded instead |
| --- | --- | --- |
| one error in a 1.6 MB log | `tr '\r' '\n' \| grep -i error` → 1 line | ~400 000 tokens |
| token consumption over 21 transcripts | a script → 15 lines | millions |
| which files carry non-English text | a loop → 2 lines | every file |

Read a file when you need to **understand** it. Run a command when you need a
**fact about** it.

⚠️ Beware the middle case: a file small enough to load but asked a question that
a command answers better — *how many*, *which ones*, *does any*, *has it
changed*. Those are command questions whatever the size.

## Scripts, for anything that may happen twice

Setup, a migration, a copy, a check, a repair. The script is the deliverable;
the conversation is not.

- **Idempotent.** Re-run after an interruption, it skips what is done. Proven on
  a 1 TB copy killed mid-file and restarted: it resumed instead of starting over.
- **Non-interactive**, except the destructive step, which stays interactive and
  is handed to the user to run.
- **Carries the check that proves it worked**, and logs the numbers — not
  "success".
- **Re-validates identity immediately before writing**, never only at the top.
- `#!/bin/bash` plus the `sh`/dash re-exec as line two, since it may be launched
  with `sh`:

```sh
#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"
```

## The trap this creates

A command that measures nothing returns a clean-looking answer — worse than
loading the file, because nobody looks again.

**So prove the command can fail**: run it against a witness built to be found.
Twelve recorded cases in `verify-claim`, including three of the same `grep -c`
mistake in one session.
