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
# usage: strip-attribution.sh <repository-path | remote-url> [workdir]
#
# A URL rewrites what is PUBLISHED: the repository is cloned fresh, so every branch tip is
# exactly the remote's. A path rewrites a working copy, which may hold local-only branches
# or lag behind its remote -- the report says which branches are safe to publish.
#
# For a fork, STRIP_KEEP_URL (and STRIP_KEEP_BRANCH, default main) names the upstream
# whose commits are not the user's: they are left untouched, and only commits after them
# are rewritten.
set -euo pipefail

TARGET=${1:?usage: strip-attribution.sh <repository-path | remote-url> [workdir]}
WORK=${2:-$(mktemp -d)}
mkdir -p "$WORK"
case "$TARGET" in
    https://*|git@*|ssh://*|file://*)
        NAME=$(basename "${TARGET%.git}")
        SRC="$WORK/$NAME-source"
        git clone -q "$TARGET" "$SRC"
        for remote_branch in $(git -C "$SRC" branch -r | grep -v -- '->' | sed 's/^ *//'); do
            git -C "$SRC" branch -q --track "${remote_branch#origin/}" "$remote_branch" 2>/dev/null || true
        done ;;
    *)
        SRC=$(cd "$TARGET" && pwd)
        NAME=$(basename "$SRC") ;;
esac
COPY="$WORK/$NAME-clean"
BUNDLE="$WORK/$NAME-original.bundle"
FILTER="$WORK/filter.py"

NOT_MINE=()
if [ -n "${STRIP_KEEP_URL:-}" ]; then
    git -C "$SRC" fetch -q "$STRIP_KEEP_URL" "${STRIP_KEEP_BRANCH:-main}"
    KEEP_SHA=$(git -C "$SRC" rev-parse FETCH_HEAD)
    NOT_MINE=("^$KEEP_SHA")   # filter-branch rejects --not; the caret form is the documented one
fi

git -C "$SRC" bundle create "$BUNDLE" --all >/dev/null 2>&1
git clone -q --no-local "$SRC" "$COPY"
for remote_branch in $(git -C "$COPY" branch -r | grep -v -- '->' | sed 's/^ *//'); do
    git -C "$COPY" branch -q --track "${remote_branch#origin/}" "$remote_branch" 2>/dev/null || true
done

# filter-branch refuses a repository whose HEAD points at nothing, and says only "Needed a
# single revision". A remote whose default branch is not the one HEAD names does this.
if ! git -C "$COPY" rev-parse -q --verify HEAD >/dev/null; then
    git -C "$COPY" checkout -q "$(git -C "$COPY" for-each-ref --format='%(refname:short)' refs/heads/ | head -1)"
fi

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
# The output is kept, not discarded: a first version silenced this command, it failed on a
# flag it did not accept, and `set -e` ended the script with no word on why.
if ! FILTER_BRANCH_SQUELCH_WARNING=1 git -C "$COPY" filter-branch -f \
        --msg-filter "python3 '$FILTER'" --tag-name-filter cat -- --branches --tags "${NOT_MINE[@]}" \
        >"$WORK/filter-branch.log" 2>&1; then
    tail -5 "$WORK/filter-branch.log" >&2
    echo "filter-branch failed; log: $WORK/filter-branch.log" >&2
    exit 2
fi
after=$(trailers "$COPY")
# Commits kept as they were (an upstream's) may legitimately still carry the trailer.
kept=0
[ -z "${KEEP_SHA:-}" ] || kept=$(git -C "$COPY" log "$KEEP_SHA" --format=%B | grep -ciE '^[[:space:]]*Co-Authored-By:.*(claude|anthropic|copilot|chatgpt|openai)' || true)
git -C "$COPY" for-each-ref --format='%(refname)' refs/original | xargs -r -n1 git -C "$COPY" update-ref -d

echo "repository        : $SRC"
echo "trailers          : $before -> $after$([ "$kept" = 0 ] || echo "   ($kept in upstream commits, left untouched)")"
echo "original bundle   : $BUNDLE"
echo "rewritten copy    : $COPY"

