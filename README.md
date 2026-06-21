# CitationTool

Prototype for generating Zotero-active Word drafts with verified references and claim-support reports.

The primary workflow is Microsoft Word plus the Zotero Word plugin. LibreOffice is kept as an optional compatibility path for users who have LibreOffice and Zotero's LibreOffice plugin, and as an optional renderer/exporter for visual QA.

## Recommended command

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --verify metadata --refresh-word
```

This reads a JSON project spec, verifies DOI/PMID metadata through PubMed/Crossref, generates a Zotero-active Word draft, generates a placeholder fallback draft, writes RIS/CSL JSON import files, imports references into the currently selected Zotero target through Zotero's local connector, and asks Zotero's Mac Word integration endpoint to refresh the active draft.

For pure offline generation without touching Zotero or external metadata services:

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --no-zotero-import --verify none
```

For a deeper citation audit that checks visible abstract support:

```bash
python3 -m citationtool.cli verify examples/immunoglobulins_fibrosis_demo.json --depth abstract
```

`metadata` verification is deterministic and checks that DOI/PMID metadata resolves and matches the spec. `abstract` verification also fetches PubMed/Crossref abstract evidence, labels each claim as `supported`, `partially_supported`, `unsupported`, or `not_assessable`, and suggests safer wording when the visible abstract evidence is weak. This is still an abstract-level triage step; human or LLM review should confirm nuanced claims against the full article when needed.

To turn weak abstract-support suggestions into a separate reviewed draft:

```bash
python3 -m citationtool.cli apply-review examples/immunoglobulins_fibrosis_demo.json --build
```

`apply-review` runs abstract verification when needed, writes a `_reviewed` JSON spec, records every rewrite in `apply_review_report.md`, and can rebuild Zotero-active Word/RIS/CSL outputs from the revised spec. It rewrites only claims with candidate safer wording; claims that require full-text review are flagged but not silently changed.

For optional visual QA:

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --no-zotero-import --verify metadata --render auto
```

`--render auto` uses Quick Look on macOS when available, otherwise tries LibreOffice. Use `--render none` for pure generation, `--render quicklook` for macOS native preview output, or `--render libreoffice` for LibreOffice-based PDF/PNG export. Rendered files are written below `artifacts/.../rendered/` and are ignored by git.

## Main outputs

- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_active.docx`: Zotero-active Word draft with generated `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_placeholders.docx`: fallback draft with visible `[ZOTERO: ...]` placeholders.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.ris`: Zotero import file.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.csl.json`: CSL JSON reference file.
- `artifacts/immunoglobulins_fibrosis_cli/claim_support_report.md`: sentence-to-reference support map.
- `artifacts/immunoglobulins_fibrosis_cli/reference_verification.json`: machine-readable reference and abstract evidence audit.
- `artifacts/immunoglobulins_fibrosis_cli/verification_report.md`: human-readable verification summary.
- `artifacts/immunoglobulins_fibrosis_cli/abstract_support_review.md`: high-depth abstract support triage with safer-claim suggestions.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_reviewed.json`: reviewed project spec produced by `apply-review`.
- `artifacts/immunoglobulins_fibrosis_cli/apply_review_report.md`: audit log of applied and skipped support-review suggestions.
- `artifacts/immunoglobulins_fibrosis_cli/automation_summary.md`: latest run summary.

## Current validation status

Manual Word/Zotero testing confirmed that the generated active fields are editable by the Zotero Word plugin. The CLI also verifies that the generated `.docx` contains the expected Zotero citation fields and one bibliography field.

Reference verification has two levels: `metadata` checks DOI/PMID existence and bibliographic consistency through PubMed/Crossref; `abstract` adds automatic abstract-level support triage plus a review file for harness/LLM follow-up and safer rewrites. `apply-review` can then create a separate reviewed spec and regenerated Word draft from the safer wording candidates.

LibreOffice is not required for the Word-first workflow. If LibreOffice is installed, it can be used for visual export with `--render libreoffice`; dedicated automated Zotero-LibreOffice refresh should be added only after that integration endpoint has been verified against a real LibreOffice/Zotero setup.

## Compatibility demo

The original hardcoded demo runner is still available:

```bash
python3 tools/run_zotero_ready_demo.py --refresh-active-word
```

The reusable CLI is the path to use for new topics.

## Harness adapters

- `.opencode/skills/citationtool/SKILL.md`: OpenCode project-local skill.
- `.opencode/commands/citationtool.md`: OpenCode `/citationtool` command wrapper.
- `harnesses/codex/citationtool/SKILL.md`: repo-local Codex skill draft.
- `harnesses/codex/citationtool/references/project-spec.md`: JSON spec contract for agents.
- `harnesses/claude-code/citationtool.md`: Claude Code adapter prompt.
- `harnesses/opencode/citationtool.md`: OpenCode adapter notes.
- `examples/project_spec_template.json`: copyable starter spec for new topics.
