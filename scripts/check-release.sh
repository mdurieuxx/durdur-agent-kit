#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# Fails when a release tag has no release (or an empty one) on the forge.
# Usage: check-release.sh <tag>   (needs gh, authenticated)
#
# The check behind scripts/release_notes.py: the tool that tags publishes the
# notes, and this proves that nothing got a tag around it (a plain `git push --tags`).
# Run by .github/workflows/release-notes.yml on every pushed tag.
set -uo pipefail
tag=${1:?usage: check-release.sh <tag>}
body=$(gh release view "$tag" --json body -q .body 2>/dev/null) || {
    echo "x $tag has no release: run  scripts/release_notes.py $tag --publish" >&2; exit 1; }
[ -n "${body//[[:space:]]/}" ] || { echo "x the release of $tag has empty notes" >&2; exit 1; }
echo "ok: $tag carries its notes"
