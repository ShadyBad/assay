---
name: operator-model
description: Maintains a self-updating model of Brandon's preferences, technical stack, business priorities, decision patterns, things he hates, and things he values. Reads at the start of every session and loads relevant sections based on task type. Updates when Brandon explicitly states a preference, when Brandon corrects Claude on a pattern, or when the same lesson recurs 3+ times across project-memory or private-journal-mcp entries. Coordinates with private-journal-mcp plugin as the backing store for raw reflections. Coordinates with claude-md-management plugin for session-learning capture. Use when Brandon makes a preference statement, when correcting a pattern, when starting any session (auto-load relevant sections), or when explicit "update your model of me" request. Never overwrites entries without showing diff. Append + dedupe only. Confidence-tagged entries.
---

# Operator Model Skill

Maintains a self-updating model of Brandon. This is the policy layer over `private-journal-mcp` plugin's storage. The journal stores raw reflections. This skill maintains a structured, queryable model derived from those reflections plus explicit statements.

## Storage

Primary file (policy layer): `$HOME/.claude/memory/global/operator-model.md`

Backing store (raw reflections): `private-journal-mcp` plugin's internal storage. Accessed via its MCP interface.

This skill never writes to the journal directly. It reads from the journal to detect patterns, then writes structured entries to operator-model.md.

## File Structure

The file has 7 sections, in this exact order:

1. Communication Preferences
2. Technical Stack Preferences
3. Business Priorities
4. Current Projects
5. Decision Patterns
6. Things Brandon Hates
7. Things Brandon Values

Each entry within a section has the format:
<ISO-date>: <observation> [confidence: low|med|high] [source: explicit|inferred|journal]

Sources:
- `explicit` — Brandon stated this directly ("I prefer X").
- `inferred` — derived from Brandon's behavior patterns.
- `journal` — extracted from `private-journal-mcp` entries showing repeated reflection on the same topic.

## Update Triggers

Append a new entry when:

1. **Explicit statement** — Brandon says "I prefer X", "I always want Y", "Never do Z". Append immediately with `confidence: high, source: explicit`.

2. **Correction** — Brandon corrects Claude on a recurring pattern. After 2 corrections of the same pattern, append with `confidence: med, source: inferred`. After 3, upgrade to `confidence: high`.

3. **Journal pattern** — `private-journal-mcp` contains 3+ entries reflecting on the same theme over 14+ days. Append with `confidence: med, source: journal`.

4. **Cross-project lesson** — Same lesson logged via `project-memory` in 3+ projects within 30 days. Append to Decision Patterns with `confidence: high, source: inferred`.

## Update Protocol

1. Before writing, search the relevant section for semantically similar entries.
2. If a similar entry exists:
   - If new entry is more specific, append the new one and mark the old as `[superseded by <date>]` inline (do NOT delete).
   - If new entry is less specific, skip the write.
   - If new entry contradicts, append the new one and mark the old as `[contradicted by <date>]` inline. Notify Brandon: "Operator model conflict detected on <topic>. Old: X. New: Y. Resolve?"
3. If no similar entry, append.
4. Show Brandon a diff of what was added before committing the change to disk, EXCEPT for explicit statements (those are pre-confirmed by the act of stating).

## Read Protocol

At the start of every session, load these sections by default:

- Communication Preferences (always — affects every response style)
- Current Projects (always — context for project detection)

Load these conditionally based on task type:

- Coding task → Technical Stack Preferences + Things Brandon Hates
- Strategy/planning task → Business Priorities + Things Brandon Values + Decision Patterns
- Decision request → Decision Patterns + Things Brandon Hates + Things Brandon Values
- Communication drafting → Communication Preferences (full section, including style overrides)
- Review/feedback task → Things Brandon Hates + Things Brandon Values

Load entries from the last 180 days by default. Older entries are still authoritative but require explicit reference.

## Confidence Decay

Entries marked `confidence: low` are downgraded if not reinforced within 90 days:

1. If no related event (correction, statement, journal mention) → mark `[stale]`.
2. If marked stale for 90+ days → mark `[archived]` (still in file, but not loaded by default).
3. Never deleted. Brandon may explicitly clear with `/operator-model clear <entry-id>`.

`confidence: high` entries do not decay.

## Conflict Resolution

When entries in different sections contradict (rare but possible):

1. Surface the conflict to Brandon at session start.
2. Show both entries and their sources.
3. Wait for explicit resolution: keep both, prefer A, prefer B, or rephrase.
4. If Brandon does not resolve within the session, default to the higher-confidence entry but note the unresolved conflict.

## Integration with claude-md-management

The `claude-md-management` plugin captures session learnings into CLAUDE.md files. This skill complements that:

- `claude-md-management` writes to project-specific CLAUDE.md (project conventions, codebase conventions).
- This skill writes to operator-model.md (Brandon's personal patterns, cross-project).

If `claude-md-management` captures a learning that is actually about Brandon (not the project), route it to this skill instead. Pattern: if the learning starts with "Brandon", "the user", "I", or uses first-person pronouns → route here. Otherwise → keep in CLAUDE.md.

## Integration with private-journal-mcp

This skill periodically queries `private-journal-mcp` for pattern detection. Specifically:

1. Once per session start, query for entries from last 14 days.
2. Cluster by topic (semantic similarity).
3. If a cluster has 3+ entries → candidate for operator-model update under appropriate section.
4. Surface the candidate to Brandon for confirmation before writing.

This skill does NOT write to the journal. The journal is Brandon's space.

## Invocation Contract

Modes:

- `load` — returns relevant sections based on task type. Input: task_type (coding|strategy|decision|communication|review).
- `append` — appends an entry. Inputs: section, observation, confidence, source.
- `query` — returns matching entries. Inputs: query string, optional section.
- `diff_preview` — shows what would be added without writing. Used for the user-confirmation flow.
- `decay_check` — runs confidence decay pass. Triggered weekly by skill-curator.

## Plugin Compatibility

Enhanced by:
- `private-journal-mcp` (backing store for raw reflections, pattern source).
- `claude-md-management` (complementary, project-scoped learnings).
- `project-memory` skill (cross-project pattern detection).

Required: none. Works with pure filesystem if plugins absent.

## Hard Constraints

- NEVER write to private-journal-mcp. Read only.
- NEVER delete entries. Mark as superseded, contradicted, stale, or archived.
- NEVER write without showing diff to Brandon, except for explicit statements.
- NEVER load more than the conditional sections for a given task type. Token budget matters.
- ALWAYS validate section name before writing. The 7 sections are fixed.
- ALWAYS preserve the section order in the file.
