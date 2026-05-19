#!/usr/bin/env bash
# proposal-count.sh — count pending skill proposals in _proposed/
#
# A proposal is a subdirectory of ~/.claude/skills/_proposed/ containing a
# SKILL.md file. Subdirs without SKILL.md (e.g. _archives, _consolidations,
# _fixes, _hookify, _operator-model, _quality, _claude-md) are excluded.
#
# Output: a single integer to stdout. Always exits 0 (never blocks anything).

PROPOSED_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/_proposed"

if [ ! -d "$PROPOSED_DIR" ]; then
  echo 0
  exit 0
fi

# Count subdirs that have a SKILL.md
count=0
for d in "$PROPOSED_DIR"/*/; do
  [ -d "$d" ] || continue
  if [ -f "$d/SKILL.md" ]; then
    count=$((count + 1))
  fi
done

echo "$count"
