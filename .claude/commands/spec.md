---
name: spec
description: Turn a fuzzy goal into a crisp, /assay-consumable spec. Wires superpowers:brainstorming + ecc:prp-prd + operator-model into one interview that produces a 1-page spec with measurable success criteria, adversarial risks, and a draft/approved/shipped status gate. The missing step between idea and execution. Most bad ships come from shipping the wrong thing well — this command forces the scoping moment. Subcommands list/show/approve/revise for managing the spec library.
argument-hint: "<fuzzy goal>" [--quick] [--namespace=<ns>] [--risk=<tier>] | list [--status=<s>] [--namespace=all] | show <spec-id> | approve <spec-id> | revise <spec-id>
---

# /spec — Scoping Gate

Entry point for the `spec-builder` skill. Sits one level upstream of `/assay`. Run this when the task is fuzzy. Run `/assay <spec-id>` once the spec is approved.

## Invocation

```
/spec "<fuzzy goal>"                    # full interrogation (brainstorm + prp-prd)
/spec "<fuzzy goal>" --quick            # skip brainstorm, jump to prp-prd
/spec "<fuzzy goal>" --namespace=<ns>   # force namespace (auto-co | margin-invest | personal)
/spec "<fuzzy goal>" --risk=<tier>      # pre-set risk classification

/spec list                              # show all specs in current namespace
/spec list --status=draft               # filter by status
/spec list --namespace=all              # across all namespaces
/spec show <spec-id>                    # print full spec
/spec approve <spec-id>                 # flip status: draft -> approved
/spec revise <spec-id>                  # reopen for edits (any status -> draft)
```

## Behavior

Delegates fully to the `spec-builder` skill at `$HOME/.claude/skills/spec-builder/SKILL.md`. See that file for the 9-step pipeline.

Summary:
1. **PARSE** — detect mode (new / list / show / approve / revise) and flags.
2. **DETECT NAMESPACE** — `.claude/project-name` → git remote → cwd → personal. `margin_invest/` and `margin-invest-backtest/` both map to `margin-invest`.
3. **LOAD CONTEXT** — operator-model + project-memory + session-recall in parallel. If a similar prior spec exists, surface it and offer to revise instead of duplicating.
4. **DIVERGE** — `superpowers:brainstorming` produces 3-5 alternative framings of the goal. Brandon picks one. Skipped with `--quick`.
5. **INTERROGATE** — `ecc:prp-prd` drives the 7-section interview: Problem, Hypothesis, Success criteria, Non-goals, Constraints, Risks, Plan sketch.
6. **SYNTHESIZE** — generate spec markdown with auto-filled frontmatter. Spec-id is `<kebab-slug>-<YYYY-MM-DD>`; collisions append `-2`, `-3`.
7. **SHOW + APPROVE** — print the spec and ask: `approve` / `draft` / `revise` / `abort`. Default is `draft`. Status only flips to `approved` on explicit `approve`.
8. **WRITE** — save to `$HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md`. Append row to `_index.md`.
9. **NEXT** — print `/assay <spec-id>` if approved, else `/spec approve <spec-id>`.

## Spec file location

```
$HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md
$HOME/.claude/memory/projects/<ns>/specs/_index.md   # table of all specs in namespace
```

Namespaces: `auto-co`, `margin-invest`, `personal`. Per project CLAUDE.md, both `margin_invest/` and `margin-invest-backtest/` map to `margin-invest`.

## Spec contract

Every spec has YAML frontmatter:

```yaml
spec-id: <slug>-<YYYY-MM-DD>
title: <short title, max 8 words>
namespace: auto-co | margin-invest | personal
created: <YYYY-MM-DD>
status: draft | approved | shipped
risk-tier: trivial | low | medium | high | critical
shipped-at: <YYYY-MM-DD or empty>
shipped-commit: <SHA or empty>
```

And 7 mandatory sections: Problem, Hypothesis, Success criteria, Non-goals, Constraints, Risks / Ways this could be wrong, Plan sketch.

Missing any mandatory section = invalid spec, `/assay` refuses.

## Status gate

| Status | `/assay` behavior |
|--------|------------------|
| `draft` | Refuses. Asks Brandon to run `/spec approve <spec-id>` first. |
| `approved` | Runs. Snapshots the spec into session state on entry. Locks for the duration of the run. |
| `shipped` | Warns. Requires `--force` to re-ship. |

This gate is what makes a spec a contract instead of a doc.

## Hard rules (inherited from spec-builder skill)

- No `status: approved` without Brandon explicitly typing `approve`.
- No overwriting `shipped` specs. Revising creates a new draft on the same id.
- No skipping the Risks section. Every spec ends with an adversarial check.
- No inferred success criteria. If Brandon refuses to give a measurable outcome, the spec is aborted with: "Without measurable success criteria, /assay cannot verify done. Walk away or come back with a number."

## When NOT to use /spec

- TRIVIAL changes (typo, comment edit, formatting). Just `/assay "fix typo in X"`.
- LOW changes with obvious success criteria (e.g. "rename function foo to bar across the codebase"). Just `/assay`.
- Emergency hotfixes. Use `/assay --force` with a written incident note.
- Anything where Brandon already has a written spec elsewhere (Notion, GitHub issue with acceptance criteria). Paste into `/assay`'s task description.

Rule of thumb: if the task description is under 8 words AND has no measurable outcome, you need `/spec`. If it's 20+ words with concrete files and a number, just `/assay`.

## Examples

```
/spec "make backtest faster"
  -> Brainstorming surfaces 4 framings: (a) speed up data loading, (b) parallelize the walk-forward loop, (c) cache feature computation, (d) precompute the index. Brandon picks (b). Interrogation produces success criteria like "walk-forward over 2010-2024 completes in <60s on M2 Pro" and risks like "parallel runs may produce non-reproducible random seeds". Spec saved as parallelize-walkforward-2026-05-17.md.

/spec "I should probably add Sharpe calculation to the engine" --risk=medium
  -> Brainstorming surfaces 3 framings of Sharpe (annualized vs daily, risk-free choice, lookback window). Brandon picks one. Interrogation produces measurable criteria and 3 risks. Spec saved.

/spec list --status=draft
  -> Shows all draft specs in current namespace.

/spec approve add-sharpe-engine-2026-05-17
  -> Flips status. Now /assay add-sharpe-engine-2026-05-17 will run.
```

## Coordination

- `/assay <spec-id>` consumes approved specs. Step 1 PARSE resolves spec-id, Step 11 COMMIT flips status to `shipped`.
- `judge-panel` reads the spec's `risk-tier` field to determine which judges to invoke.
- `done-gate` reads the spec's Success criteria section for Check 1.
- `project-memory` and `session-recall` provide the prior-context lookup in Step 3.
- `operator-model` provides the constraint bias for the interrogation.
- `notion-bridge` may push the spec to Notion at `/assay`'s Step 14 if Brandon approves the push.

## Failure modes

| Failure | Behavior |
|---------|----------|
| `superpowers:brainstorming` missing | Degrade to single-prompt 3-framing list. |
| `ecc:prp-prd` missing | Ask the 7 questions inline. |
| operator-model file missing | Continue without constraint bias. Log warning. |
| Brandon types `abort` at Step 7 | Discard. Nothing written to disk. |
| Spec-id collision | Append `-2`, `-3`, etc. until unique. |
| Brandon refuses measurable success criteria | Abort with the rule message above. |
