#!/usr/bin/env python3
"""inject-rules.sh: the cost-before-clear rule is on by default, off when the plugin option says so."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(__file__), "..")
S = os.path.join(ROOT, "hooks", "inject-rules.sh")
ok = bad = 0
def check(name, got, want):
    global ok, bad
    if got == want: ok += 1
    else: bad += 1; print(f"FAIL: {name} (got {got!r}, want {want!r})")
def run(**option):
    with tempfile.TemporaryDirectory() as home:
        open(os.path.join(home, ".claude-owned"), "w").close()
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_")}
        env.update(HOME=home, HOUSE_RULES_OWNED=os.path.join(home, ".claude-owned"), **option)
        os.makedirs(os.path.join(home, ".claude"))
        open(os.path.join(home, ".claude", "owned-owners"), "w").close()
        return subprocess.run(["bash", S], env=env, capture_output=True, text=True).stdout
RULE = "cost of a message"
check("rule on by default", RULE in run(), True)
check("rule on when true", RULE in run(CLAUDE_PLUGIN_OPTION_COST_BEFORE_CLEAR="true"), True)
check("rule off when false", RULE in run(CLAUDE_PLUGIN_OPTION_COST_BEFORE_CLEAR="false"), False)
check("standing rules kept when off", "[house-rules] 1." in run(CLAUDE_PLUGIN_OPTION_COST_BEFORE_CLEAR="false"), True)
manifest = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
option = manifest.get("userConfig", {}).get("cost_before_clear", {})
check("option declared, boolean, default on", (option.get("type"), option.get("default")), ("boolean", True))
print(f"{ok}/{ok+bad} passed"); sys.exit(bad != 0)
