#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# Installs the kit's GIT hooks into this repository.
#
# ⚠️ These are git hooks, not agent hooks. They read the staged diff and the
# commit message ($1); hooks/hooks.json is a different mechanism entirely and
# declares only the two agent hooks. Confusing the two means wiring a commit
# hook where it will never run.
#
# Idempotent. Refuses to clobber an existing hook it did not write.
set -euo pipefail

KIT=$(cd "$(dirname "$0")/.." && pwd)
GITDIR=$(git rev-parse --git-dir 2>/dev/null) || { echo "not a git repository" >&2; exit 1; }
DEST="$GITDIR/hooks"
MARQUE="# installed by durdur-agent-kit"

mkdir -p "$DEST"

poser() {
    nom=$1; shift
    cible="$DEST/$nom"
    if [ -e "$cible" ] && ! grep -q "$MARQUE" "$cible" 2>/dev/null; then
        echo "  kept    $nom (exists and was not written by the kit -- merge by hand)"
        return 0
    fi
    {
        echo '#!/bin/sh'
        echo "$MARQUE"
        echo "KIT=\"$KIT\""
        for h in "$@"; do
            echo "\"\$KIT/hooks/$h\" \"\$@\" || exit 1"
        done
    } > "$cible"
    chmod +x "$cible"
    echo "  wired   $nom -> $*"
}

poser pre-commit enforce-feature-branch.sh english-only.sh no-assistant-in-code.sh no-literal-secret.sh
poser commit-msg no-assistant-attribution.sh tdd-test-parity.sh spec-before-code.sh

echo
echo "Project exclusions go in .claude/hook-exclusions, one glob per line."
echo "Escape hatch for a release cut:  RELEASE_CUT=1 git commit ..."
echo
echo "--- proving they fire ---"
if "$KIT/hooks/no-assistant-attribution.sh" /dev/null >/dev/null 2>&1; then
    tmp=$(mktemp); printf 'fix: thing\n\nCo-Authored-By: Claude <x@y>\n' > "$tmp"
    if "$KIT/hooks/no-assistant-attribution.sh" "$tmp" >/dev/null 2>&1; then
        echo "  ⛔ the attribution hook did NOT reject an AI co-author line"; rm -f "$tmp"; exit 1
    else
        echo "  ok: an AI co-author line is rejected"
    fi
    rm -f "$tmp"
fi
