---
name: ship
description: Master orchestrator. Runs the full 14-step pipeline from task parse through commit and learn. Coordinates all custom skills (spec-builder, judge-panel, project-memory, session-recall, operator-model, skill-curator, notion-bridge, mcp-router, done-gate, commit-protocol) and key plugins (superpowers ecosystem, commit-commands, github). Use whenever Brandon wants to make a meaningful change to a project — code, docs, configuration, or strategy artifacts. Two invocation forms: /ship "<task description>" for direct execution, or /ship <spec-id> to consume an approved spec produced by /spec. Supports flags for risk classification, judge control, MCP control, check skipping, and commit behavior. Saves state on interrupt for /ship resume.
argument-hint: <spec-id> | "<task description>" [--judges] [--no-judges] [--risk=<tier>] [--mcps=<list>] [--skip-tests] [--skip-lint] [--skip-types] [--force] [--commit-message=<msg>] [--amend] [--no-push] [--auto-push] [--dry-run]
---

# /ship — Master Orchestrator

Runs the 14-step pipeline. Every step delegates to a skill. This file is the conductor, not the orchestra.

## Flag Parsing (Step 0)

Parse the invocation arguments before starting the pipeline. The first argument is the task description. Remaining flags adjust pipeline behavior.

| Flag | Effect |
|------|--------|
| `--judges` | Force judge-panel invocation even at TRIVIAL tier. |
| `--no-judges` | Skip judge-panel. Only valid for TRIVIAL/LOW tiers. HIGH/CRITICAL still enforces judges. |
| `--risk=<tier>` | Override automatic risk classification. Values: trivial, low, medium, high, critical. |
| `--mcps=<list>` | Override mcp-router's category-based loading. Comma-separated MCP names. Prefixes: `+` to add to category default, `-` to exclude. |
| `--no-mcps` | Load no MCPs (rare; pure local work). |
| `--skip-tests` | Bypass done-gate Checks 2 and 3. Requires note explaining why. |
| `--skip-lint` | Bypass done-gate Check 5. |
| `--skip-types` | Bypass done-gate Check 6. |
| `--force` | Bypass all done-gate checks except Check 8 (Brandon approval). Logged to force-bypass-log. Emergency use only. |
| `--commit-message="<msg>"` | Use exact message in commit-protocol. Skip generation. |
| `--amend` | Amend last commit instead of new commit. |
| `--no-push` | Skip the push question after commit. |
| `--auto-push` | Push immediately after commit without asking. |
| `--dry-run` | Run pipeline through Step 10 DONE GATE, surface diff + judge verdict, then halt and save state. `/ship resume` picks up at Step 11 COMMIT. Inspection sandbox — no files committed. |
| `resume` | Resume the most recent interrupted /ship session (special positional arg). |

If `--force` and `--no-judges` are both set and risk tier is HIGH/CRITICAL, refuse: "HIGH/CRITICAL changes cannot bypass judge-panel. Drop --no-judges or accept lower risk classification."

## Pipeline: The 14 Steps

### Step 1: PARSE

**Spec-id resolution (runs first).** If the first positional argument matches the pattern `<slug>-\d{4}-\d{2}-\d{2}(-\d+)?` (e.g. `parallelize-walkforward-2026-05-17` or `add-sharpe-engine-2026-05-17-2`), treat it as a spec-id from the `spec-builder` skill:

1. Detect namespace using the same rules as project-memory (`.claude/project-name` → git remote → cwd → `personal`).
2. Resolve to `$HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md`. If not found in current namespace, search across all namespaces and surface the match.
3. Load the spec's YAML frontmatter (`spec-id`, `title`, `namespace`, `created`, `status`, `risk-tier`, `shipped-at`, `shipped-commit`) and 7 sections (Problem, Hypothesis, Success criteria, Non-goals, Constraints, Risks, Plan sketch).
4. Status gate:
   - `draft` — refuse: "Spec `<spec-id>` is still draft. Run `/spec approve <spec-id>` first."
   - `shipped` — warn: "Spec `<spec-id>` already shipped on `<shipped-at>` as commit `<shipped-commit>`. Re-ship with `--force` or write a new spec."
   - `approved` — proceed.
