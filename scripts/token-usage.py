#!/usr/bin/env python3
"""Token consumption per project, read from the local session transcripts.

Why the four figures are kept apart instead of added up: they are not priced the
same. A cache read costs a fraction of a fresh input token, and cache creation
costs more than either. One total would read like a bill and be wrong.

Rates are NOT hard-coded. Prices change, and a stale rate in a script is worse
than no rate at all -- it produces a number nobody questions. Put yours in
~/.claude/token-rates.json to get a cost column:

    {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_creation": 3.75}

(dollars per million tokens, whatever your plan actually charges)
"""
import json, os, sys
from pathlib import Path

RACINE = Path.home() / ".claude" / "projects"
CHAMPS = ("input_tokens", "output_tokens",
          "cache_read_input_tokens", "cache_creation_input_tokens")


def slug(chemin: Path) -> str:
    """Claude Code's directory naming: / replaced by -."""
    return str(chemin).replace("/", "-")


def lire(dossier: Path):
    t = dict.fromkeys(CHAMPS, 0)
    t["thinking_tokens"] = 0
    t["messages"] = 0
    t["sessions"] = 0
    for f in dossier.glob("*.jsonl"):
        t["sessions"] += 1
        try:
            fh = f.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for ligne in fh:
                try:
                    u = (json.loads(ligne).get("message") or {}).get("usage")
                except Exception:
                    continue
                if not u:
                    continue
                t["messages"] += 1
                for c in CHAMPS:
                    t[c] += u.get(c) or 0
                d = u.get("output_tokens_details") or {}
                t["thinking_tokens"] += d.get("thinking_tokens") or 0
    return t


def tarifs():
    f = Path.home() / ".claude" / "token-rates.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def milliers(n: int) -> str:
    for u, s in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if n >= u:
            return f"{n / u:.1f}{s}"
    return str(n)


def cout(t, r):
    if not r:
        return ""
    d = (t["input_tokens"] * r.get("input", 0)
         + t["output_tokens"] * r.get("output", 0)
         + t["cache_read_input_tokens"] * r.get("cache_read", 0)
         + t["cache_creation_input_tokens"] * r.get("cache_creation", 0)) / 1e6
    return f"{d:9.2f}"


def main():
    args = sys.argv[1:]
    tout = "--all" in args
    r = tarifs()

    if not RACINE.is_dir():
        print(f"no transcripts under {RACINE}")
        return 1

    if tout:
        cibles = sorted(p for p in RACINE.iterdir() if p.is_dir())
    else:
        d = RACINE / slug(Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve())
        if not d.is_dir():
            print(f"no transcript directory for this project ({d.name})")
            return 1
        cibles = [d]

    entete = f"  {'project':<42} {'in':>7} {'out':>7} {'cache rd':>9} {'cache cr':>9} {'think':>7} {'msg':>6}"
    if r:
        entete += f" {'$':>9}"
    print(entete)
    total = dict.fromkeys(list(CHAMPS) + ["thinking_tokens", "messages", "sessions"], 0)
    for d in cibles:
        t = lire(d)
        if not t["messages"]:
            continue
        for k in total:
            total[k] += t[k]
        nom = d.name[:42]
        ligne = (f"  {nom:<42} {milliers(t['input_tokens']):>7} {milliers(t['output_tokens']):>7} "
                 f"{milliers(t['cache_read_input_tokens']):>9} {milliers(t['cache_creation_input_tokens']):>9} "
                 f"{milliers(t['thinking_tokens']):>7} {t['messages']:>6}")
        if r:
            ligne += f" {cout(t, r):>9}"
        print(ligne)
    print("  " + "-" * (len(entete) - 2))
    ligne = (f"  {'TOTAL (' + str(total['sessions']) + ' sessions)':<42} "
             f"{milliers(total['input_tokens']):>7} {milliers(total['output_tokens']):>7} "
             f"{milliers(total['cache_read_input_tokens']):>9} {milliers(total['cache_creation_input_tokens']):>9} "
             f"{milliers(total['thinking_tokens']):>7} {total['messages']:>6}")
    if r:
        ligne += f" {cout(total, r):>9}"
    print(ligne)
    if not r:
        print("  (no cost column: put your rates in ~/.claude/token-rates.json -- see the script header)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
