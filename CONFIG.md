# Configuration

`/assay` was extracted from a personal config. Several hard-coded strings reflect the original author's setup. This file lists what to change and why.

## Things hard-coded to the original author

| String | Where | Why it's there | Safe to swap? |
|--------|-------|----------------|---------------|
| `Brandon` | Skills + commands | Operator-model uses the operator's name in lessons/feedback prompts. | Yes — replace globally with your name. |
| `bpshay13@gmail.com` | Operator identity | Used in cross-channel comms skills. | Yes — replace if you use Gmail/communication skills. |
| `auto-co` | Project namespace | One of three project buckets the original author uses. | Yes — rename to one of your project codenames. |
| `margin-invest` | Project namespace | Another project bucket. | Yes — rename. |
| `personal` | Project namespace | Fallback bucket for anything not a named project. | Recommend keeping — every operator benefits from a personal bucket. |

## Quick rewrite

```bash
./scripts/personalize.sh "<your-name>" "<project-1>" "<project-2>"
```

This runs `sed` across `.claude/commands/` and `.claude/skills/` to swap:

- `Brandon` → `<your-name>`
- `auto-co` → `<project-1>`
- `margin-invest` → `<project-2>`

It does NOT touch `personal` — that's a useful default.

The script makes a `.backup-<timestamp>/` copy before rewriting. Diff if unsure.

## Manual rewrite

If you prefer to do it by hand:

```bash
cd ~/repos/assay/.claude
grep -rl "Brandon" .         # see what files contain the string
grep -rl "auto-co" .
grep -rl "margin-invest" .
```

Then use your editor's project-wide replace.

## What you probably DON'T want to rewrite

- **The risk tier names** (TRIVIAL/LOW/MEDIUM/HIGH/CRITICAL) — load-bearing across `/assay`, `judge-panel`, `done-gate`.
- **The pipeline step numbers and names** — `/assay` references them by step (e.g. "Step 7 EXECUTE"). Renaming requires touching every cross-reference.
- **Skill IDs in YAML frontmatter** (`name: spec-builder`, etc.) — these are the addresses other skills use to link.
- **The `Pinned Skills` list** in `skill-curator/SKILL.md` — protects the foundation from accidental archive proposals. Add your own to the list rather than replacing.

## Optional: add your own project namespace

To add a new project namespace `foo` alongside what's in the config:

1. `mkdir -p ~/.claude/memory/projects/foo/specs/{active,shipped}`
2. `touch ~/.claude/memory/projects/foo/lessons.md`
3. `touch ~/.claude/memory/projects/foo/specs/_index.md`
4. Update `project-memory/SKILL.md` and the project-detection section of your `~/.claude/CLAUDE.md` to recognize the new namespace.

## Optional: write your own CLAUDE.md

The skills reference `~/.claude/CLAUDE.md` for project-detection rules + risk tier definitions + completion contract. The original author's full CLAUDE.md is private. A minimal replacement looks like:

```markdown
# CLAUDE.md

## Project namespaces
- <project-1>
- <project-2>
- personal

## Project detection (in order)
1. .claude/project-name file (walk up to $HOME)
2. git remote URL pattern match
3. cwd path match
4. Fallback: personal

## Risk tiers
- TRIVIAL: typo, comment, format
- LOW: single-file <30 lines, isolated
- MEDIUM: 1-3 files, no schema/API change
- HIGH: multi-file, schema/API, security-adjacent, financial
- CRITICAL: irreversible — migrations, prod deploy, money paths, auth

## Completion contract
Tasks done when: success criteria met, tests pass, no debug code, lint passes,
type check passes, judges reviewed at tier, operator approved commit.
```

Drop that into `~/.claude/CLAUDE.md` (merging with what's already there) and you're set.
