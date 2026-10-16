# durdur-agent-kit

The shared layer every project **references instead of copying**: the working
agreement, the skills that encode repeatable procedures, the agents, and the
hooks that enforce the rules mechanically.

Installed once as a plugin, updated with one command, versioned here.

## Install

**Never at user scope for a trial.** A plugin installs at user scope by default,
which enables it in every session on the machine — including ones whose job is
to run the very commands the destructive guard blocks. Try it in one project:

```sh
claude plugin marketplace add mdurieuxx/durdur-agent-kit --scope local
claude plugin install house-rules@durdur-agent-kit --scope local
claude plugin details house-rules@durdur-agent-kit     # inventory + projected cost
sh scripts/install-git-hooks.sh                        # the commit hooks, see below
```

Verified end to end in a throwaway project: the marketplace and plugin declared
in that project's settings only, the user-level settings untouched.

**Private repository: the clone authenticates** (HTTPS, no prompt, with the
`gh` credentials already on the machine). What was *not* run is the full
`marketplace add` against GitHub, because a marketplace is registered under its
name in one global registry — adding a GitHub source named `durdur-agent-kit`
would overwrite a local-folder source of the same name.

⚠️ **An install from GitHub fetches `main`, and `main` is still the skeleton**
(10 files: one placeholder per folder). All the work is on `develop`. Merge only
after the content review, and bump the version with it.

### What lives here, and what does not

A plugin can ship **skills, commands, agents and hooks** — nothing else. Checked
against the 315 plugins of the official marketplace: `skills` 16, `commands` 13,
`agents` 9, `hooks` 7, and **`rules` 0**.

So there is **no `rules/` directory to put an always-on rule in.** They belong in
each project's own `AGENTS.md`, which already loads on every turn. The one
exception is a short rule injected at session start by a hook (see below). This
kit carries what is needed **on demand** — and that split is also what makes it
cheap.

## Two kinds of hook, do not confuse them

| | Mechanism | Declared in | Cost |
| --- | --- | --- | --- |
| **agent hooks** | run on tool use | `hooks/hooks.json` | 0 context tokens |
| **git hooks** | run on commit | `scripts/install-git-hooks.sh` | 0, they never touch the context |

`guard-destructive` and `token-report` are agent hooks. The five commit hooks —
`enforce-feature-branch`, `english-only`, `no-assistant-in-code`,
`no-assistant-attribution`, `tdd-test-parity` — are **git** hooks: they read the
staged diff and `$1`, the commit-message file. Wiring one into `hooks.json`
means wiring it where it will never run.

```sh
sh scripts/install-git-hooks.sh     # idempotent; refuses to clobber a foreign hook
```

Escape hatch for a release cut, which commits on protected branches by design:
`RELEASE_CUT=1 git commit ...` — **one neutral name**, because a per-project
variable means a shared hook does not recognise the release cut of the project
it runs in.

Project path exclusions go in `.claude/hook-exclusions`, one glob per line.
They are **not** hard-coded: the two projects these hooks came from each had
their own list baked in, which would silently exclude nothing elsewhere.

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
|

## Commands you type are invisible to the model

`/guard`, `/tokens` and `/install-git-hooks` carry `disable-model-invocation: true`:
only the user runs them, so there is no reason to announce them to the model on
every turn. **Verified by asking a live session which commands it can see** —
with the field, `guard` and `tokens` were absent from its list; without it, both
were there.

⚠️ `claude plugin details` does **not** reflect this: it still counts those three
(~140 tokens) in its estimate. Subtract them: **~634 tokens** reach the model.
When an estimate does not move after a change, that does not make the change
inert — ask the system what it actually does (lesson 15).

## Always-on rules: fragments, not plugin content

A plugin has no `rules/` directory (0 of 315 official plugins), so
`fragments/agents-md.md` holds the rules as sections to **copy** into a project's
own `AGENTS.md`. Two are there today, as one rule at its two ends:

> **No implementation without a spec written and committed first.**
>
> **No backlog item picked up until it states what it changes and how "done"
> will be judged.**

`spec-before-code` makes the first one mechanical: a commit adding production
code names its spec (`Spec: <path>`), stages it, or carries a traced
`SPEC-EXEMPT: <reason>`. Verified on five cases including the two that must pass.

## Attribution: injected, then enforced

The user's rule is absolute: nothing published credits or names the tool that
wrote it. The harness's default instruction is the opposite, and the default wins
wherever the rule is not loaded. **Measured on the repositories of one machine:
62 of 69 commits in one project and 46 of 64 in another carry the trailer** —
108 commits, by sessions that simply followed their defaults.

So the rule is handled at two layers, both verified live in a project with no
commit hooks installed:

