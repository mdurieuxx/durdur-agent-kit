#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# Writes ~/.claude/owned-owners from what GitHub says, once, if it does not exist.
#
# "Belongs to the user" is MEASURED: their own account, and the organisations where they
# are admin. Write access to someone else's repository is not ownership -- the case that
# prompted the rule was a repository under another person's account, on which the user
# had WRITE. Organisations where they are only a member are listed as comments, off.
#
# Never overwrites an existing list: that file is the user's decision, not this script's.
set -uo pipefail
LIST="${HOUSE_RULES_OWNED:-$HOME/.claude/owned-owners}"
[ -e "$LIST" ] && { echo "$LIST already exists, left as it is"; exit 0; }
command -v gh >/dev/null && ME=$(timeout 8 gh api user --jq .login 2>/dev/null) && [ -n "$ME" ] || {
    echo "cannot read the GitHub account (gh missing or not logged in): $LIST not created" >&2; exit 1; }

mkdir -p "$(dirname "$LIST")"
{
    echo "# Owners whose repositories belong to you. The ownership guard refuses to commit, push"
    echo "# or open anything on a repository whose remote owner is not listed here."
    echo "# Seeded from GitHub on $(date +%F): your account, and organisations where you are ADMIN."
    echo "# Edit it yourself. The agent must never add a line to get past a block."
    echo "github.com/$(echo "$ME" | tr 'A-Z' 'a-z')"
    for org in $(timeout 8 gh api user/orgs --jq '.[].login' 2>/dev/null); do
        role=$(timeout 8 gh api "orgs/$org/memberships/$ME" --jq .role 2>/dev/null || echo unknown)
        if [ "$role" = admin ]; then echo "github.com/$(echo "$org" | tr 'A-Z' 'a-z')"
        else echo "# github.com/$(echo "$org" | tr 'A-Z' 'a-z')   (role: $role -- member only, not enabled)"; fi
    done
} > "$LIST"
echo "created $LIST"
