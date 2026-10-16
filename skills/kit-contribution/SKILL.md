---
name: kit-contribution
description: Port material into the shared kit, generalised, or decide it stays in its project. Use when porting a rule, skill, agent or hook, after a mistake cost real time, at a milestone, or when asked what we learned.
---

# Into the kit, or staying put

Two standing instructions from Marc govern this:

> « Tout projet qu'on fait ensemble devra proposer d'ajouter une rule ou skill ou
> autre dans le template, sinon lui ajoute quelque chose »

> « Quand tu portes des skills, rules ou autre d'un projet, il faut généraliser
> et le sortir de son contexte »

So: **every project contributes something or states explicitly that it found
nothing** — silence is not an option.

**And at the moment of discovery, not only at the end.** A finding made while
working — a trap, a guard that misfired, a pattern used twice — is mentioned in
one line when it happens, and appended to `.claude/kit-candidates.md` in the
project (date, what, evidence). A conversation is lost at the next clear; the
file is not, and this skill processes it at the next milestone. And **nothing enters as-is**: material
arrives generalised, or it does not arrive.

## 1. Is it portable? Measure, do not judge by name

Count the project's own vocabulary in the file. Zero means portable; anything
else is the work remaining.

```sh
cpt() { c=$(grep -ciE "$2" "$1" 2>/dev/null) || true; echo "${c:-0}"; }
cpt file.md 'STORY-|projectname|domainnoun|otherdomainnoun'
```

⚠️ Two traps here, both in `verify-claim` → cases 12 and 3: never write
`|| echo 0` after `grep -c`, and **prove the counter on a witness** before
trusting a zero.

## 2. What must be stripped

The right-hand column holds **real cases observed in this setup**, kept concrete
on purpose: they make the table credible. They are illustrations, not rules, so
they do not narrow what this skill applies to — which is the distinction §3 is
about. Running the §1 counter on this file returns 2 for that reason, and the
2 are these.

| Strip | Example seen here |
| --- | --- |
| story-id prefixes | `KP-NNN`, `KF2-NNN` → "the story id" |
| domain nouns | circuit, lap, race, ranking model |
| project names | in prose, in paths, in examples |
| per-project env vars | `KART_RELEASE_CUT` → one neutral name |
| absolute paths into the project | `~/github/<project>/...` → relative, or a variable |
| references to project files | a script or ADR only that project has |

## 3. What must NOT be stripped

**The evidence.** Generalising applicability is not the same as sanding off the
incident, and confusing the two is how a kit turns into generic advice nobody
reads.

Keep the command that failed, the output that misled, and the fix — concrete.
They can stay concrete without naming the project: *"a disk was wiped while the
user was interrupting the command"* carries its whole weight with no project in
it.

**The test:** after rewriting, the entry should still answer *"why would anyone
believe this?"* If it only answers *"what should I do?"*, the scar is gone and
the rule will be argued away in six months.

## 4. Where it goes

| Kind | Destination |
| --- | --- |
| repeatable procedure | `skills/<name>/SKILL.md` |
| long material a skill opens on demand | `skills/<name>/references/` |
| delegable judgment | `agents/<name>.md` |
| mechanical enforcement | `hooks/` + a declaration in `hooks/hooks.json` |
| explicit user action | `commands/<name>.md` |
| **an always-on rule** | the project's `AGENTS.md`; or, if it must travel with the plugin, one short line in `hooks/session-rules.txt` |

⚠️ **A plugin has no `rules/` directory** — 0 of the 315 official plugins use one.
What it *can* do is inject a short rule at session start, because a SessionStart
hook's output enters the context (`hooks/session-rules.txt`). That costs its
tokens for the whole session, so it is reserved for two cases: judgment that no
hook can check, and a rule the harness's own defaults contradict. The second is
real: the default instruction is to add an attribution trailer, and without the
rule loaded 62 of 69 commits in one project and 46 of 64 in another carry it.

**And before writing one at all, try to make it unnecessary.** A rule belongs in
`AGENTS.md` only if it can be neither a hook nor a skill — a hook costs no tokens
and is obeyed rather than read; a skill is paid only when invoked. On one real
`AGENTS.md`, 7 of 15 sections already named the hook enforcing them, so they
could have been one line each.

## 5. The token budget

Only **descriptions** are charged every turn; bodies cost only when invoked;
hooks and scripts cost nothing. So write the description tight for routing, let
the body breathe — and **never compress a hook or a script to save tokens**,
there is nothing there to save.

## 6. Report

```
Contribution — <project>
  kind     : skill | agent | hook | command | reference | nothing
  target   : <path in the kit>
  because  : <the incident, one sentence>
  evidence : <the command and its misleading output>
  stripped : <what project vocabulary was removed, and the count before/after>
  duplicate: <existing entry this sharpens, or none>
```

**Propose, do not push.** The kit is Marc's; a merge to `main` changes behaviour
in every project that installed the plugin.

If the answer is *nothing*, say what was examined: *"nothing new — both traps hit
were already cases 5 and 9"* is a complete answer.