| Layer | Mechanism | What it buys |
| --- | --- | --- |
| **inject** | `inject-rules.sh` at SessionStart puts the rule in the context | the model does not attempt it, so no refused commit and retried turn |
| **enforce** | `no-attribution.sh`, a PreToolUse hook | if it is attempted anyway, nothing leaves: no commit is created |

Verified: a session asked to commit "as you normally would" produced a clean
message and quoted the rule back; a session **ordered** to add the trailer was
blocked and no commit was made.

The enforcement reads the message from where it actually is — an `-m` value, a
file given to `-F`, a heredoc fed to the command — and applies to `git commit`,
`tag`, `merge` and `gh pr create|edit|merge`. A heredoc that merely *documents*
the trailer, or a `grep` for it, is not refused: `tests/test_attribution.py`
holds 20 cases that must block and 26 that must not.

**No opt-out, on purpose.** The destructive guard has one because some projects
legitimately do disk work. Nothing legitimately needs a commit to credit a tool.

Injection is a deliberate exception to "no always-on rule from a plugin", so it is
kept short (~90 tokens, which stay in the context for the session) and reserved
for judgment no hook can check, and for rules the harness's defaults contradict.

### History that already leaked

`scripts/strip-attribution.sh <repository>` produces a copy of a repository whose
history carries no attribution trailer. It is **safe by construction**: it works on
a clone, writes a bundle of the original first, never pushes, and proves the
rewrite touched messages only — every branch tip must keep the same file tree and
commit count. It prints the push command; running it is the repository owner's
decision, because a force-push is irreversible for anyone who already pulled.

Its first run was a test against a throwaway repository with known answers. It
reported "3 trailers remain" after a rewrite that had worked: the check counted
`refs/original/`, the copies `filter-branch` keeps of what it just rewrote. The
script announced its own failure rather than a success, and the fault was the
measurement.

## Findings feed the kit

`.claude/kit-candidates.md` in each project: one line per finding made while
working — date, what, evidence — appended when it happens. The `kit-contribution`
skill reads it at the next milestone. It is a file because a conversation is lost
at the next clear.

## On SOLID, deliberately absent

SOLID is not in this kit, and that is a decision rather than an omission. Named
principles are the textbook case of what the kit refuses: **generic advice**,
true everywhere and checkable nowhere.

What earns a place is the **consequence** that cost something, stated so a hook
or a test can catch it. One real example, from the project this kit was drawn
from: *"no module reads the clock"* — that **is** dependency inversion, but as a
rule you can enforce. *"Depend on abstractions"* is not.

So if a design failure costs real time: write the consequence, with its
incident. Not the principle it illustrates.

## Layout

```
.claude-plugin/marketplace.json   this repo as a marketplace
.claude-plugin/plugin.json        the house-rules plugin (version lives HERE only)
skills/<name>/SKILL.md            repeatable procedures
skills/<name>/references/         material a skill opens only when it needs it
agents/<name>.md                  delegable judgment
hooks/hooks.json                  declares the hooks, with ${CLAUDE_PLUGIN_ROOT}
hooks/*.sh                        mechanical enforcement
commands/                         slash commands
```

## The destructive guard: on by default, switchable per project

`hooks/guard-destructive.sh` is a **hook**, so it applies in every project the
moment the plugin is enabled — no opt-in. That is deliberate: the one time it
matters is the time nobody expected it.

It blocks piped confirmations, irreversible block-device writes, force-pushes,
Docker prunes and recursive deletes on absolute paths, while letting the
legitimate forms through (`dd if=/dev/sda of=image.img` reads a disk into a file
and passes).

**Some projects do this work for a living.** A NAS admin session legitimately
runs `wipefs`, `mkfs` and `docker prune`; three such commands were needed to
format the external disk that made a Synology recovery possible. A guard that
obstructs normal work gets switched off wholesale, and then protects nothing.

So when it fires, the agent **offers the choice** rather than deciding, and
`/guard` is the switch. Three scopes, narrowest first — all four behaviours
verified:

| Scope | How | Use it when |
| --- | --- | --- |
| **one command** | `DESTRUCTIVE_GUARD=off <cmd>` | a one-off need; nothing to clean up after |
| **one project** | `/guard off "<reason>"` → `.claude/destructive-guard.off` | the project does this work for a living |
| **everywhere** | `/guard off --global` → `~/.claude/destructive-guard.off` | you mean it; it covers projects not yet created |

`/guard status` reports which scope is in force — and **proves it** by running
the guard on a command it should block, rather than reading the files.

The project marker is looked up from the working directory **upwards**, so one in
a parent covers its subtrees; verified not to leak into a sibling project.
**Commit it** — it is a recorded decision with its reason, not local noise.

⚠️ Prefer the one-command form over a permanent marker for a one-off need. A
marker left behind for a single occasion is how guards quietly disappear.

Cost: **0 tokens** while nothing is blocked; about **150** in the one turn where
it fires.

## Token counter, on by default

