---
name: spec-builder
description: Transforms a fuzzy goal into a crisp, /ship-consumable spec. Wires superpowers:brainstorming (divergent exploration), ecc:prp-prd (interrogation), and operator-model (Brandon's constraint bias) into a single interview that produces a 1-page spec at $HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md with status draft|approved|shipped. Use when Brandon types /spec, when a /ship task arrives without measurable success criteria, when Brandon says "I want to build X but I'm not sure what", or when an idea has been kicking around long enough to deserve a written hypothesis. Coordinates with project-memory (loads relevant prior lessons), session-recall (surfaces prior similar specs), and judge-panel (risk-tier classification for downstream /ship). Pinned. Never silently overwrites an existing spec — collisions get a numeric suffix.
---

# spec-builder

The missing step between fuzzy goal and `/ship`. Most bad ships come from shipping the wrong thing well. This skill forces the scoping moment.

## When to invoke

- Brandon types `/spec "<fuzzy goal>"` directly.
- Brandon types `/ship "<task>"` and the task description has no measurable success criteria (no numbers, no observable outcome, no test plan possible).
- Brandon says variations of: "I want to build X", "I should probably tackle Y", "what should I do about Z", "I have an idea for...".
- An auto-co or margin-invest task has been mentioned 3+ times across sessions without a spec being written.

## Invocation contract

```
/spec "<fuzzy goal>"                    # full interrogation
/spec "<fuzzy goal>" --quick            # skip brainstorming, jump to prp-prd
/spec "<fuzzy goal>" --namespace=<ns>   # override detection
/spec "<fuzzy goal>" --risk=<tier>      # pre-set risk classification
/spec list                              # show all specs in current namespace
/spec list --status=draft               # filter
/spec show <spec-id>                    # print spec contents
/spec approve <spec-id>                 # flip status draft -> approved
/spec revise <spec-id>                  # reopen for edits, flip status back to draft
```

## Pipeline

### Step 1: PARSE

Extract from invocation:
- Fuzzy goal string.
- Flags (`--quick`, `--namespace`, `--risk`).
- Mode (`list`, `show`, `approve`, `revise`, or default new-spec).

If mode is `list`, `show`, `approve`, or `revise`: jump to the corresponding section below. Otherwise continue.

### Step 2: DETECT NAMESPACE

Use the project detection rules from `~/.claude/CLAUDE.md`:
1. `.claude/project-name` file (walk up to $HOME).
2. `git remote -v` pattern match (`auto-co`, `margin-invest`).
3. cwd path match (`/auto-co/`, `/margin-invest/`, `/margin_invest/`, `/margin-invest-backtest/`).
4. Fallback: `personal`.

`margin_invest/` and `margin-invest-backtest/` both map to namespace `margin-invest` (per project CLAUDE.md).

If `--namespace=` flag is set, override and log.

### Step 3: LOAD CONTEXT

In parallel:
1. **operator-model** — load Brandon's preferences. Pull the relevant section based on the goal's category (technical / business / process). Pull all "Things Brandon Hates" entries unconditionally.
2. **project-memory** — load last 50 lessons from `$HOME/.claude/memory/projects/<ns>/lessons.md`. Surface 3-5 most relevant to the fuzzy goal.
3. **session-recall** — search for prior specs with overlapping keywords. If a prior spec exists for a similar goal, surface its `spec-id` and status before continuing.

If session-recall finds a prior spec with status `draft` or `approved` on the same topic: stop and ask Brandon "Looks like spec `<spec-id>` covers similar ground (status: `<status>`). Revise it, or write a new one?" Default action: revise existing.

### Step 4: DIVERGE (skipped if --quick)

Invoke `superpowers:brainstorming` plugin with:
- Fuzzy goal.
- Loaded operator-model constraints (so brainstorming respects "no premature optimization", "walk-forward before tuning", etc.).
- The 3-5 surfaced lessons from Step 3.

Goal: produce 3-5 alternative framings of the goal. Not solutions — framings. "What problem are we actually solving?" Brandon picks one (or types a new framing). The picked framing replaces the original fuzzy goal as the spec subject.

If `superpowers:brainstorming` plugin is unavailable: degrade to a single prompt — "Here are 3 ways I could read this goal: [A] [B] [C]. Which one, or describe a different framing?"

### Step 5: INTERROGATE

Invoke `ecc:prp-prd` skill with the picked framing.

The interrogation must surface answers to:

1. **Problem** — What hurts? Who feels it? Why now? (1-3 sentences)
2. **Hypothesis** — What is the proposed fix and why will it work? (1 paragraph)
3. **Success criteria** — Three measurable outcomes. At least one must be quantitative (a number, a test passing, a metric moving).
4. **Non-goals** — Three things this is explicitly NOT doing. Forces scope discipline.
5. **Constraints** — What is fixed? Pull from operator-model (no premature optimization, etc.) and project context (margin_invest frozen, aie_roadmap is tracking only, etc.).
6. **Risks / Ways this could be wrong** — Adversarial. Minimum 3 bullets. Mandatory per margin-invest-backtest convention in project CLAUDE.md.
7. **Plan sketch** — High-level steps (3-7 bullets). Not a full plan — that's `/ship`'s job in Step 3 PLAN. Just enough to estimate scope.

If `ecc:prp-prd` plugin is unavailable: ask the 7 questions directly, one at a time.

### Step 6: SYNTHESIZE

Generate the spec markdown using the template in the "Spec Template" section below. Auto-fill:
- `spec-id`: `<kebab-slug>-<YYYY-MM-DD>` where slug is kebab-cased from the title, max 4 words. If a spec with this id exists in the namespace, append `-2`, `-3`, etc.
- `created`: today's date.
- `namespace`: from Step 2.
- `status`: `draft`.
- `risk-tier`: classify using the rules from `~/.claude/CLAUDE.md` Risk Tiers section. If `--risk=` flag set, override.

Title is generated from the picked framing in Step 4, max 8 words.

### Step 7: SHOW + APPROVE

Show the full spec to Brandon. Ask:

```
Spec written: <spec-id>
Path: $HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md
Status: draft

Options:
  approve — flip status to approved, ready for /ship
  draft   — save as draft, return to it later
  revise  — re-open interrogation on a specific section
  abort   — discard, do not save
```

Default response: `draft`. Brandon must explicitly type `approve` to flip status. This is the gate that protects `/ship` from running unapproved specs.

### Step 8: WRITE

Create directory if missing: `$HOME/.claude/memory/projects/<ns>/specs/`.

Write the spec to `$HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md`.

If status is `approved`: also append a one-line entry to `$HOME/.claude/memory/projects/<ns>/specs/_index.md`:
```
| <spec-id> | <title> | <risk-tier> | approved | <created> | unset |
```

Index columns: spec-id, title, risk-tier, status, created, shipped-at.

### Step 9: PRINT NEXT ACTION

```
Spec <spec-id> saved with status=<status>.

<if approved:>
Next: /ship <spec-id>

<if draft:>
Next: /spec approve <spec-id>   # when ready to ship
       /spec revise <spec-id>   # to keep editing
```

## Spec Template

```markdown
---
spec-id: <slug>-<YYYY-MM-DD>
title: <short title, max 8 words>
namespace: auto-co | margin-invest | personal
created: <YYYY-MM-DD>
status: draft
risk-tier: trivial | low | medium | high | critical
shipped-at:
shipped-commit:
---

# <title>

## Problem

<1-3 sentences. What hurts? Who feels it? Why now?>

## Hypothesis

<1 paragraph. Proposed fix and why it will work.>

## Success criteria

- <Measurable bullet 1 — must include a number, test name, or observable outcome>
- <Measurable bullet 2>
- <Measurable bullet 3>

## Non-goals

- <Explicit out-of-scope 1>
- <Explicit out-of-scope 2>
- <Explicit out-of-scope 3>

## Constraints

- <From operator-model — e.g. no premature optimization>
- <From project — e.g. margin_invest is frozen, don't touch>
- <From session — e.g. <2 hours of work>

## Risks / Ways this could be wrong

- <Adversarial bullet 1>
- <Adversarial bullet 2>
- <Adversarial bullet 3>

## Plan sketch

- <Step / file / approach 1>
- <Step / file / approach 2>
- <Step / file / approach 3>

## Approval

- [ ] Brandon reviewed and approved
```

## Modes

### list

Show all specs in current namespace as a table:

```
| spec-id | title | tier | status | created | shipped-at |
```

Source: `$HOME/.claude/memory/projects/<ns>/specs/_index.md` if present, otherwise scan the directory and reconstruct.

`--status=<status>` filters. `--namespace=all` shows across all namespaces.

### show <spec-id>

Resolve spec-id in current namespace. If not found, search across all namespaces and surface the match. Print the full spec contents.

### approve <spec-id>

Flip status from `draft` to `approved`. Refuse if status is `shipped` (already done — write a new spec for follow-up work).

Update the `_index.md` row.

### revise <spec-id>

Flip status from any to `draft`. Re-enter interrogation, focused on the sections Brandon names. Save as same spec-id (not a new one) — preserves history.

If status was `shipped`: warn — "This spec already shipped. Revising creates a new draft on the same spec-id. Ship history will be preserved in the frontmatter."

## Coordination with /ship

`/ship` Step 1 PARSE checks if the first arg matches a spec-id pattern (`<slug>-\d{4}-\d{2}-\d{2}(-\d+)?`). If yes:

1. Resolve in current namespace's specs/ directory.
2. If found, load the spec.
3. If status is `draft`: refuse. "Run `/spec approve <spec-id>` first."
4. If status is `shipped`: warn. Allow with `--force`. Otherwise abort.
5. If status is `approved`: snapshot the spec into the session state directory. Lock it for the duration of this /ship run.

`/ship` Step 11 COMMIT, on successful commit: update spec frontmatter `status: shipped`, `shipped-at: <date>`, `shipped-commit: <SHA>`. Update `_index.md` row.

This is what makes a spec a contract, not just a doc.

## Failure modes

| Failure | Default behavior |
|---------|------------------|
| `superpowers:brainstorming` missing | Degrade to single-prompt 3-framing list. |
| `ecc:prp-prd` missing | Ask 7 questions inline. |
| operator-model file missing | Continue without constraint bias. Log warning. |
| Namespace directory creation fails | Surface error. Do not write spec. |
| Spec-id collision (same slug, same day) | Append `-2`, `-3`, etc. until unique. |
| Brandon types `abort` at Step 7 | Discard. Nothing written. |
| Brandon revises a `shipped` spec | Preserve `shipped-at` and `shipped-commit`. New draft is on the same id. |

## Hard constraints

- NEVER write a spec with `status: approved` without Brandon explicitly typing `approve`.
- NEVER overwrite a `shipped` spec. Revising creates a new draft on the same id; ship history is preserved.
- NEVER skip the Risks section. Inherited from margin-invest-backtest convention — every spec must end with an adversarial section.
- NEVER infer success criteria. If Brandon refuses to give a measurable outcome, abort the spec with "Without measurable success criteria, /ship cannot verify done. Walk away or come back with a number."
- ALWAYS load operator-model before interrogation. Brandon's constraints bias the questions.
- ALWAYS append to `_index.md` so `/spec list` and `/ship`'s spec-id resolution stay cheap.

## Plugin dependencies

- `superpowers:brainstorming` — Step 4 divergent framing. Graceful degrade.
- `ecc:prp-prd` — Step 5 interrogation. Graceful degrade.
- `operator-model` skill — Step 3 constraint loading.
- `project-memory` skill — Step 3 lesson loading.
- `session-recall` skill — Step 3 prior-spec search.

All other skills (judge-panel, done-gate, commit-protocol, notion-bridge) interact with this skill only through `/ship` once the spec is approved.
