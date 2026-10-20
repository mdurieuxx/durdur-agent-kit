#!/usr/bin/env python3
"""Shell command parsing shared by the guards.

Deciding what a command DOES means looking at what is executed, not at which words
it contains -- the lesson of the first destructive guard, which refused
`wipefs /dev/null` and every commit message that merely named a tool. Each guard
that has to read a command uses these pieces instead of re-deriving them: heredoc
bodies are text unless something consumes them as more, segments are split outside
quotes, and wrappers such as sudo or timeout are looked through.
"""
import re
import shlex

SHELLS = {'sh', 'bash', 'zsh', 'dash', 'ksh'}

# Programs that run another program. Value: the options that consume an argument.
WRAPPERS = {
    'sudo': {'-u', '-g', '-C', '-h', '-p', '-r', '-t', '-T', '-U', '-D', '-R'},
    'doas': {'-u', '-C'}, 'env': {'-u', '-C', '-S'}, 'nohup': set(), 'time': set(),
    'nice': {'-n'}, 'ionice': {'-c', '-n', '-p'}, 'timeout': {'-s', '-k'},
    'command': set(), 'exec': set(), 'stdbuf': {'-i', '-o', '-e'}, 'setsid': set(),
    'xargs': {'-I', '-n', '-P', '-L', '-d', '-s', '-E', '-a'}, 'watch': {'-n', '-d'},
}
SSH_OPTIONS_WITH_ARGUMENT = set('-b -c -D -E -e -F -I -i -J -L -l -m -O -o -p -Q -R -S -W -w'.split())

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
    """Separate heredoc bodies from the command. They are text -- unless something
    consumes them as more than text, which is for the caller to decide.

    Returns (command with bodies removed, [(consumer line, body), ...]).
    """
    bodies = []

    def drop(match):
        line_start = command.rfind('\n', 0, match.start()) + 1
        consumer = command[line_start:match.start()] + match.group(3)
        bodies.append((consumer, match.group(4)))
        return match.group(3) + '\n'

    return HEREDOC.sub(drop, command), bodies


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
