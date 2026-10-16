# AGENTS.md fragments

Always-on rules cannot ship in a plugin (`rules`: 0 of the 315 official
plugins), so they live here as sections to **copy** into a project's own
`AGENTS.md`.

⚠️ Keep `AGENTS.md` **under 200 lines, pruned like code**. A bloated instruction
file gets ignored wholesale, and then none of its rules apply. These four
sections are ~40 lines on purpose: the obligation, one line of why, and the
skill that holds the procedure. **Do not paste a skill's tables in here** — that
is what made the first version of this file 141 lines, 70 % of the budget, for
the same four rules.

---

## Spec first

> **No implementation without a spec written and committed first.**
>
> **No backlog item picked up until it states what it changes and how "done"
> will be judged.**

Code written before its spec defines its own success criteria: always correct,
never checkable. An item that only says what to do is not documented, it is
assigned.

Commits naming their spec: `Spec: <path>`. Enforced by `spec-before-code`;
traced exception `SPEC-EXEMPT: <reason>`.

## Tests

> **Every path that crosses a boundary has an integration test.**
>
> **When code changes, its tests change with it — a test rewritten to match the
> code is no longer a test.**
>
> **After a deploy, integration tests run against the deployed instance — never
> the local one.**

Unit tests cannot prove two components agree. An assertion adjusted until it
passes becomes a transcript of the implementation, and will then agree with any
future behaviour. A green suite on a developer machine says nothing about what
is running.

⛔ Never skip, comment out or loosen a test to land a change.

Procedures: `tdd`, `post-deploy-check`.

## Work on the machine, not in the context

> **A replayable action is a script, not a transcript.**
>
> **Compute on the machine; bring back the answer, not the data.**

A transcript cannot be re-run, and data loaded into the context is paid for on
every turn after. Ask a command for a fact about a file; read the file only to
understand it.

Procedure: `machine-first`.

## Verify before claiming

> **A check that cannot fail verifies nothing.**

Prove a check can fail — run it against a witness built to be found — before
trusting a reassuring answer.

Procedure and twelve recorded cases: `verify-claim`.
