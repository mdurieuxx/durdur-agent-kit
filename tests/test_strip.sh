#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# End-to-end test of scripts/strip-attribution.sh on a throwaway repository set that lives
# in a temp directory and is deleted at the end. Nothing here touches a real repository.
#
# Scenario: an upstream (whose own commit carries a trailer and must NOT be rewritten), a
# published fork with trailers on main and a feature branch, a human co-author that must
# survive, a tag, and a local-only branch that must never be offered for publication.
#
# STRIP_SCRIPT overrides the script under test (used to prove this test can fail).
set -uo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
SCRIPT=${STRIP_SCRIPT:-$HERE/scripts/strip-attribution.sh}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.test GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.test
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $1 (got '$2', want '$3')"; fi; }
has() { if grep -qE -- "$2" <<<"$3"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $1 (no match for '$2')"; fi; }
hasnt() { if grep -qE -- "$2" <<<"$3"; then fail=$((fail+1)); echo "FAIL: $1 (unexpected '$2')"; else pass=$((pass+1)); fi; }
count() { git -C "$1" log --branches --tags --format=%B | grep -ciE '^[[:space:]]*Co-Authored-By:.*(claude|anthropic|copilot|chatgpt|openai)' || true; }
commit() { echo "$1" >> "$2"; git add "$2"; git commit -q -m "$1" -m "${3:-}"; }

# upstream: one commit that carries a trailer (not the user's, must stay as it is)
git init -q --bare -b main "$T/up.git"; git clone -q "$T/up.git" "$T/up" 2>/dev/null
( cd "$T/up" && git checkout -q -b main && commit upstream-1 f "Co-Authored-By: Claude <noreply@anthropic.com>" && git push -q origin main )
UP_SHA=$(git -C "$T/up" rev-parse HEAD)

# the published fork
git clone -q --bare "$T/up.git" "$T/fork.git"
git clone -q "$T/fork.git" "$T/work" 2>/dev/null
( cd "$T/work"
  commit mine-1 f $'Co-Authored-By: Claude Sonnet <noreply@anthropic.com>'
  commit mine-2 f $'Real body.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>'
  commit mine-3 f $'Pairing.\n\nCo-Authored-By: Jane Doe <jane@example.test>'
  commit mine-4 f
  git tag v1 HEAD~1
  git checkout -q -b feat && commit feat-1 g $'Co-Authored-By: GitHub Copilot <copilot@example.test>'
  git push -q origin main feat v1 )
git -C "$T/work" checkout -q -b private main
( cd "$T/work" && commit private-1 h $'Co-Authored-By: Claude <noreply@anthropic.com>' )   # never pushed
FORK_MAIN=$(git -C "$T/fork.git" rev-parse main); FORK_FEAT=$(git -C "$T/fork.git" rev-parse feat)
BEFORE_REMOTE=$(git -C "$T/fork.git" for-each-ref --format='%(refname) %(objectname)')

# witness: the fixture really does carry trailers, otherwise a zero below proves nothing
check "witness: fixture has trailers" "$(count "$T/work")" "5"

# 1. fork by URL, upstream protected, then the same working copy by path
OUT=$(STRIP_KEEP_URL="file://$T/up.git" STRIP_KEEP_BRANCH=main bash "$SCRIPT" "file://$T/fork.git" "$T/w1" 2>&1); RC=$?
check "exit status (URL mode)" "$RC" "0"
CLEAN="$T/w1/fork-clean"
check "only the upstream's own trailer remains" "$(count "$CLEAN")" "1"
check "upstream commit untouched" "$(git -C "$CLEAN" rev-parse main~4 2>/dev/null)" "$UP_SHA"
has   "human co-author survives" "Jane Doe" "$(git -C "$CLEAN" log --branches --format=%B)"
hasnt "no robot line left" "🤖|Generated with" "$(git -C "$CLEAN" log --branches --tags --format=%B)"
check "tree of main unchanged" "$(git -C "$CLEAN" rev-parse main^{tree})" "$(git -C "$T/fork.git" rev-parse main^{tree})"
check "tree of feat unchanged" "$(git -C "$CLEAN" rev-parse feat^{tree})" "$(git -C "$T/fork.git" rev-parse feat^{tree})"
check "commit count of main unchanged" "$(git -C "$CLEAN" rev-list --count main)" "$(git -C "$T/fork.git" rev-list --count main)"
check "the tag moved with the history" "$(git -C "$CLEAN" log -1 --format=%s v1)" "mine-3"
check "no refs/original left behind" "$(git -C "$CLEAN" for-each-ref refs/original | wc -l | tr -d ' ')" "0"
check "bundle written" "$([ -s "$T/w1/fork-original.bundle" ] && echo yes)" "yes"
check "the source remote is untouched" "$(git -C "$T/fork.git" for-each-ref --format='%(refname) %(objectname)')" "$BEFORE_REMOTE"
has   "leased push for main" "force-with-lease=main:$FORK_MAIN" "$OUT"
has   "leased push for feat" "force-with-lease=feat:$FORK_FEAT" "$OUT"
has   "leased push for the tag" "force-with-lease=refs/tags/v1:" "$OUT"
hasnt "never a blanket push" "push (--all|--mirror)|--force( |$)" "$OUT"

# 2. the working copy by path: the private branch is rewritten but must not be offered
OUT2=$(STRIP_KEEP_URL="file://$T/up.git" STRIP_KEEP_BRANCH=main bash "$SCRIPT" "$T/work" "$T/w2" 2>&1); RC2=$?
check "exit status (path mode)" "$RC2" "0"
has   "private branch reported local only" "private .*local only" "$OUT2"
hasnt "private branch never in a push command" "refs/heads/private" "$(grep 'force-with-lease' <<<"$OUT2")"

# 3. a remote whose HEAD names a branch that does not exist (filter-branch fails on it)
git -C "$T/fork.git" symbolic-ref HEAD refs/heads/gone
OUT3=$(STRIP_KEEP_URL="file://$T/up.git" STRIP_KEEP_BRANCH=main bash "$SCRIPT" "file://$T/fork.git" "$T/w3" 2>&1); RC3=$?
check "unborn HEAD does not abort" "$RC3" "0"

# 4. a history with no trailer: nothing to rewrite, nothing to push
git init -q -b main "$T/clean"; ( cd "$T/clean" && git checkout -q -b main && commit one f )
OUT4=$(bash "$SCRIPT" "$T/clean" "$T/w4" 2>&1); RC4=$?
check "clean history exits 0" "$RC4" "0"
has   "clean history: nothing to publish" "Nothing to publish" "$OUT4"

echo "$pass/$((pass+fail)) passed"
[ "$fail" = 0 ]
