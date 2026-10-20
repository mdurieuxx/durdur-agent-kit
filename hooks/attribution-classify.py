#!/usr/bin/env python3
"""Does this command PUBLISH text that attributes the work to a tool?

Reads a shell command on stdin. If it would publish a commit message, tag, merge
message or pull-request text carrying an attribution, prints the offending lines
and exits 2; otherwise exits 0.

WHY THIS EXISTS. The user's rule is absolute: nothing published names or credits
the tool that wrote it. The harness's default instruction is the opposite, and
the default wins wherever the rule is not loaded: measured on the repositories
of one machine, 62 of 69 commits in one project and 46 of 64 in another carry the
trailer. So the rule travels with the plugin and is enforced where the text is
about to leave, rather than hoped for.

It reads the message from where it actually is -- an -m value, a file given with
-F, a heredoc fed to the command -- and ignores the same words anywhere else, so
a heredoc that merely DOCUMENTS the trailer, or a grep for it, is not refused.
"""
import re
import sys
from pathlib import Path

from shellparse import real_command, split_heredocs, split_segments, tokenize

TRAILER = re.compile(r'^\s*Co-Authored-By:.*(claude|anthropic|copilot|chatgpt|openai|noreply@anthropic)',
                     re.I | re.M)
# Naming the tool at all. Case-sensitive "Claude" and not inside a path, so
# `.claude/hooks` and `claude-dev-template` are not mistaken for the assistant.
MENTION = re.compile(r'(?<![./\w-])Claude(?![\w-])|\bAnthropic\b|\bCopilot\b|\bChatGPT\b|\bOpenAI\b'
                     r'|generated (by|with)\b.{0,30}\b(AI|Claude|Copilot|ChatGPT)\b|AI-generated|🤖')

GIT_PUBLISHING = {'commit', 'tag', 'merge'}
GH_PUBLISHING = {('pr', 'create'), ('pr', 'edit'), ('pr', 'merge')}
GIT_GLOBAL_OPTIONS_WITH_ARGUMENT = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}
TEXT_OPTIONS = {'--message', '--body', '--title', '--subject'}
FILE_OPTIONS = {'--file', '--body-file'}


def inline_text(args):
    """Values of -m / --message / --body / --title, in every spelling they come in."""
    found = []
    for position, arg in enumerate(args):
        name, _, attached = arg.partition('=')
        if name in TEXT_OPTIONS and attached:
            found.append(attached)
        elif name in TEXT_OPTIONS and position + 1 < len(args):
            found.append(args[position + 1])
        elif re.fullmatch(r'-[A-Za-z]*[mbt]', arg) and position + 1 < len(args):
            found.append(args[position + 1])          # -m "x", -am "x", -b "x", -t "x"
        elif re.match(r'^-[mbt].+', arg) and not arg.startswith('--'):
            found.append(arg[2:])                      # -m"x"
    return found


def file_arguments(args):
    """Paths given with -F / --file / --body-file; '-' means standard input."""
    found = []
    for position, arg in enumerate(args):
        name, _, attached = arg.partition('=')
        if name in FILE_OPTIONS and attached:
            found.append(attached)
        elif (name in FILE_OPTIONS or arg in ('-F',)) and position + 1 < len(args):
            found.append(args[position + 1])
    return found


def published_text(program, args, heredoc_bodies):
    """Everything this one command would publish, or [] if it publishes nothing."""
    if program == 'git':
        position = 0
        while position < len(args) and args[position].startswith('-'):
            position += 2 if args[position] in GIT_GLOBAL_OPTIONS_WITH_ARGUMENT else 1
        if position >= len(args) or args[position] not in GIT_PUBLISHING:
            return []
        args = args[position + 1:]
    elif program == 'gh':
        words = [a for a in args if not a.startswith('-')]
        if tuple(words[:2]) not in GH_PUBLISHING:
            return []
    else:
        return []

    texts = inline_text(args)
    for path in file_arguments(args):
        if path == '-':
            texts += heredoc_bodies          # `git commit -F - <<'EOF'`
        elif Path(path).is_file():
            texts.append(Path(path).read_text(encoding='utf-8', errors='replace'))
    return texts


def offending_lines(text):
    return [line.strip() for line in text.splitlines() if TRAILER.search(line) or MENTION.search(line)]


def main():
    command, bodies = split_heredocs(sys.stdin.read())
    heredoc_texts = [body for _, body in bodies]
    for segment, _ in split_segments(command):
        program, args = real_command(tokenize(segment))
        for text in published_text(program, args, heredoc_texts) if program else []:
            lines = offending_lines(text)
            if lines:
                print('\n'.join(lines))
                sys.exit(2)


if __name__ == '__main__':
    main()
