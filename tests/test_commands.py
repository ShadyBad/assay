"""Validate every command file: non-empty, frontmatter present, name matches stem."""

from __future__ import annotations

import pytest
from conftest import command_files, parse_frontmatter


@pytest.mark.parametrize("cmd", command_files(), ids=lambda p: p.name)
def test_command_nonempty(cmd):
    assert cmd.read_text().strip(), f"{cmd.name} is empty"


@pytest.mark.parametrize("cmd", command_files(), ids=lambda p: p.name)
def test_command_frontmatter_matches_stem(cmd):
    fm = parse_frontmatter(cmd.read_text())
    assert fm is not None, f"{cmd.name}: missing YAML frontmatter"
    assert fm.get("name") == cmd.stem, (
        f"{cmd.name}: frontmatter name {fm.get('name')!r} != file stem {cmd.stem!r}"
    )
    assert fm.get("description", "").strip(), f"{cmd.name}: empty description"
