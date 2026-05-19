---
name: cross-learn
description: Scan lessons.md across all 3 project namespaces (auto-co, margin-invest, personal), cluster recurring patterns, and propose system-level updates — new skills, CLAUDE.md rules, or operator-model entries. Closes the gap where a lesson learned in one project stays trapped there. Read-only on inputs; all outputs are proposals to _proposed/ requiring Brandon approval. Run on demand or when any project's lessons.md crosses 20+ entries.
argument-hint: "[--min-cluster=<n>] [--projects=<list>] [--dry-run] [--since=<date>]"
---

# /cross-learn — Cross-Project Lesson Federation

Scans `$HOME/.claude/memory/projects/<ns>/lessons.md` for recurring patterns across namespaces and proposes promotion to system-level: new skill, global CLAUDE.md rule, or operator-model entry. Federation, not duplication — never edits the source lessons files except to tag federated entries.

Companion to `skill-curator` (which works on skill files) and `operator-model` (which works on Brandon's preferences). This works on lessons.

## Flag Parsing (Step 0)

| Flag | Effect |
|------|--------|
| `--min-cluster=<n>` | Minimum lessons per cluster to qualify as a pattern. Default: 3. |
| `--projects=<list>` | Limit to comma-separated project list. Default: all 3 (auto-co, margin-invest, personal). |
| `--dry-run` | Surface clusters and proposals but write nothing. |
| `--since=<date>` | Only consider lessons dated ≥ this ISO date. Default: all. |

Cluster qualification: ≥ `min-cluster` entries AND spans ≥ 2 distinct projects. A cluster confined to one project is not cross-project — defer to `skill-curator` instead.

## Pipeline

### Step 1: LOAD

For each project in scope:
- Read `$HOME/.claude/memory/projects/<project>/lessons.md`.
- Parse entries (one per line, pipe-delimited per project-memory skill: `<ISO-timestamp> | <task-summary> | <lesson> | <tags>`).
- Skip entries whose tags contain `federated:*` (already promoted — see project-memory `exclude_federated` rule).
- Skip empty files. Skip files where last entry is older than `--since` if set.

Output: flat list of `(project, timestamp, task_summary, lesson, tags)` tuples.

If total entries across all projects < 10: surface "Not enough lessons to federate (have <N>, need ≥10). Run `/cross-learn` again after more `/ship` runs accumulate lessons." Halt cleanly.

### Step 2: CLUSTER

Pattern-match across the corpus. Use these signals in order:

1. **Verb match** — group by leading action verb (use, prefer, avoid, never, always, ship, skip, test).
2. **Domain noun match** — group by recurring subject nouns (test, lint, commit, MCP, judge, schema, migration, push, branch, type, mock, plan).
3. **Negation polarity** — separate "do X" from "don't do X" even when topic matches.
4. **Verbatim phrase overlap** — entries sharing a ≥3-word phrase get auto-clustered.

For each candidate cluster:
- Count entries.
- Count distinct projects.
- Drop if entries < `min-cluster` OR projects < 2.

Output: list of clusters, each `{topic, entries[], projects[], polarity}`.

### Step 3: CLASSIFY PROPOSAL TYPE

For each surviving cluster, decide proposal type using this priority:

| Pattern shape | Proposal type | Output path |
|---------------|---------------|-------------|
| Multi-step operational sequence (≥3 steps implied, reusable workflow) | **New skill** | `$HOME/.claude/skills/_proposed/<slug>/SKILL.md` |
| Constraint applicable across all projects (do X / never Y at the system level) | **CLAUDE.md rule** | `$HOME/.claude/skills/_proposed/_claude-md/<date>-<slug>.md` |
| Brandon-preference signal (style, tooling, communication, decision pattern) | **Operator-model entry** | `$HOME/.claude/skills/_proposed/_operator-model/<date>-<slug>.md` |
| Cross-cutting code/diff pattern (anti-pattern that hookify could enforce) | **Hookify rule proposal** | `$HOME/.claude/skills/_proposed/_hookify/<date>-<slug>.md` |
| Ambiguous | Present all candidate types to Brandon, let him pick. |

Each proposal file must contain:
- `## Cluster` — the topic and entry count.
- `## Source lessons` — verbatim quotes with `<project> | <timestamp> | <lesson>` prefix.
- `## Proposed promotion` — full text of the proposed skill/rule/entry, ready to copy.
- `## Brandon-action options` — promote / refine / reject / defer-to-curator.

### Step 4: APPROVAL LOOP

Present proposals one at a time to Brandon. For each:

```
Cluster: <topic>  (<N> entries, projects: <list>)
Proposed: <type> — <one-line summary>
Source: <first 2 quotes truncated>

Actions: (p)romote / (r)efine / (s)kip / (d)efer
```

- **promote** → move proposal file to its target location (skill → `~/.claude/skills/<slug>/`, CLAUDE.md → append diff to `~/.claude/CLAUDE.md` after showing diff, operator-model → invoke `operator-model` skill with the proposed entry, hookify → leave in `_proposed/_hookify/` for hookify plugin to pick up).
- **refine** → Brandon edits text inline, then re-prompt.
- **skip** → leave file in `_proposed/`, marked rejected with date.
- **defer** → leave file in `_proposed/`, no mark — Brandon revisits later.

Never auto-promote. Never auto-edit CLAUDE.md without showing the exact diff line.

### Step 5: TAG SOURCE LESSONS

For each lesson that fed an approved promotion, append `,federated:<slug>` to the tags column (last pipe-delimited field) of the original entry in its `lessons.md`. This is the ONLY write to source files. Per project-memory's federated-lessons rule, tagged entries are excluded from the next `/cross-learn` clustering pass.

Skip this step for skipped/deferred clusters. Never edit any other field of the source entry.

### Step 6: REPORT

```
CROSS-LEARN COMPLETE
Lessons scanned: <count>  Projects: <list>
Clusters found: <count>   Qualified (≥<min>): <count>
Proposals written: <count> → skill: <n>  CLAUDE.md: <n>  operator-model: <n>  hookify: <n>
Promoted: <count>
Skipped: <count>
Deferred: <count>
Next: review _proposed/ at your convenience; rerun /cross-learn after ~10 more lessons accumulate.
```

## Hard Constraints

- NEVER edit source `lessons.md` except to append `,federated:<slug>` to the tags column per Step 5.
- NEVER auto-promote. Every promotion is per-cluster Brandon approval.
- NEVER write to `CLAUDE.md` without showing the diff line and getting explicit yes.
- NEVER cluster within a single project — defer to `skill-curator` for those.
- NEVER overwrite an existing proposal file. Suffix with `-2`, `-3` on collision.
- NEVER delete proposals. Skipped ones get a `# Status: skipped <date>` line appended; deferred get no mark.
- ALWAYS produce the final report, even when zero clusters qualify.

## When to Run

- Manually: when any project's `lessons.md` crosses 20+ entries.
- Auto-trigger candidates (not wired yet): end of `/ship` Step 13 if `skill-curator` is also due AND total lessons across projects ≥ 30 since last `/cross-learn` run.
- Brandon asks: "what patterns are repeating across projects" / "any system-level lessons hiding" / "federate the lessons".

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Project dir missing | Skip that project, note in report. |
| `lessons.md` empty | Skip silently. |
| `_proposed/` dir missing | Create it. |
| Brandon types stop mid-loop | Save remaining clusters to `~/.claude/memory/sessions/<id>/cross-learn-pending.md`. Exit clean. |
| Operator-model skill unavailable | Write proposal to `_proposed/_operator-model/` and surface manual-edit instructions. |

## Coordination

- `skill-curator` — non-overlapping. Curator works on skill files; cross-learn works on lesson entries. Each can produce skill proposals; both land in `_proposed/`. No collision because slug includes source (`cross-learn-<slug>` vs `curator-<slug>`).
- `operator-model` — cross-learn proposes entries; the operator-model skill performs the actual append with Brandon-approved diff preview.
- `project-memory` — cross-learn reads its files; writes only the `[federated → ...]` tag.
- `hookify` plugin — cross-learn drops proposals in `_proposed/_hookify/`; Brandon runs `/hookify` separately to wire them up.

## Quick Reference

```
/cross-learn                                   # Default. min-cluster=3, all 3 projects.
/cross-learn --min-cluster=5                   # Stricter pattern threshold.
/cross-learn --projects=auto-co,margin-invest  # Skip personal namespace.
/cross-learn --since=2026-01-01                # Only recent lessons.
/cross-learn --dry-run                         # Show clusters and proposals; write nothing.
```
