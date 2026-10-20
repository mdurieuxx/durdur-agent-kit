#!/usr/bin/env python3
"""Would this command commit, push or open something on a repository the user does not own?

Reads a shell command on stdin, with the working directory in $OWNERSHIP_CWD. If it would
write to a repository whose owner is not in the user's list, prints the reason and exits 2.

THE RULE, in the user's words: nothing is committed on a repository that does not belong
to them. "Belongs to them" is MEASURED from the remote's owner, never guessed. The case
that prompted this: a repository assumed to be theirs sat under another person's account,
on which they merely had WRITE. Write access is not ownership.

What counts is the repository the command acts on, which is rarely the working directory
alone: `cd other && git commit`, `git -C other commit`, `git push <url>` and
`gh pr create -R owner/name` each name another place. Reading is never refused -- fetching,
cloning, logging and listing someone else's repository change nothing of theirs.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from shellparse import real_command, split_segments, tokenize

OWNED_FILE = Path(os.environ.get('HOUSE_RULES_OWNED') or Path.home() / '.claude' / 'owned-owners')
GIT_WRITING = {'commit', 'push', 'merge', 'cherry-pick', 'revert', 'am', 'tag'}
GH_WRITING = {('pr', verb) for verb in ('create', 'edit', 'merge', 'close', 'comment', 'review')} | \
             {('issue', verb) for verb in ('create', 'edit', 'close', 'comment')}
GIT_GLOBAL_OPTIONS_WITH_ARGUMENT = {'-c', '--git-dir', '--work-tree', '--namespace'}
NETWORK_URL = re.compile(r'^(?:[a-z+]+://)?(?:[^@/\s]+@)?([^/:\s]+)[:/]([^/\s]+)/')


def owned_owners():
    """Owners the user has declared theirs, as 'host/owner'; None if the list does not exist."""
    if not OWNED_FILE.is_file():
        return None
    lines = (line.strip().lower() for line in OWNED_FILE.read_text(encoding='utf-8').splitlines())
    return {line for line in lines if line and not line.startswith('#')}


def owner_of(url):
    """'host/owner' for a network remote; None for a local path, which nobody else owns."""
    if url.startswith(('/', './', '../', 'file://')):
        return None
    match = NETWORK_URL.match(url)
    return f'{match.group(1)}/{match.group(2)}'.lower() if match else None


def git_output(directory, *args):
    result = subprocess.run(['git', '-C', directory, *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ''


def remote_url(directory, name):
    return git_output(directory, 'remote', 'get-url', name)


def repository_owner(directory):
    """Owner of the repo's own remote: origin, else the first remote. None if it has none."""
    name = 'origin' if remote_url(directory, 'origin') else (git_output(directory, 'remote').split() or [''])[0]
    return owner_of(remote_url(directory, name)) if name else None


def push_target_owner(directory, args):
    """Where a push actually goes: a URL or remote named in the command, else the repo's own."""
    positional = [a for a in args if not a.startswith('-')]
    if positional:
        target = positional[0]
        url = target if NETWORK_URL.match(target) and '/' in target else remote_url(directory, target)
        if url:
            return owner_of(url)
    return repository_owner(directory)


def gh_target_owner(directory, args):
    """gh acts on -R/--repo owner/name when given, else on the working directory's repo."""
    for position, arg in enumerate(args):
        name, _, attached = arg.partition('=')
        value = attached or (args[position + 1] if name in ('-R', '--repo') and position + 1 < len(args) else '')
        if name in ('-R', '--repo') and value:
            owner = value.split('/')[-2] if value.count('/') >= 1 else value
            return f'github.com/{owner.lower()}'
    return repository_owner(directory)


def git_subcommand(args):
    """(directory override from -C, subcommand, its arguments) with git's global options skipped."""
    directory, position = None, 0
    while position < len(args) and args[position].startswith('-'):
        if args[position] == '-C' and position + 1 < len(args):
            directory = args[position + 1]
        position += 2 if args[position] in GIT_GLOBAL_OPTIONS_WITH_ARGUMENT | {'-C'} else 1
    if position >= len(args):
        return directory, None, []
    return directory, args[position], args[position + 1:]


def resolve(base, path):
    return os.path.normpath(path if os.path.isabs(path) else os.path.join(base, os.path.expanduser(path)))


def offending(command, directory, owned, depth=0):
    """(owner, what) for the first write to a repository outside the user's list."""
    if depth > 3:
        return None
    for segment, _ in split_segments(command):
        words = tokenize(segment)
        program, args = real_command(words)
        if program in ('cd', 'pushd') and args:
            directory = resolve(directory, args[-1])
            continue
        if program in ('sh', 'bash', 'zsh', 'dash', 'ksh', 'su', 'eval', 'ssh'):
            from shellparse import nested_commands
            for nested in nested_commands(program, args):
                hit = offending(nested, directory, owned, depth + 1)
                if hit:
                    return hit
            continue
        if program == 'git':
            override, subcommand, rest = git_subcommand(args)
            if subcommand not in GIT_WRITING:
                continue
            where = resolve(directory, override) if override else directory
            owner = push_target_owner(where, rest) if subcommand == 'push' else repository_owner(where)
            what = f'git {subcommand}'
        elif program == 'gh':
            positional = [a for a in args if not a.startswith('-')]
            if tuple(positional[:2]) not in GH_WRITING:
                continue
            owner, what = gh_target_owner(directory, args), 'gh ' + ' '.join(positional[:2])
        else:
            continue
        if owner and (owned is None or owner not in owned):
            return owner, what
    return None


def main():
    hit = offending(sys.stdin.read(), os.environ.get('OWNERSHIP_CWD') or os.getcwd(), owned_owners())
    if hit:
        print(f'{hit[0]}\t{hit[1]}')
        sys.exit(2)


if __name__ == '__main__':
    main()