5. Snapshot the spec into the session state directory (`$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/spec-snapshot.md`). Lock for the duration of this /ship run.
6. Use the spec's `title` as task description, `risk-tier` as the locked risk tier (skip Step 4 RISK CLASSIFY unless `--risk=` overrides), and Success criteria as inputs to done-gate Check 1.

If the first argument is not a spec-id pattern, fall through to task-description parsing below.

**Task-description parsing (default).** Parse the task description. Extract:
- Primary verb (build, fix, refactor, research, design, ship, deploy).
- Subject (what is being changed).
- Project context (auto-co, margin-invest, personal, or unspecified — infer from cwd).
- Explicit scope hints (file paths, function names, ticket numbers mentioned).

Output a structured task spec used by later steps. If task description is too vague (under 8 words and no explicit scope), ask Brandon for one clarifying detail. Otherwise proceed.

### Step 2: CONTEXT LOAD

Invoke these skills in parallel where possible:

1. **project-memory** — load `lessons.md` for the detected project. Surface 3-5 most relevant lessons to current task.
2. **session-recall** — search past sessions for matching keywords. Use 3-tier fallback (episodic-memory MCP → project-memory grep → ripgrep).
3. **operator-model** — load Brandon's preferences. Apply Things Brandon Hates filter to suppress patterns he has rejected.

Output: a context bundle (lessons + recall hits + applicable Brandon prefs) used by PLAN and EXECUTE steps.

### Step 3: PLAN

Generate a plan for the task.

- For TRIVIAL/LOW tasks: a 3-bullet plan inline.
- For MEDIUM tasks: invoke `superpowers:brainstorming` plugin if available, else generate 5-10 step plan inline.
- For HIGH/CRITICAL tasks: invoke `superpowers:writing-plans` plugin to produce a structured plan with risk analysis, fallback paths, and test strategy.

The plan must include:
- Approach (1-2 sentences).
- Affected files (best guess).
- Test strategy (write new tests, modify existing, skip with reason).
- Estimated tool call count (rough budget).

**Breadth-First Heuristic (HIGH/CRITICAL).** Anthropic finding: agents default to overly long, specific queries that return few results. For HIGH/CRITICAL plans, force a breadth-first pass first:

1. Start wide. Enumerate the affected surface (files, callers, dependent skills, downstream consumers) before drilling into any one area.
2. Evaluate what exists. Don't write changes until the existing surface is mapped.
3. Narrow progressively. Pick the smallest viable slice once the landscape is known.

Plans that skip straight to a specific file edit on HIGH/CRITICAL get a one-shot revise prompt: "Plan jumped to specifics. Show the broader surface first."

Show plan to Brandon. Accept: ship, revise, abort.
- ship — proceed to Step 4.
- revise — incorporate Brandon's feedback, regenerate, show again.
- abort — halt pipeline, save state.

### Step 4: RISK CLASSIFY

Classify the change into one of 5 risk tiers (from CLAUDE.md):

- **TRIVIAL** — typo fix, comment edit, doc-only change, formatting.
- **LOW** — single-file change, <30 lines, isolated.
- **MEDIUM** — single feature, 1-3 files, no schema/API change.
- **HIGH** — multi-file change, schema/API impact, security-adjacent, or financial.
- **CRITICAL** — irreversible (data migration, prod deploy, payment flow, auth change).

Classification signals:
- File count and diff size (from plan).
- File paths (anything under `auth/`, `payments/`, `migrations/`, `schema/`, `infra/` is HIGH+).
- Keywords in task description (deploy, migrate, delete, drop table, force, rotate keys = HIGH+).
- Project-specific overrides (margin-invest financial calc = HIGH minimum).

If `--risk=<tier>` flag is set, override. Show the override to Brandon and confirm before continuing.

