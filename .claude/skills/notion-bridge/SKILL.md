---
name: notion-bridge
description: Routes human-facing artifacts to Notion via the Notion MCP and notion plugin. Determines what gets pushed to Notion (architecture decisions, ADRs, project status, retrospectives, board materials, weekly summaries, customer-facing docs) and what stays local (lessons, session transcripts, operator-model, curator reports, ephemeral plans, code review notes, skill files). Use when a task produces a human-facing artifact, when Brandon says "push this to Notion" or "save this for the team", or at the end of a /assay run that generated documentation worth sharing. Always asks Brandon to confirm target page or database with one-line preview before pushing. Never pushes secrets, API keys, internal financial numbers, or PII without explicit per-push approval. Coordinates with notion plugin for slash commands and Notion MCP for raw operations.
---

# Notion Bridge Skill

Routes human-facing artifacts to Notion. The policy layer over the Notion MCP and `notion` plugin. Decides what gets shared with humans vs what stays in Claude Code's local memory.

## Push vs Stay Local: The Routing Rules

### Push to Notion (human-facing)

These artifacts go to Notion because humans other than Brandon (advisors, partners, future team) might need them:

- **Architecture decisions** — ADRs, design docs, technical RFCs.
- **Project status updates** — weekly summaries, milestone reports.
- **Retrospectives** — post-mortems, post-ship retros, lessons-learned reports for stakeholders.
- **Board / investor materials** — financial models, investor updates, fundraising decks.
- **Customer-facing docs** — user guides, API references, FAQ.
- **Strategic plans** — quarterly plans, OKRs, product roadmaps.
- **Meeting outputs** — meeting notes intended for shared reference, action items for others.
- **Public commitments** — anything Brandon has agreed to deliver to someone external.

### Stay Local (Brandon-only)

These artifacts stay in $HOME/.claude/ because they are Brandon's working memory:

- Lessons (`memory/projects/*/lessons.md`) — internal learning.
- Session transcripts (`memory/sessions/`) — Claude Code working memory.
- Operator model (`memory/global/operator-model.md`) — model of Brandon.
- Curator reports (`memory/global/curator-report-*.md`) — internal system audits.
- Skill files (`skills/*/SKILL.md`) — Claude Code configuration.
- Ephemeral plans — drafts and scratch work.
- Code review notes — judge-panel output unless explicitly requested.
- Private journal entries (via private-journal-mcp) — Brandon's reflections.

### Ambiguous: Ask Brandon

When an artifact could go either way, ask. Specifically when:
- It is a doc Brandon wrote alone but might share later (default: stay local, ask).
- It is a strategy doc for a project that has no external stakeholders yet (default: ask).
- It is a financial number that is not actively secret (default: ask).

## Push Protocol

When pushing to Notion:

1. **Classify** — confirm the artifact matches one of the push categories above.
2. **Sanitize check** — scan for secrets, API keys, PII, internal financials. If detected, STOP and surface to Brandon with the specific finding.
3. **Target selection** — determine target page or database:
   - Architecture decisions → "Engineering / ADRs" database.
   - Project status → "<Project Name> / Weekly Status" database.
   - Retrospectives → "Operations / Retrospectives" database.
   - Customer-facing → ask Brandon.
   - Other → ask Brandon.
4. **One-line preview** — show Brandon:
READY TO PUSH TO NOTION:
Target: <database or page>
Title: <artifact title>
Preview: <first 100 chars>
Tags: <project, type>
Confirm? (yes / no / different target)
5. **Wait for explicit yes** — never push without "yes" or equivalent.
6. **Execute via Notion MCP** — use the `notion` plugin slash commands when available, raw MCP otherwise.
7. **Confirm and link** — return the Notion URL of the created/updated page.

## Sanitize Check: Hardcoded Patterns

Never push content containing:

- Strings matching common secret patterns: `sk_[a-zA-Z0-9]{20,}`, `ghp_[a-zA-Z0-9]{36}`, `xoxb-`, `xoxp-`, AWS access keys (`AKIA[A-Z0-9]{16}`), `Bearer\s+[a-zA-Z0-9._-]{20,}`.
- Email addresses unless Brandon's own (`brandon@*`) or the page is clearly intended for the team.
- Phone numbers, SSNs, credit card-like patterns.
- File paths under `~/.ssh/`, `~/.aws/`, `~/.config/`, or anything containing `secret`, `private_key`, `password`, `token=`, `apikey=`.

If a match is found:
SANITIZE BLOCK: Notion push halted.
Found: <pattern matched, with surrounding 20 chars redacted to <REDACTED>>
At: <line number or section>
Options:

Redact and push (replaces with <REDACTED>)
Edit the artifact first
Push anyway (require explicit override: type "push with secrets")


The "push anyway" path requires Brandon to type the exact override phrase. Do not accept shortcuts.

## Pull from Notion

Symmetrical: notion-bridge also handles fetching from Notion when /assay needs context from a doc.

Use cases:
- Brandon references a Notion doc by URL or title ("the ADR on auth").
- A task needs the latest project status before starting.
- The session-recall skill returns a hit pointing to Notion content.

Pull via Notion MCP. Return the content. Do not write to local memory unless Brandon explicitly says "save this locally".

## Integration with Other Skills

- **/assay** — at end of pipeline, notion-bridge inspects generated artifacts. If any match push categories, prompts Brandon to push.
- **project-memory** — never pushes raw lessons to Notion. If Brandon asks for a "project summary for sharing", the bridge generates a summary FROM lessons but routes that summary (not the lessons themselves).
- **skill-curator** — curator reports stay local. Never pushed.
- **operator-model** — never pushed to Notion. Sensitive personal data.

## Plugin Compatibility

Enhanced by:
- `notion@claude-plugins-official` plugin — provides slash commands, structured Notion operations.
- Notion MCP — raw create/update/search operations.

If `notion` plugin is missing, fall back to direct Notion MCP calls. If Notion MCP is missing, refuse to push and explain. Never silently fail.

## Invocation Contract

Modes:

- `classify` — given an artifact, returns push|local|ambiguous.
- `push` — pushes an artifact to Notion after sanitize + preview + confirm.
- `pull` — fetches a Notion doc by URL or title.
- `sanitize_check` — runs only the secret/PII scan, returns findings without pushing.

## Hard Constraints

- NEVER push without explicit "yes" from Brandon for that specific artifact.
- NEVER push content that fails sanitize check unless Brandon types the exact override phrase.
- NEVER write Notion content to local memory without Brandon's explicit save request.
- NEVER push lessons, sessions, curator reports, or operator-model. These are local-only.
- ALWAYS show the one-line preview before pushing.
- ALWAYS return the Notion URL after a successful push.
