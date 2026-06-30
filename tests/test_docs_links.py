"""Every relative markdown link in the curated docs must resolve to a real file."""

from __future__ import annotations

import re

import pytest
from conftest import ROOT

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
EXTERNAL = ("http://", "https://", "mailto:")

DOC_FILES = [
    p
    for p in (
        ROOT / "README.md",
        ROOT / "INSTALL.md",
        ROOT / "CONFIG.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "CHANGELOG.md",
        ROOT / "hooks" / "README.md",
    )
    if p.exists()
]


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(doc):
    broken = []
    text = HTML_COMMENT.sub("", doc.read_text())
    for target in LINK.findall(text):
        target = target.split("#")[0].strip()
        if not target or target.startswith(EXTERNAL):
            continue
        if not (doc.parent / target).resolve().exists():
            broken.append(target)
    assert not broken, f"{doc.name}: broken relative links {broken}"
