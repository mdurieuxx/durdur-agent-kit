---
description: Install the kit's commit hooks in this repository.
disable-model-invocation: true
---

Run the installer in the current repository and report which hooks it wired and
which it kept:

```sh
sh "${CLAUDE_PLUGIN_ROOT}/scripts/install-git-hooks.sh"
```

It never overwrites a hook it did not write, so a repository with its own
`pre-commit` keeps it and the output says so — merge by hand in that case.

The hooks resolve the plugin at run time rather than remembering today's path, so
a plugin update does not break them. If the plugin is later removed they skip with
a warning instead of failing every commit.

Per-project path exclusions go in `.claude/hook-exclusions`, one literal path fragment per line
(matched as a substring of the path, not a glob: `src/`, not `src/**`).
