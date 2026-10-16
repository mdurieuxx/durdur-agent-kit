---
description: Report token consumption for this project or all projects, from the local transcripts. Use when asked what a project cost, which consumes most, or to check a trend.
disable-model-invocation: true
---

# /tokens — consumption per project

Argument: `$ARGUMENTS` — empty for this project, `--all` for every project.

```sh
python3 "$CLAUDE_PLUGIN_ROOT/scripts/token-usage.py" $ARGUMENTS
```

## Reading the output, and what not to say

Four figures, deliberately **not added together**: they are not priced the same.
A cache read costs a fraction of a fresh input token; cache creation costs more
than either. **Never present a single total as "what the project cost"** — that
reads like a bill and is wrong.

| Column | What it is |
| --- | --- |
| `in` | fresh input tokens — usually tiny, because almost everything is cached |
| `out` | generated tokens, thinking included |
| `cache rd` | context re-read from cache each turn — the big number, and the cheap one |
| `cache cr` | context written to cache |
| `think` | the thinking share of `out` |

**The shape to look for**: `cache rd` dwarfs everything by two to three orders of
magnitude. That is normal and desirable — it means the context is being reused
rather than re-sent. A *falling* cache-read-to-output ratio is the signal worth
reporting: it means context is being rebuilt instead of reused.

## The cost column

Absent unless `~/.claude/token-rates.json` exists:

```json
{"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_creation": 3.75}
```

Dollars per million tokens. **Do not invent these rates** — the script has none
hard-coded on purpose. A stale rate in a script is worse than no rate: it
produces a number nobody questions. Ask the user for the figures their plan
actually charges, or leave the column out.

## Caveat to state when reporting

This counts what is in the **local transcripts** under `~/.claude/projects/`.
Sessions run elsewhere, or transcripts cleaned up, are not in it. It is a floor,
not a bill.
