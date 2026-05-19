---
name: commit-protocol
description: Engineer-in-the-loop commit flow. Generates conventional commit messages, shows Brandon a brief overview (file count, additions, deletions, changed files, message), waits for explicit ship or y approval, then commits. After commit, asks if Brandon wants to push. Never commits with --no-verify, never force pushes, never auto-pushes — all require explicit Brandon override. Builds on commit-commands plugin's primitives. Use at the end of every /ship after done-gate Check 7 passes, when Brandon asks "commit this" or "ready to commit", or after a long-running task produces stage-able changes. Coordinates with done-gate for Check 8 (Brandon approval).
---

# Commit Protocol Skill

Engineer-in-the-loop commit flow. The handoff from done-gate (after Checks 1-7) through to git commit and optional push. Brandon stays in control at every irreversible step.

## The Flow

### Step 1: Generate Commit Message

Generate a commit message in Conventional Commits format:
<type>(<scope>): <description>
[optional body]
[optional footer]

Types:
- `feat` — new feature.
- `fix` — bug fix.
- `refactor` — code change that neither fixes a bug nor adds a feature.
- `test` — adding or modifying tests.
- `docs` — documentation only.
- `style` — formatting, no logic change.
- `perf` — performance improvement.
- `chore` — maintenance (deps, config).
- `revert` — reverts a previous commit.
- `build` — build system changes.
- `ci` — CI config changes.

Scope: short module/area name (e.g., `auth`, `scoring`, `ui`). Optional but encouraged.

Description: imperative mood, lowercase, no period. Max 72 chars including type/scope.

Body: explains *why*, not *what*. Wrap at 72 chars. Skip if description is self-evident.

Footer: `BREAKING CHANGE: <description>` for breaking changes. `Closes #N` or `Refs LIN-123` for issue refs.

### Step 1.5: Verify Diff Reality

Before showing Brandon the overview, run:

`git diff --cached --shortstat` for staged changes
`git diff --shortstat` for unstaged
`git status --short` to detect untracked files about to be added

If any of these conditions are true, add a WARNING line to the overview:

- Untracked file being added (status shows `??`): "⚠ NEW FILE: <path> (entire file content will be committed, +<N> lines)"
- Diff size significantly larger than the conceptual change (>10x ratio of expected lines): "⚠ DIFF SIZE: changeset is +<N>/-<M> lines, which is larger than expected for this task. Verify before approving."
- Files staged that were NOT mentioned in the plan: "⚠ UNEXPECTED FILES STAGED: <list>. These were not in the plan. Continue?"

The warnings appear above the standard overview. Brandon still types ship/y/abort. The warnings are surfaced, not blocking.

### Step 2: Show Brandon the Overview

Format:
COMMIT OVERVIEW
Message: <commit message>
Files changed: <count> (+<additions> -<deletions>)

<file 1>: +<adds> -<dels>
<file 2>: +<adds> -<dels>
...

Risk tier: <tier from done-gate>
Judge verdict: <verdict from judge-panel>
Ready? (ship | revise message | abort)

### Step 3: Wait for Approval

Accepted approvals:
- `ship`
- `y`
- `yes`
- `commit`
- `go`

If Brandon types `revise message`, return to Step 1 with his feedback.
If Brandon types `abort`, halt the pipeline. Do not commit. Do not modify any files.

If Brandon's response does not match any accepted approval and is not `revise` or `abort`, ask: "I didn't catch that. Type 'ship' to commit, 'revise' to change the message, or 'abort' to stop."

### Step 4: Commit

Once approved:

```bash
git commit -m "<message>"
```

Hardcoded constraints:
- NEVER use `--no-verify`. Pre-commit hooks must run. If hooks fail, surface to Brandon.
- NEVER use `--amend` without Brandon's explicit `--amend` instruction.
- NEVER include `-Skip-Sign-Off` or similar bypasses.

If git commit succeeds:
✓ Committed: <short SHA> <commit message>

If git commit fails (e.g., pre-commit hook rejected):
✗ Commit failed: <git error output>
This usually means a pre-commit hook rejected the change. Fix the issue and run /ship to re-attempt.

### Step 5: Push Decision

After successful commit, ask:
Commit successful. Push to remote?

y / push — push to current branch's upstream
n / no — don't push (commit stays local)
pr — push and open a PR (via github plugin if installed)


If Brandon chooses push:

```bash
git push
```

Hardcoded constraints:
- NEVER use `--force` or `-f`. If force push is needed, Brandon must explicitly type `force push` AND confirm with `yes I understand this overwrites remote history`.
- NEVER push to a protected branch (main, master, production) without explicit Brandon confirmation per push, regardless of current branch.

If Brandon chooses PR (and `github` plugin is installed), invoke github plugin's PR creation flow.

## Pre-Commit Hook Handling

If git commit fails due to a hook:

1. Capture the hook's output.
2. Parse for common patterns:
   - Linting failures → suggest re-running `done-gate` Check 5.
   - Test failures → suggest re-running `done-gate` Check 3.
   - Format violations → suggest auto-fix command if available.
3. Surface to Brandon: "Hook rejected commit. Reason: <parsed>. Options: (a) auto-fix and retry, (b) view full hook output, (c) abort."
4. Never silently bypass hooks. The pre-commit hooks exist for a reason.

## Commit Message Quality Rules

The skill enforces these on the generated message before showing Brandon:

1. Type must be one of the 11 conventional types.
2. Description must be imperative ("add feature" not "added feature" or "adds feature").
3. Description must NOT start with capital letter (after the colon).
4. Description must NOT end with period.
5. Description must NOT exceed 72 chars (including type/scope/colon).
6. Body lines must wrap at 72 chars.
7. If the diff includes breaking changes (interface change, schema migration, removed function), the message MUST include a `BREAKING CHANGE:` footer.

If any rule is violated by the generated message, regenerate before showing Brandon.

## Override Flags

- `/ship --commit-message="<exact message>"` — use Brandon's exact message, skip generation.
- `/ship --amend "<task>"` — amend last commit instead of new commit. Confirms with Brandon before amending.
- `/ship --no-push "<task>"` — skip the push question, commit only.
- `/ship --auto-push "<task>"` — push immediately after commit without asking. Use sparingly.

## Integration with Other Skills

- **done-gate** — hands off to commit-protocol after Checks 1-7 pass. commit-protocol owns Check 8.
- **judge-panel** — verdict is shown in the overview for context.
- **/ship** — invokes commit-protocol as the final pipeline step before LEARN.
- **github plugin** — used for PR creation when Brandon chooses `pr`.

## Plugin Compatibility

Enhanced by:
- `commit-commands@claude-plugins-official` — provides the underlying commit/push/PR primitives.
- `github@claude-plugins-official` — used for PR creation.

Required: git (always available in any code repo).

If `commit-commands` plugin is missing, use raw `git` commands directly. Functionality identical.

## Hard Constraints

- NEVER commit without Brandon's explicit approval (Check 8 from done-gate).
- NEVER use `git commit --no-verify`.
- NEVER use `git push --force` without double confirmation from Brandon.
- NEVER push to protected branches (main, master, production) without per-push confirmation.
- NEVER amend a commit that has been pushed without confirming Brandon understands the implications.
- ALWAYS run pre-commit hooks. If they fail, surface to Brandon and offer auto-fix.
- ALWAYS show the commit overview before committing.
- ALWAYS ask about push (do not auto-push) unless `--auto-push` flag is set.
