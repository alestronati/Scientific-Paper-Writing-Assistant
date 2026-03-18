# Scientific Paper Writer - Design Specification

**Date:** 2026-03-18
**Status:** Approved by user
**Skill name:** `scientific-paper-writer` (invoked as `/paper`)
**Location:** `~/.claude/skills/scientific-paper-writer/`

## Objective

A skill + agent team that helps write high-impact scientific papers by:
1. Organizing research data, manuscripts, and references into an AI-friendly standardized structure
2. Iteratively improving each section through specialized agents with full claim verification
3. Producing the final manuscript as LaTeX or .docx with all figures, tables, captions, and bibliography

## Architecture: Single Orchestrator Skill + 11 Agents

One main skill (`/paper`) acts as the entry point and dispatcher. It routes to 11 specialized agents. Each agent has access to relevant `/scientific-skills`, `/gsd`, `/systematic-review-agent`, `/chain-of-verification`, and NotebookLM (on demand).

This mirrors the proven `financial-advisor` pattern: one command to invoke, clean dispatch table, agents work in parallel where possible.

---

## Project Directory Structure

When `/paper init` is called, the orchestrator creates this standardized structure:

```
<project-name>/
├── 00_Title_Keywords/
│   ├── title_v1.0.txt
│   └── keywords_v1.0.txt
├── 01_Abstract/
│   └── abstract_v1.0.txt
├── 02_Introduction/
│   └── introduction_v1.0.txt
├── 03_Methods/
│   └── methods_v1.0.txt
├── 04_Results/
│   └── results_v1.0.txt
├── 05_Discussion/
│   └── discussion_v1.0.txt
├── 06_Conclusions/
│   └── conclusions_v1.0.txt
├── 07_Figures/
│   ├── figures/                   # PNG/SVG files
│   ├── figure_captions.txt        # All figure captions, journal-style
│   └── figures_v1.0.txt           # Figure descriptions/legends
├── 08_Tables/
│   ├── tables/                    # CSV/XLSX table files
│   ├── table_captions.txt         # All table captions, journal-style
│   └── tables_v1.0.txt            # Table descriptions/legends
├── 09_Bibliography/
│   ├── cited_papers/              # PDFs named AuthorYear.pdf
│   ├── bibliography.txt           # Nature format default, adapts to journal
│   └── missing_papers.txt         # Papers still needed
├── 10_Data_Availability/
│   └── data_availability_v1.0.txt
├── 11_Author_Contributions/
│   └── author_contributions_v1.0.txt
├── 12_Competing_Interests/
│   └── competing_interests_v1.0.txt
├── 13_Supplementary_Material/
│   └── supplementary_v1.0.txt
├── scripts/                       # Analysis scripts (.py, .R)
├── data/
│   └── data_manifest.yaml         # Source file hashes, extracted values, linked Results paragraphs
├── images/                        # Source images (ECG, photos, etc.)
├── OLD_Version_Files/             # ARCHIVE ONLY - agents never read from here
├── .claude/
│   └── rules/                     # Path-scoped writing rules
│       ├── no-em-dashes.md        # Scoped to **/*.txt
│       ├── citation-integrity.md  # Scoped to 09_Bibliography/**
│       ├── writing-style.md       # Scoped to 0*_*/*.txt
│       └── old-version-files-forbidden.md  # Scoped to OLD_Version_Files/**
├── journal_guidelines.md          # Fetched + cached per journal
├── project_state.yaml             # Structured project state (see schema below)
├── evolution_log.jsonl            # Self-learning from past runs (30-day decay)
├── section_contracts.yaml         # Definition of Done per section
├── writing_rules.yaml             # Anti-LLM rules, externalized per section type
└── CLAUDE.md                      # Project-specific instructions
```

### Key Rules

- **Custom sections:** User can add any section at init (e.g., `04b_PK_Model/`). Gets next available number or decimal insert.
- **Version bumping:** Every agent edit creates a new version (`v1.0` -> `v1.1`). Major revisions (post-review restructuring) bump to `v2.0`.
- **OLD_Version_Files/:** Hard-coded in every agent system prompt: "Never read from, search in, or reference OLD_Version_Files/. This folder contains archived originals and outdated data."
- **Citation format:** Nature format by default for all first versions. Auto-adapts when `journal_guidelines.md` is created/selected. The `bibliography-manager` reads citation format rules from guidelines and reformats accordingly.
- **Figure/table captions:** `figure_captions.txt` and `table_captions.txt` follow the same writing guidelines as manuscript text (no LLM language, no em dashes, journal-specific style).
- **Data provenance:** `data/data_manifest.yaml` tracks every source file with SHA-256 hash, extracted values, and which Results paragraph uses them. When a data file changes, the orchestrator flags stale Results sentences.

