---
name: morning
description: Daily kickoff. Reads memory, calendar, lessons, and open proposals to surface what matters today as a 5-bullet brief plus a single "first action." Read-only — never writes lessons, pushes to Notion, or mutates state (/eod does that). Use at the start of a work day, when Brandon says "good morning", "/morning", or "what's on today".
argument-hint: "[--project=<ns>] [--quick] [--no-cal]"
---

# /morning — Daily Kickoff

Surfaces what matters today. Reads memory + calendar + lessons + open proposals. Outputs a 5-bullet brief and a single "first action."

This is a **read-only** command. It never writes lessons, never pushes to Notion, never modifies state. /eod does that.

## Usage

```
/morning                 # default: full brief
/morning --project=X     # scope to one project namespace (auto-co|margin-invest|personal)
/morning --quick         # 3 bullets, skip calendar + proposed
/morning --no-cal        # skip Google Calendar MCP fetch
```

## Pipeline

Run steps 1-5 in parallel where possible, then synthesize in step 6.

### Step 1: Operator Model Load

Read `$HOME/.claude/memory/global/operator-model.md`. Extract:
- Today's date relative to any active deadlines or commitments noted.
- "Things Brandon is currently optimizing for" section if present.
- Top 3 "Things Brandon hates" — used to filter suggestions.

If file missing or malformed: log and continue. Do not block.

### Step 2: Calendar Pull

Invoke Google Calendar MCP (`mcp__claude_ai_Google_Calendar__list_events`) with:
- `timeMin`: today 00:00 in Brandon's local tz.
- `timeMax`: today 23:59.
- `calendarId`: `primary` (and any other calendars surfaced in operator-model as relevant).

Honor `--no-cal` flag. If MCP unreachable: skip with note "(calendar unavailable)".

Extract: meeting titles, times, durations, prep notes if any. Flag conflicts and back-to-backs.

### Step 3: Lessons Scan

For each project in `$HOME/.claude/memory/projects/`:
- Read `lessons.md`.
- Pull last 5 entries.
- Pull any entry from the last 14 days tagged `#followup`, `#unresolved`, or `#blocker`.

Honor `--project=` flag to scope.

### Step 4: Proposed Items

Read `$HOME/.claude/skills/_proposed/` directory tree. Count items in:
- `_quality/` — skill-curator quality issues awaiting review.
- `_consolidations/` — duplicate/merge proposals.
- `_fixes/` — broken skill fixes.
- `_archives/` — archive proposals.
- Root `_proposed/` — new skill drafts.

Surface counts and the 2 oldest items by mtime (these are decaying).

### Step 5: Yesterday's Session

Find most recent session under `$HOME/.claude/memory/sessions/`. If yesterday's /eod wrote a `tomorrow-first-action.md`, read and surface it verbatim. Otherwise pull the session summary's "Next" line if present.

If no recent session or no follow-up captured: note "(clean slate)".

### Step 6: Synthesize

Generate brief in this exact format:

```
☀ MORNING BRIEF — <date> — <project filter if applied>

Calendar today:
  • <HH:MM> <event> (<duration>)
  ... (max 5; "+N more" if overflow)
  Conflicts: <list or "none">

Carry-over from yesterday:
  → <first action from /eod, or "clean slate">

Active followups (last 14 days):
  • [<project>] <lesson excerpt, 1 line>
  ... (max 3; rank by recency × tag severity)

Decaying proposals:
  • <type>/<name> — <age>d old
  ... (max 3; oldest first)

────────────────────────────────────────
HIGHEST-LEVERAGE TODAY:
  → <one concrete next action, derived from above>

  Rationale: <one sentence — which signal drove this>
```

The HIGHEST-LEVERAGE line is the single most important output. Derive it by:
1. Calendar fixed-time commitments first (you cannot move these).
2. Yesterday's tomorrow-first-action if no fixed conflict.
3. Otherwise: oldest `#blocker`/`#unresolved` lesson on the active project.
4. Otherwise: oldest decaying proposal.
5. Otherwise: ask Brandon what he wants to work on.

Never recommend a pattern from the operator-model "Things Brandon hates" list.

## Failure Modes

| Source | Failure | Behavior |
|--------|---------|----------|
| operator-model | Missing/corrupt | Skip the filter step. Continue. |
| Calendar MCP | Unreachable | Note "(calendar unavailable)". Continue. |
| Lessons | Project dir missing | Skip that project. Continue. |
| Proposed | Dir empty | Skip section. Continue. |
| Session | None recent | "(clean slate)". |

If ALL sources fail: surface to Brandon. Offer to run `/ship "<task>"` directly.

## Hard Constraints

- READ-ONLY. Never write to lessons, operator-model, sessions, or _proposed/.
- NEVER push to Notion from /morning. That is /weekly's job.
- NEVER auto-invoke /ship. Just surface the recommendation.
- NEVER suggest more than ONE highest-leverage action. The whole point is focus.

## Coordination

- `operator-model` skill: used for Brandon prefs filter.
- `project-memory` skill: used for lessons scan.
- `session-recall` skill: NOT invoked here (too heavy for a daily brief). /morning reads session dir directly.
- `mcp-router`: not invoked. Calendar MCP loaded directly.
- Coordinates with `/eod` (reads yesterday's tomorrow-first-action) and `/weekly` (Sunday extends this with cross-project pattern detection).
