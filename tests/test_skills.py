"""Validate every skill: SKILL.md present, frontmatter well-formed, name matches dir."""

from __future__ import annotations

import re

import pytest
from conftest import parse_frontmatter, skill_dirs

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIN_DESCRIPTION_LEN = 40


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_skill_has_skill_md(skill_dir):
    assert (skill_dir / "SKILL.md").is_file(), f"{skill_dir.name}: no SKILL.md"


@pytest.mark.parametrize("skill_dir", skill_dirs(), ids=lambda p: p.name)
def test_skill_frontmatter_well_formed(skill_dir):
    fm = parse_frontmatter((skill_dir / "SKILL.md").read_text())
    assert fm is not None, f"{skill_dir.name}: missing YAML frontmatter"
    assert fm.get("name") == skill_dir.name, (
        f"{skill_dir.name}: frontmatter name {fm.get('name')!r} != directory name"
    )
    assert KEBAB.match(fm["name"]), f"{fm['name']!r}: name is not kebab-case"
    assert len(fm.get("description", "")) >= MIN_DESCRIPTION_LEN, (
        f"{skill_dir.name}: description shorter than {MIN_DESCRIPTION_LEN} chars"
    )