### project_state.yaml Schema

```yaml
journal: "npj Microgravity"
sections:
  00_Title_Keywords:
    current_version: "v1.2"
    last_agent: "section-writer"
    last_modified: "2026-03-18T14:30:00"
    verification_status: "pending"  # passed | failed | pending | not_required
    word_count: 18
  01_Abstract:
    current_version: "v1.1"
    last_agent: "section-writer"
    last_modified: "2026-03-18T15:00:00"
    verification_status: "passed"
    word_count: 245
  # ... all sections follow same schema
open_issues:
  - id: 1
    section: "09_Bibliography"
    description: "3 PDFs still missing"
    severity: "medium"
    created: "2026-03-18T12:00:00"
linked_notebooks: []  # NotebookLM notebook IDs
data_files_stale: []  # Sections with changed source data
```

---

## Sub-commands

| Command | Action |
|---------|--------|
| `/paper init <path> [--journal <name>] [--import <source-dir>]` | Create project or import existing manuscript |
| `/paper write <section> [--from-notes\|--from-data]` | Draft or revise a section (hybrid mode) |
| `/paper verify [<section>\|all]` | Full CoVe + 4-layer citation verification |
| `/paper bibliography [add\|verify\|format\|missing]` | Manage references |
| `/paper figures [check\|caption\|generate]` | Validate figures, write captions, generate from data |
| `/paper tables [check\|caption]` | Validate tables, write captions |
| `/paper review` | Pre-submission audit |
| `/paper status` | Project state overview |
| `/paper guidelines <journal-name>` | Fetch + cache journal guidelines |
| `/paper notebook [connect\|query]` | NotebookLM integration (on-demand) |
| `/paper export [--format latex\|docx] [--template <name>] [--cover-letter]` | Final manuscript assembly (optionally with cover letter) |
| `/paper diff <section> [v1.2] [v1.4]` | Compare two versions of a section, show changes |
| `/paper respond-to-reviewers <comments-file>` | Ingest reviewer comments, map to sections, produce point-by-point response, bump to v2.0 |
| `/paper consistency-check` | Cross-section coherence: Abstract numbers match Results, all figures referenced, Discussion cites real findings |

### Dispatch Flow

`/paper` skill receives sub-command -> reads `project_state.yaml` for context -> dispatches to the right agent(s). After every write cycle, the orchestrator calls `scripts/update_state.py` (deterministic, no LLM) to update `project_state.yaml` with new version numbers, word counts, and timestamps.

---

## Agent Team (11 Agents)

### 1. manuscript-orchestrator
- **Model:** opus
- **Role:** Project initialization, task routing, state management, evolution store
- **Tools:** All tools + `/gsd:*`
- **Integrations:** Prompt manager (YAML rule overrides), evolution log (self-learning from past manuscript runs)

### 2. section-writer
- **Model:** opus
- **Role:** Drafts/revises section text in anti-LLM style. Adapts to journal tone. Handles both "from notes" (user provides bullet points) and "from scratch" modes.
- **Tools:** Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep
- **Integrations:** `/scientific-skills:scientific-writing`, `writing_rules.yaml`, template content quality gate (13 regex patterns from AutoResearchClaw)
- **Quality gate:** Every output passes template content detector. Reject if >5% placeholder text.

### 3. data-extractor
- **Model:** sonnet
- **Role:** Reads CSVs, parses Python/R scripts, extracts statistical results from plots and analysis outputs
- **Tools:** Read, Bash, Glob, Grep
- **Integrations:** `/scientific-skills:statistical-analysis`, `/scientific-skills:exploratory-data-analysis`, hardware-aware script execution (GPU/MPS/CPU detection from AutoResearchClaw)

### 4. statistical-methods-writer
- **Model:** opus
- **Role:** Writes Methods statistics sections so anyone can reproduce the analysis. Includes all test details, software versions, parameters, sample sizes, correction methods.
- **Tools:** Read, Write, Edit, Bash, Glob, Grep
- **Integrations:** `/clinical-statistics-expert`, `/scientific-skills:statistical-analysis`

