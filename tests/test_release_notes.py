#!/usr/bin/env python3
"""Replayable proof of scripts/release_notes.py, check-release.sh and tag-release.sh.

Everything runs on a throwaway git repository in a temp directory, with a stub `gh`
on PATH that records its calls. Nothing here touches a real repository or the forge.

Run:  python3 tests/test_release_notes.py        exits non-zero on any failure.
"""
import os, subprocess, sys, tempfile, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NOTES = os.path.join(ROOT, 'scripts', 'release_notes.py')
CHECK = os.path.join(ROOT, 'scripts', 'check-release.sh')
TAGGER = os.path.join(ROOT, 'scripts', 'tag-release.sh')
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.test',
       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.test', 'GIT_CONFIG_GLOBAL': '/dev/null'}
failures = []


def run(cmd, cwd, env=None, **kw):
    return subprocess.run(cmd, cwd=cwd, env=env or ENV, capture_output=True, text=True, stdin=kw.pop('stdin', subprocess.DEVNULL), **kw)


def git(cwd, *a):
    r = run(['git', *a], cwd)
    assert r.returncode == 0, (a, r.stderr)
    return r.stdout.strip()


def commit(cwd, path, msg):
    full = os.path.join(cwd, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'a') as f:
        f.write(msg + '\n')
    git(cwd, 'add', path)
    git(cwd, 'commit', '-q', '-m', msg)


def check(name, ok, detail=''):
    if not ok:
        failures.append(name)
        print(f'FAIL: {name} {detail}')


tmp = tempfile.mkdtemp()
try:
    repo = os.path.join(tmp, 'repo')
    git(tmp, 'init', '-q', '-b', 'main', repo)
    commit(repo, 'app/a', 'feat: app first')
    git(repo, 'tag', 'app-v1.2.0')
    commit(repo, 'app/a', 'feat: app 1.9 work\n\nFixes #11')
    commit(repo, 'lib/l', 'feat: lib only, must not appear in app notes')
    git(repo, 'tag', 'app-v1.9.0')
    # a merge commit on top of real work: left out, its parents' commits stay
    git(repo, 'switch', '-q', '-c', 'side')
    commit(repo, 'app/b', 'fix: from a side branch (closes #12)')
    git(repo, 'switch', '-q', 'main')
    commit(repo, 'app/a', 'chore: main moves on')
    git(repo, 'merge', '-q', '--no-ff', 'side', '-m', 'Merge side into main')
    git(repo, 'tag', 'app-v1.10.0')           # name order puts it BEFORE 1.9.0; version order after
    git(repo, 'tag', 'lib-v0.1.0')
    git(repo, 'tag', 'v0.0.1')

    out = run([sys.executable, NOTES, 'app-v1.10.0', '--artifact', 'registry.example/app:1.10.0'], repo)
    n = out.stdout
    check('exits 0', out.returncode == 0, out.stderr)
    check('previous tag is chosen by version, not by name', 'since `app-v1.9.0`' in n, n)
    check('commits of the range are listed', 'main moves on' in n and 'from a side branch' in n, n)
    check('commits before the previous tag are not', 'app 1.9 work' not in n and 'app first' not in n, n)
    check('other components are left out', 'lib only' not in n, n)
    check('merge commits are left out', 'Merge side' not in n, n)
    check('the issues the commits fix are listed', '- #12' in n and '- #11' not in n, n)
    check('the artifact the tag names is printed', '`registry.example/app:1.10.0`' in n, n)

    first = run([sys.executable, NOTES, 'app-v1.2.0'], repo).stdout
    check('first tag says so', 'First release of app' in first and 'since' not in first, first)
    check('first tag lists its commits', 'app first' in first, first)

    fixed = run([sys.executable, NOTES, 'app-v1.9.0'], repo).stdout
    check('issue closed by a body line is found', '- #11' in fixed, fixed)

    plain = run([sys.executable, NOTES, 'v0.0.1'], repo).stdout
    check('a plain vX.Y.Z covers the whole repository', 'lib only' in plain and 'app first' in plain, plain)

    check('a tag whose component has no folder fails', run([sys.executable, NOTES, 'ghost-v1.0.0'], repo).returncode != 0)
    check('a name that is not a release tag fails', run([sys.executable, NOTES, 'nightly'], repo).returncode != 0)

    # stub gh: `gh release view` succeeds only for tags listed in $GH_RELEASES; calls are logged
    stub = os.path.join(tmp, 'bin'); os.makedirs(stub)
    log = os.path.join(tmp, 'gh.log')
    with open(os.path.join(stub, 'gh'), 'w') as f:
        f.write('#!/bin/sh\n'
                'echo "$@" >> "$GH_LOG"\n'
                'if [ "$1 $2" = "release view" ]; then\n'
                '  case " $GH_RELEASES " in *" $3 "*) ;; *) exit 1;; esac\n'
                '  case "$*" in *--json*) printf "%s\\n" "$GH_BODY";; esac\n'
                'fi\n'
                'cat >/dev/null 2>&1 || true\n')
    os.chmod(os.path.join(stub, 'gh'), 0o755)
    genv = {**ENV, 'PATH': stub + os.pathsep + ENV['PATH'], 'GH_LOG': log, 'GH_RELEASES': '', 'GH_BODY': 'notes'}

    r = run([sys.executable, NOTES, 'app-v1.10.0', '--publish'], repo, genv)
    calls = open(log).read()
    check('--publish creates the release for the tag', r.returncode == 0 and 'release create app-v1.10.0' in calls, calls + r.stderr)

    # the witness: a tag with no release must FAIL the check; one with notes must pass
    check('check fails on a tag without a release', run(['bash', CHECK, 'app-v1.10.0'], repo, genv).returncode == 1)
    check('check passes on a tag with notes', run(['bash', CHECK, 'app-v1.10.0'], repo, {**genv, 'GH_RELEASES': 'app-v1.10.0'}).returncode == 0)
    check('check fails on empty notes', run(['bash', CHECK, 'app-v1.10.0'], repo, {**genv, 'GH_RELEASES': 'app-v1.10.0', 'GH_BODY': ''}).returncode == 1)

    # the tag tool: pushes the tag AND publishes, in that order, from one command
    bare = os.path.join(tmp, 'origin.git'); git(tmp, 'init', '-q', '--bare', bare)
    git(repo, 'remote', 'add', 'origin', bare)
    open(log, 'w').close()
    commit(repo, 'app/a', 'feat: next')
    r = run(['bash', TAGGER, 'app-v1.11.0', 'registry.example/app:1.11.0'], repo, genv)
    pushed = git(repo, 'ls-remote', '--tags', 'origin')
    check('tag-release pushes the tag', r.returncode == 0 and 'refs/tags/app-v1.11.0' in pushed, r.stderr)
    check('previous tag is 1.10.0, not the name-sorted 1.9.0', 'since `app-v1.10.0`' in run([sys.executable, NOTES, 'app-v1.11.0'], repo).stdout)
    check('tag-release publishes its notes', 'release create app-v1.11.0' in open(log).read())
    r = run(['bash', TAGGER, 'nightly'], repo, genv)
    check('tag-release refuses a bad name before tagging anything', r.returncode != 0 and 'refs/tags/nightly' not in git(repo, 'ls-remote', '--tags', 'origin') and 'nightly' not in git(repo, 'tag', '--list'))
finally:
    shutil.rmtree(tmp)

print('release notes:', 'FAILED ' + ', '.join(failures) if failures else 'all passed')
sys.exit(1 if failures else 0)
