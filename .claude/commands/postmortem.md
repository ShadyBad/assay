---
name: postmortem
description: Capture failure context after a /ship abort or any non-success exit, and route lessons to project-memory, operator-model, and optionally Notion. Closes the asymmetry where /ship Step 12 only learns from green commits — failures, blocks, and aborts produce zero learning by default. Invoke manually after a failed attempt, or rely on /ship's auto-trigger on pipeline halt.
argument-hint: "[freeform note about what went wrong]" [--auto] [--from-session=<session-id>] [--skip]
---

# /postmortem — Failure Capture Loop

Thin wrapper around the `postmortem` skill. The skill holds the policy; this command provides the user-facing entry point.

## When to Invoke

- **Manual review after a failure** — a /ship aborted, a deploy rolled back, a test environment broke, a judge blocked you and you exited. Type `/postmortem` to capture the lesson before the context fades.
- **Catch-up logging** — you fixed the failure yesterday but never wrote it down. `/postmortem` with a freeform note prompts the structured capture.
- **Near-miss** — nothing aborted, but something almost did. Worth logging.

For automatic invocation from /ship's halt paths, the orchestrator calls the skill directly in `auto` mode. This command is for the human-initiated path.

## Flags

| Flag | Effect |
|------|--------|
| `--auto` | Run in /ship-driven mode. Skips the 5-question interview, pulls context from the most recent halted session-state file under `$HOME/.claude/memory/sessions/`. |
| `--from-session=<session-id>` | Use a specific older session as the failure source. Useful for retroactive postmortems on earlier work. |
| `--skip` | Record a deliberate skip into `$HOME/.claude/memory/global/postmortem-skipped-log.md` with a one-line reason. Useful when the failure was already documented elsewhere or has no actionable lesson. |

If a freeform note is provided as the first positional argument, it seeds the "root cause" prompt — the skill will still ask the follow-up routing questions but starts with the user's framing rather than a blank.

## Flow

Hand off to the `postmortem` skill in the appropriate mode (`manual` by default, `auto` if the flag is set). The skill drives the rest:

1. Detect project (via project-memory's detection contract).
2. Collect failure context (interactive in manual mode, from session state in auto mode).
3. Show routing menu (lesson / operator-model / skill suggestion / infra todo / Notion).
4. Brandon confirms each route.
5. Write approved routes. Append-only.
6. Return summary.

The skill's hard constraints apply: never push to Notion without explicit "yes", never edit operator-model without diff preview, never edit skill files inline, always allow skip.

## Quick Reference

```
/postmortem                                # Manual interview, current project context.
/postmortem "test env can't reach staging DB"  # Seed root cause, continue interactive.
/postmortem --auto                         # Run after /ship halt, pulls from session state.
/postmortem --from-session=2026-05-15-abc  # Retroactive postmortem on older session.
/postmortem --skip                         # Record deliberate skip with reason.
```

## Integration

- `postmortem` skill — does the actual capture and routing.
- `project-memory` skill — Route 1 destination (always).
- `operator-model` skill — Route 2 destination (with diff preview).
- `notion-bridge` skill — Route 4 destination (with sanitize + explicit yes).
- `/ship` — auto-invokes the skill at halt paths so manual /postmortem is rarely needed mid-pipeline.

## Hard Constraints

These mirror the skill. Restated here so the command file is self-contained:

- NEVER write to operator-model without diff preview to Brandon.
- NEVER push to Notion without explicit per-push "yes".
- NEVER edit skill files inline; produce a one-line suggestion that skill-curator picks up.
- ALWAYS allow `--skip`. Friction kills the loop.
- ALWAYS tag lessons with both `postmortem` and `failure` for findability.
