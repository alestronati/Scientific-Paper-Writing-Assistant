#!/usr/bin/env python3
"""Tests for project_init.py"""

import os
import sys
import tempfile
import unittest

import yaml

# Add parent scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from project_init import SECTIONS, create_project


class TestNewProjectCreatesStructure(unittest.TestCase):
    """Verify that a new project creates all directories and files with correct schema."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.tmpdir, "test_manuscript")
        create_project(self.project_path, journal="", import_path=None)

    def test_all_section_dirs_exist(self):
        for section in SECTIONS:
            section_dir = os.path.join(self.project_path, section)
            self.assertTrue(os.path.isdir(section_dir), f"Missing section dir: {section}")

    def test_section_files_exist(self):
        expected_files = {
            "00_Title_Keywords": ["title_v1.0.txt", "keywords_v1.0.txt"],
            "01_Abstract": ["abstract_v1.0.txt"],
            "03_Methods": ["methods_v1.0.txt"],
            "04_Results": ["results_v1.0.txt"],
            "07_Figures": ["figure_captions.txt", "figures_v1.0.txt"],
            "08_Tables": ["table_captions.txt", "tables_v1.0.txt"],
            "09_Bibliography": ["bibliography.txt", "missing_papers.txt"],
        }
        for section, files in expected_files.items():
            for fname in files:
                fpath = os.path.join(self.project_path, section, fname)
                self.assertTrue(os.path.isfile(fpath), f"Missing file: {section}/{fname}")

    def test_subdirs_exist(self):
        self.assertTrue(os.path.isdir(os.path.join(self.project_path, "07_Figures", "figures")))
        self.assertTrue(os.path.isdir(os.path.join(self.project_path, "08_Tables", "tables")))
        self.assertTrue(os.path.isdir(os.path.join(self.project_path, "09_Bibliography", "cited_papers")))

    def test_top_level_dirs_exist(self):
        for d in ["scripts", "images", "OLD_Version_Files", "data"]:
            self.assertTrue(os.path.isdir(os.path.join(self.project_path, d)), f"Missing dir: {d}")

    def test_project_state_schema(self):
        with open(os.path.join(self.project_path, "project_state.yaml")) as f:
            state = yaml.safe_load(f)

        self.assertIn("journal", state)
        self.assertIn("created", state)
        self.assertIn("sections", state)
        self.assertIn("open_issues", state)
        self.assertIn("linked_notebooks", state)
        self.assertIn("data_files_stale", state)
        self.assertIsInstance(state["open_issues"], list)
        self.assertIsInstance(state["sections"], dict)
        self.assertEqual(len(state["sections"]), len(SECTIONS))

        for section_name, section_data in state["sections"].items():
            self.assertIn("current_version", section_data)
            self.assertIn("last_agent", section_data)
            self.assertIn("last_modified", section_data)
            self.assertIn("verification_status", section_data)
            self.assertIn("word_count", section_data)
            self.assertEqual(section_data["current_version"], "v1.0")
            self.assertEqual(section_data["last_agent"], "project_init")
            self.assertEqual(section_data["verification_status"], "pending")
            self.assertEqual(section_data["word_count"], 0)

    def test_writing_rules_exist(self):
        with open(os.path.join(self.project_path, "writing_rules.yaml")) as f:
            rules = yaml.safe_load(f)
        self.assertIn("banned_phrases", rules)
        self.assertTrue(rules["no_em_dashes"])
        self.assertTrue(rules["prefer_active_voice"])
        self.assertIn("per_section", rules)

    def test_section_contracts_exist(self):
        with open(os.path.join(self.project_path, "section_contracts.yaml")) as f:
            contracts = yaml.safe_load(f)
        for section in SECTIONS:
            self.assertIn(section, contracts, f"Missing contract for {section}")
            self.assertIn("done_when", contracts[section])

    def test_claude_md_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(self.project_path, "CLAUDE.md")))

    def test_rule_files_exist(self):
        rules_dir = os.path.join(self.project_path, ".claude", "rules")
        for fname in ["no-em-dashes.md", "citation-integrity.md", "writing-style.md", "old-version-files-forbidden.md"]:
            self.assertTrue(os.path.isfile(os.path.join(rules_dir, fname)), f"Missing rule: {fname}")

    def test_data_manifest(self):
        with open(os.path.join(self.project_path, "data", "data_manifest.yaml")) as f:
            manifest = yaml.safe_load(f)
        self.assertIn("files", manifest)
        self.assertIn("last_updated", manifest)
        self.assertIsInstance(manifest["files"], list)


class TestNewProjectWithJournal(unittest.TestCase):
    """Verify that --journal sets the journal name in state and CLAUDE.md."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.project_path = os.path.join(self.tmpdir, "nature_paper")
        create_project(self.project_path, journal="Nature", import_path=None)

    def test_journal_in_state(self):
        with open(os.path.join(self.project_path, "project_state.yaml")) as f:
            state = yaml.safe_load(f)
        self.assertEqual(state["journal"], "Nature")

    def test_journal_in_claude_md(self):
        with open(os.path.join(self.project_path, "CLAUDE.md")) as f:
            content = f.read()
        self.assertIn("Nature", content)


if __name__ == "__main__":
    unittest.main()
