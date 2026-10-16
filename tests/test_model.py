#!/usr/bin/env python3
"""set-default-model.py: sets the key, keeps the others, is idempotent, refuses bad JSON."""
import json, os, subprocess, sys, tempfile
S = os.path.join(os.path.dirname(__file__), "..", "scripts", "set-default-model.py")
ok = bad = 0
def check(name, got, want):
    global ok, bad
    if got == want: ok += 1
    else: bad += 1; print(f"FAIL: {name} (got {got!r}, want {want!r})")
def run(d, *a):
    return subprocess.run([sys.executable, S, *a], env={**os.environ, "CLAUDE_CONFIG_DIR": d},
                          capture_output=True, text=True)
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "settings.json")
    check("creates a missing file", (run(d).returncode, json.load(open(p))), (0, {"model": "opusplan"}))
    json.dump({"model": "sonnet", "permissions": {"allow": ["Bash(ls)"]}}, open(p, "w"))
    run(d); cfg = json.load(open(p))
    check("replaces the model", cfg["model"], "opusplan")
    check("keeps other keys", cfg["permissions"], {"allow": ["Bash(ls)"]})
    check("idempotent", "already" in run(d).stdout, True)
    run(d, "haiku"); check("explicit model", json.load(open(p))["model"], "haiku")
    open(p, "w").write("{not json"); r = run(d)
    check("invalid JSON refused", (r.returncode != 0, open(p).read()), (True, "{not json"))
print(f"{ok}/{ok+bad} passed"); sys.exit(bad != 0)
