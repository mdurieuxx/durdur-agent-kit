#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# pre-commit hook. Refuses what looks like a literal secret in staged content.
#
# A secret value is never versioned: the reference is, the value is not. And
# .gitignore does NOT act on an already-tracked file -- a value committed once
# must be revoked, not merely ignored. That is why this fires before the commit.
#
# Origin: a missing secret broke a deployment three times in one session, and a
# database password is versioned in clear in an infrastructure repository to
# this day. Review caught neither.
#
# Deliberate, traced override: SECRET-OK: <reason> in the commit message.
set -uo pipefail
. "$(dirname "$0")/lib-exclusions.sh"
EXCL=$(exclusions_regex)

staged=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null) || staged=""
[ -n "$staged" ] || exit 0

# Shapes, not a dictionary of provider names: a dictionary is always one
# provider behind.
RX='(aws_secret_access_key|BEGIN [A-Z ]*PRIVATE KEY)'
RX="$RX|((api[_-]?key|secret|token|passwd|password|pwd)[\"'[:space:]]*[:=][\"'[:space:]]*[A-Za-z0-9/+_.-]{12,})"
RX="$RX|(gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,})"
RX="$RX|([a-z]+://[^/[:space:]]+:[^@/[:space:]]+@)"

hits=""
while IFS= read -r f; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    printf '%s' "$f" | grep -qE "$EXCL" && continue
    case "$f" in
        *.example|*.sample|*.md) continue ;;
        .claude/hooks/*|hooks/*) continue ;;
    esac
    m=$(grep -inE "$RX" "$f" 2>/dev/null | head -3) || true
    [ -n "$m" ] && hits="$hits$(printf '%s' "$m" | sed "s|^|    $f:|")"$'\n'
done <<< "$staged"

[ -n "$hits" ] || exit 0

MSG="${1:-}"
if [ -f "$MSG" ] && grep -qE '^SECRET-OK:[[:space:]]*\S' "$MSG" 2>/dev/null; then
    echo "! Literal-secret check explicitly bypassed - reason is in the message." >&2
    exit 0
fi

echo "x Commit rejected: what looks like a literal secret." >&2
printf '%s' "$hits" | cut -c1-140 >&2
cat >&2 <<'TXT'
  Version the reference, never the value.
  False positive:  SECRET-OK: <reason>
  If a real value was ever committed it must be REVOKED -- .gitignore does not
  act on an already-tracked file.
TXT
exit 1