**Effort Budget by Tier.** Risk tier locks a ceiling on subagent count and per-subagent tool calls. Pattern adapted from the Anthropic multi-agent research system: scale agent effort to query complexity, embed budgets in the prompt to prevent overinvestment in simple work. Ceilings are calibrated for /ship's code-orchestrator task shape, not research-product fan-out.

TRIVIAL/LOW always execute inline (single agent); no subagent budget applies. Budget table covers MEDIUM+.

| Tier | Max subagents | Max tool calls / subagent | Soft total ceiling |
|------|---------------|---------------------------|---------------------|
| MEDIUM | 2–3 | 15 | 45 |
| HIGH | 3–5 | 20 | 100 |
| CRITICAL | 5–8 | 25 | 200 (logged per call when exceeded) |

The lead maintains a `tool_call_tally` field in `state.json`, updated on each subagent dispatch and return. Subagent counts are hard; total tool-call ceiling is soft (a single overrun is allowed if a subagent is mid-finalization). If a subagent approaches its per-agent cap, it must finalize and return an artifact ref (Step 7) rather than continue. If the soft total ceiling is hit, halt EXECUTE and surface to Brandon: "(a) raise budget, (b) take results so far, (c) abort and save state."

Output: risk tier + effort budget locked for the rest of the pipeline.

### Step 5: DISPATCH

Decide execution strategy:

- TRIVIAL/LOW: execute inline (single agent).
- MEDIUM: execute inline unless plan has 3+ independent subtasks → invoke `superpowers:subagent-driven-development` for parallelization.
- HIGH/CRITICAL: always invoke `superpowers:subagent-driven-development`. Each subagent gets only its slice of context.

If subagent-driven-development plugin is not installed, fall back to sequential inline execution. Note in final report.

**Structured Delegation Brief (mandatory for every dispatched subagent).** Anthropic finding: vague tasks cause duplicate work, scope gaps, and misinterpretation. Every actual subagent dispatch (via the Agent/Task tool, `superpowers:subagent-driven-development`, or equivalent) must include all four fields. Inline lead execution does NOT require a brief — the lead already has the plan and operator-model in context. The brief exists to compress what the lead knows into what a fresh subagent needs.

```
objective:     <one sentence stating the exact outcome. Not "research X" — "produce a list of all callers of function X with file:line refs">
output_format: <exact shape of the return value. e.g. "JSON: {findings: [{file, line, snippet}]}" or "markdown table with columns A|B|C">
tool_list:     <explicit tools/skills/MCPs the subagent may use. Anything not listed is off-limits. e.g. "Grep, Read; do not edit files">
boundaries:    <what is OUT of scope. e.g. "do not touch tests/, do not propose alternative designs, do not exceed 15 tool calls per Step 4 budget">
```

Lead fills the brief from the plan + risk tier's effort budget. Before dispatch, lead validates all four fields are non-empty; if any field is missing, halt and log `BRIEF_INCOMPLETE: <field>` before re-attempting. Subagents that return work outside `boundaries` are rejected; lead re-dispatches with sharpened boundaries. Boundary-violation re-dispatches are capped at 2 per subagent slot; third violation halts EXECUTE and surfaces to Brandon with the offending output.

**Parallel Tool Call Rule.** Subagents and inline lead executions issue 3+ tool calls in a single message when the calls are independent. Sequential tool use is reserved for genuinely dependent operations. This codifies what's already best practice — it's here so the rule is greppable when a slow sequential pattern is observed.

### Step 6: MCP ROUTE

Invoke **mcp-router** with the task spec from Step 1. Router classifies into one of 9 categories and loads relevant MCPs. Honor `--mcps=` and `--no-mcps` flags from Step 0.

Output: loaded MCPs list. Pass to EXECUTE step.

### Step 7: EXECUTE

Run the plan.

