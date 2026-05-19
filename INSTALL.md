# Install

Pick one of three install paths.

## Path 1 — Claude Code plugin (recommended)

If Claude Code's plugin loader is enabled, drop the repo into your local plugins directory:

```bash
git clone https://github.com/shadybad/claude-ship.git ~/.claude/plugins/local/claude-ship
```

Verify the manifest is found:

```bash
ls ~/.claude/plugins/local/claude-ship/.claude-plugin/plugin.json
```

Restart Claude Code. Commands appear under their own names (`/ship`, `/spec`, etc.). Skills surface via the `Skill` tool's available list.

## Path 2 — Direct drop into `~/.claude/`

If you don't want a plugin wrapper, copy commands and skills directly:

```bash
git clone https://github.com/shadybad/claude-ship.git /tmp/claude-ship

# Commands
cp -i /tmp/claude-ship/.claude/commands/*.md ~/.claude/commands/

# Skills — copy each subdirectory
cp -ri /tmp/claude-ship/.claude/skills/* ~/.claude/skills/
```

Use `-i` to avoid overwriting your existing files. Diff first if you already have a `ship.md` or any skill with the same name.

## Path 3 — Symlink (for development)

If you want to edit the files in one place and have them reflected everywhere:

```bash
git clone https://github.com/shadybad/claude-ship.git ~/repos/claude-ship

# Plugin layer
mkdir -p ~/.claude/plugins/local
ln -s ~/repos/claude-ship ~/.claude/plugins/local/claude-ship
```

Or symlink the inner directories directly into `~/.claude/`:

```bash
for cmd in ~/repos/claude-ship/.claude/commands/*.md; do
  ln -s "$cmd" ~/.claude/commands/$(basename "$cmd")
done

for skill_dir in ~/repos/claude-ship/.claude/skills/*/; do
  ln -s "$skill_dir" ~/.claude/skills/$(basename "$skill_dir")
done
```

## Personalize before first use

The skills reference the original author's name and project namespaces. Personalize before running `/ship` for real:

```bash
cd ~/repos/claude-ship   # or wherever you cloned
./scripts/personalize.sh "<your-name>" "<project-1>" "<project-2>" "<project-3>"
```

Then re-copy or re-symlink. See [CONFIG.md](./CONFIG.md) for what changes.

## Required directories

`/ship` writes session state and lessons under `~/.claude/memory/`. Create the tree on first use:

```bash
mkdir -p ~/.claude/memory/{global,sessions,projects/personal/specs/active,projects/personal/specs/shipped}
touch ~/.claude/memory/projects/personal/lessons.md
touch ~/.claude/memory/projects/personal/specs/_index.md
```

If you ran `personalize.sh` with extra project names, add their directories too.

## CLAUDE.md hook (optional)

The skills assume a `~/.claude/CLAUDE.md` exists with project detection rules + risk tier definitions. Either:

- Write your own — see [CONFIG.md](./CONFIG.md) for a minimal `CLAUDE.md` template, or
- Skim each skill's SKILL.md — every skill is self-contained enough to run without the global config, the global file just centralizes shared rules.

## Verify

```bash
# In Claude Code:
/ship "test task — print hello"
```

If you hit a missing-plugin warning (e.g. `superpowers:brainstorming` not installed), `/ship` will note the degradation and continue. That's working as intended.
