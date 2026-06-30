"""Shell hooks and scripts must have a shebang and the executable bit set."""

from __future__ import annotations

import os

import pytest
from conftest import ROOT

SCRIPTS = sorted((ROOT / "hooks").glob("*.sh")) + sorted((ROOT / "scripts").glob("*.sh"))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_has_shebang(script):
    first_line = script.read_text().splitlines()[0]
    assert first_line.startswith("#!"), f"{script.name}: missing shebang"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_is_executable(script):
    assert os.access(script, os.X_OK), f"{script.name}: not executable"