- Inline execution: agent executes the plan step by step.
- Subagent execution: dispatch parallel subagents per plan section. Each subagent receives:
  - Its assigned plan section.
  - Its Structured Delegation Brief from Step 5 (objective, output_format, tool_list, boundaries).
  - Loaded MCPs from Step 6.
  - Relevant lessons from Step 2 (filtered to its section).
  - The operator-model summary.

Subagents return results. Orchestrator merges and resolves conflicts.

If any subagent times out or errors:
- Log the failure.
- Surface to Brandon: "(a) retry that subagent, (b) take over inline, (c) abort and save state."

**Artifact Reference Protocol.** Anthropic finding: routing every subagent result through the lead's context window creates a game of telephone and burns tokens copying large outputs through conversation history. Trigger is structural, not token-counted (token counting at write-time is not reliably available to the subagent): use the protocol for any structured artifact (code patch, table, diff plan, JSON, analysis report) OR any prose output longer than ~10 lines. Short prose findings (≤10 lines) may be inlined.

1. Subagent writes the full output to `$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/artifacts/<slug>.md`.
2. Subagent returns to lead a compact ref: `{path: "<artifact path>", summary: "<≤10-line gist>", schema: "<what's in the artifact>"}`.
3. Lead reads `path` and writes the state.json entry `{path, slug, producer: <subagent-id>, created_at: <ISO timestamp>}` from filesystem metadata — the subagent does not need to populate those fields.
4. Lead works from refs; reads the full artifact only when it needs the body (e.g., to merge into changeset, to feed to a judge, to compose final answer).
5. On `--dry-run` halt: full artifact bodies ARE written to disk (refs alone are useless on resume — resume needs the bodies).

Cleanup: session artifacts inherit the 90-day session GC rule from session-recall. Cleanup applies to `artifacts/` and `phase_summaries` together.

**Extended Thinking Guidance.** Anthropic finding: extended thinking acts as a controllable scratchpad and improves instruction-following, reasoning, and efficiency. Use it at two points:

- **Lead, before dispatch.** Think through the plan, tool fit, query complexity, subagent count, and each subagent's role. Output a thinking block that the dispatch step consumes — do not dispatch silently.
- **Subagents, interleaved after tool results.** After each tool call returns, the subagent uses interleaved thinking to evaluate quality, identify gaps, decide the next call. This adapts the subagent to its findings instead of running a pre-baked sequence.

Tier policy: TRIVIAL/LOW — not required. MEDIUM/HIGH — advisory (use when subagents fan out or when the plan is non-obvious). CRITICAL — required for both lead and subagents.

Output: changeset (modified files, new files, deletions) + artifact ref list.

### Step 8: JUDGE PANEL

Invoke **judge-panel** with the changeset and risk tier from Step 4.

- TRIVIAL: skip judges (unless `--judges` flag forces).
- LOW: 1-2 Tier 1 judges based on change type.
- MEDIUM: 3-5 Tier 1 judges.
- HIGH: full Tier 1 + minimum 2 relevant Tier 2 judges.
- CRITICAL: full Tier 1 + full Tier 2 + relevant Tier 3 judges.

Honor `--no-judges` flag for TRIVIAL/LOW only. Refuse for HIGH/CRITICAL.

Judges output verdict: `ship` | `revise` | `block`.
- ship — proceed to Step 10.
- revise — go to Step 9.
- block — halt pipeline, surface blocking concerns, save state.

### Step 9: REVISE

Address judge feedback marked `must_address_before_ship`.

- For each must-address item, apply fix (inline or via subagent).
- Re-run affected tests.
- Return to Step 8 for re-review (up to 2 revision cycles).

After 2 revision cycles, if judges still block: STOP and surface to Brandon. Do not enter infinite loop.

### Step 10: DONE GATE

Invoke **done-gate** to run all 8 checks. Risk-tier adjustments from done-gate's SKILL.md apply.

Honor skip flags: `--skip-tests`, `--skip-lint`, `--skip-types`, `--force`. Each logged.

If any check fails: surface failure, halt pipeline, save state.

