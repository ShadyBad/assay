# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-06-29

### Added
- Python test harness (`tests/`) validating the plugin's own structure: manifest
  integrity, skill/command frontmatter, judge-panel roster count, doc-link
  resolution, and hook executability.
- GitHub Actions CI (`.github/workflows/ci.yml`) running ruff + pytest on every
  push and pull request.
- `CONTRIBUTING.md` and this `CHANGELOG.md`.
- Architecture diagram and demo scaffold (`demo/`) in the README.
- YAML frontmatter for the `/eod`, `/morning`, and `/weekly` commands, matching
  the other commands.

### Fixed
- `plugin.json` description claimed 11 supporting skills; the repo ships 12. The
  manifest test now prevents this count from drifting again.

### Removed
- Placeholder `main.py` Hello-World stub left over from `uv init`.

### Changed
- `pyproject.toml` is now a real, described, virtual (non-package) project with a
  pinned dev-dependency group and ruff/pytest config.
- `.gitignore` now covers `.venv/` and Python tool caches.

## [0.1.0] - 2026-05-18

### Added
- Initial extraction of the `/assay` 14-step orchestrator and supporting skills
  from a personal Claude Code configuration into an installable plugin.
- 7 commands (`/assay`, `/spec`, `/postmortem`, `/morning`, `/eod`, `/weekly`,
  `/cross-learn`), 12 skills, and 3 proposal-surfacing hooks.

[Unreleased]: https://github.com/shadybad/assay/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/shadybad/assay/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/shadybad/assay/releases/tag/v0.1.0
