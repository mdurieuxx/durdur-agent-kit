#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# commit-msg hook. Production code must name the spec it implements.
#
# No implementation without a spec written and committed first. Code written
# before its spec defines its own success criteria -- always correct, never
# checkable. The spec is what makes "done" falsifiable.
#
# Accepts, in the message:   Spec: <path or id>
# Accepts, staged:           a spec file in the same commit
# Explicit, traced override: SPEC-EXEMPT: <reason>
set -euo pipefail

MSG="${1:-}"
staged=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null) || staged=""
[ -n "$staged" ] || exit 0

prod=$(printf '%s\n' "$staged" \
  | grep -E '^(src|apps|packages|lib)/.*\.(py|ts|tsx|js|jsx|go|rs|dart|java|kt)$' \
  | grep -vE '(^|/)tests?/|(^|/)test_|_test\.|\.test\.|\.spec\.' || true)
[ -n "$prod" ] || exit 0

spec=$(printf '%s\n' "$staged" | grep -iE '(^|/)(spec|specs)/|\.spec\.md$|(^|/)docs/spec' || true)
[ -z "$spec" ] || exit 0

if [ -f "$MSG" ]; then
    grep -qiE '^Spec:[[:space:]]*\S' "$MSG" && exit 0
    if grep -qE '^SPEC-EXEMPT:[[:space:]]*\S' "$MSG"; then
        echo "! Spec requirement explicitly bypassed - the reason is in the message." >&2
        exit 0
    fi
fi

echo "x Commit rejected: production code with no spec." >&2
printf '%s\n' "$prod" | sed 's/^/    /' >&2
cat >&2 <<'TXT'
  No implementation without a spec written and committed first.
  Either stage the spec, or name it in the message:
      Spec: docs/spec/<name>.md
  Legitimate exception, traced:
      SPEC-EXEMPT: <reason>
TXT
exit 1
