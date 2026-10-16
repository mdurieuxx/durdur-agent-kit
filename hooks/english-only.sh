#!/usr/bin/env bash
#
# Rejects accented Latin characters in source and documentation. Catches the
# common case (French comments) without a language detector.
#
# The Latin-1 Supplement block holds two characters that are not letters and
# are legitimate in English: MULTIPLICATION SIGN and DIVISION SIGN. They are
# excluded by byte. Found by the hook firing on "x1, xN" written with the
# multiplication sign - the first version of this comment claimed the check
# never fires on English, which was wrong.
#
# Uses perl, not `grep -P`: BSD grep on macOS has no -P and the failure is
# silent when stderr is discarded. Portability beats elegance in a hook that
# runs on every machine.
#
# Exceptions are data or deliberately transitional, never source:
# Exclusions are NOT hard-coded here: a project declares its own in
# .claude/hook-exclusions (see lib-exclusions.sh). Files named *.<locale>.md or
# *.<locale>.json are always excluded -- that is where other languages belong.
. "$(dirname "$0")/lib-exclusions.sh"
EXCL=$(exclusions_regex)
set -euo pipefail

staged="$(git diff --cached --name-only --diff-filter=AM \
  | grep -E '\.(py|ts|tsx|js|md|sh|sql|yml|yaml|dart)$' \
  | grep -vE "$EXCL" | grep -vE '\.[a-z]{2}\.(md|json)$' || true)"

[ -z "$staged" ] && exit 0

hits=""
while IFS= read -r f; do
  [ -n "$f" ] && [ -f "$f" ] || continue
  if perl -ne 'exit 1 if /\xc3[\x80-\x96\x98-\xb6\xb8-\xbf]|\xc4[\x80-\xbf]/' "$f"; then :; else
    hits="$hits$f"$'\n'
  fi
done <<< "$staged"

if [ -n "$hits" ]; then
  echo "x Commit rejected: non-English text in versioned files." >&2
  printf '%s' "$hits" | sed 's/^/    /' >&2
  echo "  Everything committed is written in English." >&2
  exit 1
fi
