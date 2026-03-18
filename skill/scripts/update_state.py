#!/usr/bin/env python3
"""
update_state.py - Scan a manuscript project and update project_state.yaml.

Usage:
    python3 update_state.py /path/to/project              # update silently
    python3 update_state.py --display /path/to/project     # update + print status table
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone

import yaml

VERSION_RE = re.compile(r"_v(\d+\.\d+)\.txt$")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_version(filename: str) -> tuple[int, int] | None:
    """Extract (major, minor) version tuple from a filename, or None."""
    m = VERSION_RE.search(filename)
    if not m:
        return None
    major, minor = m.group(1).split(".")
    return (int(major), int(minor))


def version_string(major: int, minor: int) -> str:
    return f"v{major}.{minor}"


def find_latest_version_file(section_dir: str) -> tuple[str | None, str | None]:
    """Return (filepath, version_string) for the highest-version .txt in section_dir."""
    best_path = None
    best_ver = (-1, -1)
    best_ver_str = None

    if not os.path.isdir(section_dir):
        return None, None

    for fname in os.listdir(section_dir):
        ver = parse_version(fname)
        if ver and ver > best_ver:
            best_ver = ver
            best_path = os.path.join(section_dir, fname)
            best_ver_str = version_string(*ver)

    return best_path, best_ver_str


def count_words(filepath: str) -> int:
    """Count words in a file."""
    if not filepath or not os.path.isfile(filepath):
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        return len(f.read().split())


def update_state(project_path: str) -> dict:
    """Scan project, update project_state.yaml, return the updated state dict."""
    project_path = os.path.abspath(project_path)
    state_file = os.path.join(project_path, "project_state.yaml")

    if not os.path.isfile(state_file):
        print(f"Error: project_state.yaml not found in {project_path}", file=sys.stderr)
        sys.exit(1)

    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)

    timestamp = iso_now()
    sections = state.get("sections", {})

    # Scan directories matching ^\d{2}_ pattern
    for entry in sorted(os.listdir(project_path)):
        if not re.match(r"^\d{2}_", entry):
            continue
        section_dir = os.path.join(project_path, entry)
        if not os.path.isdir(section_dir):
            continue

        latest_path, latest_ver = find_latest_version_file(section_dir)

        if entry not in sections:
            sections[entry] = {
                "current_version": "v1.0",
                "last_agent": "update_state",
                "last_modified": timestamp,
                "verification_status": "pending",
                "word_count": 0,
            }

        if latest_ver:
            sections[entry]["current_version"] = latest_ver
        sections[entry]["word_count"] = count_words(latest_path)
        sections[entry]["last_modified"] = timestamp

    state["sections"] = sections

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    return state


def display_state(state: dict) -> None:
    """Print a formatted status table to stdout."""
    journal = state.get("journal", "Not set")
    print(f"Journal: {journal}")

    header = f"{'Section':<35}{'Version':<11}{'Words':<9}{'Verified':<10}"
    print(header)
    print("-" * len(header))

    total_words = 0
    sections = state.get("sections", {})
    for name in sorted(sections.keys()):
        info = sections[name]
        ver = info.get("current_version", "v1.0")
        words = info.get("word_count", 0)
        status = info.get("verification_status", "pending")
        total_words += words
        print(f"{name:<35}{ver:<11}{words:<9}{status:<10}")

    print("-" * len(header))
    print(f"{'Total':<35}{'':<11}{total_words:<9}")

    open_issues = state.get("open_issues", [])
    print(f"\nOpen Issues: {len(open_issues)}")
    for issue in open_issues:
        severity = issue.get("severity", "info")
        section = issue.get("section", "general")
        msg = issue.get("message", str(issue))
        print(f"  - [{severity}] {section}: {msg}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan a manuscript project and update project_state.yaml."
    )
    parser.add_argument("project_path", help="Path to the manuscript project directory")
    parser.add_argument("--display", action="store_true",
                        help="Print a formatted status table after updating")
    args = parser.parse_args()

    state = update_state(args.project_path)

    if args.display:
        display_state(state)


if __name__ == "__main__":
    main()
