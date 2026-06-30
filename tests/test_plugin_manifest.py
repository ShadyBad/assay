"""Validate .claude-plugin/plugin.json — the plugin's entry manifest."""

from __future__ import annotations

import re

from conftest import ROOT, skill_dirs

SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+].+)?$")
REQUIRED_KEYS = ("name", "version", "description", "commands", "skills")


def test_manifest_required_keys(manifest):
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    assert not missing, f"plugin.json missing keys: {missing}"


def test_manifest_name(manifest):
    assert manifest["name"] == "claude-ship"


def test_manifest_version_is_semver(manifest):
    assert SEMVER.match(manifest["version"]), manifest["version"]


def test_manifest_command_paths_exist(manifest):
    for rel in manifest["commands"]:
        assert (ROOT / rel).exists(), f"commands path does not exist: {rel}"


def test_manifest_skill_paths_exist(manifest):
    for rel in manifest["skills"]:
        assert (ROOT / rel).exists(), f"skills path does not exist: {rel}"


def test_manifest_skill_count_matches_reality(manifest):
    """The '<N> supporting skills' claim must match the directories on disk."""
    match = re.search(r"(\d+)\s+supporting skills", manifest["description"])
    assert match, "description should state the supporting-skill count"
    claimed, actual = int(match.group(1)), len(skill_dirs())
    assert claimed == actual, f"description claims {claimed} skills, found {actual}"
