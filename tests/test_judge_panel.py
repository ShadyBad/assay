"""Validate judge-panel roster integrity: the '29 judges' claim must hold."""

from __future__ import annotations

import re

from conftest import SKILLS_DIR, parse_frontmatter

JUDGE_PANEL = SKILLS_DIR / "judge-panel" / "SKILL.md"
EXPECTED_JUDGES = 29
MODELS = ("Opus", "Sonnet", "Haiku")


def _text() -> str:
    return JUDGE_PANEL.read_text()


def test_tier_header_counts_sum_to_expected():
    counts = re.findall(r"^### Tier \d+ .*\((\d+)\)", _text(), re.MULTILINE)
    assert counts, "no '### Tier N ... (count)' headers found"
    assert sum(int(c) for c in counts) == EXPECTED_JUDGES


def test_numbered_judge_entries_count():
    entries = re.findall(r"^\d+\.\s+\*\*", _text(), re.MULTILINE)
    assert len(entries) == EXPECTED_JUDGES, f"found {len(entries)} numbered judges"


def test_description_claims_expected_count():
    fm = parse_frontmatter(_text())
    assert re.search(rf"\b{EXPECTED_JUDGES}\b", fm["description"]), (
        f"description should state {EXPECTED_JUDGES} as a standalone number"
    )


def _model_assignment_section() -> str:
    """The text between '## Per-Judge Model Assignment' and the next '## ' header."""
    text = _text()
    start = text.index("## Per-Judge Model Assignment")
    rest = text[start + 1 :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_model_assignment_covers_all_tiers():
    section = _model_assignment_section()
    missing = [m for m in MODELS if f"**{m}**" not in section]
    assert not missing, f"models absent from model-assignment section: {missing}"
