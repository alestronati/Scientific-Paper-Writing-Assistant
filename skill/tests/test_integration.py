#!/usr/bin/env python3
"""End-to-end integration tests for Phase 1: init, write, quality gate, status."""

import os
import subprocess
import sys
import tempfile
import unittest

import yaml

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)
PROJECT_INIT = os.path.join(SCRIPTS_DIR, "project_init.py")
QUALITY_GATE = os.path.join(SCRIPTS_DIR, "quality_gate.py")
UPDATE_STATE = os.path.join(SCRIPTS_DIR, "update_state.py")

# Check whether update_state.py exists; skip tests that need it if not.
HAS_UPDATE_STATE = os.path.isfile(UPDATE_STATE)

ABSTRACT_TEXT = (
    "Synthetic torpor induced by GABA-ergic activation of the raphe pallidus "
    "protects mice from hypergravity-induced physiological stress at 2G for 21 days."
)

METHODS_TEXT = (
    "Male C57BL/6J mice (n=6 per group) were exposed to 2G centrifugation for 21 days. "
    "Core body temperature was recorded via telemetry. "
    "Data were analyzed using two-way ANOVA followed by Tukey post-hoc tests in SPSS v28."
)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Python script and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, script, *args],
        capture_output=True,
        text=True,
    )


class TestFullInitWriteStatusFlow(unittest.TestCase):
    """Init project, write content, run quality gate, display status, verify state."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.project = os.path.join(self._tmpdir.name, "torpor_paper")
        result = run_script(PROJECT_INIT, self.project, "--journal", "npj Microgravity")
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _write(self, relpath: str, text: str) -> str:
        fpath = os.path.join(self.project, relpath)
        with open(fpath, "w") as f:
            f.write(text)
        return fpath

    def test_full_init_write_status_flow(self):
        # 1. Write realistic abstract
        abstract_path = self._write("01_Abstract/abstract_v1.0.txt", ABSTRACT_TEXT)

        # 2. Write realistic methods
        self._write("03_Methods/methods_v1.0.txt", METHODS_TEXT)

        # 3. Quality gate on abstract -- expect PASS
        qg = run_script(QUALITY_GATE, abstract_path)
        self.assertEqual(qg.returncode, 0, f"Quality gate should PASS:\n{qg.stdout}")
        self.assertIn("PASS", qg.stdout)

        # 4. update_state --display (skip if script missing)
        if not HAS_UPDATE_STATE:
            self.skipTest("update_state.py not available yet")

        us = run_script(UPDATE_STATE, "--display", self.project)
        self.assertEqual(us.returncode, 0, f"update_state failed:\n{us.stderr}")
        self.assertIn("npj Microgravity", us.stdout)
        self.assertIn("01_Abstract", us.stdout)

        # 5. Load project_state.yaml and verify
        with open(os.path.join(self.project, "project_state.yaml")) as f:
            state = yaml.safe_load(f)
        self.assertEqual(state["journal"], "npj Microgravity")


class TestQualityGateCatchesTemplate(unittest.TestCase):
    """Quality gate must FAIL when template ratio exceeds 5%."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.project = os.path.join(self._tmpdir.name, "template_paper")
        run_script(PROJECT_INIT, self.project)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_quality_gate_catches_template_in_project(self):
        # Write content dominated by template placeholders (>5% ratio)
        template_content = (
            "[INSERT abstract here]\n"
            "[TODO: write abstract]\n"
            "[INSERT methods summary]\n"
            "[TODO: add results]\n"
            "[PLACEHOLDER: conclusions]\n"
            "[ADD references here]\n"
            "Real sentence about synthetic torpor.\n"
        )
        abstract_path = os.path.join(self.project, "01_Abstract", "abstract_v1.0.txt")
        with open(abstract_path, "w") as f:
            f.write(template_content)

        result = run_script(QUALITY_GATE, abstract_path)
        self.assertEqual(result.returncode, 1, f"Expected FAIL but got PASS:\n{result.stdout}")
        self.assertIn("FAIL", result.stdout)


class TestImportCopiesToOldVersions(unittest.TestCase):
    """--import should copy files into OLD_Version_Files, not into section dirs."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        # Create a source directory with some files
        self.source = os.path.join(self._tmpdir.name, "old_manuscript")
        os.makedirs(self.source)
        for name in ["draft.docx", "figures.pptx", "refs.bib"]:
            with open(os.path.join(self.source, name), "w") as f:
                f.write(f"content of {name}")

        self.project = os.path.join(self._tmpdir.name, "imported_paper")
        result = run_script(
            PROJECT_INIT, self.project,
            "--journal", "Nature",
            "--import", self.source,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_import_copies_to_old_versions(self):
        old_dir = os.path.join(self.project, "OLD_Version_Files")
        for name in ["draft.docx", "figures.pptx", "refs.bib"]:
            self.assertTrue(
                os.path.isfile(os.path.join(old_dir, name)),
                f"{name} should exist in OLD_Version_Files/",
            )

    def test_imported_files_not_in_sections(self):
        from project_init import SECTIONS

        for section in SECTIONS:
            section_dir = os.path.join(self.project, section)
            for name in ["draft.docx", "figures.pptx", "refs.bib"]:
                self.assertFalse(
                    os.path.isfile(os.path.join(section_dir, name)),
                    f"{name} should NOT be in {section}/",
                )


class TestPathScopedRulesExist(unittest.TestCase):
    """Verify .claude/rules/ contains the required rule files with correct content."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.project = os.path.join(self._tmpdir.name, "rules_paper")
        run_script(PROJECT_INIT, self.project)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_no_em_dashes_rule(self):
        path = os.path.join(self.project, ".claude", "rules", "no-em-dashes.md")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("paths:", content)

    def test_citation_integrity_rule(self):
        path = os.path.join(self.project, ".claude", "rules", "citation-integrity.md")
        self.assertTrue(os.path.isfile(path))

    def test_writing_style_rule(self):
        path = os.path.join(self.project, ".claude", "rules", "writing-style.md")
        self.assertTrue(os.path.isfile(path))

    def test_old_version_files_rule(self):
        path = os.path.join(self.project, ".claude", "rules", "old-version-files-forbidden.md")
        self.assertTrue(os.path.isfile(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("OLD_Version_Files", content)


class TestVersionFilesAreEmptyOnInit(unittest.TestCase):
    """Section files should exist but be empty (0 bytes) on a fresh init."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.project = os.path.join(self._tmpdir.name, "empty_paper")
        run_script(PROJECT_INIT, self.project)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_abstract_empty(self):
        path = os.path.join(self.project, "01_Abstract", "abstract_v1.0.txt")
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(os.path.getsize(path), 0)

    def test_methods_empty(self):
        path = os.path.join(self.project, "03_Methods", "methods_v1.0.txt")
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()
