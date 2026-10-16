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

A project then carries only what is **specific to it** — its own `AGENTS.md`
section, its own path-scoped rules under `.claude/rules/`. Everything general
comes from here and stays in step on its own.

## Layout

```
.claude-plugin/marketplace.json   this repo as a marketplace
.claude-plugin/plugin.json        the house-rules plugin
rules/                            always-on rules (AGENTS.md material)
skills/<name>/SKILL.md            repeatable procedures
agents/<name>.md                  delegable judgment
hooks/*.sh                        mechanical enforcement
commands/                         slash commands
docs/lessons.md                   11 checks that returned a plausible answer
                                  while measuring nothing
```

## Status: content under review

The structure is in place. **What goes in is being decided**, from material that
already exists and has been used:

- the **measured common core** of `apex-analyzer-v4` and `k-forge-v2` — the ten
  items present in both, which is the empirical definition of "reusable here"
- `docs/lessons.md`, the only piece that existed nowhere else

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
