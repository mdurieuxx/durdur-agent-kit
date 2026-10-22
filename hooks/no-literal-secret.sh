#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# commit-msg hook. Refuses what looks like a literal secret in staged content.
#
# It runs at commit-msg, not pre-commit, so that the override below can be read:
# the message does not exist yet when pre-commit runs, so a `SECRET-OK:` given
# with `git commit -m` / `-F` was never seen and the commit stayed refused. The
# staged diff is already complete at that point. Run without an argument (an old
# pre-commit wiring, until the installer is run again) only the inline override works.
#
# A secret value is never versioned: the reference is, the value is not. And
# .gitignore does NOT act on an already-tracked file -- a value committed once
# must be revoked, not merely ignored. That is why this fires before the commit.
#
# Origin: a missing secret broke a deployment three times in one session, and a
# database password is versioned in clear in an infrastructure repository to
# this day. Review caught neither.
#
# Only a VALUE is flagged: a quoted literal right after `:` or `=`, as in
# `token = "..."`. A call or an attribute (`os.environ.get("X")`, `cfg.api_key`)
# is a reference and passes -- the first version took any 12 characters for a
# value and refused both, which pushed people to rename variables to satisfy it.
# In files that hold only configuration (.env, yaml, ini, toml ...) a value is
# usually unquoted, so there an unquoted value counts too.
#
# Deliberate, traced overrides, either one:
#   - `SECRET-OK: <reason>` in the commit message
#   - `SECRET-OK: <reason>` in a comment on the line itself
set -uo pipefail
. "$(dirname "$0")/lib-exclusions.sh"
EXCL=$(exclusions_regex)

staged=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null) || staged=""
[ -n "$staged" ] || exit 0

# Shapes, not a dictionary of provider names: a dictionary is always one
# provider behind.
KEYS='(api[_-]?key|secret|token|passwd|password|pwd)'
VALUE='[A-Za-z0-9/+_.-]{12,}'
RX='(aws_secret_access_key|BEGIN [A-Z ]*PRIVATE KEY)'
RX="$RX|($KEYS[\"']?[[:space:]]*[:=][[:space:]]*[\"']$VALUE)"
RX="$RX|(gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,})"
RX="$RX|([a-z]+://[^/[:space:]]+:[^@/[:space:]]+@)"
RX_CONF="$KEYS[\"']?[[:space:]]*[:=][[:space:]]*$VALUE"
OVERRIDE='SECRET-OK:[[:space:]]*[^[:space:]]'

hits=""
while IFS= read -r f; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    printf '%s' "$f" | grep -qE "$EXCL" && continue
    case "$f" in
        *.example|*.sample|*.md) continue ;;
        .claude/hooks/*|hooks/*) continue ;;
    esac
    rx=$RX
    case "$f" in
        .env|.env.*|*/.env.*|*.env|*.ini|*.cfg|*.conf|*.toml|*.yaml|*.yml|*.properties) rx="$RX|($RX_CONF)" ;;
    esac
    m=$(grep -inE "$rx" "$f" 2>/dev/null | grep -vE "$OVERRIDE" | head -3) || true
    [ -n "$m" ] && hits="$hits$(printf '%s' "$m" | sed "s|^|    $f:|")"$'\n'
done <<< "$staged"

[ -n "$hits" ] || exit 0

MSG="${1:-}"
if [ -f "$MSG" ] && grep -qE "^$OVERRIDE" "$MSG" 2>/dev/null; then
    echo "! Literal-secret check explicitly bypassed - reason is in the message." >&2
    exit 0
fi

echo "x Commit rejected: what looks like a literal secret." >&2
printf '%s' "$hits" | cut -c1-140 >&2
cat >&2 <<'TXT'
  Version the reference, never the value.
  False positive:  SECRET-OK: <reason>   in the commit message (needs the commit-msg
                   hook: run scripts/install-git-hooks.sh again) or in a comment on the line
  If a real value was ever committed it must be REVOKED -- .gitignore does not
  act on an already-tracked file.
TXT
exit 1
