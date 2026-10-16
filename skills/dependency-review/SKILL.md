---
name: dependency-review
description: Justify a dependency before adding or upgrading it. Use it on every change to a dependency manifest.
---

# Dependency review

Every dependency is code executed on the maintainer's own machine.

## Four lines in the PR, no more

1. **What it replaces** — the hand-written alternative, and its size. *"About 40
   lines of standard library"* is a legitimate reason to refuse.
2. **What it pulls in** — the transitive count, not just the direct name.
3. **Whether it touches an asset** — the input boundary, credentials, the
   database. A dependency on the input boundary deserves a different level of
   care than a formatting helper.
4. **How it is removed** — if the answer is "it cannot be", say so now.

## State the bias per layer, not per project

A single policy across a whole repository is usually wrong. Name the layers:

- A component that must **run unattended for hours** earns a
  zero-dependency bias: a recorder that stops because a transitive upgrade
  changed a signature loses an event that will never happen again.
- A user interface layer earns the opposite bias, where reinventing is the
  greater risk.

Write which layer is which, once, where the manifest lives.

## Upgrades

An upgrade is a change like any other: tested, and reverted if it goes red.
**A pinned version with no reason written is a decision nobody can revisit.**
