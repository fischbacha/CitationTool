# CitationTool

Prototype for generating Zotero-active Word drafts with verified references and claim-support reports.

The primary workflow is Microsoft Word plus the Zotero Word plugin. LibreOffice is kept as an optional compatibility path for users who have LibreOffice and Zotero's LibreOffice plugin, and as an optional renderer/exporter for visual QA.

## Recommended command

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --refresh-word
```

This reads a JSON project spec, generates a Zotero-active Word draft, generates a placeholder fallback draft, writes RIS/CSL JSON import files, imports references into the currently selected Zotero target through Zotero's local connector, and asks Zotero's Mac Word integration endpoint to refresh the active draft.

For offline generation without touching Zotero:

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --no-zotero-import
```

For optional visual QA:

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --no-zotero-import --render auto
```

`--render auto` uses Quick Look on macOS when available, otherwise tries LibreOffice. Use `--render none` for pure generation, `--render quicklook` for macOS native preview output, or `--render libreoffice` for LibreOffice-based PDF/PNG export. Rendered files are written below `artifacts/.../rendered/` and are ignored by git.

## Main outputs

- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_active.docx`: Zotero-active Word draft with generated `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_placeholders.docx`: fallback draft with visible `[ZOTERO: ...]` placeholders.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.ris`: Zotero import file.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.csl.json`: CSL JSON reference file.
- `artifacts/immunoglobulins_fibrosis_cli/claim_support_report.md`: sentence-to-reference support map.
- `artifacts/immunoglobulins_fibrosis_cli/automation_summary.md`: latest run summary.

## Current validation status

Manual Word/Zotero testing confirmed that the generated active fields are editable by the Zotero Word plugin. The CLI also verifies that the generated `.docx` contains the expected Zotero citation fields and one bibliography field.

LibreOffice is not required for the Word-first workflow. If LibreOffice is installed, it can be used for visual export with `--render libreoffice`; dedicated automated Zotero-LibreOffice refresh should be added only after that integration endpoint has been verified against a real LibreOffice/Zotero setup.

## Compatibility demo

The original hardcoded demo runner is still available:

```bash
python3 tools/run_zotero_ready_demo.py --refresh-active-word
```

The reusable CLI is the path to use for new topics.

## Harness adapters

- `harnesses/codex/citationtool/SKILL.md`: repo-local Codex skill draft.
- `harnesses/codex/citationtool/references/project-spec.md`: JSON spec contract for agents.
- `harnesses/claude-code/citationtool.md`: Claude Code adapter prompt.
- `examples/project_spec_template.json`: copyable starter spec for new topics.