### 5. results-composer
- **Model:** opus
- **Role:** Transforms extracted data into high-impact journal prose for Results section. Uses data-extractor output.
- **Tools:** Read, Write, Edit, Glob, Grep
- **Integrations:** `/scientific-skills:scientific-writing`, template content quality gate

### 6. bibliography-manager
- **Model:** sonnet
- **Role:** Fetches PDFs (named AuthorYear.pdf), formats references (Nature default, adapts to journal), tracks missing papers, discovers related literature
- **Tools:** Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep
- **Integrations:** PubMed (MCP), OpenAlex + Semantic Scholar + arXiv APIs (from AutoResearchClaw `literature/search.py`), 4-layer citation verification (from AutoResearchClaw `literature/verify.py`), `/fetch-papers`, `/systematic-review-agent`
- **API rate limits:** OpenAlex 10K/day, Semantic Scholar 1K/5min, arXiv 1/3s

### 7. claim-verifier
- **Model:** opus
- **Role:** Full Chain of Verification on every factual statement against cited PDFs and PubMed. Read-only adversarial agent. NEVER modifies manuscript files.
- **Tools:** Read, Bash, Glob, Grep, WebSearch, WebFetch
- **disallowedTools:** Edit, Write (adversarial separation - can only READ and REPORT, never fix)
- **Integrations:** `/chain-of-verification`, `/systematic-review-agent`, PubMed MCP, PDF reading, hallucination detection logic (from AutoResearchClaw `literature/verify.py`)
- **Output:** CoVe verification report returned as agent result string. The orchestrator writes it to `VERIFICATION_REPORT.md`. Report includes claim-by-claim results (SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED / UNVERIFIABLE) and a list of hallucinated citations flagged for removal.
- **Hallucination workflow:** Verifier REPORTS hallucinated citations. User reviews the report. Then `section-writer` removes them on user approval. The verifier never writes to files.

### 8. figure-table-curator
- **Model:** sonnet
- **Role:** Validates figures match data, generates/validates captions per journal specs, figure generation pipeline
- **Tools:** Read, Write, Edit, Bash, Glob, Grep
- **Integrations:** `/scientific-skills:scientific-visualization`, `/scientific-skills:matplotlib`, FigureAgent 5-sub-agent pipeline from AutoResearchClaw (planner -> codegen -> renderer -> critic -> integrator)
- **DPI rule:** 300 DPI during development, 900 DPI PNG + SVG only when final (per user preference)

### 9. journal-compliance-checker
- **Model:** sonnet
- **Role:** Validates word counts, section structure, reference format, figure specs (DPI, format, color mode) against `journal_guidelines.md`. Checks section contracts (Definition of Done per section). Also checks Methods reproducibility: flags missing software versions, ambiguous test choices, missing sample size justifications.
- **Tools:** Read, Bash, Glob, Grep
- **disallowedTools:** Edit, Write (read-only checker)
- **Integrations:** `journal_guidelines.md`, `section_contracts.yaml`, `/scientific-skills:venue-templates`
- **Output:** Compliance report returned as agent result string. The orchestrator writes it to `COMPLIANCE_REPORT.md`. All read-only agents communicate findings via their return value, never by writing files directly.

### 10. submission-reviewer
- **Model:** opus
- **Role:** Final pre-submission audit. Dispatches all verification agents in parallel. Produces SUBMISSION_REVIEW_REPORT.md.
- **Tools:** All tools + Agent dispatch
- **Integrations:** Dispatches `claim-verifier`, `journal-compliance-checker`, `bibliography-manager verify` in parallel. Optional novelty audit (from AutoResearchClaw `literature/novelty.py`). Multi-agent peer review pattern.
- **Output:** SUBMISSION_REVIEW_REPORT.md with checklist, word counts, reference format compliance, missing sections, verification status

### 11. manuscript-assembler
- **Model:** sonnet
- **Role:** Compiles final LaTeX or .docx from all sections, figures, tables, captions, bibliography
- **Tools:** Read, Write, Edit, Bash, Glob, Grep
- **Integrations:** LaTeX conference/journal templates (from AutoResearchClaw `templates/styles/`), `/scientific-skills:docx`, `/scientific-skills:venue-templates`, cross-reference generation

