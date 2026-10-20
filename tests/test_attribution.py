#!/usr/bin/env python3
"""Replayable proof that the attribution guard refuses what PUBLISHES a credit, and
only that. Same two-list discipline as test_guard.py: a guard tested only on what
it must block drifts toward blocking everything.

The allowed list is the one that matters. The kit's own commit messages and docs
talk about the trailer constantly, and a guard that refused them would be switched
off within a day.

Run:  python3 tests/test_attribution.py      exits non-zero on any failure.
"""
import json, os, subprocess, sys, tempfile

HOOK = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'no-attribution.sh')
TRAILER = 'Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>'

with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
    f.write(f'feat: x\n\n{TRAILER}\n'); DIRTY_FILE = f.name
with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
    f.write('feat: x\n\nplain message\n'); CLEAN_FILE = f.name

MUST_BLOCK = [
    f'git commit -m "feat: x\n\n{TRAILER}"',
    f"git commit -m 'feat: x' -m '{TRAILER}'",
    f'git commit -am "fix: y\n\n{TRAILER}"',
    f"git commit -F - <<'EOF'\nfeat: x\n\n{TRAILER}\nEOF",
    f'git commit -F {DIRTY_FILE}',
    'git commit -m "Generated with [Claude Code](https://claude.com/claude-code)"',
    'git commit -m "feat: x 🤖"',
    'git commit -m "docs: Claude Code reports the cost"',
    'git commit -m "fix: ask Copilot to retry"',
    f'git commit --amend -m "feat: x\n\n{TRAILER}"',
    f'git -C /repo commit -m "x\n\n{TRAILER}"',
    f'cd /repo && git commit -m "x\n\n{TRAILER}"',
    f'sudo -u deploy git commit -m "x\n\n{TRAILER}"',
    f'git tag -a v1 -m "release\n\n{TRAILER}"',
    f'git merge feature -m "merge\n\n{TRAILER}"',
    'gh pr create --title "x" --body "🤖 Generated with [Claude Code](https://claude.com/claude-code)"',
    f'gh pr create --title x --body "ok\n\n{TRAILER}"',
    "gh pr create --title x --body-file - <<'EOF'\nSummary\n\n🤖 Generated with Claude Code\nEOF",
    'gh pr edit 3 --body "written by Claude"',
    'gh pr merge 3 --body "Generated with Claude"',
]

MUST_ALLOW = [
    # ordinary publishing
    'git commit -m "feat: add the guard"', 'git commit -am "fix: typo"',
    f'git commit -F {CLEAN_FILE}', "git commit -F - <<'EOF'\nfeat: x\n\nplain\nEOF",
    'git commit --amend --no-edit', 'git tag -a v1 -m "release"',
    'gh pr create --title "x" --body "Summary of the change"',
    "gh pr create --title x --body-file - <<'EOF'\nSummary\nEOF",
    # the words as TEXT, not as a credit
    f"cat > docs/rule.md <<'EOF'\n{TRAILER}\nGenerated with Claude Code\nEOF",
    f"cat >> notes.md <<'EOF'\nNever add: {TRAILER}\nEOF",
    f'echo "{TRAILER}" >> blocked-patterns.txt', f'grep -rn "Co-Authored-By" .',
    'grep -rn "Generated with" docs/', 'git log --grep="Claude" --oneline',
    'git log --format=%B | grep -i anthropic', 'git diff -- .claude/settings.json',
    # paths and names that contain the word but are not the assistant
    'git commit -m "chore: move rules under .claude/hooks"',
    'git commit -m "feat: scaffold claude-dev-template"',
    'git commit -m "fix: read ~/.claude/settings.json"',
    'git add .claude/ && git status', 'git push -u origin develop', 'gh pr list', 'gh pr view 3',
    'git commit-tree HEAD^{tree}', 'ls -la', 'echo hello',
]

def blocked(command):
    payload = json.dumps({'tool_input': {'command': command}, 'cwd': '/tmp'})
    env = {'PATH': os.environ['PATH'], 'HOME': '/nonexistent'}
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode == 2

failures = [('should BLOCK', c) for c in MUST_BLOCK if not blocked(c)]
failures += [('should ALLOW', c) for c in MUST_ALLOW if blocked(c)]
for verdict, command in failures:
    print(f"  FAIL {verdict}: {' '.join(command.split())[:96]}")
os.unlink(DIRTY_FILE); os.unlink(CLEAN_FILE)
total = len(MUST_BLOCK) + len(MUST_ALLOW)
print(f"{total - len(failures)}/{total} passed ({len(MUST_BLOCK)} must block, {len(MUST_ALLOW)} must allow)")
sys.exit(1 if failures else 0)
