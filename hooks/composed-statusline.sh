#!/usr/bin/env bash
# composed-statusline.sh — wraps existing statusline command(s) and appends
# a pending-proposal segment when ~/.claude/skills/_proposed/ has entries.
#
# Runs the caveman statusline first (if present), then appends `📋 N` segment
# when proposal count > 0. Silent appendix when count is 0.
#
# Configure ~/.claude/settings.json:
#   "statusLine": { "type": "command", "command": "bash <path>/composed-statusline.sh" }

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# 1. Run caveman statusline if present (existing line content)
CAVEMAN_STATUSLINE="$CLAUDE_DIR/hooks/caveman-statusline.sh"
if [ -f "$CAVEMAN_STATUSLINE" ] && [ ! -L "$CAVEMAN_STATUSLINE" ]; then
  bash "$CAVEMAN_STATUSLINE"
fi

# 2. Append proposal segment when count > 0
count=$("$SCRIPT_DIR/proposal-count.sh" 2>/dev/null || echo 0)

if [ "$count" -gt 0 ]; then
  # Color 220 = yellow-orange. Bold for visibility.
  printf ' \033[1;38;5;220m📋 %d\033[0m' "$count"
fi
