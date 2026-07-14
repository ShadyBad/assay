---
name: weekly
description: Sunday review — the slow loop. Detects cross-project patterns across the week's lessons, runs the full skill-curator audit, and offers per-section Notion push for team-relevant retros. Reads everything /eod wrote across the week and writes one consolidated retro file. Never auto-pushes. Use once a week (default Sunday), when Brandon says "/weekly" or "run the weekly review".
argument-hint: "[--range=<7d|14d|30d>] [--project=<ns>] [--no-curator] [--no-notion] [--dry-run]"
---

# /weekly — Sunday Review

The slow loop. Runs once a week (default Sunday). Detects cross-project patterns across the week's lessons, runs the full skill-curator audit, and offers per-section Notion push for team-relevant retros.

Reads everything /eod wrote across the week. Writes one consolidated retro file. Never auto-pushes.

## Usage

```
/weekly                          # default: full Sunday review
/weekly --range=7d               # explicit window (default 7d; accepts 14d, 30d)
/weekly --project=X              # scope to one namespace
/weekly --no-curator             # skip skill-curator audit
/weekly --no-notion              # skip Notion push prompts entirely
/weekly --dry-run                # produce retro file but no curator writes, no Notion prompts
```

If today is not Sunday, /weekly still runs but adds a one-line note: "(running off-cycle — last Sunday was YYYY-MM-DD)". Brandon may invoke any day.

## Pipeline

### Step 1: Window Determination

Resolve the window:
- Start: today minus `--range` (default 7 days). End: today.
- Find all `memory/sessions/<YYYY-MM-DD>-<id>/summary.md` with dates in range.
- Find all `memory/projects/<ns>/lessons.md` entries with `[YYYY-MM-DD]` prefix in range.
- Find all `memory/global/force-bypass-log.md` entries in range.

If window has zero session summaries: surface to Brandon — "No /eod summaries in window. Run /weekly anyway? (yes/no)". Yes proceeds; no aborts.

### Step 2: Cross-Project Pattern Detection

Read this week's lessons across all 3 namespaces. Detect:

- **Recurring tag clusters** — a tag (e.g., `#process`, `#blocker`) appearing 3+ times across distinct entries, especially when crossing project boundaries.
- **Same root word** — keyword overlap across projects (e.g., "test", "deploy", "scoring") suggests shared infra friction.
- **Force-bypass pattern** — if force-bypass-log has 2+ entries this week, surface as a quality signal.
- **Slip-to-ship ratio** — count slips across week's EOD summaries vs shipped commits. If slips > shipped, flag.

Output up to 5 cross-project patterns. Each with:
- One-line statement.
- Supporting evidence (project + date list).
- Suggested action (one sentence).

### Step 3: Skill Curator Audit

If `--no-curator` not set:

- Invoke `skill-curator` skill in `full` mode.
- Update `memory/global/last-curator-run.txt` with today's ISO timestamp.
- Capture curator output: counts in `_quality/`, `_consolidations/`, `_fixes/`, `_archives/` and net deltas vs last run.

Curator never auto-installs or auto-archives. /weekly surfaces proposal counts in the retro. Brandon reviews `skills/_proposed/` at his discretion.

### Step 4: Operator-Model Drift Check

Compare this week's lessons against `operator-model.md` "Things Brandon hates" and "Things Brandon values" sections. Surface:

- Patterns Brandon followed that contradict a stated preference (operator-model entry may be stale).
- Patterns Brandon repeatedly avoided that aren't in operator-model yet (worth proposing as new entries).

For each: propose to /eod-style at next session, do not auto-write. Add to retro file as "Operator-model candidates."

### Step 5: Retro File Write

Write to:
```
$HOME/.claude/memory/weekly/<YYYY-MM-DD>.md
```

Filename uses today's ISO date (the Sunday). Create `memory/weekly/` dir if missing.

