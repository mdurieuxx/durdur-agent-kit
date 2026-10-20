#!/usr/bin/env python3
"""Does this shell command EXECUTE something irreversible?

Reads the command on stdin. If it does, prints "<reason>\t<matched>" and exits 2;
otherwise exits 0.

WHY A PARSER AND NOT A SUBSTRING MATCH. The first version of the guard matched
words anywhere in the command line. Run as a real plugin it refused
`wipefs /dev/null` -- a read-only listing -- and replayed over one session's 300
real commands it would have blocked 26, of which about four were genuinely
destructive. The rest were commit messages, heredocs and greps that merely NAMED
these tools while writing the documentation about them. A guard that obstructs
normal work gets switched off wholesale, and then protects nothing.

So the decision is made on what is EXECUTED, in command position, and the
read-only forms of each tool go through. The same rewrite closed three holes the
substring version had: `git push -f` with nothing after it, `mkswap`, and
`printf CONFIRM |`.
"""
import re
import sys

from shellparse import (FEEDS_A_SHELL, flags_of, nested_commands, real_command,
                        split_heredocs, split_segments, tokenize)

DISK = re.compile(r'^/dev/(sd|hd|vd|xvd|nvme|mmcblk|md|dm-|mapper/|loop|nbd|zram|disk/)')
CONFIRMATIONS = {'CONFIRM', 'EFFACER', 'DELETE', 'YES'}


# Flags that only LOOK, per tool. Anything else on these tools writes.
SGDISK_READ_ONLY = {'-p', '--print', '-v', '--verify', '-i', '--info', '-E', '--end-of-largest',
                    '-f', '--first-in-largest', '-F', '--first-aligned-in-largest',
                    '-P', '--pretend', '-O', '--print-mbr', '-b', '--backup'}
SFDISK_READ_ONLY = {'-l', '--list', '-d', '--dump', '-s', '--show-size', '-F', '--list-free',
                    '-V', '--verify', '-g', '--show-geometry', '--list-types', '-T', '-n', '--no-act'}
PARTED_WRITE_COMMANDS = {'mklabel', 'mktable', 'mkpart', 'rm', 'resizepart', 'name', 'set', 'toggle',
                         'rescue', 'move', 'resize', 'mkfs', 'disk_set', 'disk_toggle'}

BLOCK_DEVICE_WRITE = 'irreversible write to a block device'


def piped_confirmation(words, separator):
    """`yes | cmd`, `echo CONFIRM | cmd`: the only window to interrupt is gone."""
    if separator != '|':
        return None
    program, args = real_command(words)
    if program == 'yes':
        return 'a confirmation is being piped in', 'yes |'
    if program in ('echo', 'printf') and CONFIRMATIONS & set(args):
        return 'a confirmation is being piped in', program + ' ... |'
    return None


def redirect_to_disk(words):
    for position, word in enumerate(words):
        if not word.startswith('>'):
            continue
        target = word.lstrip('>') or (words[position + 1] if position + 1 < len(words) else '')
        if DISK.match(target):
            return BLOCK_DEVICE_WRITE, '> /dev/...'
    return None


def is_safe_to_delete(path):
    return path.startswith(('/tmp/', '/var/tmp/')) and path.rstrip('/') not in ('/tmp', '/var/tmp')


def destructive(program, args):
    """(reason, matched) when this program with these arguments writes irreversibly."""
    flags = flags_of(args)
    if flags & {'--help', '--version'} or (program.startswith('mkfs') and '-V' in flags):
        return None  # asking the tool about itself writes nothing

    if program == 'wipefs':
        if flags & {'-a', '--all', '-o', '--offset'} and not flags & {'-n', '--no-act'}:
            return BLOCK_DEVICE_WRITE, 'wipefs'
    elif program == 'sgdisk':
        if flags - SGDISK_READ_ONLY:
            return BLOCK_DEVICE_WRITE, 'sgdisk'
    elif program == 'sfdisk':
        if not flags & SFDISK_READ_ONLY:
            return BLOCK_DEVICE_WRITE, 'sfdisk'
    elif program == 'parted':
        if set(args) & PARTED_WRITE_COMMANDS:
            return BLOCK_DEVICE_WRITE, 'parted'
    elif program.startswith('mkfs') or program in ('mke2fs', 'mkswap'):
        dry_run_capable = program in ('mkfs.ext2', 'mkfs.ext3', 'mkfs.ext4', 'mke2fs')
        if not (dry_run_capable and '-n' in flags):
            return BLOCK_DEVICE_WRITE, program
    elif program in ('blkdiscard', 'shred'):
        return BLOCK_DEVICE_WRITE, program
    elif program == 'dd':
        if any(arg.startswith('of=') and DISK.match(arg[3:]) for arg in args):
            return 'dd writing to a block device', 'dd ... of=/dev/'
    elif program == 'tee':
        if any(DISK.match(arg) for arg in args):
            return BLOCK_DEVICE_WRITE, 'tee /dev/...'
    elif program == 'docker':
        words = [arg for arg in args if not arg.startswith('-')]
        if set(zip(words, words[1:])) & {('system', 'prune'), ('volume', 'prune'),
                                          ('volume', 'rm'), ('volume', 'remove')}:
            return ("several agents may share this Docker; an orphan volume can be a stopped "
                    "stack's data"), 'docker prune/rm'
    elif program == 'git':
        return destructive_git(args)
    elif program == 'rm':
        paths = [arg for arg in args if not arg.startswith('-')]
        if flags & {'-r', '-R', '--recursive'} and flags & {'-f', '--force'}:
            if any(p.startswith('/') and not is_safe_to_delete(p) for p in paths):
                return 'recursive delete on an absolute path', 'rm -rf /'
    return None


def destructive_git(args):
    arguments_of_global_options = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}
    position = 0
    while position < len(args) and args[position].startswith('-'):
        position += 2 if args[position] in arguments_of_global_options else 1
    if position >= len(args):
        return None
    subcommand, flags = args[position], flags_of(args[position + 1:])
    if subcommand == 'push' and flags & {'-f', '--force', '--force-with-lease', '--force-if-includes'}:
        return 'force-push rewrites published history', 'push --force'
    if subcommand == 'clean' and flags & {'-f', '--force'} and not flags & {'-n', '--dry-run'}:
        return 'git clean removes untracked work', 'git clean'
    return None


def verdict(command, depth=0):
    if depth > 4:
        return None
    command, bodies = split_heredocs(command)
    shell_scripts = [body for consumer, body in bodies if FEEDS_A_SHELL.search(consumer)]
    for script in shell_scripts:
        hit = verdict(script, depth + 1)
        if hit:
            return hit
    for segment, separator in split_segments(command):
        words = tokenize(segment)
        if not words:
            continue
        hit = piped_confirmation(words, separator) or redirect_to_disk(words)
        program, args = real_command(words)
        hit = hit or (destructive(program, args) if program else None)
        for nested in nested_commands(program, args) if program else []:
            hit = hit or verdict(nested, depth + 1)
        if hit:
            return hit
    return None


if __name__ == '__main__':
    result = verdict(sys.stdin.read())
    if result:
        print('\t'.join(result))
        sys.exit(2)
