# Deploy target — `.claude/deploy.md`

Per-project deploy contract read by `/ship` **Step 11.5: DEPLOY → CANARY**.
Copy this file to a project's `.claude/deploy.md` and fill the block below.
No `.claude/deploy.md` in a project → Step 11.5 finds no target and skips (deploy stays inert).

Step 11.5 never runs without explicit approval regardless of this file. This file
only tells the pipeline *how* to deploy once you say "deploy"; it does not authorize one.

## Contract

The pipeline parses the fenced `yaml` block below. Required keys: `env`, `command`,
`health_url`, `expected_status`. Everything else has a default.

```yaml
env:             production          # label surfaced in the approval prompt
command:         mcp:vercel          # deploy command to run. Special values:
                                     #   mcp:vercel  → Vercel MCP deploy_to_vercel
                                     #   else        → run verbatim as a shell command
health_url:      https://example.com/api/health   # polled during canary
expected_status: 200                 # HTTP status that counts as healthy
canary_window:   5m                  # poll duration (e.g. 90s, 5m, 10m). Default 5m
metrics:         none                # error-rate / p95 source: posthog | sentry | none
rollback:        mcp:vercel          # how to redeploy the prior SHA. Special values:
                                     #   mcp:vercel  → Vercel MCP redeploy prior deployment
                                     #   manual      → pipeline surfaces steps, does not auto-rollback
                                     #   else        → run verbatim as a shell command
```

## How each field is used

| Field | Step 11.5 stage | Behavior |
|-------|-----------------|----------|
| `env` | Gate | Shown in the CRITICAL approval prompt with project + commit SHA. |
| `command` | Deploy | Run after commit+push confirmed. Build failure → HALT + postmortem, no canary. |
| `health_url` / `expected_status` | Canary | Polled for `canary_window`; wrong status = `degraded`. |
| `canary_window` | Canary | Poll duration. |
| `metrics` | Canary | If `posthog`/`sentry` (and MCP wired), also checks error-rate delta + p95 latency. |
| `rollback` | Verdict | Used only if you approve rollback on a `degraded`/`error-spike` verdict. Rollback is itself explicit-approval only. |

## Notes

- `command: mcp:vercel` prefers the Vercel MCP (`deploy_to_vercel`); it needs the Vercel MCP connected.
- `metrics: posthog` reads the active PostHog project; `metrics: sentry` needs the Sentry MCP authenticated.
- Keep secrets OUT of this file — it is committed. Reference env/CI-managed credentials, never inline tokens.
