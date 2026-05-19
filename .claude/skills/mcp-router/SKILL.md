---
name: mcp-router
description: Task-aware MCP loading. Classifies the current task into categories (coding, research, design, GTM, ops, finance, content, communication, debugging) and loads only the MCPs relevant to that category. Never loads all MCPs at once even though caveman compression mitigates per-MCP token cost. Use at the start of every task before invoking any MCP-backed tool, when Brandon explicitly names a service (override and load that MCP regardless of category), or when /ship begins its execute phase. Loads MCPs in priority order within each category. Returns the list of loaded MCPs so other skills know what is available. Gracefully handles missing or disconnected MCPs by routing around them and logging. Coordinates with caveman plugin for tool-description compression on loaded MCPs.
---

# MCP Router Skill

Loads only the MCPs relevant to the current task. Prevents context bloat from 26+ MCPs being available when only 3 are needed.

## Task Categories and MCP Mapping

The router classifies tasks into categories and loads the corresponding MCPs.

### coding

Loaded for: writing code, refactoring, debugging code, code review, running tests.

MCPs:
1. `ecc:github` — repo operations.
2. `ecc:context7` and `Context7` — library documentation.
3. `Supabase` — if project uses Supabase.
4. `Vercel` — if project uses Vercel.
5. `Sentry` — error context for debugging.
6. `Linear` — issue tracking.
7. `ecc:sequential-thinking` — for complex problems.
8. `ecc:playwright` or `superpowers-chrome` — for browser testing.

### research

Loaded for: reading papers, looking up regulations, market analysis, competitor research.

MCPs:
1. `ecc:exa` — semantic web search.
2. `PubMed` — medical/scientific papers.
3. `Microsoft Learn` — Microsoft/Azure docs.
4. `Hugging Face` — ML papers and models.
5. `Context7` — library docs.
6. `firecrawl` (plugin) — web scraping.

### design

Loaded for: UI/UX work, design system updates, mockups.

MCPs:
1. `Excalidraw` — quick diagrams.
2. `Mermaid Chart` — technical diagrams.
3. Plus skill-level: `impeccable`, `ui-ux-pro-max` (not MCPs but loaded as context).

### GTM (go-to-market)

Loaded for: marketing campaigns, SEO, content strategy, conversion optimization.

MCPs:
1. `PostHog` — analytics, feature flags, funnels.
2. `Gmail` — outreach.
3. `Google Calendar` — meeting scheduling.
4. Plus skill-level: `marketing-skills` (33 skills) as context.

### ops (operations)

Loaded for: deploys, monitoring, infrastructure changes.

MCPs:
1. `Vercel` — deploy operations.
2. `Sentry` — error monitoring.
3. `PostHog` — production analytics.
4. `Supabase` — database operations.
5. `ecc:github` — release management.

### finance

Loaded for: financial calculations, modeling, reporting (margin-invest project).

MCPs:
1. `Supabase` — financial data.
2. `firecrawl` — public filings scraping.
3. `ecc:exa` — financial news.
4. `Postman` — financial API testing.

### content

Loaded for: writing posts, documentation, marketing copy.

MCPs:
1. `Notion` — content storage.
2. `Google Drive` — document handling.
3. `firecrawl` — competitor content research.

### communication

Loaded for: drafting emails, scheduling, team coordination.

MCPs:
1. `Gmail`.
2. `Google Calendar`.
3. `Notion` — team docs.
4. `Linear` — issue tracking integration.

### debugging

Loaded for: investigating production issues, log analysis, root-cause analysis.

MCPs:
1. `Sentry` — error details.
2. `PostHog` — user behavior leading to error.
3. `Supabase` — query database state.
4. `Vercel` — deploy logs.
5. `ecc:sequential-thinking` — structured RCA.

## Default Always-Available MCPs

Regardless of category, these are always considered available (lightweight, broadly useful):

- `ecc:memory` — Claude's working memory.
- `prompts.chat` — prompt and skill marketplace.

These are not "loaded" in the heavy sense; they are available because their cost is minimal.

## Classification Algorithm

1. Read the task description (from /ship invocation or current message).
2. Look for explicit category signals:
   - Code-related verbs: write, refactor, debug, test, deploy → coding or ops.
   - Research verbs: research, find papers, look up, what is the market → research.
   - Design verbs: design, mock up, style, layout → design.
   - Marketing verbs: campaign, SEO, copy, conversion → GTM.
   - Money verbs: model, forecast, P&L, ROI, valuation → finance.
3. Look for explicit service mentions (override category mapping). If Brandon mentions a specific service by name, load that MCP regardless of category.
4. Look for project context: margin-invest tasks often need finance MCPs, auto-co often needs ops MCPs.
5. If ambiguous, ask Brandon: "Task category? (coding | research | design | GTM | ops | finance | content | communication | debugging | mixed)"

## Loading Protocol

After classifying:

1. List the MCPs to load.
2. Check each MCP's connection status via `claude mcp list`.
3. For each connected MCP, ensure it is active in the current session.
4. For disconnected MCPs:
   - If critical to category (top 3 in the list), surface to Brandon: "MCP <name> is disconnected. (a) attempt reconnect, (b) continue without, (c) abort task."
   - If supporting (lower in list), log and continue.
5. Report loaded MCPs:
MCP-ROUTER: Loaded for category "<category>":

<mcp1> ✓
<mcp2> ✓
<mcp3> ✗ (disconnected, continuing without)


## Override Flags

When /ship is invoked with explicit MCP control:

- `/ship --mcps=Supabase,PostHog "<task>"` — load only these.
- `/ship --mcps=+Linear "<task>"` — add Linear to category defaults.
- `/ship --mcps=-Sentry "<task>"` — exclude Sentry from category defaults.
- `/ship --no-mcps "<task>"` — load no MCPs (rare; use for pure local work).

## Caveman Integration

The `caveman` plugin compresses tool descriptions for loaded MCPs. Router does not need to invoke caveman directly — caveman's MCP middleware runs automatically. Router only needs to ensure caveman is healthy:

`claude plugin list 2>&1 | grep caveman | grep enabled`

If caveman is disabled, warn Brandon: each MCP loaded will cost more tokens.

## Integration with Other Skills

- **/ship** — invokes mcp-router during the "context load" phase, before subagent dispatch.
- **judge-panel** — for HIGH/CRITICAL changes, mcp-router may load Sentry/PostHog so judges can reference production behavior.
- **session-recall** — if a recall result mentions a service, that service's MCP is loaded by the router on follow-up.

## Plugin Compatibility

Required: none (router works with whatever MCPs are connected).
Enhanced by:
- `caveman` — compresses tool descriptions for loaded MCPs.
- Plugin-bundled MCPs from `ecc` (github, exa, memory, playwright, sequential-thinking, context7).

## Hard Constraints

- NEVER load all MCPs at once. Token budget is finite.
- NEVER load an MCP without checking its connection status first.
- NEVER skip the classification step. Even short tasks get classified.
- NEVER override Brandon's explicit `--mcps=` flag.
- ALWAYS report loaded MCPs so other skills know what is available.
- ALWAYS log disconnected MCPs in the report (do not silently skip).
