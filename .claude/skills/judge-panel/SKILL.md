---
name: judge-panel
description: Multi-judge code review system invoked before any commit by /ship command. Reviews diffs at five risk tiers (TRIVIAL, LOW, MEDIUM, HIGH, CRITICAL) using a roster of 29 specialized judges across three tiers. Use when about to commit code changes, when /ship is invoked, when a diff needs review, or when Brandon explicitly requests "judge this" or "review this diff". Tier 1 judges focus on code quality and delegate to pr-review-toolkit agents where possible. Tier 2 judges focus on systemic risks (security, threat modeling, cost). Tier 3 judges apply business and product wisdom for strategic decisions. Risk tier determines which subset is invoked. Brandon can override with --judges, --no-judges, or --risk flags. Returns aggregate verdict of ship, revise, or block with structured concerns.
---

# Judge Panel: 29-Judge Code Review System

This skill is the core review mechanism invoked by `/ship` before any commit. It scales judge invocation to risk tier, parallelizes calls where possible, and delegates to plugin agents (`pr-review-toolkit`, `ecc`'s reviewer agents) to minimize token cost.

## Invocation Contract

The skill receives:
- `diff` — the unified diff to review
- `task_context` — exactly 2 sentences describing what the change accomplishes
- `risk_tier` — one of TRIVIAL, LOW, MEDIUM, HIGH, CRITICAL (from `/ship` classification)
- `project` — one of auto-co, margin-invest, personal
- Optional `judges_override` — comma-separated list to invoke instead of tier defaults
- Optional `no_judges` — boolean flag, skip entirely

The skill returns:
{
"aggregate_verdict": "ship" | "revise" | "block",
"blocking_concerns": [list],
"must_address_before_ship": [list],
"log_for_later": [list],
"judges_invoked": [list of judge names],
"tokens_used": <estimate>
}

## Judge Roster

### Tier 1 — Code Quality Judges (16)

Tier 1 judges focus on the diff itself. For MEDIUM and above, 3-5 are invoked. For HIGH and above, all relevant ones. Tier 1 judges delegate to `pr-review-toolkit` agents where the function matches. The `pr-review-toolkit` plugin's 6 specialized agents cover comments, tests, error handling, type design, code quality, and code simplification — these map directly to judges 1, 3, 4, 13, 15, 16 below.

1. **Senior Staff Engineer** — code quality, maintainability, abstraction level, mental model alignment. Delegate to `pr-review-toolkit:code-quality-reviewer` when available.
2. **Security Reviewer** — auth, secrets, injection, OWASP top 10. Delegate to `ecc:security-reviewer` or `ecc:vulnerability-scanner` agent.
3. **Performance Engineer** — latency, memory, query patterns, N+1, complexity.
4. **Test Architect** — coverage, edge cases, test isolation, flake-resistance. Delegate to `pr-review-toolkit:test-reviewer`.
5. **API Designer** — interface contracts, versioning, backward compatibility, RFC-style naming.
6. **Data Engineer** — schema, migrations, query plans, indexing, denormalization tradeoffs.
7. **DevOps Engineer** — deploy safety, rollback, observability, blast radius if it goes wrong.
8. **Accessibility Auditor** — WCAG 2.2 AA, keyboard nav, screen reader, contrast, focus order.
9. **Frontend Specialist** — component design, state, rerender cost, hydration.
10. **Backend Specialist** — service boundaries, error handling, idempotency, retries.
11. **Database Specialist** — transactions, isolation level, consistency guarantees, locking.
12. **Concurrency Reviewer** — race conditions, deadlocks, async correctness, ordering.
13. **Error Handler** — failure modes, retry logic, user-facing messages, fail-loud vs fail-quiet. Delegate to `pr-review-toolkit:error-handling-reviewer`.
14. **Documentation Reviewer** — README, inline comments where needed, ADRs for non-obvious decisions.
15. **Naming Critic** — variables, functions, files, modules. Match domain language. Delegate to `pr-review-toolkit:comments-reviewer` for comment naming concerns.
16. **Simplicity Judge** — would a junior engineer understand this in 30 seconds? Delegate to `pr-review-toolkit:code-simplification-reviewer`.

### Tier 2 — Systemic Risk Judges (5)

Tier 2 judges are invoked for HIGH and CRITICAL changes. They assess risks beyond the diff itself.

17. **Karpathy** — surfaces silent assumptions, calls out overengineering, asks "would this be in the minimum code?" Pulls from `andrej-karpathy-skills` plugin context.
18. **Threat Modeler** — STRIDE analysis on auth/data flows. Delegate to `ecc:threat-modeler` agent if available.
19. **Cost Accountant** — token cost (LLM API), infra cost (compute/storage), third-party API call budget. Estimates per-request and per-month.
20. **Regulatory Reviewer** — GDPR for EU data, SOC2 controls, financial reporting rules for margin-invest, vehicle data regulations for auto-co.
21. **Failure Mode Analyst** — what breaks when X dependency fails? Blast radius? Cascade risk? Recovery procedure?

### Tier 3 — Business and Product Judges (8)

Tier 3 judges are invoked only for CRITICAL changes affecting product strategy, pricing, or user-facing decisions. They speak in the voice of the operator they represent.

22. **Hormozi** — offer clarity, conversion, dollar-per-decision. "What is the value of the offer here in one sentence?"
23. **Naval** — leverage, permissionless, asymmetric upside. "Does this scale with my attention or independent of it?"
24. **Bezos** — customer obsession, two-pizza scope, reversible vs irreversible. "Is this a one-way door?"
25. **Buffett** — moat, margin of safety, simplicity. "Would I want to own this for 10 years?"
26. **Munger** — invert the problem, second-order effects. "What would make this fail catastrophically?"
27. **Thiel** — "What important truth do few people agree with you on?" Contrarian-but-correct test.
28. **Graham** — what would users actually use, do things that don't scale, ship the thing.
29. **Ive** — would Brandon be proud to ship this? Detail-craft level.

## Risk Tier → Judge Invocation Map

### TRIVIAL
No judges. `/ship` skips the panel entirely. Return immediate `ship` verdict.

### LOW
1-2 Tier 1 judges, picked by change type:
- Test-only change → judge 4 (Test Architect)
- Rename only → judges 15 (Naming Critic) + 16 (Simplicity)
- Single-file refactor, no logic change → judges 1 (Senior Staff) + 16 (Simplicity)
- Comment/doc only → judge 14 (Documentation) only
- Dependency bump → judge 2 (Security) only

### MEDIUM
3-5 Tier 1 judges, picked by change surface area:
- New function added → 1, 4, 13, 15, 16
- Modified business logic → 1, 3, 4, 13, 16
- New endpoint → 1, 2, 4, 5, 13
- UI component change → 1, 8, 9, 16
- Schema change (non-breaking) → 1, 6, 11

### HIGH
ALL relevant Tier 1 + at least 2 Tier 2:
- All Tier 1 judges whose domain the diff touches
- Always include: 17 (Karpathy), 21 (Failure Mode Analyst)
- Add 18 (Threat Modeler) if auth/data flow
- Add 19 (Cost Accountant) if introduces new external API calls
- Add 20 (Regulatory Reviewer) if touches user data or financial calculation

### CRITICAL
Full Tier 1 + full Tier 2 + relevant Tier 3:
- All Tier 1 + all Tier 2
- Tier 3 selection by change type:
  - Pricing/offer change → 22 (Hormozi)
  - Architectural one-way door → 24 (Bezos) + 26 (Munger)
  - Long-term platform decision → 25 (Buffett) + 27 (Thiel)
  - User-facing product launch → 22, 28, 29
  - Always include 26 (Munger) for invert-the-problem on any CRITICAL change

## Override Flags

Brandon can override the tier-based selection via `/ship`:

- `/ship --no-judges "<task>"` — skip the panel entirely. Used for trivial fixes Brandon already verified.
- `/ship --judges=karpathy,security "<task>"` — invoke only the named judges. Match by name (case-insensitive, partial match allowed).
- `/ship --judges=tier1 "<task>"` — invoke all of Tier 1.
- `/ship --judges=+hormozi "<task>"` — add judges to the tier defaults (the `+` prefix).
- `/ship --judges=-naming "<task>"` — exclude judges from tier defaults (the `-` prefix).
- `/ship --risk=high "<task>"` — force a specific risk tier regardless of automatic classification.

## Per-Judge Invocation Protocol

Each judge call must:

1. Receive ONLY:
   - The unified diff (compressed by caveman if available)
   - The 2-sentence task context
   - The judge's name and role
   - The risk tier
2. NOT receive: full session transcript, project lessons, other judges' output.
3. Return a structured response:
{
"judge": "<judge name>",
"verdict": "approve" | "block" | "nit",
"concerns": [up to 3 items],
"concrete_suggestion": "<one specific change>" | null
}
4. Time out after 30 seconds. If a judge times out, record `verdict: "timeout"` and continue.

When invoking multiple judges, parallelize the calls. Use Claude Code's subagent dispatch (via `superpowers` plugin's subagent-driven-development) to run them concurrently.

