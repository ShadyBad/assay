---
name: postmortem
description: Captures failure context when /assay aborts, blocks, or hits an uncovered gate, and routes the resulting lessons to project-memory, operator-model, and optionally Notion. Closes the asymmetry where /assay Step 12 only learns from successful commits. Use when /assay aborts at any step (auto-trigger), when Brandon invokes /postmortem manually after a failed attempt, when a judge-panel returns block, when done-gate halts the pipeline, or when Brandon explicitly says "we should learn from that miss". Append-only. Always asks Brandon to confirm each route (lessons, operator-model, Notion) before writing. Never logs to operator-model without diff preview. Never pushes to Notion without explicit per-push approval. Recovers cleanly from partial state.
---

# Postmortem Skill

Captures failure context and routes lessons. The asymmetric counterpart to project-memory's success-path capture. /assay learns from green commits at Step 12; this skill learns from red exits at any step.

## Why This Exists

/assay's LEARN step (Step 12) writes lessons only after a successful commit. Every aborted run, blocked judge verdict, halted gate, or manual interrupt produces zero learning. Failures carry higher signal than successes — "we blocked because the test environment can't reach the staging DB" outweighs "we added a helper with tests" by orders of magnitude. This skill closes that loop.

## Invocation Modes

### `auto` mode

Called by /assay when the pipeline exits non-successfully:

- Step 3 PLAN: Brandon answered `abort`.
- Step 7 EXECUTE: subagent timeout, Brandon chose `abort`.
- Step 8 JUDGE: verdict `block`.
- Step 9 REVISE: 2 revise cycles exceeded.
- Step 10 DONE GATE: any check failed and Brandon did not override.
- Step 11 COMMIT: pre-commit hook rejection with no auto-fix path.
- Any step: Brandon types "stop" or "abort".

Inputs from /assay:
- `failure_step` — which pipeline step halted.
- `attempted_action` — one-line summary of what was being tried.
- `gate_verdict` — judge or done-gate output if applicable.
- `partial_changeset` — files touched before halt (for context, not routed).

### `manual` mode

Called by user via `/postmortem`. Used when:
- Brandon wants to retroactively log a failure from earlier in the session.
- A failure happened outside /assay (a non-pipeline experiment, a broken build, a deployment that rolled back).
- Brandon wants to log a near-miss that did not abort but should have.

In manual mode, inputs are collected from Brandon interactively:
1. What were you trying to do? (one sentence)
2. Which step or stage failed? (free text — does not have to be a /assay step)
3. What did the gate or system say? (paste error, judge output, or "n/a")
4. Why did it fail, in your read? (1-2 sentences — root cause)
5. What should change going forward? (multi-select: operator-model, project lesson, skill description, infra todo, no change)

## Capture Template

Every postmortem produces a structured record:

```
POSTMORTEM <ISO-timestamp>
Project: <detected project>
Mode: <auto | manual>
Failure step: <step name or freeform>
Attempted action: <one line>
Gate verdict: <judge/done-gate output, or n/a>
Root cause: <1-2 sentences, Brandon's read>
Changes proposed:
  - lesson: <text or none>
  - operator-model: <section + entry or none>
  - skill change: <skill name + suggested edit or none>
  - infra todo: <text or none>
  - notion: <push target or none>
```

## Routing Rules

The skill routes the postmortem to up to four destinations. Each route is opt-in per postmortem. Brandon confirms each before write.

### Route 1: Project Lessons (project-memory)

**Always proposed.** Failure postmortems are the highest-quality lessons.

Invoke `project-memory append` with:
- `task_summary` — `POSTMORTEM: <attempted_action>`
- `lesson` — root cause + change going forward, 1-3 sentences.
- `tags` — `postmortem,failure,<failure_step_tag>,<any_topic_tag>`

The `postmortem` and `failure` tags make these entries findable for future retrospective queries (e.g., "show me every time judge-panel blocked").

### Route 2: Operator Model (operator-model)

**Proposed when the lesson is about Brandon's preferences, Claude's behavior, or a recurring pattern.**

Signals that a postmortem should update operator-model:
- The failure was caused by Claude making an assumption Brandon would not have made.
- Brandon corrected the same pattern earlier in the session.
- The root cause names a habit ("I keep skipping X", "Claude keeps doing Y").
- The change going forward is phrased as a rule for future sessions, not a one-off fix.

Invoke `operator-model diff_preview` with the proposed entry. Brandon confirms before write. Source is `inferred` (postmortems are interpretations, not explicit statements) unless Brandon explicitly states the preference in step 4 of manual mode — then `explicit`.

### Route 3: Skill Description Tweak

**Proposed when the failure points to a specific skill that did not trigger when it should have, or triggered incorrectly.**

Signals:
- Root cause names a skill by name and says it should have fired earlier / differently.
- A skill's description does not match how it is actually being used.
- A skill is missing a guardrail that the postmortem reveals.

This route does not auto-edit the skill. It produces a one-line suggestion: `Skill <name> SKILL.md description should mention: <X>`. The suggestion goes into the project lessons.md entry as a referenced action. skill-curator picks it up on its next pass.

Never edit skill files inline from a postmortem. Curator review prevents skill churn.

### Route 4: Notion (notion-bridge)

**Proposed when the failure is team-relevant or process-level.**

Signals:
- The failure blocks others (waiting on infra, waiting on access).
- The failure points to a process change (we should update the ADR on X).
- The root cause involves a tool, service, or environment outside Brandon's local control.
- Brandon explicitly says "share this".

Hand off to `notion-bridge push` with target category `Retrospectives` (default) or whatever Brandon prefers. The standard sanitize check applies.

## Auto Mode Flow

When /assay hands off to postmortem skill on abort:

