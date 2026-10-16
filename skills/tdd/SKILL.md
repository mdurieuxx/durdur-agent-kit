---
name: tdd
description: Write production code test-first: how to get a real red, what does not count, and the traps already paid for. Use when a change adds or alters production code.
---

# TDD

Red → green → refactor. No production code without a failing test written first.

## Getting a real red

1. Write the test describing the expected behaviour.
2. **Run it and read the failure.** A test failing for the wrong reason —
   missing import, typo — is not a red, it is a broken test.
3. The failure message must describe the missing behaviour, not a crash.

## What does not count as red

- A test that passes on the first run: it tests nothing new.
- A test never executed before the implementation.
- **A test green by accident.** Trap already paid for: a strict equality on an
  environment variable absent from the CI runner but present in the deployed
  process. **Reading the real environment in a test is forbidden** — neutralise
  explicitly whatever the test depends on.
- **A test green because the clock cooperated.** Inject the clock, never read
  it. Any code involving durations will otherwise pass on a fast machine and
  fail on a slow one, or the reverse.

## Traps specific to this repository

<!-- Each project fills this in. The entries that belong here are the ones
     nobody can reconstruct: a red that was only a stale build, a flakiness
     that was chased and abandoned, a fixture that lies.
     An empty section is an honest section; a generic one is noise. -->

_None recorded yet._

## What a green is worth

A green is only worth what it proves. A guard is tested only if **removing it
turns the suite red** — if the suite stays green without the guard, the guard is
not covered, whatever the coverage report says.