## Aggregation Rules

After all judges respond, aggregate:

1. If any judge returns `verdict: "block"` → aggregate verdict is `block`. Surface all blocking concerns.
2. If 2+ judges return the same `concern` (semantic match, not exact string) → promote to `must_address_before_ship`.
3. If a single judge returns a `nit` not echoed by others → put in `log_for_later`.
4. If all judges return `approve` → aggregate verdict is `ship`.
5. Mixed approve/nit with no blocks → aggregate verdict is `revise`. Brandon decides whether to address each item now or log.

Output format to Brandon:
JUDGE PANEL RESULT (risk tier: <tier>)
Verdict: SHIP | REVISE | BLOCK
Judges invoked: <list>
[if BLOCK]
Blocking concerns:

<judge>: <concern>
<judge>: <concern>

[if REVISE]
Address before ship:

<concern> (raised by <judges>)

Log for later:


<concern>


[if SHIP]
All judges approved. Ready to commit.
Tokens used: <count>

## Delegation Priority

When a Tier 1 judge has a `pr-review-toolkit` equivalent, prefer delegation:

| Judge | Delegated to | Plugin |
|-------|-------------|--------|
| Senior Staff Engineer | code-quality-reviewer | pr-review-toolkit |
| Test Architect | test-reviewer | pr-review-toolkit |
| Error Handler | error-handling-reviewer | pr-review-toolkit |
| Naming Critic (comments) | comments-reviewer | pr-review-toolkit |
| Simplicity Judge | code-simplification-reviewer | pr-review-toolkit |
| Security Reviewer | security-reviewer or vulnerability-scanner | ecc |
| Threat Modeler | threat-modeler | ecc (if available) |
| Documentation Reviewer | type-design-reviewer (for type docs) | pr-review-toolkit |

