---
name: threat-check
description: Name the asset, the abuse, and the test that proves it impossible. Use on any change touching accounts, entitlements, credentials or external input.
---

# Threat check

Short on purpose. A long security procedure gets skipped; this one fits in a
pull request description.

## Four questions, answered in the PR

1. **Which asset does this touch?** Credentials and sessions, the data feed,
   entitlements, an admin account. If the answer is "none", say so and stop —
   that is a valid outcome.
2. **What is the abuse?** Concrete: *a member reads another customer's data*,
   not *insufficient security*.
3. **What makes it structurally impossible?** Ownership in the model, a central
   guard, a bound, a parameterised query. **Not vigilance.**
4. **Which test proves it?** A test that fails if the guard is removed. **If
   removing the guard keeps the suite green, the guard is not tested.**

## Classes already paid for

| Class | What it cost | The mechanism |
|---|---|---|
| Missing authorisation | a **critical IDOR across 14 routers** | ownership in the model, central guard, fail-closed |
| Secret missing at deploy | three times in one session | versioned reference + startup verification |
| Secret versioned in clear | found still true in an infrastructure repository | a hook that refuses a literal |
| Green-by-accident test | see `tdd` | reading the real environment in a test is forbidden |

## Two false comforts

- **A presentation field is not a mechanism.** A hidden button is not an
  authorisation.
- **A green is only worth what it proves** (`tdd`). Health is verified by a
  probe that queries real state, never by the absence of an error — and for a
  data feed, on **content**, never on connectivity.

## What is deliberately out of scope

Write down what the current version does **not** do — multi-factor, email
recovery, full audit log, fine-grained rate limiting — as **dated choices**, in
a decision record. An absence that is written down is a decision; an absence
that is not is a discovery waiting to happen.

⚠️ The one exception worth shipping early: **login attempt throttling**. Without
it, "password only" plus "closed registration" still leaves guessing open, which
cancels both decisions.
