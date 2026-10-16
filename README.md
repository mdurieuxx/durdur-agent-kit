# durdur-agent-kit

The shared layer every project **references instead of copying**: the working
agreement, the skills that encode repeatable procedures, the agents, and the
hooks that enforce the rules mechanically.

Installed once as a plugin, updated with one command, versioned here.

## Install

```sh
/plugin marketplace add mdurieuxx/durdur-agent-kit
/plugin install house-rules@durdur-agent-kit
```

⚠️ **Unverified against a private repository.** This repo is private; whether a
marketplace install authenticates against it has not been tested. Test it before
relying on it, and fall back to a public repo or a local marketplace path if it
does not.

### What lives here, and what does not

A plugin can ship **skills, commands, agents and hooks** — nothing else. Checked
against the 315 plugins of the official marketplace: `skills` 16, `commands` 13,
`agents` 9, `hooks` 7, and **`rules` 0**.

So **always-on rules cannot come from here.** They belong in each project's own
`AGENTS.md`, which already loads on every turn. This kit carries what is needed
**on demand** — and that split is also what makes it cheap.

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

What a consuming project pays, per turn, just for having this installed:

| | Idle cost |
| --- | --- |
| a **hook** | **0** — it runs outside the context |
| an **agent** | **0** until it is spawned |
| a **skill** | **~40 tokens** — its description only, for routing |
| a skill's **body** | 800–2500 tokens, **only when invoked** |
| an always-on **rule** | its full weight, **every turn** |

Measured across every installed plugin (18 skills): descriptions run
106–203 characters, so **26–50 tokens each**; bodies run 3.3–10 KB and cost
nothing until used.

⚠️ An earlier version of this line said 144–204. That came from measuring one
plugin's five skills and generalising — the kind of inference case 12 is about.

**Design order, cheapest first: hook → agent → skill → never an always-on rule
here.** Ten well-described skills cost about 400 tokens of standing overhead
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

What earns a place: a mistake that cost real time, with its evidence; a guard
proven by making it fail on purpose; a tool-specific trap measured here; a
pattern reused a second time.

What does not: generic advice, anything the code already documents, anything
untested, or a near-duplicate — sharpen the existing entry instead.
