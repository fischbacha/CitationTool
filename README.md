# CitationTool

Prototype for generating Zotero-active Word drafts with verified references and claim-support reports.

## Recommended command

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --refresh-word
```

This reads a JSON project spec, generates a Zotero-active Word draft, generates a placeholder fallback draft, writes RIS/CSL JSON import files, imports references into the currently selected Zotero target through Zotero's local connector, and asks Zotero's Mac Word integration endpoint to refresh the active draft.

For offline generation without touching Zotero:

```bash
python3 -m citationtool.cli run examples/immunoglobulins_fibrosis_demo.json --no-zotero-import
```

## Main outputs

- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_active.docx`: Zotero-active Word draft with generated `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_zotero_placeholders.docx`: fallback draft with visible `[ZOTERO: ...]` placeholders.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.ris`: Zotero import file.
- `artifacts/immunoglobulins_fibrosis_cli/immunoglobulins_fibrosis_demo_references.csl.json`: CSL JSON reference file.
- `artifacts/immunoglobulins_fibrosis_cli/claim_support_report.md`: sentence-to-reference support map.
- `artifacts/immunoglobulins_fibrosis_cli/automation_summary.md`: latest run summary.

## Current validation status

Manual Word/Zotero testing confirmed that the generated active fields are editable by the Zotero Word plugin. The CLI also verifies that the generated `.docx` contains four Zotero citation fields and one bibliography field.

## Compatibility demo

The original hardcoded demo runner is still available:

```bash
python3 tools/run_zotero_ready_demo.py --refresh-active-word
```

The reusable CLI is the path to use for new topics.
