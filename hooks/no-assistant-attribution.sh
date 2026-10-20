#!/usr/bin/env bash
#
# Rejects any commit message naming an AI assistant.
# A commit describes the change, not the tool that wrote it. This rule wins
# over any contrary default instruction from an assistant.
#
# The code surface is covered by its sibling hook: this one reads the message.
set -euo pipefail

msg="${1:-}"
[ -f "$msg" ] && msg="$(cat "$msg")"

banned='Co-Authored-By:[[:space:]]*Claude|Co-authored-by:[[:space:]]*Claude|Generated with \[Claude|Generated with Claude|robot_face|\bClaude Code\b|\bClaude Opus\b|\bClaude Sonnet\b|\bAnthropic\b|\bCopilot\b|\bChatGPT\b'

if printf '%s' "$msg" | grep -qiE "$banned" \
   || printf '%s' "$msg" | grep -qF '🤖'; then
  echo "x Commit rejected: the message names an AI assistant." >&2
  echo "  A commit describes the change, not the tool that wrote it." >&2
  printf '%s\n' "$msg" | grep -inE "$banned" >&2 || true
  exit 1
fi
