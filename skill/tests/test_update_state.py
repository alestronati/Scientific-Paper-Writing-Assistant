#!/usr/bin/env python3
"""Tests for update_state.py."""

import os
import subprocess
import sys
import tempfile

import yaml

SCRIPTS_DIR = os.path.expanduser("~/.claude/skills/scientific-paper-writer/scripts")
PROJECT_INIT = os.path.join(SCRIPTS_DIR, "project_init.py")
UPDATE_STATE = os.path.join(SCRIPTS_DIR, "update_state.py")


def _init_project(project_path: str, journal: str = "Nature") -> None:
    """Helper: run project_init.py to create a project."""
    result = subprocess.run(
        ["python3", PROJECT_INIT, project_path, "--journal", journal],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"project_init failed: {result.stderr}"


def _read_state(project_path: str) -> dict:
    with open(os.path.join(project_path, "project_state.yaml"), "r") as f:
        return yaml.safe_load(f)


def test_update_state_counts_words():
    """Create a project, write content to abstract, run update_state, verify word count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test_project")
        _init_project(project_path)

        # Write 10 words into the abstract file
        abstract_file = os.path.join(project_path, "01_Abstract", "abstract_v1.0.txt")
        with open(abstract_file, "w") as f:
            f.write("This is a test abstract with exactly ten words here")

        result = subprocess.run(
            ["python3", UPDATE_STATE, project_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"update_state failed: {result.stderr}"

        state = _read_state(project_path)
        word_count = state["sections"]["01_Abstract"]["word_count"]
        assert word_count == 10, f"Expected 10 words, got {word_count}"

        # Sections without content should have 0 words
        assert state["sections"]["02_Introduction"]["word_count"] == 0

    print("PASSED: test_update_state_counts_words")


def test_update_state_display_mode():
    """Verify --display outputs section names and versions to stdout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test_display")
        _init_project(project_path, journal="Nature")

        result = subprocess.run(
            ["python3", UPDATE_STATE, "--display", project_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"update_state --display failed: {result.stderr}"

        output = result.stdout
        assert "Journal: Nature" in output, f"Missing journal header in output"
        assert "01_Abstract" in output, f"Missing section name in output"
        assert "v1.0" in output, f"Missing version in output"
        assert "Total" in output, f"Missing total row in output"

    print("PASSED: test_update_state_display_mode")


def test_finds_latest_version():
    """Create multiple version files (v1.0, v1.1, v1.2), verify it picks v1.2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, "test_versions")
        _init_project(project_path)

        abstract_dir = os.path.join(project_path, "01_Abstract")

        # v1.0 already exists from init; create v1.1 and v1.2
        with open(os.path.join(abstract_dir, "abstract_v1.1.txt"), "w") as f:
            f.write("Version one point one")
        with open(os.path.join(abstract_dir, "abstract_v1.2.txt"), "w") as f:
            f.write("Final version three words")

        result = subprocess.run(
            ["python3", UPDATE_STATE, project_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"update_state failed: {result.stderr}"

        state = _read_state(project_path)
        section = state["sections"]["01_Abstract"]
        assert section["current_version"] == "v1.2", \
            f"Expected v1.2, got {section['current_version']}"
        # "Final version three words" = 4 words
        assert section["word_count"] == 4, \
            f"Expected 4 words, got {section['word_count']}"

    print("PASSED: test_finds_latest_version")


if __name__ == "__main__":
    test_update_state_counts_words()
    test_update_state_display_mode()
    test_finds_latest_version()
    print("\nAll tests passed.")