---

## Writing Modes

### Hybrid Writing (User Choice Per Section)

- **You draft, agents refine:** You write v1.0, agents review for LLM-detectable language, verify claims, check statistical reproducibility, produce v1.1
- **Agents draft from your notes:** You provide bullet points/data, section-writer or results-composer produces v1.0
- **Data-driven drafting:** For Results/Methods, agents extract from CSVs, scripts, and plots via data-extractor, then results-composer or statistical-methods-writer produces the section

### Import Workflow (Existing Manuscript)

```
/paper init ~/my-project --import ~/existing-manuscript/
```
1. `manuscript-orchestrator` scans source directory
2. Dispatches agents to extract sections from .docx/.txt/.pdf
3. Creates standardized folder structure (strict normalization)
4. Originals copied to `OLD_Version_Files/`
5. Generates `project_state.md` with current status

### New Manuscript Workflow

```
/paper init ~/my-project --journal "npj Microgravity"
```
1. Creates empty folder structure
2. Fetches + caches journal guidelines
3. Generates section contracts from guidelines
4. User starts adding data, notes, and drafts

---

## Quality Gates

Every agent output passes through these gates:

### 1. Template Content Detector (from AutoResearchClaw `quality.py`)
13 regex patterns catching `[INSERT...]`, `[TODO:...]`, `[PLACEHOLDER:...]`, future tense placeholders, lorem ipsum. Reject if template_ratio > 5%.

### 2. Anti-LLM Language Check
Enforced via `writing_rules.yaml` and `.claude/rules/writing-style.md`:
- No em dashes
- No "delve into", "it's worth noting", "in conclusion", "notably"
- No recognizable LLM writing patterns
- Active voice preferred
- Specific numbers over vague quantifiers
- **Hedging inflation detection:** Frequency-based check for excessive "may," "might," "could potentially," "it is possible that" against typical academic writing baselines. Subtler LLM fingerprint than banned phrases.

### 3. Section Contract DoD (from AutoResearchClaw `contracts.py`)
Per-section acceptance criteria defined in `section_contracts.yaml`:
- Methods: All statistical test details stated, software versions included, reproducible by third party
- Results: Numbers match data files, figures referenced correctly
- Bibliography: All citations verified, no hallucinated references, format matches journal

### 4. Caption Consistency
Figure/table captions follow same writing rules as manuscript text. Checked by `journal-compliance-checker`.

### 5. PostToolUse Hook (Auto-Enforcement)
Configured in project `.claude/settings.json`:
- Every time an agent edits a `.txt` section file: auto-run template content detector
- Every time bibliography.txt is modified: auto-run citation format check

---

## Citation Verification (Defense in Depth)

### Layer 1: Chain of Verification (CoVe)
Every factual statement verified against cited PDFs and PubMed by `claim-verifier` (read-only adversarial agent). Results: SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED / UNVERIFIABLE.

### Layer 2: 5-Layer Citation Integrity (from AutoResearchClaw `verify.py` + retraction check)
1. arXiv ID validation (if present)
2. CrossRef/DataCite DOI lookup
3. Semantic Scholar title/year match (Jaccard similarity >= 0.80 = VERIFIED)
4. LLM relevance scoring against paper content
5. **Retraction check:** CrossRef API exposes retraction status in metadata. Any retracted citation is flagged as CRITICAL and must be removed or replaced before submission.

### Layer 3: Hallucination Reporting and Removal
The `claim-verifier` (read-only) REPORTS hallucinated citations in its verification report. The user reviews the report. Then `section-writer` removes flagged citations on user approval using `annotate_paper_hallucinations()` logic from AutoResearchClaw. The verifier never modifies files directly.

### Layer 4: Citation Quality Analysis
The `bibliography-manager` flags:
- **Citation clustering:** Too many references from the same research group
- **Narrow year range:** Over-reliance on a single decade
- **Preprint over-reliance:** Excessive non-peer-reviewed sources
- Reviewers notice these patterns; flagging them preemptively prevents desk rejection comments.

### Layer 5: Path-Scoped Rules
`.claude/rules/citation-integrity.md` scoped to `09_Bibliography/**` enforces: never generate citations from memory, only cite papers from bibliography.txt or verified via DOI lookup.

---

## Self-Learning (Evolution Store)

