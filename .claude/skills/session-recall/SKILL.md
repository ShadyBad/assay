---
name: session-recall
description: Searches past sessions and project lessons for relevant prior context. Wraps the episodic-memory MCP plugin as primary backend and falls back to ripgrep across local memory if MCP is unavailable. Use when Brandon asks "have we done X before", "what did we decide about Y", "remind me how we handled Z", or "continue where we left off". Also invoke automatically when starting a task that smells familiar — pattern match against project-memory lessons and session transcripts. Returns top 3-5 matches with date, project context, and relevant excerpt. Searches in parallel across episodic-memory MCP, project lessons via project-memory skill, and session transcripts in $HOME/.claude/memory/sessions/. Combines and deduplicates results by semantic similarity. Garbage collects session transcripts older than 90 days unless tagged keep.
---

# Session Recall Skill

Searches across past sessions and lessons to surface relevant prior context. This skill wraps `episodic-memory` MCP rather than duplicating it.

## Storage Layout
$HOME/.claude/memory/sessions/
├── 2026-05-16-a1b2c3/
│   ├── transcript.md
│   ├── metadata.json
│   └── tags
├── 2026-05-15-d4e5f6/
│   └── ...

$HOME/.claude/memory/projects/<ns>/specs/
├── <spec-id>.md      # YAML frontmatter + 7 sections (from spec-builder)
├── _index.md         # table of all specs in namespace
└── ...

Plus the `episodic-memory` MCP plugin's internal storage (which we do not touch directly — we query through the MCP).

## Backends, in Priority Order

1. **`episodic-memory` MCP** (primary). Query via its standard search interface. Faster, semantic, already indexed.
2. **`project-memory` skill** (secondary). Calls project-memory's `search` mode on the current project's lessons.md plus archives.
3. **Spec library** (tertiary). Ripgrep over `$HOME/.claude/memory/projects/<ns>/specs/*.md` for the current namespace. Surfaces prior specs matching the query — critical for the "have I scoped this before" lookup that `spec-builder` Step 3 relies on.
4. **Ripgrep over session transcripts** (fallback). Used if MCP is unavailable or returns empty.

## Trigger Patterns

Auto-invoke when Brandon's message contains:

- "have we" or "have I" (e.g., "have we built this before")
- "what did we" or "what did I" (e.g., "what did we decide")
- "remind me" (e.g., "remind me how we configured X")
- "last time" or "previously" or "before"
- "continue" + "from where" or "left off"
- Direct reference to past work without enough context to act ("the thing we built last week")

Also invoke without explicit ask when:
- Task description matches a project lesson tag with high confidence (e.g., user says "add a new bond scoring rule" and the project has 5+ lessons tagged `scoring`).
- Starting a task in a project with 100+ lessons — load relevant subset before acting.

## Query Construction

When invoked:

1. Extract the core noun phrase from Brandon's message (e.g., "bond scoring formula", "auth flow refactor").
2. Submit to all three backends in parallel.
3. Set max results per backend: 5.

For `episodic-memory` MCP: use semantic search via the MCP's search tool.
For `project-memory`: pass query as the search string.
For spec library: `rg -i --max-count=3 -C 3 "<query>" $HOME/.claude/memory/projects/<ns>/specs/`. Extract `spec-id` and `status` from each match's frontmatter and surface as part of the result.
For ripgrep fallback: `rg -i --max-count=3 -C 3 "<query>" $HOME/.claude/memory/sessions/`

## Result Aggregation

After all backends return:

1. Combine results into a unified list.
2. Deduplicate: if two results reference the same session ID or lesson timestamp, keep only one.
3. Score each result:
   - Same project as current task: +2
   - Within last 30 days: +2
   - Within last 90 days: +1
   - Tagged with `keep`: +1
   - Exact phrase match in title/summary: +3
   - Semantic match only: +1
   - Spec match with `status: draft` or `status: approved`: +4 (actionable prior scoping — surfaces first so spec-builder can offer to revise instead of duplicate)
   - Spec match with `status: shipped`: +2 (historical context)
4. Sort descending by score.
5. Return top 3-5 to the user with this format:
RECALL RESULTS for "<query>":

[<date>] [<project>] <session-or-lesson-title>
Excerpt: <5-line context>
Source: <episodic-memory | project-memory | session-file>
...
...

If none of these match what you remember, search wider with: /recall "<broader query>"

If all backends return empty:
RECALL: No matches for "<query>" in last 90 days of sessions or project lessons.
Suggestions:

Try a broader query
Check the archived-lessons.md for this project: <path>


## Manual Invocation

Brandon can invoke directly with a slash command (defined elsewhere in `/recall`):

- `/recall "<query>"` — full search.
- `/recall --project=auto-co "<query>"` — restrict to one project.
- `/recall --last=30d "<query>"` — restrict to recency window.
- `/recall --tag=<tag> "<query>"` — restrict to a tag.

## Session Lifecycle

Every Claude Code session that uses `/assay` saves a transcript:

1. Session directory: `$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<short-id>/`
2. `transcript.md` — task description, plan, executed steps, outcomes, lessons logged.
3. `metadata.json` — `{"project": "<name>", "tags": [...], "duration_seconds": N, "ship_verdict": "..."}`.
4. `tags` — newline-delimited tags for fast ripgrep.

The `episodic-memory` MCP indexes these automatically. If MCP unavailable, ripgrep does it the slow way.

## Garbage Collection

Run weekly (triggered by `skill-curator`):

1. List sessions older than 90 days.
2. For each, check `metadata.json` for `keep: true` or `tags` containing `keep`.
3. If not marked keep, delete the session directory.
4. If marked keep, archive to `$HOME/.claude/memory/sessions/_archive/<year>/<month>/`.
5. Notify `episodic-memory` MCP to reindex.

NEVER delete sessions that contain blocking concerns from judge-panel reviews — those are forensic value. Tag them `keep` automatically when the panel returns BLOCK.

## Plugin Compatibility

Required: none (ripgrep fallback works with pure filesystem).
Enhanced by:
- `episodic-memory` MCP plugin (primary backend, faster, semantic).
- `project-memory` skill (secondary backend, structured lessons).
- ripgrep (fallback).

If episodic-memory MCP is unreachable, log degradation and continue with ripgrep + project-memory. Performance drops but correctness does not.

## Hard Constraints

- NEVER return more than 5 results unless Brandon explicitly asks for more.
- NEVER include session content from a different user's namespace (this is single-user, but enforce by always restricting to $HOME).
- NEVER delete a session without garbage-collection check (keep tag, age, blocking-concern history).
- ALWAYS attempt all three backends in parallel. Do not fail fast on one.
- ALWAYS deduplicate before returning. Showing the same lesson 3 times across backends is noise.