### Step 11: COMMIT

If `--dry-run` flag is set: halt pipeline before committing. Surface to Brandon:
- Full diff (file count, +/- lines, changed paths).
- Judge verdict from Step 8.
- Done-gate check results from Step 10.

Save state to `$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/` with `state.json` field `dry_run: true` and `next_step: 11`. Skip Steps 12-14. Tell Brandon: "Dry-run complete. Inspect changes, then `/ship resume` to commit, or modify files and re-run."

Otherwise, invoke **commit-protocol** for the 5-step engineer-in-the-loop commit flow.

- Generate commit message (or use `--commit-message=` if provided).
- Show overview to Brandon.
- Wait for explicit approval (ship, y, yes, commit, go).
- Commit (honors `--amend` flag).
- Push decision (honors `--no-push` and `--auto-push` flags).

If commit fails (pre-commit hook rejection): surface, offer auto-fix, do not bypass.

**Spec status flip (only when this /ship was invoked with a spec-id).** On commit success, if `state.json` has a `spec-snapshot` reference:
1. Re-open the spec at `$HOME/.claude/memory/projects/<ns>/specs/<spec-id>.md`.
2. Update frontmatter: `status: shipped`, `shipped-at: <YYYY-MM-DD>`, `shipped-commit: <full SHA>`.
3. Update the matching row in `$HOME/.claude/memory/projects/<ns>/specs/_index.md`.
4. Leave the spec body unchanged — it's the historical record of what was shipped.

If the spec file has been edited since the snapshot (mtime diverges), surface to Brandon: "Spec `<spec-id>` was modified during the ship run. Apply status update anyway? (yes/no/diff)." Default no — abort the status flip but keep the commit.

### Step 12: LEARN

Skipped on `--dry-run` halts (no commit to learn from). Runs on the eventual `/ship resume` commit instead.

After successful commit:

1. **project-memory** — extract lessons from this run. Append to project's `lessons.md`. Format: `[<date>] <project>: <takeaway>`.
2. **operator-model** — if Brandon corrected, overrode, or rejected anything during the pipeline, update operator-model with the new signal.
3. **session-recall** — write session summary to `$HOME/.claude/memory/sessions/<date>-<session-id>/`.

These updates are append-only. Never overwrite existing lessons or operator-model entries.

### Step 13: CURATE CHECK

Check `$HOME/.claude/memory/global/last-curator-run.txt`:

- If file missing OR timestamp is 7+ days old: invoke **skill-curator** in `full` mode as a background pass.
- Otherwise: invoke **skill-curator** in `propose` mode only (checks if this run produced a generalizable pattern that should become a new skill).

If skill-curator proposes anything, surface count to Brandon in final report: "Curator proposed N items in _proposed/. Review at your convenience."

### Step 14: NOTION ROUTE + REPORT

Invoke **notion-bridge** to inspect artifacts generated during the run:

- For each artifact matching push categories (ADRs, status, retros, customer-facing docs): prompt Brandon "Push <artifact> to Notion? (yes/no/different target)".
- For each artifact in stay-local categories: skip silently.
- For ambiguous: ask Brandon.

Generate final /ship report:
SHIP COMPLETE ✓
Task: <task description>
Project: <project>
Risk tier: <tier>
Duration: <elapsed time>
Plan: <one-line summary>
Files changed: <count> (+<adds> -<dels>)
Tests: <pass count>/<total>
Judge verdict: <verdict> (<judge count> judges, <tier>)
Commit: <SHA> <message>
Push: <pushed | local-only>
Lessons captured: <count>
Operator model updates: <count>
Curator proposals: <count>
Notion artifacts: <pushed count>/<eligible count>
Next: <suggested next action if applicable>

## State Management

### Saving State on Interrupt

If pipeline is interrupted (Brandon types "stop", subagent times out and Brandon chooses abort, judge-panel returns block, etc.), save:

