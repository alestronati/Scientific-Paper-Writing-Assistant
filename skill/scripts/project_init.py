#!/usr/bin/env python3
"""
project_init.py - Create a standardized manuscript project directory structure.

Usage:
    python3 project_init.py /path/to/project [--journal "Nature"] [--import /path/to/existing]
"""

import argparse
import os
import shutil
import sys
from datetime import datetime, timezone

import yaml


SECTIONS = [
    "00_Title_Keywords",
    "01_Abstract",
    "02_Introduction",
    "03_Methods",
    "04_Results",
    "05_Discussion",
    "06_Conclusions",
    "07_Figures",
    "08_Tables",
    "09_Bibliography",
    "10_Data_Availability",
    "11_Author_Contributions",
    "12_Competing_Interests",
    "13_Supplementary_Material",
]

# Map section dir name to the text files that go inside it
SECTION_FILES = {
    "00_Title_Keywords": ["title_v1.0.txt", "keywords_v1.0.txt"],
    "01_Abstract": ["abstract_v1.0.txt"],
    "02_Introduction": ["introduction_v1.0.txt"],
    "03_Methods": ["methods_v1.0.txt"],
    "04_Results": ["results_v1.0.txt"],
    "05_Discussion": ["discussion_v1.0.txt"],
    "06_Conclusions": ["conclusions_v1.0.txt"],
    "07_Figures": ["figure_captions.txt", "figures_v1.0.txt"],
    "08_Tables": ["table_captions.txt", "tables_v1.0.txt"],
    "09_Bibliography": ["bibliography.txt", "missing_papers.txt"],
    "10_Data_Availability": ["data_availability_v1.0.txt"],
    "11_Author_Contributions": ["author_contributions_v1.0.txt"],
    "12_Competing_Interests": ["competing_interests_v1.0.txt"],
    "13_Supplementary_Material": ["supplementary_v1.0.txt"],
}

# Sub-directories inside certain sections
SECTION_SUBDIRS = {
    "07_Figures": ["figures"],
    "08_Tables": ["tables"],
    "09_Bibliography": ["cited_papers"],
}

