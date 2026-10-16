---
name: readme
description: Maintains README.md, the developer entry point. Use it at every batch or sprint closure, before a release, and whenever setup, architecture or contribution rules change.
---

# README

`README.md` answers one question: **how do I run this and contribute to it?**
Setup, architecture overview, conventions, how to run the tests.

It is not the user manual and it is not an architecture decision record.

## Five surfaces, one question each

Getting this boundary wrong is what makes documentation rot.

| Surface | Audience | Question |
|---|---|---|
| `README.md` | developer, integrator | how do I run and contribute to this? |
| `docs/guide/user-manual.md` | user | what does each screen do? |
| `docs/decisions/` | future maintainer | why is it like this? |
| `AGENTS.md` | agent | what must I always do? |
| `docs/knowledge/` | agent and maintainer | what must I know about this module or trap? |

A fact lives in **exactly one** surface. Repeating it across two is not a
reminder, it is a future contradiction.

## What earns a place in it

Not a feature tour. The operations someone cannot discover alone:

- the command that **must never fail**, and how to run it in isolation;
- how to reproduce a run from recorded input, if the project has any — that is
  usually how most of it is tested;
- the one command that installs the hooks. **A convention that lives on one
  machine is not a convention.**