`$HOME/.claude/memory/sessions/<YYYY-MM-DD>-<session-id>/`
  - `state.json` — current step, completed steps, flag values, classifications. For `--dry-run` halts: also includes `dry_run: true` and `next_step: 11`. Carries `artifacts: [...]` (Step 7 Artifact Reference Protocol), `phase_summaries: {<phase>: <summary>}` (Long-Horizon Hand-off, below), `tool_call_tally: {<subagent-slot>: <count>}` (Step 4 Effort Budget), `handoff_pending: bool` (Hand-off flag), and `subagent_failures: [{slug, reason, timestamp}]`.
  - `task-spec.md` — parsed task from Step 1.
  - `plan.md` — plan from Step 3.
  - `changeset.md` — partial changes if applicable.
  - `judge-output.md` — last judge verdict if applicable.
  - `artifacts/<slug>.md` — subagent outputs persisted by the Artifact Reference Protocol.
  - `spec-snapshot.md` — spec frozen at pipeline entry (when invoked with a spec-id).

### Resuming

`/ship resume` (or `/ship resume <session-id>` for specific older session):
- Loads most recent session state.
- Shows Brandon the summary: "Resuming from Step <N>. Last action: <description>. Continue? (yes / restart / abort)."
- On yes, picks up at the next step.
- If state has `dry_run: true`, resume re-verifies the working tree matches the saved changeset (warn if drift), then runs Step 11 COMMIT onward as a normal commit (no second judge pass unless files changed since dry-run).

### Long-Horizon Hand-off (context-overflow guard)

Anthropic finding: production agents engage in long conversations that exceed standard context windows; the fix is intelligent compression + memory hand-offs, not larger context. /ship inherits this pattern for long-running sessions (HIGH/CRITICAL with many subagents, or a /ship resume that has accumulated many phases).

Trigger: any of (a) Claude Code emits a compaction or context-pressure warning, (b) the SessionStart context reports token usage in the high band, (c) the lead has dispatched ≥3 subagents in a single HIGH/CRITICAL run with artifacts accumulating in `state.json.artifacts`. If none of these signals are available, the protocol is opt-in — Brandon or the lead invokes it manually when a long run feels close to the limit.

Protocol:

1. **Summarize completed phases.** For each pipeline step already completed (e.g., PARSE, CONTEXT LOAD, PLAN, DISPATCH), write a ≤300-line summary into `state.json.phase_summaries[<step-name>]`. Include: what was decided, what artifacts were produced (paths only, by ref), what was rejected. If a summary exceeds 300 lines, write it in full with a `truncation_marker: false` field AND surface to Brandon: "phase summary for <step> oversize — review before continuing hand-off."
2. **Preserve full artifacts.** The Artifact Reference Protocol already wrote the full bodies to `artifacts/<slug>.md`. Do not duplicate them in summaries — refs are enough.
3. **Fresh subagent, clean context.** When dispatching the next subagent, hand it: (a) its Structured Delegation Brief, (b) the relevant `phase_summaries` entries, (c) the artifact refs it needs by path. Do not pass full prior conversation history.
4. **Lead can also restart its own context.** If lead approaches the threshold, lead writes a `lead_handoff.md` checkpoint into the session dir capturing remaining steps + outstanding subagent results, sets `state.json.handoff_pending: true`, then a fresh lead instance resumes from that checkpoint.
5. **Continuity check on resume.** `/ship resume` ALWAYS checks `state.json.handoff_pending`. If `true`, read `lead_handoff.md` first and reconstruct from `phase_summaries` + `artifacts` + checkpoint; do not replay original conversation. If `false`, resume by the original step pointer.

Hand-offs are append-only: phase_summaries entries never overwrite prior ones; if a phase is re-entered (e.g., revise loop), append `<step>-r1`, `<step>-r2`.

### Pipeline Halt → Postmortem (failure-side learning loop)

Step 12 (LEARN) only fires after a successful commit. Without a counterpart, every aborted, blocked, or halted run produces zero learning — and failures carry the highest-signal lessons.