# What is published, branch by branch. A rewrite may only be pushed over a branch whose
# remote tip IS the commit this copy was made from; anything else would publish a private
# branch, or move a remote branch backwards and drop commits this copy never saw.
declare -A REMOTE_TIP
URL=$(git -C "$SRC" remote get-url origin 2>/dev/null || true)
if [ -n "$URL" ]; then
    while read -r sha ref; do REMOTE_TIP["${ref#refs/heads/}"]=$sha; done \
        < <(git -C "$SRC" ls-remote --heads origin 2>/dev/null || true)
fi

echo "branches (file tree, commits, and whether the rewrite may be published):"
status=0
PUSHES=()
for branch in $(git -C "$COPY" for-each-ref --format='%(refname:short)' refs/heads/); do
    git -C "$SRC" rev-parse -q --verify "refs/heads/$branch" >/dev/null || continue
    old_tip=$(git -C "$SRC" rev-parse "refs/heads/$branch")
    old_tree=$(git -C "$SRC" rev-parse "refs/heads/$branch^{tree}")
    new_tree=$(git -C "$COPY" rev-parse "refs/heads/$branch^{tree}")
    old_n=$(git -C "$SRC" rev-list --count "refs/heads/$branch")
    new_n=$(git -C "$COPY" rev-list --count "refs/heads/$branch")
    if [ "$old_tree" = "$new_tree" ] && [ "$old_n" = "$new_n" ]; then verdict=ok; else verdict=DIFFERS; status=1; fi
    new_tip=$(git -C "$COPY" rev-parse "refs/heads/$branch")
    if [ "$new_tip" = "$old_tip" ]; then
        publish="unchanged -- nothing on it to rewrite, nothing to push"
    elif [ -z "${REMOTE_TIP[$branch]:-}" ]; then
        publish="local only -- never published, keep it private"
    elif [ "${REMOTE_TIP[$branch]}" = "$old_tip" ]; then
        publish="publishable (remote tip matches this copy)"
        PUSHES+=("git -C $COPY push --force-with-lease=$branch:${REMOTE_TIP[$branch]} $URL refs/heads/$branch:refs/heads/$branch")
    else
        publish="DIVERGED from remote -- do not push: it would drop or rewrite commits this copy never saw"
    fi
    printf '  %-26s %-8s %5s commits   %s\n' "$branch" "$verdict" "$new_n" "$publish"
done
[ "$after" = "$kept" ] || { echo "WARNING: $after trailer(s) remain, expected $kept"; status=1; }
empty=$(git -C "$COPY" log --branches --tags --format=%s | grep -c '^$' || true)
[ "$empty" = 0 ] || { echo "WARNING: $empty commit message(s) became empty"; status=1; }

# Tags: a rewritten history leaves each tag on its old commit unless it is moved too.
declare -A REMOTE_TAG
while read -r sha ref; do REMOTE_TAG["${ref#refs/tags/}"]=$sha; done \
    < <(git -C "$SRC" ls-remote --tags origin 2>/dev/null | grep -v '\^{}' || true)
for tag in "${!REMOTE_TAG[@]}"; do
    new=$(git -C "$COPY" rev-parse -q --verify "refs/tags/$tag" || true)
    old=$(git -C "$SRC" rev-parse -q --verify "refs/tags/$tag" || true)
    if [ -n "$new" ] && [ "$new" != "$old" ] && [ "$old" = "${REMOTE_TAG[$tag]}" ]; then
        PUSHES+=("git -C $COPY push --force-with-lease=refs/tags/$tag:${REMOTE_TAG[$tag]} $URL refs/tags/$tag:refs/tags/$tag")
    fi
done

echo
if [ "${#PUSHES[@]}" -gt 0 ]; then
    echo "To publish -- the owner's decision, irreversible for anyone who already pulled."
    echo "One command per publishable branch, each leased on the remote tip read just now:"
    printf '  %s\n' "${PUSHES[@]}"
else
    echo "Nothing to publish: no branch is both rewritten and in sync with its remote."
fi
echo "Then, in every clone: move the local branch refs (git update-ref <ref> <new> <old>) rather than pulling --"
echo "a pull would merge the old and the new history and bring the trailers back."
echo "To go back:  git clone $BUNDLE restored"
exit $status
