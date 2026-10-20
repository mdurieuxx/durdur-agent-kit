#!/usr/bin/env python3
"""Set the default model in a Claude Code settings file, keeping every other key.

usage: set-default-model.py [--project] [model]      (model defaults to opusplan)
User scope is ~/.claude/settings.json; --project writes ./.claude/settings.json.
Refuses to touch a file that is not valid JSON rather than overwrite it.
"""
import json, os, sys

args = [a for a in sys.argv[1:] if a != "--project"]
model = args[0] if args else "opusplan"
home = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
path = ".claude/settings.json" if "--project" in sys.argv else os.path.join(home, "settings.json")

settings = {}
if os.path.exists(path):
    try:
        settings = json.load(open(path))
    except ValueError as e:
        sys.exit(f"{path} is not valid JSON ({e}); left untouched")
before = settings.get("model")
if before == model:
    sys.exit(print(f"{path}: model already {model}") or 0)
settings["model"] = model
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(settings, f, indent=2); f.write("\n")
print(f"{path}: model {before!r} -> {model!r}")
