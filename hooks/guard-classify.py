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
import shlex
import sys

DISK = re.compile(r'^/dev/(sd|hd|vd|xvd|nvme|mmcblk|md|dm-|mapper/|loop|nbd|zram|disk/)')
SHELLS = {'sh', 'bash', 'zsh', 'dash', 'ksh'}
CONFIRMATIONS = {'CONFIRM', 'EFFACER', 'DELETE', 'YES'}

# Programs that run another program. Value: the options that consume an argument.
WRAPPERS = {
    'sudo': {'-u', '-g', '-C', '-h', '-p', '-r', '-t', '-T', '-U', '-D', '-R'},
    'doas': {'-u', '-C'}, 'env': {'-u', '-C', '-S'}, 'nohup': set(), 'time': set(),
    'nice': {'-n'}, 'ionice': {'-c', '-n', '-p'}, 'timeout': {'-s', '-k'},
    'command': set(), 'exec': set(), 'stdbuf': {'-i', '-o', '-e'}, 'setsid': set(),
    'xargs': {'-I', '-n', '-P', '-L', '-d', '-s', '-E', '-a'}, 'watch': {'-n', '-d'},
}
SSH_OPTIONS_WITH_ARGUMENT = set('-b -c -D -E -e -F -I -i -J -L -l -m -O -o -p -Q -R -S -W -w'.split())

# Flags that only LOOK, per tool. Anything else on these tools writes.
SGDISK_READ_ONLY = {'-p', '--print', '-v', '--verify', '-i', '--info', '-E', '--end-of-largest',
                    '-f', '--first-in-largest', '-F', '--first-aligned-in-largest',
                    '-P', '--pretend', '-O', '--print-mbr', '-b', '--backup'}
SFDISK_READ_ONLY = {'-l', '--list', '-d', '--dump', '-s', '--show-size', '-F', '--list-free',
                    '-V', '--verify', '-g', '--show-geometry', '--list-types', '-T', '-n', '--no-act'}
PARTED_WRITE_COMMANDS = {'mklabel', 'mktable', 'mkpart', 'rm', 'resizepart', 'name', 'set', 'toggle',
                         'rescue', 'move', 'resize', 'mkfs', 'disk_set', 'disk_toggle'}

BLOCK_DEVICE_WRITE = 'irreversible write to a block device'
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2[ \t]*(?:\n|$)", re.S)
FEEDS_A_SHELL = re.compile(r'(^|[\s;|&])((ba|z|da|k)?sh|ssh)(\s|$)')


def flags_of(args):
    """Flags present, with combined short flags split: -af -> {-a, -f}; --x=1 -> {--x}."""
    flags = set()
    for arg in args:
        arg = arg.split('=')[0]
        if arg.startswith('--'):
            flags.add(arg)
        elif re.fullmatch(r'-[A-Za-z]+', arg):
            flags.update('-' + letter for letter in arg[1:])
    return flags


def split_heredocs(command):
    """Drop heredoc bodies -- they are text -- but keep any handed to a shell, which runs them."""
    scripts = []

    def drop(match):
        line_start = command.rfind('\n', 0, match.start()) + 1
        consumer = command[line_start:match.start()] + match.group(3)
        if FEEDS_A_SHELL.search(consumer):
            scripts.append(match.group(4))
        return match.group(3) + '\n'

    return HEREDOC.sub(drop, command), scripts


def split_segments(command):
    """Split on ; & | newline ( ) and backtick, outside quotes. Yields (segment, separator)."""
    segments, current, quote, i = [], [], None, 0
    while i < len(command):
        char = command[i]
        if quote:
            current.append(char)
            if char == '\\' and quote == '"' and i + 1 < len(command):
                i += 1
                current.append(command[i])
            elif char == quote:
                quote = None
        elif char in '\'"':
            quote = char
            current.append(char)
        elif char == '\\' and i + 1 < len(command):
            current.append(char)
            i += 1
            current.append(command[i])
        elif char in ';&|\n()`':
            separator = char
            if char in '|&' and command[i + 1:i + 2] == char:
                separator, i = char * 2, i + 1
            segments.append((''.join(current), separator))
            current = []
        else:
            current.append(char)
        i += 1
    segments.append((''.join(current), ''))
    return segments


def tokenize(segment):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def real_command(words):
    """Skip VAR=value and wrappers such as sudo/timeout; return (program, its arguments)."""
    i = 0
    while i < len(words):
        word = words[i]
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', word):
            i += 1
            continue
        name = word.rsplit('/', 1)[-1]
        if name not in WRAPPERS:
            return name, words[i + 1:]
        i += 1
        while i < len(words) and words[i].startswith('-'):
            i += 2 if words[i] in WRAPPERS[name] else 1
        if name == 'timeout' and i < len(words):
            i += 1  # the duration
    return None, []


def nested_commands(program, args):
    """Commands carried inside an argument: sh -c '...', ssh host '...', eval ..."""
    if program in SHELLS or program == 'su':
        for position, arg in enumerate(args):
            if re.fullmatch(r'-[a-z]*c[a-z]*', arg) and position + 1 < len(args):
                return [args[position + 1]]
    if program == 'eval':
        return [' '.join(args)]
    if program == 'ssh':
        position = 0
        while position < len(args) and args[position].startswith('-'):
            position += 2 if args[position] in SSH_OPTIONS_WITH_ARGUMENT else 1
        remote = args[position + 1:]  # position is the host
        return [' '.join(remote)] if remote else []
    return []


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
    command, shell_scripts = split_heredocs(command)
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
