# Shared path exclusions for the commit hooks. Sourced, not executed.
#
# WHY THIS FILE EXISTS. The hooks it serves came from two projects where the
# exclusion lists were hard-coded: docs/framing/, analysis/, i18n/,
# infra/systemd/claude-*.service. Ported as-is, they would silently exclude
# nothing in a project with different paths -- and silently fail to exclude a
# legitimate case in one with other paths. A hard-coded list is a project
# pretending to be a convention.
#
# A project adds its own, one glob per line, in .claude/hook-exclusions:
#     i18n/
#     docs/legacy/
#
# Lines starting with # are comments.
exclusions_regex() {
    base='(^|/)\.reference/|(^|/)vendor/|(^|/)node_modules/'
    f="${1:-.claude/hook-exclusions}"
    if [ -f "$f" ]; then
        extra=$(grep -vE '^\s*(#|$)' "$f" 2>/dev/null | sed 's/[].[^$*\\]/\\&/g' | paste -sd'|' -) || true
        [ -n "${extra:-}" ] && base="$base|$extra"
    fi
    printf '%s' "$base"
}