`/tokens` reports this project's cumulative consumption, read from the local
transcripts under `~/.claude/projects/`. `--all` compares every project.

A **SessionStart** hook prints one line when a session opens — about **28
tokens, once**:

```
[tokens] this project: out 11.6M, cache read 3.8G, 8575 messages over 6 sessions.
```

⚠️ **SessionStart and not UserPromptSubmit, deliberately.** A counter that spends
tokens every turn to tell you about tokens is self-defeating. Once per session is
enough to notice a trend; the command is there for detail.

### Four figures, never one total

They are not priced the same: a cache read costs a fraction of a fresh input
token, cache creation costs more than either. **A single total reads like a bill
and is wrong.** The shape to watch is that `cache rd` dwarfs the rest by two or
three orders of magnitude — that is context being reused rather than re-sent. A
*falling* cache-read-to-output ratio is the signal worth reporting.

### No hard-coded prices

The cost column appears only if `~/.claude/token-rates.json` exists:

```json
{"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_creation": 3.75}
```

Rates are not baked into the script on purpose. **A stale rate is worse than no
rate** — it produces a number nobody questions.

### Overlap, stated honestly

`token-optimizer` (third party, non-commercial licence) already ships a
`token-dashboard`. It targets context-window *waste* and a quality score; this
targets *cumulative consumption per project*. Different question, and no
dependency on someone else's plugin.

It counts local transcripts only — sessions run elsewhere, or transcripts cleaned
up, are not in it. **A floor, not a bill.**

## Token economy, measured

What a consuming project pays just for having this installed. **Read from
`claude plugin details`, not estimated**: an earlier version of this table
counted only the description line (about 667 tokens for the whole kit) and
missed the per-entry overhead — the tool's own figure was **~884**, and is **~774** after
trimming descriptions, with **~634** actually reaching the model (see below).

| | Idle cost |
| --- | --- |
| a **hook** | **0** — runs outside the context |
| an **agent** | **0** until spawned |
| a **skill or command** | **~40–90 tokens**, its listing entry, for routing |
| a skill's **body** | ~430–1600 tokens, **only when invoked** |
| an always-on **rule** | its full weight, **every turn** |

Per component, as the tool reports it: `verify-claim` ~90, `modular-design`,
`readable-code`, `machine-first` ~80, `kit-contribution` ~70, down to `guard`
~40. The long descriptions are the ones costing most, which is where compression
pays.

**Design order, cheapest first: hook → agent → skill → an always-on rule only as
a last resort.** Ten well-described skills cost about 400 tokens of standing overhead
across every project. Twenty always-on rules would cost thousands per turn.

That is why `lessons.md` is a skill **reference** and not a document: ~40 tokens
idle instead of ~1930 always — or 0 and unreachable, which is where it sat
before this review.

## Status: content under review

The structure is in place. **What goes in is being decided**, from material that
already exists and has been used:

- the **measured common core** of `apex-analyzer-v4` and `k-forge-v2` — the ten
  items present in both, which is the empirical definition of "reusable here"
- the three gitflow pieces already proven in both projects: the
  `enforce-feature-branch` hook, the `## Git` section, and the release flow
  (today an ADR plus a script, which means you must know they exist to find
  them — a skill would make it discoverable)

Nothing is copied in before it is reviewed. A kit that accumulates becomes a kit
nobody reads.

## Branches

`main` is the released state and the default branch — a marketplace is fetched
from the default branch, so `main` is what an install sees. **Work happens on
`develop`**, and reaches `main` by merge.

This is the house convention across these repositories, stated by Marc on
2026-10-16: **`develop` and `main`**. Fifteen of his repositories default to
`main`, six carry a `develop`; `durdur-home-infra-stacks` is the reference — its
GitOps follows `develop` while `main` holds what is released.

⚠️ Consequence for this repo specifically: a rule, skill or hook merged to `main`
**changes behaviour in every project that installed the plugin**. Merge
deliberately, and bump the version in `.claude-plugin/plugin.json`.

## The one rule about this repository

**Every project either contributes a rule, a skill, an agent or a lesson here, or
states explicitly that it found nothing worth adding.** Silence is not an option:
an unfed kit dies, and then nobody trusts it.

The `kit-contribution` skill carries the procedure, including the part that is
easy to get wrong: **material arrives generalised or it does not arrive.** Strip
the story-id prefixes, the domain nouns, the project names, the per-project
environment variables — and **keep the evidence**, which is a different thing.

> Generalising applicability is not sanding off the incident. Confusing the two
> is how a kit turns into generic advice nobody reads.

What earns a place: a mistake that cost real time, with its evidence; a guard
proven by making it fail on purpose; a tool-specific trap measured here; a
pattern reused a second time.

What does not: generic advice, anything the code already documents, anything
untested, or a near-duplicate — sharpen the existing entry instead. And an
always-on rule only if no hook or skill can do the job (see below).
