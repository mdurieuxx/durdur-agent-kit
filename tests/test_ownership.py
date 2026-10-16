#!/usr/bin/env python3
"""Replayable proof that nothing is committed, pushed or opened on a repository whose
owner is not in the user's list -- and that everything else, reads included, is left alone.

Real git repositories are built in a temporary directory with the remotes that matter:
the user's own account, a third party's, none at all, and a local path. A guard tested
only on the command line would never notice that the repository it runs in is the thing
that decides.

Run:  python3 tests/test_ownership.py       exits non-zero on any failure.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / 'hooks' / 'no-foreign-commit.sh'
root = Path(tempfile.mkdtemp())
home = root / 'home'; (home / '.claude').mkdir(parents=True)
OWNED = home / '.claude' / 'owned-owners'
OWNED.write_text("# test\ngithub.com/me\ngithub.com/myorg\n")

def repo(name, remotes):
    p = root / name; p.mkdir()
    subprocess.run(['git', 'init', '-q'], cwd=p, check=True)
    for remote, url in remotes.items():
        subprocess.run(['git', 'remote', 'add', remote, url], cwd=p, check=True)
    return str(p)

MINE = repo('mine', {'origin': 'https://github.com/me/mine.git'})
ORG = repo('org', {'origin': 'git@github.com:myorg/thing.git'})
THEIRS = repo('theirs', {'origin': 'git@github.com:mavaag/theirs.git'})
FORK = repo('fork', {'origin': 'https://github.com/me/fork.git', 'upstream': 'https://github.com/mavaag/theirs.git'})
LOCAL = repo('local', {})
BARE = repo('bare', {'origin': str(root / 'somewhere.git')})

def blocked(command, cwd, owned=True):
    env = {'PATH': os.environ['PATH'], 'HOME': str(home)}
    if not owned:
        env['HOUSE_RULES_OWNED'] = str(root / 'missing-file')
    payload = json.dumps({'tool_input': {'command': command}, 'cwd': cwd})
    return subprocess.run([str(HOOK)], input=payload, capture_output=True, text=True, env=env).returncode == 2

MUST_BLOCK = [
    ('git commit -m x', THEIRS), ('git commit --amend', THEIRS), ('git push', THEIRS),
    ('git push origin main', THEIRS), ('git push --force-with-lease origin main', THEIRS),
    ('git merge feature', THEIRS), ('git tag -a v1 -m x', THEIRS), ('git cherry-pick abc', THEIRS),
    ('git add -A && git commit -m x', THEIRS), ('sudo git commit -m x', THEIRS),
    (f'git -C {THEIRS} commit -m x', MINE), (f'cd {THEIRS} && git commit -m x', MINE),
    (f'cd {THEIRS}; git push', MINE),
    ('git push https://github.com/mavaag/theirs.git main', MINE),
    ('git push git@github.com:mavaag/theirs.git main', MINE),
    ('git push upstream main', FORK), ('git push -u upstream main', FORK),
    ('gh pr create --title x --body y', THEIRS), ('gh pr merge 3', THEIRS), ('gh pr comment 3 --body x', THEIRS),
    ('gh pr create -R mavaag/theirs --title x', MINE), ('gh issue create --repo mavaag/theirs --title x', MINE),
    ("bash -c 'git commit -m x'", THEIRS), (f"ssh nas 'cd {THEIRS} && git commit -m x'", MINE),
]
MUST_ALLOW = [
    ('git commit -m x', MINE), ('git push', MINE), ('git push origin main', MINE), ('git tag v1', MINE),
    ('git commit -m x', ORG), ('git push', ORG), ('git commit -m x', LOCAL), ('git commit -m x', BARE),
    ('git push', BARE), ('git commit -m x', FORK), ('git push origin main', FORK), ('git push', FORK),
    ('gh pr create --title x', MINE), ('gh pr create -R me/mine --title x', THEIRS),
    # reading and fetching from someone else's repository changes nothing of theirs
    ('git status', THEIRS), ('git log --oneline', THEIRS), ('git diff', THEIRS), ('git fetch', THEIRS),
    ('git pull', THEIRS), ('git clone https://github.com/mavaag/theirs.git /tmp/x', MINE),
    ('git branch -a', THEIRS), ('git show HEAD', THEIRS), ('git remote get-url origin', THEIRS),
    ('gh pr list -R mavaag/theirs', MINE), ('gh pr view 3 --repo mavaag/theirs', MINE),
    ('gh repo view mavaag/theirs', MINE), ('ls -la', THEIRS), ('echo git commit', THEIRS),
    ('grep -r "git push" docs/', THEIRS), ('cat notes.md', THEIRS),
    (f'cd {MINE} && git commit -m x', THEIRS),          # the cd moves into a repo that IS his
    (f'git -C {MINE} commit -m x', THEIRS),
    ('git commit-tree HEAD^{tree}', THEIRS),
]
MISSING_FILE_BLOCK = [('git commit -m x', MINE), ('git push', ORG)]
MISSING_FILE_ALLOW = [('git commit -m x', LOCAL), ('git status', MINE)]

failures = [('should BLOCK', c, w) for c, w in MUST_BLOCK if not blocked(c, w)]
failures += [('should ALLOW', c, w) for c, w in MUST_ALLOW if blocked(c, w)]
failures += [('no list: should BLOCK', c, w) for c, w in MISSING_FILE_BLOCK if not blocked(c, w, owned=False)]
failures += [('no list: should ALLOW', c, w) for c, w in MISSING_FILE_ALLOW if blocked(c, w, owned=False)]
for verdict, command, where in failures:
    print(f"  FAIL {verdict}: {command[:70]}   (in {Path(where).name})")
total = len(MUST_BLOCK) + len(MUST_ALLOW) + len(MISSING_FILE_BLOCK) + len(MISSING_FILE_ALLOW)
print(f"{total - len(failures)}/{total} passed")
sys.exit(1 if failures else 0)
