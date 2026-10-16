---
description: Set opusplan as the default model.
disable-model-invocation: true
---

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/set-default-model.py"
```

Add `--project` to write this repository's `.claude/settings.json` instead of the user
file, or a model name to use something other than `opusplan`. Other keys are kept; a
file that is not valid JSON is left untouched. Takes effect in the next session.
