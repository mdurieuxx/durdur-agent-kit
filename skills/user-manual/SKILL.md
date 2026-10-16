---
name: user-manual
description: Maintains the user manual, English as the source of truth for translations. Use in the same turn as any user-visible change: screen, field, button, command, configuration prerequisite.
---

# User manual

The manual describes the product **from the point of view of the person using
it** — screens, available actions, what each control does. Never implementation:
the README stays aimed at developers and integrators.

If it does not exist yet, this skill **creates it** rather than assuming it is
there.

## Language

**Written in English**, always. It is the base locale and the language of every
versioned artifact.

Other languages are **derived** from the English version:

| File | `provenance` | Editing |
|---|---|---|
| `user-manual.md` | `human` | by hand, source of truth |
| `user-manual.<locale>.md` | `derived` | regenerated — **never hand-edited** |

Regenerate what is derived, never touch it by hand. A correction is made in
English, then propagated.

## When

In the **same turn** as any change that, from the screen's point of view, adds,
alters or removes:

- a screen, a route, a tab;
- a field, a button, a visual state;
- a command-line command;
- **an external configuration prerequisite** found to be necessary — the most
  frequently missed one.

Not at the end of the batch, not before a release: **a manual updated later
describes a product that no longer exists.**

**Does not apply** to purely internal changes: refactors with no visible impact,
extraction, test fixes.

## How to write it

- Name things the way the user recognises them, not the way the system
  implements them.
- Active voice; a control says exactly what it does.
- One section per screen, ordered by the real user journey — not by the order
  things appear in the code.
- Error messages explain what to do next.
- **Say what the product does not decide.** A manual that oversells gets the
  maintainer blamed for a judgment the tool never claimed to make.

## Checked, not hoped for

- **A gate**: a change with visible impact cannot reach "done" while the manual
  is stale.
- **A parity check**: every route has a matching section. Coverage only, not
  fidelity — but coverage is what is usually missing.
- **Rotation**: past a size threshold, split by domain rather than let one file
  grow without end.
