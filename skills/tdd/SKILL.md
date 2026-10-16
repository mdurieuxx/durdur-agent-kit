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

## Integration tests

Unit tests prove a function; they cannot prove that two components agree.

**Every path that crosses a boundary has an integration test** — a process
boundary, a network call, a queue, a database, a third-party API. That is where
the failures live, and where unit tests are structurally blind.

Two shapes paid for already:

- four applications answered `200` on their health endpoints while every
  registration returned 500 — a component between two of them was not running;
- a guard was verified by checking that a table existed, on a dump where the
  column that mattered was empty on every row.

So an integration test **writes and reads back**, crosses every boundary the
real request crosses, and asserts on **a value** — never on a status code, never
on the mere existence of something.

## When code changes, its tests change with it

**A test rewritten to match the code is no longer a test.** Updating an
assertion until it passes turns a specification into a transcript of the
implementation: it will then agree with any future behaviour, including the wrong
one.

When a change makes a test fail, decide **which one is wrong**:

| The test was | Then |
| --- | --- |
| right | the code is wrong — fix the code |
| describing behaviour that deliberately changed | rewrite it, and say in the commit that the contract changed |
| asserting nothing useful | delete it, and say what replaces it |

⛔ **Never skip, comment out or loosen a test to land a change.** A skipped test
is one that will never be re-enabled, and its guard is gone while its name still
suggests coverage.

And the check that catches the rest: **remove the guard and the suite must go
red.** If it stays green, the test was already a transcript.

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