For judges without a plugin equivalent (Performance Engineer, Database Specialist, all Tier 2 systemic, all Tier 3 business), use direct prompts with judge-specific personas.

If a delegation target plugin is not installed, fall back to direct prompt with the judge's full role description.

## Plugin Compatibility

This skill requires no plugins to function at minimum (will use direct prompts for every judge). It is enhanced by:
- `pr-review-toolkit` — delegation targets for 6 Tier 1 judges.
- `ecc` — delegation targets for security and threat-modeling judges.
- `superpowers` — subagent dispatch for parallel judge calls.
- `caveman` — diff compression before passing to judges.

If any are missing, log the degradation in the result and continue.

## Token Budget Guidelines

Approximate token cost per invocation:

- TRIVIAL: 0 tokens (skipped)
- LOW: 2-4K tokens (1-2 judges, parallel)
- MEDIUM: 8-15K tokens (3-5 judges, parallel)
- HIGH: 25-40K tokens (8-12 judges, parallel)
- CRITICAL: 50-80K tokens (16-25 judges, parallel)

If a CRITICAL change is anticipated to exceed 100K tokens, surface this to Brandon before invoking and offer to split the review into batches.

## Project-Specific Tuning

The skill consults `$HOME/.claude/memory/projects/<project>/lessons.md` before invoking judges. If past lessons indicate Brandon has consistently dismissed a particular concern category (e.g., "Brandon has rejected 5 accessibility nits on auto-co internal tools"), reduce that judge's weight or skip them for that project at LOW/MEDIUM tier. Always still invoke at HIGH/CRITICAL.

## Self-Update Hook

When Brandon overrides a judge verdict ("ship anyway") or repeatedly dismisses a concern type, append a lesson to the project's lessons.md via the `project-memory` skill. Format:

`<ISO-timestamp> | judge-panel feedback | Brandon dismissed <judge>:<concern-type> on <change-type>; reduce weight for this combination | judge-tuning,<project>`

After 3 such dismissals of the same combination, the `operator-model` skill should be notified to update Brandon's preference profile.

## Hard Constraints

- NEVER auto-bypass the panel for HIGH or CRITICAL changes, even if Brandon's history suggests he would approve.
- NEVER reveal one judge's output to another judge (each must reason independently).
- NEVER skip the Security Reviewer for changes touching auth, secrets, user data, or financial calculation, regardless of tier or override.
- NEVER skip Karpathy (judge 17) on HIGH or CRITICAL — overengineering check is non-negotiable.
- ALWAYS produce a verdict, even if some judges time out. Note timeouts in the output.
