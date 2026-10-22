#!/usr/bin/env python3
"""Release notes for one tag, generated from git, and optionally published as the tag's release.

    release_notes.py <tag> [--artifact TEXT] [--repo DIR] [--publish]

Tags are `<component>-vX.Y.Z` (the component's folder, at the repository root, is
named after it) or a plain `vX.Y.Z` (the component is the whole repository).

The notes are the commits that touched the component since its PREVIOUS TAG BY VERSION
(not by name, not by date, and not the nearest tag in the history), merge commits
and other components left out, the issues those commits fix, and the artifact the tag
names (`--artifact`, e.g. an image reference). The first tag of a component says so.

Why a script and not a hand step after tagging: a hand step is the one that gets
skipped. On a real project 18 tags existed and no release, so what an image contained
could only be read from `git log`.
"""
import argparse, os, re, subprocess, sys

TAG_RE = re.compile(r'^(?:(?P<component>.+)-)?v(?P<version>\d+(?:\.\d+)*)$')
FIXES_RE = re.compile(r'\b(?:fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s+#(\d+)', re.I)


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'git {" ".join(args)}: {r.stderr.strip()}')
    return r.stdout


def parse_tag(tag):
    m = TAG_RE.match(tag)
    if not m:
        sys.exit(f'{tag}: not a release tag (<component>-vX.Y.Z or vX.Y.Z)')
    return m['component'], tuple(int(p) for p in m['version'].split('.'))


def previous_tag(repo, component, version):
    """The highest version of the same component that is below `version`."""
    older = []
    for t in git(repo, 'tag', '--list').split():
        m = TAG_RE.match(t)
        if m and m['component'] == component:
            v = tuple(int(p) for p in m['version'].split('.'))
            if v < version:
                older.append((v, t))
    return max(older)[1] if older else None


def commits(repo, rev, component, folder):
    out = git(repo, 'log', '--no-merges', '--format=%h%x1f%s%x1f%b%x1e', rev, '--', *([folder] if component else []))
    for rec in filter(None, (r.strip('\n') for r in out.split('\x1e'))):
        sha, subject, body = (rec.split('\x1f') + ['', ''])[:3]
        yield sha.strip(), subject, body


def notes(repo, tag, artifact=None):
    component, version = parse_tag(tag)
    if component and not os.path.isdir(os.path.join(repo, component)):
        sys.exit(f'{tag}: no folder {component}/ at the repository root (component = folder, by convention)')
    prev = previous_tag(repo, component, version)
    rev = f'{prev}..{tag}' if prev else tag
    rows = list(commits(repo, rev, component, component))
    name = component or os.path.basename(os.path.abspath(repo))
    ver = '.'.join(map(str, version))
    lines = [f'## {name} {ver}', '']
    lines.append(f'Changes since `{prev}`.' if prev else f'First release of {name}: there is no previous tag.')
    if artifact:
        lines += ['', f'Artifact: `{artifact}`']
    lines += ['', '### Changes', '']
    lines += [f'- {s} ({sha})' for sha, s, _ in rows] or [f'- No commit touched {component + "/" if component else "the repository"} since `{prev}`.']
    issues = sorted({int(n) for _, s, b in rows for n in FIXES_RE.findall(f'{s}\n{b}')})
    if issues:
        lines += ['', '### Issues fixed', ''] + [f'- #{n}' for n in issues]
    return '\n'.join(lines) + '\n'


def publish(repo, tag, body):
    exists = subprocess.run(['gh', 'release', 'view', tag], cwd=repo, capture_output=True).returncode == 0
    verb = 'edit' if exists else 'create'
    extra = [] if exists else ['--title', tag, '--verify-tag']
    r = subprocess.run(['gh', 'release', verb, tag, *extra, '--notes-file', '-'], cwd=repo, input=body, text=True)
    if r.returncode:
        sys.exit(f'gh release {verb} {tag} failed: the tag has no notes')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('tag')
    ap.add_argument('--artifact')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--publish', action='store_true', help="publish as the tag's release with gh")
    a = ap.parse_args()
    body = notes(a.repo, a.tag, a.artifact)
    if a.publish:
        publish(a.repo, a.tag, body)
    else:
        sys.stdout.write(body)


if __name__ == '__main__':
    main()
