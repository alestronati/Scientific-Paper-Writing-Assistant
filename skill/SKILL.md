---
name: scientific-paper-writer
description: "Use when the user asks to write, revise, or manage a scientific manuscript. Handles /paper commands for drafting sections, managing bibliography, generating figures/tables, responding to reviewers, and exporting publication-ready documents. Orchestrates 11 specialized writing agents."
argument-hint: "init | write <section> | verify | bibliography | figures | tables | review | status | guidelines | notebook | export | diff | respond-to-reviewers | consistency-check"
triggers:
  - paper
  - manuscript
  - write section
  - bibliography
  - respond to reviewers
  - scientific writing
  - figures
  - tables
  - export manuscript
---

# Scientific Paper Writer

## Sub-commands

| Command | Description | Routing |
|---------|-------------|---------|
| `init` | Initialize a new manuscript project (creates `project_state.yaml`, directory scaffold) | agent |
| `write <section>` | Draft or revise a specific section (introduction, methods, results, discussion, abstract, etc.) | agent |
| `verify` | Run claim verification and fact-checking across the manuscript | agent |
| `bibliography` | Manage references: add, format, deduplicate, verify DOIs | agent |
| `figures` | Generate, refine, or caption figures | agent |
| `tables` | Generate, format, or caption tables | agent |
| `review` | Internal peer-review simulation -- structural, logical, and stylistic audit | agent |
| `status` | Show manuscript progress, word counts, completeness per section | script |
| `guidelines` | Display or set target journal formatting rules | agent |
| `notebook` | Sync with NotebookLM sources for literature grounding | agent |
| `export` | Export manuscript to DOCX, LaTeX, or PDF via Pandoc | agent |
| `diff` | Show changes since last committed draft | script |
| `respond-to-reviewers` | Draft point-by-point reviewer response letter | agent |
| `consistency-check` | Cross-check terminology, abbreviations, numbering, and internal references | agent |

## Dispatch Logic

Parse `$ARGUMENTS` to extract the sub-command (first token).

### Project detection
Before any command except `init`, look for `project_state.yaml` in the working directory or its parents. If not found, prompt the user to run `/paper init` first.

### Deterministic commands (no agent needed)
- **status**: Run `python3 ~/.claude/skills/scientific-paper-writer/scripts/update_state.py --display <project-root>` and print a summary table.
- **diff <section> [v1.x] [v1.y]**: Find the two version files in the section folder, run `diff` between them. If only one version given, diff against previous. If none, diff the two most recent.

### Agent-routed commands
All other sub-commands dispatch to the `manuscript-orchestrator` agent:
```
SendMessage -> manuscript-orchestrator
  payload: { command: "<sub-command>", args: "<remaining tokens>", project_root: "<detected root>" }
```
The orchestrator then delegates to the appropriate specialist agent (e.g., `section-writer`, `bibliography-manager`, `figure-agent`, `reviewer-response-agent`).

## Writing Rules (apply to ALL agents)

These rules are non-negotiable and override any agent-specific defaults.

### Style
- Never use em dashes (--). Use commas, semicolons, colons, or parentheses instead.
- Never use these LLM-tell phrases: "delve", "notably", "importantly", "it is worth noting", "interestingly", "in the context of", "a testament to", "the landscape of", "shed light on", "pave the way", "a nuanced understanding", "multifaceted".
- Prefer active voice. Use passive only when the actor is genuinely irrelevant.
- Keep sentences under 35 words where possible.

### Rigor
- Every factual claim must be verifiable. Use `/chain-of-verification` before asserting any quantitative result or mechanistic claim.
- 5-layer citation verification: (1) DOI resolves, (2) authors match, (3) year matches, (4) journal matches, (5) claim actually appears in cited source.
- Methods sections must contain enough detail for full reproducibility: reagent catalog numbers, software versions, statistical tests with exact parameters.

### Formatting defaults
- Citation format: Nature style (superscript numbered) unless the user specifies otherwise via `guidelines`.
- Figure DPI: 300 during drafting; 900 DPI PNG + SVG only on final export.

### Safety
- Never read or reference files inside any `OLD_Version_Files/` directory.
- Never fabricate references. If a citation cannot be verified, flag it with `[UNVERIFIED]`.

## Reference Files

- @references/dispatch-table.md -- sub-command to agent routing with section name resolution
- @references/writing-rules-default.yaml -- default anti-LLM rules per section type
- @references/section-contracts-default.yaml -- Definition of Done per section