On any non-success exit from Steps 3, 7, 8, 9, 10, or 11 (Brandon abort, subagent timeout chosen abort, judge `block`, revise cycles exceeded, done-gate failure, pre-commit hook rejection with no auto-fix), and on any `stop`/`abort` input mid-pipeline:

1. Save state per "Saving State on Interrupt" above.
2. Invoke the **postmortem** skill in `auto` mode with `failure_step`, `attempted_action`, `gate_verdict`, and `partial_changeset` pulled from the saved state.
3. The skill surfaces two questions (root cause + change going forward) and routes Brandon's response to project-memory (always proposed), operator-model (when about Brandon/Claude behavior), a skill-description suggestion (when a skill is named), and notion-bridge (when team-relevant).
4. If Brandon types `skip`, the skill logs to `$HOME/.claude/memory/global/postmortem-skipped-log.md` and exits clean. Skipping never blocks the state-save-and-exit.
5. Postmortem skill failures are non-blocking — /ship's own halt path completes regardless.

The skill is opportunistic — it runs after state is already safe on disk. Brandon can also invoke `/postmortem --from-session=<session-id>` later if he skipped at the time and wants to revisit.

## Failure Modes Per Step

| Step | Common failure | Default behavior |
|------|----------------|------------------|
| 1 PARSE | Task too vague | Ask Brandon one clarifying question. |
| 1 PARSE | Spec-id not found in current namespace | Search other namespaces; surface match or refuse with "Spec `<spec-id>` not found." |
| 1 PARSE | Spec status is `draft` | Refuse. Tell Brandon to run `/spec approve <spec-id>` first. |
| 1 PARSE | Spec status is `shipped` | Warn. Allow only with `--force`. |
| 11 COMMIT | Spec mtime diverged from snapshot | Surface to Brandon. Default: keep commit, skip status flip. |
| 2 CONTEXT | Memory file corrupt | Log warning. Continue with empty context. |
| 3 PLAN | Plan tool unavailable | Generate inline plan. Note degradation. |
| 4 RISK | Cannot classify | Default to MEDIUM. Surface to Brandon. |
| 5 DISPATCH | Subagent plugin missing | Sequential inline. Note. |
| 6 MCP ROUTE | All MCPs disconnected | Surface to Brandon. Offer continue without MCPs or abort. |
| 7 EXECUTE | Subagent times out | Brandon picks: retry, inline, abort. |
| 8 JUDGE | Judge unreachable | Skip that judge. If panel cannot form quorum (≥50% of expected judges), surface to Brandon. |
| 9 REVISE | 2 cycles exceeded | Halt. Surface unresolved blockers. |
| 10 DONE GATE | Any check fails | Halt. Show fix. |
| 11 COMMIT | Hook rejection | Surface. Offer auto-fix. Never bypass. |
| 12 LEARN | Memory write fails | Retry once. Then log error. Do not block. |
| 13 CURATE | Curator errors | Log. Skip. Do not block. |
| 14 NOTION | MCP disconnected | Skip Notion push. Note in report. |
| 14 REPORT | Report write fails | Print report to stdout. Log error. Do not block. |
| State (Hand-off) | phase_summaries write fails | Retry once. On second failure, surface to Brandon — hand-off cannot proceed safely without persisted summaries. |
| State (Hand-off) | lead_handoff.md missing on resume | Refuse resume with handoff_pending=true. Tell Brandon to inspect session dir or restart. |
| State (Artifacts) | artifact write fails | Subagent retries write; on second failure, returns inline body with `inline_fallback: true` marker. Lead logs the fallback. |

## Hard Constraints

