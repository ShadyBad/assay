# /eod — End-of-Day Wrap

Closes the day. Captures what shipped, what slipped, what got learned, and the first action for tomorrow. Writes through the existing memory skills — never bypasses them.

This is a **write** command, but every write is gated on explicit Brandon approval. /eod never silently mutates state.

## Usage

```
/eod                              # interactive wrap (default)
/eod --quick                      # one-shot: just capture tomorrow-first-action
/eod --project=X                  # scope lessons to one namespace
/eod --note="<freeform>"          # attach a freeform note to today's session summary
/eod --no-operator-update         # skip the operator-model diff prompt even if signals warrant it
```

## Pipeline

### Step 1: Day Recon

Gather what happened today without asking Brandon yet:

- Read `$HOME/.claude/memory/sessions/` for any session dirs dated today.
- For each, read `state.json` and any `judge-output.md` to surface successes, blocks, aborts.
- Scan today's `/ship` runs by date prefix. Count: shipped, blocked, aborted, force-bypassed.
- Read `$HOME/.claude/memory/global/force-bypass-log.md` — flag any entry from today.

If nothing happened today (no session dirs, no commits): ask Brandon directly "What did you work on today?" Skip Step 1 outputs.

### Step 2: Slip Detection

A "slip" is something planned that did not ship. Detect by:

- Yesterday's `tomorrow-first-action.md` (from `memory/sessions/<yesterday>-<id>/`) — was that action completed today? Check git log + session state.
- Any `/ship resume` state file under `memory/sessions/` from earlier this week still in non-terminal state.
- Any TODO Brandon flagged in a prior session marked `#followup` that did not move.

Surface up to 3 slips with one-line reason each.

### Step 3: Lesson Harvest

Ask Brandon: "Anything to capture from today?" Then walk through prompts in this order:

1. **Bug or correction that recurred** — anything you had to fix twice or correct mid-flight.
2. **Pattern that worked surprisingly well** — non-obvious win worth keeping.
3. **Thing that felt slow that shouldn't have** — process friction, missing skill, bad default.
4. **Decision deferred** — anything you punted that you will need to face again.

For each non-empty answer, classify via project-memory:
- Project namespace (auto-co | margin-invest | personal) based on context.
- Tag inline: `#followup`, `#unresolved`, `#blocker`, `#win`, `#process`, `#pattern`.
- Append to `memory/projects/<ns>/lessons.md` as `[<YYYY-MM-DD>] <ns>: <takeaway> #<tag>`.

Honor `--project=` to lock namespace. Skip entire section if `--quick`.

### Step 4: Operator-Model Signals

Scan for signals that should update `operator-model.md`:

- Brandon corrected Claude on a pattern today (e.g., "stop suggesting X", "always do Y").
- Same lesson appeared 3+ times across project-memory entries (cross-check via grep).
- An explicit preference statement ("I prefer", "I hate when", "from now on").

If any signal detected AND `--no-operator-update` not set:
- Invoke `operator-model` skill.
- Show Brandon the proposed diff (additions only — never silent overwrite).
- Accept: `yes` (apply) | `no` (skip) | `edit` (Brandon rewrites the entry).

Never write without diff preview. Never overwrite an existing entry — append + dedupe only (per operator-model skill contract).

### Step 5: Tomorrow's First Action

Ask Brandon one question: "What's the first action tomorrow?"

Constraints on the answer:
- Single concrete action. Not a category, not a goal. ("Write the slot scoring tests" not "work on margin-invest scoring".)
- Estimable in under 90 minutes. If bigger, ask Brandon to break off the first step.
- If Brandon says "nothing" or "not sure" — write "clean slate" verbatim. /morning handles that case.

Write the action to:
```
$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/tomorrow-first-action.md
```

One line, no prose. /morning reads this verbatim.

### Step 6: Session Summary Write

Write a session summary to:
```
$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/summary.md
```

Format:
```markdown
# EOD <YYYY-MM-DD>

## Shipped
- <commit SHA + one-line description, per project>

## Slipped
- <slip + one-line reason>

## Lessons
- [<project>] <lesson + tag>

## Operator-model updates
- <yes/no — if yes, which section + one-line delta>

## Force-bypasses
- <if any — surface them; these get curator-reviewed weekly>

## Tomorrow
→ <tomorrow-first-action>
```

If the file already exists (multiple /eod runs same day): append a `## Wrap N` section, never overwrite.

### Step 7: Confirm

Show Brandon the summary file path and a one-line preview:
```
✓ EOD wrapped — <date>
  Lessons: <N> captured · Slips: <N> · Tomorrow: <first 60 chars>
  → $HOME/.claude/memory/sessions/<dated>/summary.md
```

Done. /eod never auto-pushes to Notion. /weekly handles team-relevant retros.

## Failure Modes

| Step | Failure | Behavior |
|------|---------|----------|
| 1 | No session dir today | Ask Brandon directly. |
| 2 | No yesterday session | Skip slip detection. |
| 3 | project-memory skill missing | Write directly to lessons.md with same format. Log degradation. |
| 4 | operator-model skill missing | Skip Step 4 entirely. Note in summary. |
| 5 | Brandon says "stop" mid-flow | Save partial summary as `<dated>/summary-partial.md`. Exit clean. |
| 6 | sessions dir missing | Create it. Write summary. |

## Hard Constraints

- NEVER write a lesson without showing it to Brandon first (project-memory skill enforces).
- NEVER update operator-model without diff preview AND Brandon approval.
- NEVER push to Notion from /eod. Local-only writes.
- NEVER block on missing data. Always produce at least a `tomorrow-first-action.md` if Brandon answered Step 5.
- ALWAYS append, never overwrite. Multiple /eod runs in one day stack as `Wrap 1`, `Wrap 2`, etc.

## Coordination

- `project-memory` — primary write path for lessons.
- `operator-model` — gated write path for preference updates.
- `session-recall` — NOT invoked. /eod writes the session record; /morning + session-recall consume it later.
- `notion-bridge` — NOT invoked. /weekly handles team-relevant push.
- `/morning` reads what /eod writes (tomorrow-first-action.md).
- `/weekly` reads the week's summary.md files to detect cross-project patterns.
