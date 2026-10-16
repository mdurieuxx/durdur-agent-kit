#!/usr/bin/env python3
"""Replayable proof that the destructive guard blocks what executes, and only that.

Two lists, both load-bearing. A guard tested only on what it must BLOCK drifts
toward blocking everything; the first version did, and a real session showed it
refusing `wipefs /dev/null` (a read-only listing) and would have refused every
commit message and heredoc that merely mentions these commands.

Run:  python3 tests/test_guard.py        exits non-zero on any failure.
"""
import json, os, subprocess, sys

HOOK = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'guard-destructive.sh')

MUST_BLOCK = [
    # block-device writes
    'sudo wipefs -a /dev/sdz', 'wipefs --all /dev/sdz', 'wipefs -o 0x0 /dev/sdz',
    'sudo sgdisk --zap-all /dev/sdf', 'sgdisk -n 1:0:0 -t 1:8300 /dev/sdf',
    'sudo sfdisk /dev/sdz', 'parted -s /dev/sdz mklabel gpt',
    'mkfs.ext4 -L x /dev/sdz1', 'sudo mkfs.ext4 -L recup -i 262144 /dev/sdf1', 'mkswap /dev/sdz2',
    'blkdiscard /dev/sdz', 'shred -n1 /dev/sdz',
    'dd if=/dev/zero of=/dev/sdz bs=1M', 'sudo dd of=/dev/sda if=img',
    'cat x > /dev/sdb', 'echo x | sudo tee /dev/nvme0n1',
    # piped confirmations
    # `yes |` is blocked in EVERY form, deliberately: it exists almost only to answer
    # a prompt, and a harmless use (`yes | head`) is rare enough that the opt-out
    # covers it. First listed under MUST_ALLOW on a guess -- the test was wrong, not the code.
    'yes | mkfs.ext4 /dev/sdz', 'yes | head -3', 'echo EFFACER | sudo ./wipe.sh', 'printf CONFIRM | ./destroy',
    # containers, git, deletes
    'docker system prune -af', 'docker volume rm foo', 'docker volume prune',
    'git push --force origin main', 'git push -f', 'git push --force-with-lease',
    'git clean -fd', 'rm -rf /volume1/DivX', 'rm -fr /home/x', 'sudo rm -rf /srv/fast/x',
    # hidden inside another command
    "sudo sh -c 'wipefs -a /dev/sdz'", "ssh nas 'sudo wipefs -a /dev/sdb'",
    'bash -c "mkfs.ext4 /dev/sdz1"', 'ssh -p 22 nas wipefs -a /dev/sdb',
    'timeout 600 sgdisk --zap-all /dev/sdz', 'VAR=1 sudo -u root wipefs -a /dev/sdz',
    "bash <<'EOF'\nwipefs -a /dev/sdz\nEOF", 'echo $(wipefs -a /dev/sdz)',
    'ls && wipefs -a /dev/sdz', 'true; sudo sgdisk --zap-all /dev/sdz',
]

MUST_ALLOW = [
    # read-only forms of the same tools
    'wipefs /dev/null', 'sudo wipefs /dev/sda', 'wipefs -n -a /dev/sda',
    'sudo sfdisk -l /dev/sdg', 'sfdisk -d /dev/sda', 'sgdisk -p /dev/sda',
    'parted -l', 'parted /dev/sda print', 'mkfs.ext4 -n /dev/sdz1',
    'mkfs.ext4 -V', 'sfdisk --version', 'sgdisk --help', 'wipefs --version',
    'dd if=/dev/sda of=image.img bs=4M', 'dd if=/dev/zero of=/mnt/usb/test bs=4M count=1',
    # the words, appearing as TEXT
    'git commit -m "fix: wipefs and mkfs docs"', 'grep -rn mkfs docs/',
    'echo "run wipefs -a later"', 'cat docs/wipefs.md',
    "cat > f <<'EOF'\nwipefs -a /dev/sdz\ndd if=/dev/zero of=/dev/sdz\nEOF",
    "sudo tee conf <<'EOF'\nwipefs -a\nmkfs.ext4 /dev/sdz\nEOF",
    "git commit -F - <<'EOF'\nfix: guard now allows wipefs listing\n\nwipefs and sfdisk finish fast.\nEOF",
    'python3 -c "print(\'docker system prune\')"', 'command -v wipefs', 'type mkfs.ext4',
    # unrelated and routine
    'ls -l /dev', 'lsblk', 'blockdev --setro /dev/sda', 'echo hi > /dev/null',
    'rm -rf /tmp/x', 'rm -rf /var/tmp/y/z', 'rm -rf build', 'docker builder prune',
    'docker ps', 'git push -u origin ma-branche', 'git clean -n', 'git status',
    'ls 2>/dev/null | grep -i usb',
]

def blocked(command):
    payload = json.dumps({'tool_input': {'command': command}, 'cwd': '/tmp'})
    env = {'PATH': os.environ['PATH'], 'HOME': '/nonexistent'}
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode == 2

failures = [('should BLOCK', c) for c in MUST_BLOCK if not blocked(c)]
failures += [('should ALLOW', c) for c in MUST_ALLOW if blocked(c)]
for verdict, command in failures:
    print(f"  FAIL {verdict}: {' '.join(command.split())[:90]}")
total = len(MUST_BLOCK) + len(MUST_ALLOW)
print(f"{total - len(failures)}/{total} passed ({len(MUST_BLOCK)} must block, {len(MUST_ALLOW)} must allow)")
sys.exit(1 if failures else 0)
