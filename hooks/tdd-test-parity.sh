#!/usr/bin/env bash
#
# Does not prove TDD, which is impossible after the fact. Catches the blatant
# case: production code added with no test in the same commit.
# Explicit, traced override: TDD-EXEMPT: <reason> in the message.
set -euo pipefail

staged="$(git diff --cached --name-only --diff-filter=AM || true)"
prod="$(printf '%s\n' "$staged" \
  | grep -E '^(src|apps|packages)/.*\.(py|ts|tsx|dart)$' \
  | grep -vE '(^|/)tests?/|(^|/)test_|_test\.|\.test\.' || true)"
tests="$(printf '%s\n' "$staged" \
  | grep -E '(^|/)tests?/|(^|/)test_|_test\.|\.test\.' || true)"

[ -z "$prod" ] && exit 0
[ -n "$tests" ] && exit 0

msg_file="${1:-}"
if [ -f "$msg_file" ] && grep -q '^TDD-EXEMPT:' "$msg_file"; then
  echo "! TDD explicitly bypassed - the reason is in the message." >&2
  exit 0
fi

echo "x Commit rejected: production code with no test in the same commit." >&2
printf '%s\n' "$prod" | sed 's/^/    /' >&2
echo "  Red first. If this is legitimate: TDD-EXEMPT: <reason>" >&2
exit 1