From AutoResearchClaw `evolution.py`:

- `evolution_log.jsonl` stores lessons from each writing session
- Categories: WRITING (template content, passive voice), LITERATURE (hallucinations, formatting), ANALYSIS (weak methods), PIPELINE (workflow issues), REVIEWER (patterns from reviewer responses -- learns which objections manuscripts tend to attract and preemptively addresses them in future drafts)
- 30-day exponential time decay on lesson relevance (90-day max age)
- Lessons injected into agent prompts before each revision pass via `build_overlay()`
- Each manuscript run improves the next

---

## Journal Guidelines

### Fetching
`/paper guidelines <journal-name>` uses WebSearch/WebFetch to find official author guidelines, extracts formatting rules, and generates `journal_guidelines.md`.

### Caching
Stored in `~/.claude/skills/scientific-paper-writer/references/journal-templates/<journal-name>.md` for reuse across manuscripts.

### Impact
When guidelines are set, `bibliography-manager` auto-reformats citations from Nature default to journal-specific format. `journal-compliance-checker` validates against all journal requirements.

---

## External Integrations

### NotebookLM (On-Demand)
- No automatic notebook creation
- User tells orchestrator which notebook(s) to use via `/paper notebook connect`
- Any agent can query connected notebooks via `mcp__notebooklm__ask_question`

### Existing Skills (Delegated To)
| Skill | Used By |
|-------|---------|
| `/scientific-skills:scientific-writing` | section-writer, results-composer |
| `/scientific-skills:statistical-analysis` | data-extractor, statistical-methods-writer |
| `/scientific-skills:scientific-visualization` | figure-table-curator |
| `/scientific-skills:citation-management` | bibliography-manager |
| `/scientific-skills:peer-review` | submission-reviewer |
| `/scientific-skills:venue-templates` | journal-compliance-checker, manuscript-assembler |
| `/scientific-skills:docx` | manuscript-assembler |
| `/clinical-statistics-expert` | statistical-methods-writer, claim-verifier |
| `/chain-of-verification` | claim-verifier |
| `/systematic-review-agent` | section-writer, claim-verifier, bibliography-manager, submission-reviewer |
| `/fetch-papers` | bibliography-manager |

### AutoResearchClaw Components (Extracted)
| Component | Source File | Used By |
|-----------|------------|---------|
| Template content detector | `quality.py` | All writing agents |
| Citation verification | `literature/verify.py` | bibliography-manager, claim-verifier |
| Hallucination detection + removal | `literature/verify.py` | claim-verifier (detection only), section-writer (removal on user approval) |
| Writing rules | `writing_guide.py` | section-writer (as YAML) |
| Evolution store | `evolution.py` | manuscript-orchestrator |
| Prompt manager | `prompts.py` | All agents (YAML overrides) |
| Section contracts | `pipeline/contracts.py` | journal-compliance-checker |
| FigureAgent pipeline | `agents/figure_agent/` | figure-table-curator |
| Novelty detection | `literature/novelty.py` | submission-reviewer (optional) |
| Literature search APIs | `literature/search.py` | bibliography-manager |
| LaTeX templates | `templates/styles/` | manuscript-assembler |

---

## File Organization (Skill Directory)

```
~/.claude/skills/scientific-paper-writer/
├── SKILL.md                           # Main skill definition + dispatch table
├── references/
│   ├── dispatch-table.md              # Sub-command routing logic
│   ├── writing-rules-default.yaml     # Default anti-LLM rules per section
│   ├── section-contracts-default.yaml # Default DoD per section type
│   ├── output-template.md             # Report templates
│   └── journal-templates/             # Cached journal guidelines
│       ├── nature.md
│       ├── npj-microgravity.md
│       └── ...
├── scripts/
│   ├── quality_gate.py                # Template content detector (from AutoResearchClaw)
│   ├── verify_citations.py            # 4-layer citation verification (from AutoResearchClaw)
│   ├── evolution_store.py             # Self-learning store (from AutoResearchClaw)
│   ├── literature_search.py           # Multi-source search (from AutoResearchClaw)
│   ├── project_init.py               # Directory structure creation + import logic
│   └── update_state.py               # Deterministic state updater (no LLM) - versions, word counts, timestamps
└── agents/                            # Agent definition references (actual .md in ~/.claude/agents/)
```

