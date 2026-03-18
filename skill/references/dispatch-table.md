# Dispatch Table

## Command -> Agent Mapping

| Sub-command | Primary Agent | Parallel Agents |
|------------|--------------|-----------------|
| write abstract | section-writer | - |
| write introduction | section-writer | - |
| write methods | statistical-methods-writer | - |
| write results --from-data | data-extractor, then results-composer | - |
| write results | results-composer | - |
| write discussion | section-writer | - |
| write conclusions | section-writer | - |
| verify <section> | claim-verifier | bibliography-manager verify |
| verify all | claim-verifier | bibliography-manager verify, journal-compliance-checker |
| bibliography * | bibliography-manager | - |
| figures * | figure-table-curator | - |
| tables * | figure-table-curator | - |
| review | submission-reviewer | claim-verifier, journal-compliance-checker, bibliography-manager |
| respond-to-reviewers | manuscript-orchestrator | section-writer (per section) |
| consistency-check | journal-compliance-checker | - |
| export | manuscript-assembler | - |

## Section Name Resolution

- "abstract" -> 01_Abstract
- "intro" or "introduction" -> 02_Introduction
- "methods" -> 03_Methods
- "results" -> 04_Results
- "discussion" -> 05_Discussion
- "conclusions" -> 06_Conclusions
- "figures" -> 07_Figures
- "tables" -> 08_Tables
- "bibliography" or "refs" -> 09_Bibliography
- "title" or "keywords" -> 00_Title_Keywords
