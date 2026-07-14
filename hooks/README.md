# hooks/

Hook scripts that surface pending skill proposals from `~/.claude/skills/_proposed/` so they don't rot unseen.

## Why

skill-curator proposes new skills, consolidations, and fixes — but its hard constraint is *propose, never execute*. Without a surfacing mechanism, proposals sit untouched until you remember to check `_proposed/` manually. These hooks fix that.

## What's in here

| Script | Hook type | What it does |
|--------|-----------|--------------|
| `proposal-count.sh` | helper | Counts subdirs of `_proposed/` that contain a `SKILL.md`. Emits a single integer. Used by the other two. |
| `proposal-watcher.sh` | SessionStart | When count > 0, emits a banner naming each pending proposal with a truncated description. Silent when zero. |
| `composed-statusline.sh` | statusLine | Wraps the existing statusline command (caveman if present) and appends a `📋 N` segment when count > 0. Silent when zero. |

All three:
- Skip subdirs without `SKILL.md` (the meta dirs like `_archives/`, `_consolidations/`, `_fixes/`).
- Skip proposals whose `_proposal_metadata.md` contains `# Status: promoted` or `# Status: rejected` (audit-trail entries don't count as pending).
- Exit 0 in all cases. Never block a session or statusline render.

## Install

If you're using the `assay` plugin install paths from the root README, the scripts already live at `~/.claude/hooks/<name>.sh` as symlinks (or copies) into the repo. To wire them into Claude Code, append the two settings.json entries below.

### Add to `~/.claude/settings.json`

**SessionStart hook** — append a second entry to the `hooks.SessionStart` array (keeps any existing SessionStart hooks intact):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"/Users/<you>/.claude/hooks/proposal-watcher.sh\"",
            "timeout": 5,
            "statusMessage": "Checking pending skill proposals..."
          }
        ]
      }
    ]
  }
}
```

**statusLine** — flip the existing command to the composed wrapper:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash \"/Users/<you>/.claude/hooks/composed-statusline.sh\""
  }
}
```

The composed script first runs `~/.claude/hooks/caveman-statusline.sh` if present (preserving the caveman badge), then appends the proposal segment when needed. If you don't have caveman installed, the script silently skips that call and just emits the proposal segment.

## Behavior

| Pending count | SessionStart output | statusLine append |
|---------------|---------------------|-------------------|
| 0 | nothing | nothing |
| ≥ 1 | banner + per-proposal list | `📋 N` in yellow-bold |

Both scripts read from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/_proposed/`, so they respect a custom config directory if set.

## Rollback

Restore the saved settings.json backup made when you installed:

```bash
cp ~/.claude/settings.json.pre-assay-hooks-<timestamp> ~/.claude/settings.json
rm ~/.claude/hooks/{proposal-count,proposal-watcher,composed-statusline}.sh
```

## Performance

- `proposal-count.sh` and `composed-statusline.sh` are called on every keystroke for the statusline. Both shell-only, scan a single small directory, complete in single-digit milliseconds.
- `proposal-watcher.sh` runs once at session start. Wall-clock impact: negligible.

## Hardening

`proposal-watcher.sh` writes stderr to `/tmp/proposal-watcher.err` so a malformed SKILL.md never propagates a noisy banner to the session start context. The status command never blocks the statusline render (it exits 0 even on parse errors).
