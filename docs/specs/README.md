# Shipped specs

Archived copies of specs that produced commits in this repository. They explain
why a thing exists, which a commit message can only gesture at.

**These are records, not the working copy.** `/spec` and `/assay` read specs
from `~/.claude/memory/projects/<namespace>/specs/`, which is operator state and
lives outside version control. A spec is copied here once it reaches
`status: shipped`, with its `shipped-commit` already filled in.

So: edit the live copy, never this one. A spec here that disagrees with the live
copy is stale by definition, and the `shipped-commit` field is what ties it to
the history it explains.

| Spec | Shipped | Commit |
|------|---------|--------|
| [judge-enforcement-model-2026-09-12](judge-enforcement-model-2026-09-12.md) — enforce the mandatory-judge floor with a commit-msg hook | 2026-09-12 | `026ba49` |
