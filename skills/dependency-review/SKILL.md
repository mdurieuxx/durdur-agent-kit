---
name: dependency-review
description: Justify a dependency before adding or upgrading it. Use on any change to a dependency manifest.
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

## Versions and upgrades

**The latest version is preferred.** An upgrade is a change like any other:
tested, and reverted if it goes red. **A pin with no reason written is a decision
nobody can revisit** — and the version then drifts out of support while everyone
assumes someone chose it deliberately.

A pin earns its place when the reason is written next to it. Three that qualify:

- a consumer you do not control cannot read the newer output — **measured here:
  a filesystem created with current tooling enabled features the older kernel
  meant to read it refuses**, so the newest version would have silently produced
  an unusable result;
- a component that must run unattended, where a transitive signature change is a
  failure nobody is watching;
- a reproducibility requirement, stated as such.

⚠️ "It works today" is not one of them. Neither is "upgrading is risky" without
naming what breaks.
