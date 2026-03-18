#!/usr/bin/env python3
"""Quality gate: detect template/placeholder content in text files.

Usage: python3 quality_gate.py <filepath>
Exit 0 = PASS, Exit 1 = FAIL (template ratio > 5%).
"""

import re
import sys

PATTERNS = [
    (r"\[INSERT\s+.*?\]", "INSERT placeholder"),
    (r"\[TODO:?\s*.*?\]", "TODO placeholder"),
    (r"\[PLACEHOLDER:?\s*.*?\]", "PLACEHOLDER marker"),
    (r"\[ADD\s+.*?\]", "ADD placeholder"),
    (r"(?i)this section will describe", "future tense placeholder"),
    (r"(?i)this section provides", "generic section opener"),
    (r"(?i)add your content here", "template instruction"),
    (r"(?i)replace this text", "template instruction"),
    (r"(?i)lorem ipsum", "lorem ipsum"),
    (r"(?i)insert (?:figure|table|reference|citation) here", "insert-here instruction"),
    (r"(?i)describe the .{0,30} methodology", "methodology placeholder"),
    (r"(?i)\bTBD\b", "TBD marker"),
    (r"(?i)content goes here", "template instruction"),
]

COMPILED = [(re.compile(p), label) for p, label in PATTERNS]


def check_file(filepath: str) -> int:
    """Return 0 for PASS, 1 for FAIL."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content_lines = [(i + 1, line) for i, line in enumerate(lines) if line.strip()]
    total = len(content_lines)

    if total == 0:
        print("PASS: No template content detected")
        return 0

    matches: list[tuple[int, str, str]] = []
    for lineno, line in content_lines:
        for regex, label in COMPILED:
            m = regex.search(line)
            if m:
                matches.append((lineno, label, m.group()))
                break  # one match per line is enough

    ratio = len(matches) / total

    if not matches:
        print("PASS: No template content detected")
        return 0

    if ratio > 0.05:
        print(
            f"FAIL: Template content ratio {ratio:.1%} exceeds 5% threshold\n"
            f"Found {len(matches)} template matches in {total} content lines:"
        )
        for lineno, label, text in matches:
            print(f"  L{lineno}: [{label}] {text}")
        return 1

    # Matches exist but under threshold
    print(
        f"PASS (with warnings): {len(matches)} template matches in {total} "
        f"content lines ({ratio:.1%})"
    )
    for lineno, label, text in matches:
        print(f"  L{lineno}: [{label}] {text}")
    return 0


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filepath>", file=sys.stderr)
        sys.exit(2)
    sys.exit(check_file(sys.argv[1]))


if __name__ == "__main__":
    main()
