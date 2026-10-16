# AGENTS.md fragments

Always-on rules **cannot** ship in a plugin — checked against the 315 plugins of
the official marketplace: `rules` 0. They belong in each project's own
`AGENTS.md`, which already loads every turn.

So they live here as **fragments to copy**, not as something the plugin
delivers. Copy the section, keep the wording.

⚠️ Keep `AGENTS.md` **under 200 lines and pruned like code**. A bloated
instruction file gets ignored wholesale, and then none of its rules apply.

---

## Spec first

> **No implementation without a spec written and committed first.**
>
> **No backlog item picked up until it states what it changes and how "done"
> will be judged.**

The two are one rule at its two ends: nothing enters implementation
undocumented, and nothing leaves it unjudgeable.

### What makes an item implementable

Three lines, and an item missing one is sent back rather than guessed at:

1. **What changes**, in the product's own vocabulary — a screen, a field, a
   command. Not a task verb.
2. **How "done" is judged** — the observable that will be checked. If nobody can
   name it, the item is not ready.
3. **What it deliberately does not do** — the boundary. Its absence is what
   turns one item into three during implementation.

⚠️ **An item that only says what to do is not documented, it is assigned.** The
difference shows up the day someone else picks it up, or the same person picks it
up three weeks later.

Not a design document and not a ceremony: the smallest statement of what is
being built and how it will be judged done. One file, committed before the first
line of production code.

A commit that adds production code names its spec:

```
Spec: docs/spec/<name>.md
```

Enforced by `spec-before-code`. Deliberate exception, traced in the message:
`SPEC-EXEMPT: <reason>`.

**Why an obligation rather than a habit.** Code written before its spec defines
its own success criteria, so it is always correct and never checkable. The spec
is what makes "done" falsifiable.

---

## Integration tests after a deploy

> **After a deploy, integration tests run against the deployed instance — never
> the local one.**

A green test suite on a developer machine, or a green CI job on a branch, proves
nothing about what is actually running. Only a transaction executed against the
deployed instance does.

**And a connectivity check is not an integration test.** Paid for twice:

- four applications answered `200` on their health endpoints while **every
  registration returned 500** — a gateway between two of them was not running,
  and nothing that only checked reachability could see it;
- a port was open and a service reported healthy while the component behind it
  had never started.

So the test exercises **one real transaction end to end**, the one whose failure
would matter most, and asserts on **content** — never on a status code alone.

Not done until it has run. A deploy whose integration tests have not run is a
deploy nobody can vouch for.

---

## Work on the machine, not in the context

> **A replayable action is a script, not a transcript.**
>
> **Compute on the machine; bring back the answer, not the data.**

Two halves of one rule, and both save the same thing: a transcript cannot be
re-run, and data loaded into the context is paid for on every turn that follows.

**The first half.** Any action that may be needed twice — setup, a migration, a
copy, a check — goes into an idempotent script, with the command that proves it
worked. A sequence narrated in a conversation is lost the moment the context is
cleared, and it was never verifiable anyway.

**The second half, with the numbers.** Loading a file to answer a question about
it is almost always the expensive way:

| Question | On the machine | If loaded instead |
| --- | --- | --- |
| one error in a 1.6 MB log | `tr '\r' '\n' \| grep -i error` → 1 line | ~400 000 tokens |
| consumption across 21 session transcripts | a script → 15 lines | millions |
| which of 2 repositories contain French | a loop → 2 lines | every file |

So: grep, awk, `find`, `du`, a short script — then read the result. **Never page
a large file into the context to look for something a command can find.**

⚠️ **And the trap this creates.** A command that measures nothing returns a
clean-looking answer, which is worse than loading the file. Prove the command can
fail: run it against a witness built to be found. See `verify-claim`.
