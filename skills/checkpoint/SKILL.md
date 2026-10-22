---
name: checkpoint
description: Write a session checkpoint before clearing context, decide whether to clear, and propose the clear yourself with the prompt to paste after it. Use when the context fills, the subject changes, or a session ends.
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
summary, the work item in progress, last test result, open pull requests, and any
unprocessed entry in `.claude/kit-candidates.md` — a finding not yet offered to the kit.

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

## Asking for the clear

**It is the agent's job to ask for the clear, never the owner's.** The skill says
when a clear is justified; without this section nobody starts it, and the owner
ends up asking "do you want a clear?" with the window already past 80%.

1. When a signal under "When to clear" holds, **propose the clear yourself**, at
   the end of a turn, without being asked.
2. Before proposing, the checkpoint is written, committed and **pushed**, and the
   tree is clean (the two commands above). Say so, with the commit id.
3. Report three numbers, so the owner can judge the proposal rather than take it
   on trust:
   - **cost per message**: tokens re-read on each turn, i.e. the context size at
     the last turn (the first turn after a clear gives the baseline);
   - **context size**: tokens used and the fill percentage of the window;
   - **context quality**: the token-optimizer score (e.g. `B (78/100)`), or
     "not measured" when it is unavailable. Never invent one.

   One line is enough:
   `Context: 142k tokens (71%), quality B (78/100); one message costs ~142k tokens now vs ~64k after the clear.`
4. Always give, with the proposal, **the prompt to paste after the clear**, in one
   fenced block ready to copy. It names:
   - the repository and the branch holding the checkpoint;
   - "read `checkpoint.md`, then memory X";
   - "first tell me the cost of a message";
   - the next step;
   - "without asking me questions", when that is the working mode.
5. **Never clear by yourself.** The owner types `/clear`.
6. Counter-signal unchanged: a task in flight with unwritten state means
   checkpoint first, *then* propose.

Witnessed: a session at 83% of the window, after several work items and a
diagnosis, with the checkpoint already pushed. The only thing missing was the
initiative and the resume prompt; the owner had to ask for both.

## If the checkpoint disagrees with what you observe

Trust the commands — branch, worktree, open pull requests — and treat the
narrative as stale. Never the other way round. **The tree is the authority, not
the document.**
