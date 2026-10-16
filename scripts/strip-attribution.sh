#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# Produces a copy of a repository whose history carries no attribution trailer.
#
# SAFE BY CONSTRUCTION. It works on a clone and never touches the source; it never
# pushes; it writes a bundle of the original first, which is the way back; and it
# proves the rewrite changed messages only -- every branch tip must have the same
# file tree as before. Publishing the result is a separate act, taken by whoever
# owns the repository, with the command this prints. A force-push is irreversible
# for anyone who has already pulled, which is why it is not done here.
#
# usage: strip-attribution.sh <repository> [workdir]
set -euo pipefail

SRC=$(cd "${1:?usage: strip-attribution.sh <repository> [workdir]}" && pwd)
WORK=${2:-$(mktemp -d)}
NAME=$(basename "$SRC")
COPY="$WORK/$NAME-clean"
BUNDLE="$WORK/$NAME-original.bundle"
FILTER="$WORK/filter.py"
mkdir -p "$WORK"

git -C "$SRC" bundle create "$BUNDLE" --all >/dev/null 2>&1
git clone -q --no-local "$SRC" "$COPY"
for remote_branch in $(git -C "$COPY" branch -r | grep -v -- '->' | sed 's/^ *//'); do
    git -C "$COPY" branch -q --track "${remote_branch#origin/}" "$remote_branch" 2>/dev/null || true
done

cat > "$FILTER" <<'PY'
import re, sys
CREDIT = re.compile(r'^\s*Co-Authored-By:.*(claude|anthropic|copilot|chatgpt|openai|noreply@anthropic)', re.I)
GENERATED = re.compile(r'Generated with.*(Claude|Copilot|ChatGPT)', re.I)
lines = [l for l in sys.stdin.read().splitlines()
         if not (CREDIT.match(l) or GENERATED.search(l) or '🤖' in l)]
while lines and not lines[-1].strip():
    lines.pop()
sys.stdout.write('\n'.join(lines) + '\n')
PY

# Count on branches and tags only. `--all` would also count refs/original/, the copies
# filter-branch keeps of what it just rewrote, and report a failure that did not happen.
trailers() { git -C "$1" log --branches --tags --format=%B | grep -ciE '^[[:space:]]*Co-Authored-By:.*(claude|anthropic|copilot|chatgpt|openai)' || true; }
before=$(trailers "$COPY")
FILTER_BRANCH_SQUELCH_WARNING=1 git -C "$COPY" filter-branch -f \
    --msg-filter "python3 '$FILTER'" --tag-name-filter cat -- --branches --tags >/dev/null 2>&1
after=$(trailers "$COPY")
git -C "$COPY" for-each-ref --format='%(refname)' refs/original | xargs -r -n1 git -C "$COPY" update-ref -d

echo "repository        : $SRC"
echo "trailers          : $before -> $after"
echo "original bundle   : $BUNDLE"
echo "rewritten copy    : $COPY"

echo "branch tips (same file tree, count of commits):"
status=0
for branch in $(git -C "$COPY" for-each-ref --format='%(refname:short)' refs/heads/); do
    git -C "$SRC" rev-parse -q --verify "refs/heads/$branch" >/dev/null || continue
    old_tree=$(git -C "$SRC" rev-parse "refs/heads/$branch^{tree}")
    new_tree=$(git -C "$COPY" rev-parse "refs/heads/$branch^{tree}")
    old_n=$(git -C "$SRC" rev-list --count "refs/heads/$branch")
    new_n=$(git -C "$COPY" rev-list --count "refs/heads/$branch")
    if [ "$old_tree" = "$new_tree" ] && [ "$old_n" = "$new_n" ]; then verdict=ok; else verdict="DIFFERS"; status=1; fi
    printf '  %-28s %-8s %s commits\n' "$branch" "$verdict" "$new_n"
done
[ "$after" = 0 ] || { echo "WARNING: $after trailer(s) remain"; status=1; }
empty=$(git -C "$COPY" log --branches --tags --format=%s | grep -c '^$' || true)
[ "$empty" = 0 ] || { echo "WARNING: $empty commit message(s) became empty"; status=1; }

echo
echo "To publish -- the owner's decision, and irreversible for anyone who already pulled:"
echo "  cd $COPY && git push --force-with-lease --all \"\$(git -C $SRC remote get-url origin)\""
echo "  cd $COPY && git push --force --tags \"\$(git -C $SRC remote get-url origin)\"   # rewritten tags too"
echo "To go back:  git clone $BUNDLE restored"
exit $status
