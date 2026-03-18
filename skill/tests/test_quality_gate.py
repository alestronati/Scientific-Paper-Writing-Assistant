"""Tests for quality_gate.py template content detector."""

import os
import sys
import tempfile
import unittest

# Allow importing from sibling scripts/ directory
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts")
)
from quality_gate import check_file


class TestQualityGate(unittest.TestCase):
    """Verify pass/fail behaviour of the quality gate."""

    def _write_temp(self, text: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def test_clean_text_passes(self):
        text = (
            "Synthetic torpor was induced in rats via intracerebroventricular\n"
            "injection of muscimol targeting the RPa nucleus. Core body\n"
            "temperature decreased to 28 C within 45 minutes. Heart rate\n"
            "dropped proportionally, consistent with prior observations.\n"
            "Metabolic rate, measured by indirect calorimetry, fell by 60%.\n"
        )
        path = self._write_temp(text)
        self.assertEqual(check_file(path), 0)

    def test_template_content_fails(self):
        text = (
            "[INSERT your abstract here]\n"
            "The study investigated metabolic suppression.\n"
            "[TODO: add methods]\n"
            "[INSERT results summary]\n"
        )
        path = self._write_temp(text)
        self.assertEqual(check_file(path), 1)

    def test_placeholder_detected(self):
        # 1 placeholder among 25 real lines -> under threshold but warned
        real_lines = [
            f"Line {i}: real scientific content about neuronal inhibition.\n"
            for i in range(24)
        ]
        real_lines.insert(5, "This section will describe the experimental setup.\n")
        text = "".join(real_lines)
        path = self._write_temp(text)
        # ratio = 1/25 = 4% < 5%, so it should pass (with warning)
        self.assertEqual(check_file(path), 0)


if __name__ == "__main__":
    unittest.main()
