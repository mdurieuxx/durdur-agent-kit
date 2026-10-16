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