1. Receive context from /assay (`failure_step`, `attempted_action`, `gate_verdict`, `partial_changeset`).
2. Surface to Brandon:
   ```
   POSTMORTEM — /assay halted at <failure_step>.
   Attempted: <attempted_action>
   Verdict: <gate_verdict>

   Two questions:
   1. Why did it fail, in your read? (1-2 sentences)
   2. What should change? (lesson / operator-model / skill / infra / nothing / multiple)
   ```
3. Wait for Brandon's response. If Brandon types `skip`, exit cleanly — no postmortem written, but log to `$HOME/.claude/memory/global/postmortem-skipped-log.md` so skill-curator can detect chronic skipping.
4. For each route Brandon selected, generate the proposed change and show diff preview.
5. Brandon confirms per route. Defaults: lesson `yes`, operator-model `ask`, skill `propose-only`, Notion `ask`.
6. Write approved routes. Return summary.

## Manual Mode Flow

When Brandon types `/postmortem`:

1. Detect project via project-memory's detection contract.
2. Ask the 5 interactive questions (see Manual Mode section above).
3. Build the structured record.
4. Show routing menu with proposed destinations and one-line previews of each.
5. Brandon confirms per route.
6. Write approved routes. Return summary.

## Interaction with /assay Pipeline

The /assay orchestrator invokes this skill at the following exit points. Each invocation is wrapped in a try/skip so that postmortem failure never blocks /assay's own state-save-and-exit.

| Step | Trigger | Pass-through context |
|------|---------|---------------------|
| 3 | Brandon picks `abort` on plan | step=PLAN, action=plan-summary, verdict=brandon-rejected |
| 7 | subagent timeout, Brandon picks `abort` | step=EXECUTE, action=task-summary, verdict=subagent-timeout |
| 8 | judges return `block` | step=JUDGE, action=task-summary, verdict=judge-output |
| 9 | 2 revise cycles exceeded | step=REVISE, action=task-summary, verdict=unresolved-blockers |
| 10 | done-gate check failed and no skip flag | step=DONE_GATE, action=task-summary, verdict=failed-check-name |
| 11 | pre-commit hook rejected, no auto-fix | step=COMMIT, action=task-summary, verdict=hook-output |
| any | Brandon types `stop` | step=<current>, action=task-summary, verdict=user-stopped |

The skill's auto-mode flow handles all of these uniformly. The pass-through context is shown to Brandon so he does not have to re-explain what he just saw.

## State and Storage

- Postmortem records do not get their own file. They live as entries inside the project's `lessons.md` (Route 1), inside `operator-model.md` (Route 2 if approved), and optionally in Notion (Route 4 if approved).
- Skipped postmortems append a one-liner to `$HOME/.claude/memory/global/postmortem-skipped-log.md` with format `<ISO-timestamp> | <failure_step> | <reason if Brandon gave one>`.
- The session state file written by /assay at interrupt time already contains the failure context. Postmortem skill reads from that file when invoked in auto mode, so Brandon can resume `/assay resume` and the postmortem can still fire after the fact if he chooses.

## Skipped Postmortem Tracking

If Brandon types `skip` on 3+ postmortems within a 14-day window, skill-curator flags this on its weekly pass with: `Postmortem skip rate elevated. Possible causes: postmortem prompts too long, root-cause questions too vague, postmortem feels redundant. Consider tuning.` This prevents the skill from becoming friction Brandon ignores.

## Invocation Contract

Modes:

- `auto` — called by /assay. Inputs: failure_step, attempted_action, gate_verdict, partial_changeset, project_name (optional, defaults to detected).
- `manual` — called by /postmortem command. Inputs: none (interactive).
- `query` — returns past postmortems. Inputs: query string (e.g., tag filter, date range, failure step). Useful for `/postmortem review last week` or skill-curator audits.

## Integration with Other Skills

- **project-memory** — postmortem is the primary writer of `postmortem,failure`-tagged entries. project-memory's read rules treat these the same as any other lesson.
- **operator-model** — postmortem proposes diffs to operator-model when the lesson is about Brandon or Claude behavior. operator-model's diff_preview is mandatory before any write.
- **notion-bridge** — postmortem hands off team-relevant findings. notion-bridge's sanitize check and explicit-yes rule apply.
- **session-recall** — past postmortems are searchable via session-recall's standard query interface (they live in lessons.md).
- **skill-curator** — reads postmortem-skipped-log for tuning signals. Picks up skill-description suggestions from Route 3.
- **/assay** — auto-invokes this skill at the 7 failure-path exit points listed above.

## Plugin Compatibility

Required: none. Works with pure filesystem.

Enhanced by:
- `notion@claude-plugins-official` — Route 4 push target.
- `private-journal-mcp@superpowers-marketplace` — Brandon can journal reflections separately; postmortem does not write here.
- `episodic-memory@superpowers-marketplace` — past postmortems become recall hits.

If notion plugin or MCP is missing, Route 4 degrades to "save to a local file at $HOME/.claude/memory/global/notion-pending/<date>-postmortem.md" and prompts Brandon to push later.

## Hard Constraints

- NEVER write to operator-model.md without showing diff preview to Brandon.
- NEVER push to Notion without explicit per-push "yes".
- NEVER edit skill files directly. Always go through skill-curator's review pass.
- NEVER block /assay's own state-save-and-exit. Postmortem is opportunistic — if it errors, log and exit clean.
- NEVER write a lesson longer than project-memory's 3-sentence cap.
- ALWAYS tag entries with `postmortem` AND `failure` (both, for findability).
- ALWAYS allow `skip`. Friction kills the loop.
- ALWAYS pass through the gate verdict verbatim — do not paraphrase judge or done-gate output. Brandon needs the raw text.