Agent definitions live in `~/.claude/agents/`:
- `manuscript-orchestrator.md`
- `section-writer.md`
- `data-extractor.md`
- `statistical-methods-writer.md`
- `results-composer.md`
- `bibliography-manager.md`
- `claim-verifier.md`
- `figure-table-curator.md`
- `journal-compliance-checker.md`
- `submission-reviewer.md`
- `manuscript-assembler.md`

---

## Reviewer Response Workflow

`/paper respond-to-reviewers <comments-file>` triggers a structured revision cycle:

1. **Ingest:** Orchestrator parses reviewer comments (txt, docx, or PDF) and extracts individual points
2. **Map:** Each reviewer point is mapped to the relevant section(s) using keyword matching and content analysis
3. **Response draft:** `section-writer` produces a point-by-point response document with:
   - Original reviewer comment (quoted)
   - Response explaining what was changed (or why it was not changed)
   - Reference to the specific section and version where the change was made
4. **Section revision:** Flagged sections are revised by the appropriate agent. All revisions bump to v2.0 (major revision)
5. **Evolution logging:** Reviewer patterns are logged to `evolution_log.jsonl` under the REVIEWER category for future preemptive addressing
6. **Output:** `REVIEWER_RESPONSE.md` with the complete point-by-point response, ready for journal resubmission

---

## Consistency Check

`/paper consistency-check` runs cross-section coherence validation:

- **Abstract vs Results:** Do all numbers, percentages, and p-values in the Abstract match the Results section?
- **Figure references:** Are all figures in `07_Figures/` referenced in the Results or Methods? Are there references to figures that do not exist?
- **Table references:** Same check for tables in `08_Tables/`
- **Discussion vs Results:** Does the Discussion reference findings that are actually present in Results?
- **Bibliography completeness:** Are all in-text citations present in `bibliography.txt`? Are there bibliography entries not cited in the text?
- **Data provenance:** Do extracted values in Results match the current `data_manifest.yaml` hashes? Flag stale data.

Output: `CONSISTENCY_REPORT.md` with pass/fail per check and specific line references for failures.

---

## Design Decisions

1. **Skill + Agent Team over Plugin:** Plugins are for MCP servers (persistent background processes). This is orchestration + writing, matching the financial-advisor pattern.

2. **Standard sections with custom additions over flexible templates:** IMRaD + standard extras (Data Availability, Author Contributions, etc.) are universal. Custom sections added per project.

3. **Nature citation format as default:** Universal starting point. Auto-adapts when journal guidelines are set.

4. **Separate Figures and Tables folders:** Each with its own `*_captions.txt` for independent caption management.

5. **Adversarial claim-verifier (read-only):** `disallowedTools: [Edit, Write]` forces separation of powers. Verifier reports, writer fixes.

6. **Path-scoped rules over global CLAUDE.md:** `.claude/rules/` files activate precisely when relevant files are edited. More reliable enforcement.

7. **PostToolUse hooks for auto-verification:** System-level enforcement. No agent needs to remember to verify.

8. **Self-learning evolution store:** 30-day decay prevents stale lessons. Each manuscript improves the next.

9. **Strict import normalization:** Existing manuscripts get reorganized into standard structure. Originals preserved in `OLD_Version_Files/` (off-limits to all agents).

10. **Hybrid writing mode:** User drafts where they have domain expertise (Methods), agents draft where literature synthesis is heavy (Introduction/Discussion), agents extract from data for Results.

11. **Read-only agents report via return value:** `claim-verifier` and `journal-compliance-checker` have `disallowedTools: [Edit, Write]`. They return findings as their agent result string. The orchestrator writes report files. This enforces adversarial separation cleanly.

12. **State updates via deterministic script, not an agent:** `update_state.py` updates `project_state.yaml` after every write cycle. No LLM needed to update a YAML file. Keeps the orchestrator focused on routing.

13. **Retraction checking as 5th citation layer:** CrossRef API exposes retraction status. A retracted citation in a submitted paper is a serious problem. Cheap to check, high value.

14. **Data provenance via `data_manifest.yaml`:** SHA-256 hashes of source files linked to Results paragraphs. When data changes, stale sentences are immediately flagged without re-running scripts.

15. **Reviewer response as first-class workflow:** `/paper respond-to-reviewers` is a structured revision cycle, not an afterthought. Reviewer patterns feed the evolution store for preemptive improvement.
