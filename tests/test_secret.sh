#!/bin/bash
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@" # started with sh (dash): re-exec
#
# End-to-end test of hooks/no-literal-secret.sh on a throwaway repository (a temp
# directory, deleted at the end). Two lists, as for the guard: what must be refused
# (a value) and what must pass (a reference), and the two overrides.
#
# HOOK_DIR overrides the directory holding the hook under test (used to prove this
# test can fail, by running it against the version before the fix).
set -uo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
HOOK=${HOOK_DIR:-$HERE/hooks}/no-literal-secret.sh
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.test GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.test
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $1 (got '$2', want '$3')"; fi; }

git init -q "$T/r"; cd "$T/r"

# exit status of the hook on a staged file with this content; $3 = message file, if any
run() {
    git rm -q --cached -rf . >/dev/null 2>&1; rm -rf ./* .env* 2>/dev/null
    mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; git add -f "$1"
    "$HOOK" ${3:+"$3"} >/dev/null 2>&1; echo $?
}

MUST_REFUSE=(
    'app.py|token = "abcdef0123456789abcd"'
    'app.py|api_key="abcdef0123456789abcd"'
    "app.py|PASSWORD: 'hunter2hunter2hunter2'"
    'app.py|{"secret": "abcdef0123456789abcd"}'
    'app.py|aws_secret_access_key'
    'app.py|ghp_abcdefghijklmnopqrstuvwx'
    'app.py|url = "postgres://user:pw12345678@db/x"'
    '.env|DB_PASSWORD=hunter2hunter2hunter2'
    'conf/app.yaml|token: abcdef0123456789abcd'
    'conf/.env.prod|API_KEY=abcdef0123456789abcd'
)
MUST_PASS=(
    'app.py|url, token = os.environ.get("BRAIN_URL"), os.environ.get("BRAIN_TOKEN")'
    'app.py|api_key=cfg.litellm_api_key'
    'app.py|token = os.environ["BRAIN_TOKEN_NAME"]'
    'app.py|if token == "abcdef0123456789abcd": pass'
    'app.py|password = ""'
    'app.py|token = "short"'
    '.env|DB_PASSWORD=${DB_PASSWORD_FROM_VAULT}'
    'conf/app.yaml|token: ${{ secrets.DEPLOY_TOKEN }}'
    'app.py|token = "abcdef0123456789abcd"  # SECRET-OK: test fixture'
    '.env.example|DB_PASSWORD=hunter2hunter2hunter2'
    'README.md|token = "abcdef0123456789abcd"'
)

for c in "${MUST_REFUSE[@]}"; do check "refuses: ${c#*|}" "$(run "${c%%|*}" "${c#*|}")" 1; done
for c in "${MUST_PASS[@]}";   do check "passes:  ${c#*|}" "$(run "${c%%|*}" "${c#*|}")" 0; done

# the message override: only reachable when the hook gets the message file (commit-msg)
printf 'feat: x\n\nSECRET-OK: fixture value, not a credential\n' > "$T/ok.msg"
printf 'feat: x\n\nno override here\n'                           > "$T/no.msg"
printf 'feat: x\n\nSECRET-OK:\n'                                  > "$T/empty.msg"
v='app.py|token = "abcdef0123456789abcd"'
check "message override accepted"       "$(run "${v%%|*}" "${v#*|}" "$T/ok.msg")"    0
check "message without override refused" "$(run "${v%%|*}" "${v#*|}" "$T/no.msg")"    1
check "override without a reason refused" "$(run "${v%%|*}" "${v#*|}" "$T/empty.msg")" 1

# the installer wires the hook where the message exists, and not where it does not
cd "$T"; git init -q w; cd w
sh "$HERE/scripts/install-git-hooks.sh" >/dev/null 2>&1
check "wired in commit-msg"        "$(grep -c 'no-literal-secret' .git/hooks/commit-msg)" 1
check "not wired in pre-commit"    "$(grep -c 'no-literal-secret' .git/hooks/pre-commit)" 0

echo "secret hook: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
