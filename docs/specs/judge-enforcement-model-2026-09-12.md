---
spec-id: judge-enforcement-model-2026-09-12
title: Enforce the mandatory-judge floor with a commit-msg hook
namespace: personal
created: 2026-09-12
status: shipped
risk-tier: high
shipped-at: 2026-09-12
shipped-commit: 026ba49a720636847a72ebadfbf0663033f96105
---

## Problem

judge-panel's Hard Constraints are absolutes — "NEVER skip the Security
Reviewer for changes touching auth, secrets, user data, or financial
calculation, regardless of tier or override." Every mechanism that would
enforce one is conditional: on risk tier, on a tag the pre-pass detected, on
the pre-pass surviving, on no override flag, and on the orchestrator choosing
to invoke the skill at all.

Five review rounds on 2026-09-12 each found a different reachable path from a
security-relevant diff to `ship` with judge 2 never run:

1. The pre-pass intersected tags with the tier template, and no MEDIUM template
   lists judge 2 except "New endpoint" — a MEDIUM business-logic diff touching
   auth silently lost its security review. Live in the pipeline, not
   hypothetical.
2. A failed judge was recorded `unreachable`, a state no aggregation rule read.
3. Pre-pass failure fell back to the tag-free tier template, deleting every
   tag-conditional floor at the moment detection broke.
4. `/assay` Step 8 skipped invoking the skill at TRIVIAL and under
   `--no-judges`, so none of the above executed on those paths.
5. Stale budget and dry-run-resume text describing the old behavior.

Each fix was correct and each was followed by another path. All five fixes are
prose, and prose enforcing prose has no failure signal: nothing breaks when the
guarantee and the mechanism disagree, so they drift until someone traces
control flow by hand.

## Hypothesis

Only code running outside the agent's discretion is enforcement. A paragraph is
a request; a Python function the agent may or may not call is also a request. A
pre-commit hook is neither — it runs whether or not the agent thought about it,
and its verdict is not negotiable from inside the conversation.

Moving the floor into a hook makes the guarantee testable in a way prose never
was, and collapses the five restatements into one instruction plus one check.

## Success criteria

1. `scripts/check_mandatory_judges.py` exposes a pure
   `check_commit(staged_diff: str, receipt: dict | None, commit_msg: str) -> Verdict`,
   and a parametrized test table asserts an exact Verdict for each of: no
   receipt; receipt whose `diff_sha256` does not match; matching receipt
   carrying a judge-2 verdict; matching receipt missing judge 2; valid
   `Security-Review: skipped` trailer; detector finds nothing; receipt present
   but malformed.
2. `hooks/git/pre-commit` is versioned, executable, and activated by
   `git config core.hooksPath hooks/git`. A staged diff containing
   security-relevant content, with no receipt and no trailer, exits nonzero.
3. Exactly one statement of the mandatory judge set exists in the repository. A
   drift test fails if a second restatement appears in SKILL.md or assay.md.
4. The hook fails closed: any internal error exits nonzero with the error text.
   A test asserts this for a malformed receipt and an unreadable one.
5. After 20 commits under the hook, `git log --grep='Security-Review: skipped'`
   gives the real false-positive rate. Above 50%, the detector is wrong and
   gets narrowed — this is the decision criterion for whether the pattern list
   survives, and for whether the hook widens to other repos.

## Non-goals

- Defending against an agent that fabricates a receipt. The threat model is an
  agent that skipped a step because the instructions had a gap, which is what
  all five rounds actually were. Forgery resistance would require the hook to
  re-run the judge itself, and that cost is not justified by any observed
  behavior.
- Building the computed `mandatory_judges()` function from this spec's earlier
  draft. The hook subsumes it. Two mechanisms encoding one rule is the drift
  this spec exists to stop.
- Widening to margin_invest, patient-pipe, or ai-job-search before the
  false-positive data from criterion 5 exists.
- Improving the pre-pass. This spec assumes the tag set may be absent or wrong
  and asks what the floor does anyway.
- Rewriting the judge roster or rubrics. Shipped 2026-09-12 in af8db0a.

## Constraints

- `.git/hooks` is not versioned, so the hook ships at `hooks/git/pre-commit`
  and is activated per clone with one `core.hooksPath` command. This repo
  already versions its other hooks in `hooks/` and symlinks them, so the
  pattern exists.
- The hook must not read the receipt's tags for detection. It runs its own
  pathspec and content scan over the staged diff, deliberately dumber and more
  conservative than the pre-pass.
- Receipt lives at a fixed repo-relative path, gitignored, and carries
  `{diff_sha256, judges: [{judge, verdict}], ts}`.
- No plugin dependencies. Python 3.13.5 + uv, ruff, pytest.
- The hook contradicts assay.md's run-recorder rule ("instrumentation that can
  halt a ship is worse than no instrumentation") on purpose. That rule governs
  instrumentation; this is a gate, and a gate that opens when it breaks is not
  a gate. The contradiction must be stated in both files, not left implicit.

## Risks / Ways this could be wrong

- **The detector is wrong and the trailer becomes reflexive.** If every commit
  in this repo needs `Security-Review: skipped`, the gate has taught you to
  type a magic phrase and stopped meaning anything. Criterion 5 exists to catch
  this with data rather than vibes, and its threshold is the kill switch.
- **A hook is not enforcement against the failure that actually happened.** Every
  one of the five rounds was a *reasoning* gap — the agent read conditional
  instructions and followed them correctly. A hook catches the commit, not the
  bad review. It guarantees a judge ran; it cannot guarantee the judge was
  given the right diff, the right rubric, or was listened to.
- **Fail-closed can brick the repo.** A typo in the hook blocks every commit,
  including the commit that fixes the hook. `--no-verify` is the only escape and
  operator-model forbids it. The recovery path must be written down before
  this ships.
- **n is small.** judge-panel has fired 3 times in 8 lifetime `/assay` runs. The
  floor has never been exercised in anger, and the 2026-08-01 lesson
  ("compute what the output will actually say at current n") argues for
  instrumenting first and building later. The counter-argument is that the
  MEDIUM-auth hole was live and unbounded in time, not rate-dependent — but if
  criterion 5's data comes back thin, that lesson wins and this gets reverted.
- **Deleting `--no-judges` may be strictly better.** Five rounds found five
  bypasses because five bypasses exist. If the grill's own framing question had
  gone the other way, ~30 deleted lines would beat a hook plus a script plus a
  test table. This remains the cheaper alternative if the hook proves annoying.

## Plan sketch

1. Write the failing test table for `check_commit` first — every row from
   criterion 1, before any implementation.
2. Implement `check_commit` as a pure function. Make the table pass.
3. Write `hooks/git/pre-commit` as a thin wrapper: gather staged diff, receipt,
   commit message; exit on the Verdict.
4. Teach `/assay` Step 8 to write the receipt after the final revise cycle,
   keyed to the staged diff it actually judged.
5. Collapse the prose: one mandatory-set statement in SKILL.md, a citation in
   assay.md, and the drift test from criterion 3.
6. Document the fail-closed recovery path.
7. Run 20 commits. Read criterion 5. Decide whether the detector narrows, the
   hook widens, or the whole thing reverts in favor of deleting `--no-judges`.
