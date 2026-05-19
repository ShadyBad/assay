#!/usr/bin/env bash
# proposal-watcher.sh — SessionStart hook: surface pending skill proposals
#
# Reads ~/.claude/skills/_proposed/ for subdirs with SKILL.md and emits a
# Claude-readable context block. Silent when count is 0.
#
# Output contract: stdout is injected into the SessionStart context.
# stderr is logged to /tmp/proposal-watcher.err. Exit 0 always.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROPOSED_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/_proposed"

# Count pending
count=$("$SCRIPT_DIR/proposal-count.sh" 2>/dev/null || echo 0)

# Silent when zero — no banner on clean sessions
if [ "$count" -eq 0 ]; then
  exit 0
fi

# Render banner
{
  echo "📋 $count skill proposal(s) pending review at \`~/.claude/skills/_proposed/\`."
  echo
  echo "Pending:"

  # List each proposal: name + first line of SKILL.md description
  for d in "$PROPOSED_DIR"/*/; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue

    name=$(basename "$d")

    # Status check — skip if already promoted or rejected
    if [ -f "$d/_proposal_metadata.md" ]; then
      if grep -q "^# Status: promoted" "$d/_proposal_metadata.md" 2>/dev/null; then
        continue
      fi
      if grep -q "^# Status: rejected" "$d/_proposal_metadata.md" 2>/dev/null; then
        continue
      fi
    fi

    # Pull description first sentence (up to first period) — capped at 120 chars
    desc=$(awk '/^description:/{
      sub(/^description:[ \t]*/,"")
      while (NF==0 || $0 !~ /\./) { gsub(/^[ \t]+|[ \t]+$/,""); printf "%s ", $0; if ((getline line) > 0) { $0 = line } else { break } }
      sub(/\..*$/,".")
      print
      exit
    }' "$d/SKILL.md" 2>/dev/null | head -c 120)

    echo "  - $name: $desc"
  done

  echo
  echo "To review: run \`/skill-curator\` for full audit, or inspect each at the path above. Promote with \`mv\`."
} 2>/tmp/proposal-watcher.err

exit 0
