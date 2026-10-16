---
name: checkpoint
description: Write a session checkpoint before clearing context, and decide whether clearing is the right move. Use it when the context window is filling, when the subject changes, or before ending a work session.
---

# Session checkpoint

A checkpoint is a **handover**, not an archive. It answers one question: what
does the next session need in order to pick this up cold?

## The rule that cannot be broken

**Never clear before the checkpoint is committed and pushed.**

A cleared context is unrecoverable. An unpushed checkpoint lives on one machine,
and a fix that was never shipped is a fix that does not exist.

Measured in one repository: **53 of 97 findings files were present on disk,
absent from git, and absent from any off-machine copy.** Nothing had failed — the
gap was invisible precisely because the files were there when looked at.
**Presence on disk is not durability.**

So gate the clear on state, not on intention:

```sh
git status --porcelain                       # must be empty
git rev-list --count @{u}..HEAD 2>/dev/null  # must be 0
```

Refuse to green-light a clear while the tree is dirty, commits are unpushed, or
the checkpoint file is older than the last commit.

## Generated, then narrated

Most of a checkpoint is derivable, so do not type it. Collect by command:
current branch and its upstream, ahead/behind counts, staged and unstaged
summary, the work item in progress, last test result, open pull requests.

You write only what cannot be derived, in three short sections:

1. **Where this stands** — one paragraph, present tense.
2. **Next step** — the single next action, concrete enough to start on.
3. **Traps** — what nearly went wrong, and what a cold reader would get wrong.
   This is the part that pays for itself.

⚠️ If the collecting script does not exist in this project yet, collect by hand
and **do not describe it as automated**.

## The exit rule

The checkpoint file is **replaced, never appended to**. Its history is in git,
which is what git is for.

Deliberate: a previous mechanism grew to 156 KB because every session added and
none removed, until reading the handover cost more than re-exploring the
repository — the exact opposite of the point.

## One checkpoint per project, never shared

Several sessions may run on one machine over different directories. A checkpoint
holds the context of the repository it sits in; never mix two.

## When to clear

Do not freeze the criteria in theory. Record real cases — including the ones
where clearing turned out to be wrong, which are the informative ones — and let
the rule emerge.

Signals so far:

- **The subject changed** and the loaded context no longer relates to it. The
  strongest signal, and the most often missed.
- The window is filling and the remaining work is a fresh start rather than a
  continuation.
- A long exploration ended in a decision: keep the decision, drop the
  exploration.

Counter-signal: a task in flight with unwritten state in the conversation.
Checkpoint first, then decide.

## If the checkpoint disagrees with what you observe

Trust the commands — branch, worktree, open pull requests — and treat the
narrative as stale. Never the other way round. **The tree is the authority, not
the document.**