Format:
```markdown
# Weekly Review — <YYYY-MM-DD>
Window: <start> → <end>
Project filter: <if applied, else "all">

## Shipped this week
<per-project bullet list, sorted by commit count>

## Slipped this week
<aggregated from EOD summaries>

## Cross-project patterns
<from Step 2; max 5>

## Skill curator audit
<proposal counts + net delta vs last run; link to _proposed/ paths>

## Force-bypasses this week
<from force-bypass-log; flag if count > 0>

## Operator-model candidates
<from Step 4; never auto-written>

## Notion push log
<populated by Step 6>
```

If file already exists (re-running same Sunday): append a `## Rerun N — <HH:MM>` section. Never overwrite.

### Step 6: Notion Push (Section-by-Section)

If `--no-notion` not set:

Invoke `notion-bridge`. For each section that matches push categories (per notion-bridge rules — retrospectives, status, board materials, customer-facing docs), prompt Brandon once:

```
Section: Cross-project patterns
Preview: <first 200 chars>

Push to Notion? (y / n / different-target)
```

- `y` → push via notion-bridge, log target page URL in retro file's `## Notion push log` section.
- `n` → skip, log "skipped" in push log.
- `different-target` → prompt for page or DB.

Skip silently for sections in stay-local categories (lessons-only, raw skill stats, force-bypass details — these stay in memory).

Never push secrets, API keys, or financial numbers without explicit per-push approval (per notion-bridge skill contract).

### Step 7: Confirm + Surface

Final output:
```
✓ WEEKLY REVIEW COMPLETE — <YYYY-MM-DD>
  Window: <range>
  Patterns surfaced: <N>
  Curator proposals: <N> new, <N> aged
  Notion pushes: <pushed> / <eligible>
  Force-bypasses this week: <N> (review)
  → $HOME/.claude/memory/weekly/<date>.md
```

If curator proposed anything: add a line "Review proposals: ls $HOME/.claude/skills/_proposed/".

## Failure Modes

| Step | Failure | Behavior |
|------|---------|----------|
| 1 | No summaries in window | Ask Brandon to confirm proceed. |
| 2 | Lessons missing for a project | Skip that project's contribution. Note in retro. |
| 3 | skill-curator missing | Skip Step 3 entirely. Note in retro. |
| 4 | operator-model missing | Skip Step 4. Note in retro. |
| 5 | weekly dir missing | Create it. Continue. |
| 6 | Notion MCP unreachable | Skip prompts. Log "Notion unreachable" in push log. Continue. |

If ALL of Steps 2-4 produce no output: still write the retro file with whatever was found in Step 1. A near-empty retro is still data ("quiet week").

## Hard Constraints

- NEVER auto-push to Notion. Always prompt per section.
- NEVER overwrite an existing weekly file. Append as `Rerun N` sections.
- NEVER skip curator without `--no-curator` flag. The audit IS the point.
- NEVER write operator-model changes from /weekly. Surface as candidates only — /eod or explicit `/operator-model` invocation does the actual write.
- ALWAYS log force-bypass count, even if zero. Establishes baseline.
- ALWAYS append-only on the retro file.

## Coordination

- `project-memory` — week's lessons read.
- `skill-curator` — full audit (the heavy job).
- `operator-model` — drift detection only (no writes).
- `notion-bridge` — per-section push gate.
- `session-recall` — NOT invoked. /weekly walks the session dir directly with date filter.
- `mcp-router` — not invoked at top. notion-bridge handles its own Notion MCP load.
- Reads what `/eod` writes (week's `summary.md` files).
- Complements `/morning` (daily focus) and `/eod` (daily wrap) as the slow loop.

## When to Run

- **Default cadence**: Sunday evening.
- **Off-cycle triggers**: after a `/assay --force` was used (force-bypass review), after a project namespace ships its first MVP, before any external commitment (investor update, customer demo, team retro).
- **Skip if**: window has zero activity AND last weekly was within 14 days. Surface "Nothing changed since <date>. Skip? (yes/no)".
