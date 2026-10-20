---
name: modular-design
description: Decide where a module boundary goes and check it holds. Use when adding a module, when a file grows, or when a one-line change touches several files.
---

# Modular design

Not the named principles — the **observable consequences**, each one checkable
on the code in front of you.

## Six questions that decide a boundary

1. **Can you delete it?** A module you cannot remove without editing five others
   is not a module, it is a region of one big thing. Deletability is the sharpest
   test there is, and the cheapest to apply: try it on paper.

2. **Does it change for one reason?** Operational version: if two unrelated
   reasons make you edit the same file, it is two files. *"Needs `and` in its
   name"* is the same test on the name.

3. **Can it be tested without the rest?** A unit needing a database, a clock and
   a network to be exercised is coupled to all three — whatever the diagram says.
   This is the test that cannot be argued with.

4. **Which way do dependencies point?** Inner knows nothing of outer. A core
   module importing from the web layer, the CLI or the test helpers is an
   inversion, and it will be discovered the day one of them is replaced.

5. **Is there one way in?** Two entry points to the same capability will
   diverge; it is only a question of when. Measured on two real repositories:
   the **same ten pieces, reimplemented in both, had drifted by 17 to 86 lines.**

6. **Does its name describe a thing?** `utils`, `helpers`, `common`, `manager`,
   `misc` are names for *"I did not decide"*. A module whose name cannot say what
   it owns has no boundary yet.

## The measurement that settles an argument

**Count the files a one-line behaviour change has to touch.** More than two and
the boundary is in the wrong place. Do it before redesigning anything — it
usually names a different seam than the one being debated.

## The coupling that hides

The dangerous kind is not the visible import. It is the **assumption two
components share without saying so**, because nothing fails when it breaks.

Paid for here:

- a backup pointed at a service by name. The service **moved**; the backup kept
  running and kept reporting success, having backed up nothing. **A hidden
  coupling does not announce its own failure.**
- a container's user id written as a literal. The host was rebuilt, the id no
  longer existed, and the process ran as a user who could not write its own
  database.

So: when a module depends on something it did not create — a path, an id, a
port, a name — **the dependency is declared and verified at startup**, not
assumed. And the check says what it found, not "ok".

## What not to do in the name of modularity

- **An abstraction with one implementation** is a layer of indirection, not a
  boundary. Add it at the second implementation, not in anticipation of it.
- **Splitting by technical kind** (`controllers/`, `models/`, `services/`) groups
  things that change for different reasons and separates things that change
  together. Split by what the code is *about*.
- **A module per file** is not modularity, it is file management.
