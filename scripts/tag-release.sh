#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# Tags, pushes the tag, and publishes its notes in the same breath, so that a tag
# without notes cannot come out of this tool. A build tool that pushes tags calls
# release_notes.py --publish right after its own push, the same way.
# Usage: tag-release.sh <tag> [artifact] [remote]
set -euo pipefail
tag=${1:?usage: tag-release.sh <tag> [artifact] [remote]}
artifact=${2:-}
remote=${3:-origin}
here=$(cd "$(dirname "$0")" && pwd)
notes() { python3 "$here/release_notes.py" "$tag" ${artifact:+--artifact "$artifact"} "$@"; }
git tag -a "$tag" -m "$tag"
# dry run on the local tag: a bad name or a missing component folder must fail BEFORE the push
notes >/dev/null || { git tag -d "$tag" >/dev/null; exit 1; }
git push "$remote" "$tag"
notes --publish