BANNED_PHRASES = [
    "delve into",
    "notably",
    "furthermore",
    "it is worth noting",
    "it is important to note",
    "in conclusion",
    "in summary",
    "plays a crucial role",
    "sheds light on",
    "paves the way",
    "a myriad of",
    "a plethora of",
    "paradigm shift",
    "cutting-edge",
    "groundbreaking",
    "novel insights",
    "robust",
    "landscape",
    "leveraging",
    "holistic",
    "multifaceted",
    "underscores",
    "pivotal",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_project_state(journal: str, timestamp: str) -> dict:
    sections = {}
    for s in SECTIONS:
        sections[s] = {
            "current_version": "v1.0",
            "last_agent": "project_init",
            "last_modified": timestamp,
            "verification_status": "pending",
            "word_count": 0,
        }
    return {
        "journal": journal,
        "created": timestamp,
        "sections": sections,
        "open_issues": [],
        "linked_notebooks": [],
        "data_files_stale": [],
    }


def build_writing_rules() -> dict:
    return {
        "banned_phrases": BANNED_PHRASES,
        "no_em_dashes": True,
        "prefer_active_voice": True,
        "hedging_max_frequency": 0.03,
        "template_content_max_ratio": 0.05,
        "per_section": {
            "03_Methods": {
                "require_software_versions": True,
                "require_statistical_tests": True,
                "require_sample_sizes": True,
            },
            "04_Results": {
                "require_data_provenance": True,
                "require_effect_sizes": True,
                "require_confidence_intervals": True,
            },
            "05_Discussion": {
                "require_limitations_paragraph": True,
                "max_speculation_sentences": 3,
            },
            "01_Abstract": {
                "max_words": 250,
                "require_structured": False,
            },
        },
    }


def build_section_contracts() -> dict:
    return {
        "00_Title_Keywords": {
            "done_when": [
                "Title is under 20 words",
                "Keywords list contains 4-8 terms",
                "No banned phrases in title",
            ]
        },
        "01_Abstract": {
            "done_when": [
                "Word count within journal limit",
                "Contains objective, methods, results, conclusion",
                "No citations",
                "No abbreviations without definition",
            ]
        },
        "02_Introduction": {
            "done_when": [
                "Ends with clear hypothesis or aim statement",
                "Cites at least 5 primary sources",
                "No results discussed",
            ]
        },
        "03_Methods": {
            "done_when": [
                "All software versions specified",
                "Statistical tests named with justification",
                "Sample sizes stated",
                "Reproducible by an independent researcher",
            ]
        },
        "04_Results": {
            "done_when": [
                "Every figure/table referenced in text",
                "Effect sizes and confidence intervals reported",
                "No interpretation or speculation",
                "Data provenance clear",
            ]
        },
        "05_Discussion": {
            "done_when": [
                "Opens with principal findings",
                "Limitations paragraph present",
                "Comparison with prior work cited",
                "Speculation limited to 3 sentences max",
            ]
        },
        "06_Conclusions": {
            "done_when": [
                "No new data introduced",
                "Directly answers the aim from Introduction",
            ]
        },
        "07_Figures": {
            "done_when": [
                "All figures have captions",
                "Resolution at least 300 DPI",
                "Figures numbered sequentially",
            ]
        },
        "08_Tables": {
            "done_when": [
                "All tables have captions",
                "No duplicate data from figures",
                "Tables numbered sequentially",
            ]
        },
        "09_Bibliography": {
            "done_when": [
                "All in-text citations have bibliography entry",
                "No orphan bibliography entries",
                "Format matches journal style",
            ]
        },
        "10_Data_Availability": {
            "done_when": [
                "Repository URL or accession numbers listed",
                "Access conditions described",
            ]
        },
        "11_Author_Contributions": {
            "done_when": [
                "All authors listed",
                "CRediT taxonomy used if journal requires it",
            ]
        },
        "12_Competing_Interests": {
            "done_when": [
                "Statement present even if none to declare",
            ]
        },
        "13_Supplementary_Material": {
            "done_when": [
                "All supplementary items referenced in main text",
                "Numbered sequentially",
            ]
        },
    }


def build_claude_md(project_name: str, journal: str, timestamp: str) -> str:
    return f"""# {project_name}

- **Journal target**: {journal or "Not set"}
- **Created**: {timestamp}

## Core rules

1. Never use em-dashes. Use commas, parentheses, or separate sentences.
2. Never use banned phrases listed in `writing_rules.yaml`.
3. Prefer active voice over passive voice.
4. Every claim in Results must trace to a data file or figure.
5. Every citation in the text must have a matching entry in 09_Bibliography.
6. When modifying a section, update `project_state.yaml` version, timestamp, and word count.
7. Before moving old files, place them in `OLD_Version_Files/` with a date prefix.
8. All figures: 300 DPI during drafting, 900 DPI PNG + SVG for final submission.
"""


RULE_NO_EM_DASHES = """---
paths:
  - "**/*.txt"
  - "**/*.md"
---

# No em-dashes

Never use em-dashes (---, or the Unicode character). Replace with:
- Commas
- Parentheses
- Separate sentences
"""

RULE_CITATION_INTEGRITY = """---
paths:
  - "02_Introduction/**"
  - "03_Methods/**"
  - "04_Results/**"
  - "05_Discussion/**"
---

# Citation integrity

- Every in-text citation must have a corresponding entry in `09_Bibliography/bibliography.txt`.
- Log any missing reference in `09_Bibliography/missing_papers.txt`.
- Never invent a citation. If unsure, add to `missing_papers.txt` and flag in `project_state.yaml` open_issues.
"""

RULE_WRITING_STYLE = """---
paths:
  - "**/*.txt"
---

# Writing style

- Prefer active voice.
- Do not use any phrase from the `banned_phrases` list in `writing_rules.yaml`.
- Keep hedging below 3% of total sentences.
- Template boilerplate must not exceed 5% of section content.
"""

RULE_OLD_VERSION_FILES = """---
paths:
  - "OLD_Version_Files/**"
---

# OLD_Version_Files is read-only archive

- Never edit files inside `OLD_Version_Files/`.
- Never read from `OLD_Version_Files/` to source content for current sections.
- This directory is an archive only. Use current section directories for all work.
"""


def create_project(project_path: str, journal: str, import_path: str | None) -> None:
    project_path = os.path.abspath(project_path)
    project_name = os.path.basename(project_path)
    timestamp = iso_now()

    os.makedirs(project_path, exist_ok=True)

    # Section directories and files
    for section in SECTIONS:
        section_dir = os.path.join(project_path, section)
        os.makedirs(section_dir, exist_ok=True)

        # Create sub-directories
        for subdir in SECTION_SUBDIRS.get(section, []):
            os.makedirs(os.path.join(section_dir, subdir), exist_ok=True)

        # Create files
        for fname in SECTION_FILES.get(section, []):
            fpath = os.path.join(section_dir, fname)
            if not os.path.exists(fpath):
                with open(fpath, "w") as f:
                    f.write("")

    # Top-level directories
    for d in ["scripts", "images", "OLD_Version_Files"]:
        os.makedirs(os.path.join(project_path, d), exist_ok=True)

    # data/data_manifest.yaml
    data_dir = os.path.join(project_path, "data")
    os.makedirs(data_dir, exist_ok=True)
    manifest = {"files": [], "last_updated": timestamp}
    with open(os.path.join(data_dir, "data_manifest.yaml"), "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)

    # .claude/rules/ with path-scoped rule files
    rules_dir = os.path.join(project_path, ".claude", "rules")
    os.makedirs(rules_dir, exist_ok=True)
    rules = {
        "no-em-dashes.md": RULE_NO_EM_DASHES,
        "citation-integrity.md": RULE_CITATION_INTEGRITY,
        "writing-style.md": RULE_WRITING_STYLE,
        "old-version-files-forbidden.md": RULE_OLD_VERSION_FILES,
    }
    for fname, content in rules.items():
        with open(os.path.join(rules_dir, fname), "w") as f:
            f.write(content.lstrip("\n"))

    # project_state.yaml
    state = build_project_state(journal, timestamp)
    with open(os.path.join(project_path, "project_state.yaml"), "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    # writing_rules.yaml
    with open(os.path.join(project_path, "writing_rules.yaml"), "w") as f:
        yaml.dump(build_writing_rules(), f, default_flow_style=False, sort_keys=False)

    # section_contracts.yaml
    with open(os.path.join(project_path, "section_contracts.yaml"), "w") as f:
        yaml.dump(build_section_contracts(), f, default_flow_style=False, sort_keys=False)

    # CLAUDE.md
    with open(os.path.join(project_path, "CLAUDE.md"), "w") as f:
        f.write(build_claude_md(project_name, journal, timestamp))

    # Handle --import
    if import_path:
        import_path = os.path.abspath(import_path)
        if not os.path.isdir(import_path):
            print(f"Error: import path does not exist or is not a directory: {import_path}")
            sys.exit(1)
        dest = os.path.join(project_path, "OLD_Version_Files")
        for item in os.listdir(import_path):
            src = os.path.join(import_path, item)
            dst = os.path.join(dest, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        print(f"Imported contents of {import_path} into OLD_Version_Files/")
        print("Run the orchestrator agent to extract sections from the imported files.")

    print(f"Project initialized at: {project_path}")
    print(f"Journal: {journal or 'Not set'}")
    print(f"Sections created: {len(SECTIONS)}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a standardized manuscript project directory."
    )
    parser.add_argument("project_path", help="Path where the project will be created")
    parser.add_argument("--journal", default="", help="Target journal name")
    parser.add_argument("--import", dest="import_path", default=None,
                        help="Path to existing manuscript to import into OLD_Version_Files/")
    args = parser.parse_args()
    create_project(args.project_path, args.journal, args.import_path)


if __name__ == "__main__":
    main()