- NEVER skip judge-panel for HIGH/CRITICAL risk, regardless of flags.
- NEVER auto-push without `--auto-push` flag.
- NEVER push to protected branches without per-push confirmation.
- NEVER bypass done-gate Check 8 (Brandon approval). Even `--force` does not bypass approval.
- NEVER write to operator-model.md without Brandon's explicit acknowledgment of the change.
- NEVER infinite-loop the revise step. Hard cap at 2 cycles.
- ALWAYS save state on interrupt. Brandon should be able to resume.
- ALWAYS produce the final report, even on partial completion or failure.
- ALWAYS log force-bypass usage. Every `--force` invocation is reviewed by skill-curator weekly.
- NEVER run a `/ship <spec-id>` when the spec status is `draft`. Force Brandon through `/spec approve` first.
- NEVER overwrite a spec's `shipped-at` or `shipped-commit` fields once set. Re-shipping with `--force` requires a new spec.
- ALWAYS snapshot the spec into session state on entry. The snapshot is the contract for this ship run; later edits to the spec file do not affect a run in progress.
- NEVER commit when `--dry-run` flag is set. Always save state and surface diff + verdict instead.
- NEVER dispatch a subagent without a Structured Delegation Brief (objective, output_format, tool_list, boundaries). Free-form delegation is rejected — re-dispatch with a brief.
- NEVER inline a subagent output longer than ~200 tokens in lead context. Use the Artifact Reference Protocol — write the body to `sessions/<id>/artifacts/<slug>.md`, return a ref.
- NEVER exceed a tier's per-subagent tool-call ceiling without explicit Brandon override. At the ceiling, the subagent must finalize and return an artifact ref.
- NEVER replay full conversation history into a fresh subagent on Long-Horizon Hand-off. Pass `phase_summaries` + artifact refs only.
- NEVER dispatch a subagent with an incomplete Structured Delegation Brief. Lead validates all four fields are non-empty before dispatch; missing field → halt and log `BRIEF_INCOMPLETE: <field>`.
- NEVER re-dispatch a subagent more than 2 times for boundary violations. Third violation surfaces the offending output to Brandon and halts EXECUTE.
- NEVER resume a session with `handoff_pending: true` by replaying — always read `lead_handoff.md` first.

## Design Influences

- Anthropic Engineering, "How we built our multi-agent research system" (Jun 13, 2025). Effort Budget by Tier (Step 4), Structured Delegation Brief + Parallel Tool Call Rule (Step 5), Breadth-First Heuristic (Step 3), Artifact Reference Protocol + Extended Thinking Guidance (Step 7), Long-Horizon Hand-off (State Management) all adapt patterns from that post. /ship is a single-user code-oriented orchestrator, not a multi-user research product — the patterns are ported as architectural moves, not as performance promises.

## Plugin Compatibility

Required: none — the orchestrator degrades gracefully when plugins are missing.

Enhanced by (in order of impact):
- `superpowers:brainstorming` — better plans for MEDIUM tasks.
- `superpowers:writing-plans` — structured plans for HIGH/CRITICAL.
- `superpowers:subagent-driven-development` — parallel execution.
- `plugin-dev` — used downstream by skill-curator.
- `commit-commands` — commit primitives.
- `github` — PR creation.
- `hookify` — done-gate hook enforcement.
- `pyright-lsp` — done-gate Check 6.
- `caveman` — MCP description compression.

## Quick Reference
/ship "<task>"                          # Default. Auto risk, judges per tier, ask-before-push.
/ship <spec-id>                         # Consume approved spec. Status, risk-tier, success criteria pre-loaded.
/ship <spec-id> --force                 # Re-ship a previously-shipped spec (rare; usually write a new spec instead).
/ship "<task>" --risk=high              # Force HIGH tier.
/ship "<task>" --no-judges              # Skip judges (TRIVIAL/LOW only).
/ship "<task>" --skip-tests --skip-lint # Bypass selected gates with logging.
/ship "<task>" --force                  # Emergency hotfix. All gates bypassed except approval.
/ship "<task>" --commit-message="..."   # Use exact commit message.
/ship "<task>" --auto-push              # Push immediately after commit.
/ship "<task>" --dry-run                # Run through done-gate, show diff + verdict, halt before commit. Resume to commit.
/ship resume                            # Resume last interrupted session (or finish a dry-run).
