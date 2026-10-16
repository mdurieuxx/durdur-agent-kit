# AGENTS.md fragments

Always-on rules cannot ship in a plugin (`rules`: 0 of the 315 official
plugins), so they live here as sections to **copy** into a project's own
`AGENTS.md`.

## What belongs in AGENTS.md — three questions, not a line count

A line limit is the wrong constraint. Measured: a 196-line `AGENTS.md` costs
~2 242 tokens a turn against ~378 000 tokens of context re-read per message —
**0.6 %**. Cost is not the argument, and "lines" is not the unit: a table does
not weigh what prose weighs.

A cap also creates a bad reflex. On hitting it you cut the **newest** rule rather
than the weakest, or compress until the *why* disappears — and a rule without its
why gets argued away.

**A rule belongs here only if it can be neither a hook nor a skill.** Ask, per
rule:

| | If yes |
| --- | --- |
| Could a hook catch it? | make it a hook — 0 tokens, and mechanical enforcement is not read, it is obeyed |
| Is it a procedure? | make it a skill — paid only when invoked |
| Is it always-on judgment? | then it belongs here |

Measured on one real `AGENTS.md`: **7 of its 15 sections already named the hook
that enforces them.** Those can shrink to one line of reference — a hook does not
argue. The remaining 8 were judgment and earned their place.

⚠️ So the thing to prune is not length, it is **duplication with a mechanism**.
The first version of this very file ran to 141 lines for four rules because it
had pasted the skills' tables in. Each section here is the obligation, one line
of why, and the skill that holds the procedure. **Nothing else.**

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

---

## Secrets

> **A secret value is never versioned. The reference is versioned; the value is
> not.**
>
> **Verified at startup, masked on display.**

A missing secret broke a deployment three times in one session; a database
password is versioned in clear to this day. ⚠️ `.gitignore` does **not** act on
an already-tracked file — a value committed once must be **revoked**.

Enforced by `no-literal-secret`.

## Authorisation

> **Fail-closed, and ownership lives in the model — not in a review habit.**

A **critical IDOR across 14 routers**, every one trusting an identifier read
from the request. The mechanism is structural, not a review habit: ownership in
the model, one central guard, a default that denies.

Procedure, and the false comforts to avoid: `threat-check`.

## The input boundary

> **Never interpolate a parsed value into a query, a template, a shell command
> or a path.**

Third-party input is the highest-value target and the least watched component.
Parameterise, or reject. **Bound everything from outside** — size, count, depth,
rate.

---

## Modular

> **A module you cannot delete without editing five others is not a module.**
>
> **A dependency on something you did not create is declared and verified at
> startup, never assumed.**

Deletability and isolated testability are the two tests that cannot be argued
with. And the dangerous coupling is the one nothing reports: a backup pointed at
a service by name kept succeeding after the service moved, having saved nothing.

Procedure, with six questions and the measurement that settles an argument:
`modular-design`.

## Readable over clever

> **Ten descriptive lines beat one line nobody can read.**
>
> **Code says what it does; a comment says why it exists.**

Terseness correct only under a condition invisible at the call site is the
expensive kind: `grep -c X f || echo 0` returns `0\n0` and broke every later
comparison, three times in one session. A comment restating the code is noise;
one carrying the incident is usually the most valuable line in the file.

Procedure, with five such lines and what each cost: `readable-code`.

---

## Dependency versions

> **The latest version of a library is preferred. A pin needs a written reason.**

An unexplained pin is a decision nobody can revisit, and the version drifts out
of support while everyone assumes someone chose it.

⚠️ **The boundary: latest on your side can break a consumer you do not control.**
Measured here — a filesystem created with the newest tooling enabled features
that the **older kernel meant to read it refuses**. Newest is the default, not
the goal: check what has to consume the output.

Procedure: `dependency-review`.

## Performance

> **Quality first, performance immediately after, everything else behind both.**

Never the reverse: a fast answer that is wrong, or unreadable, costs more than
it saves. But "we will optimise later" is how later never comes.

⚠️ **Measure before optimising, and expect the measurement to point elsewhere.**
Measured here: a kit's always-loaded text was ~600 tokens a turn while the same
project re-read ~378 000 tokens of context per message. Compressing the first
was visible work and almost no gain; the cost was architectural.

So: profile, fix the layer the numbers name, and re-measure. An optimisation
without a before-and-after number is a guess with extra steps.
