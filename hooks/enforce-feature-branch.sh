#!/usr/bin/env bash
#
# Rejects a direct commit on a protected branch.
# Origin: a fix chained straight onto a production branch at the end of a
# session, afterwards only correctable through a public force-push.
#
# Escape hatch for a release cut, which commits on protected branches by
# design: export RELEASE_CUT so this hook can tell that apart from an
# accidental commit.
# The escape hatch is deliberately ONE neutral name: a per-project variable
# (KART_RELEASE_CUT, KFORGE_RELEASE_CUT) means a shared hook does not recognise
# the release cut of the project it runs in.
set -euo pipefail

[ -n "${RELEASE_CUT:-}" ] && exit 0

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"

if [[ "$branch" =~ ^(main|master|develop)$ ]]; then
  echo "x Commit rejected: protected branch \"$branch\"." >&2
  echo "  Always a feature branch, docs-only changes included." >&2
  echo "  git switch -c feature/<id>-<subject>" >&2
  exit 1
fi
