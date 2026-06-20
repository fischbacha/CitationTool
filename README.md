# CitationTool Zotero Demo

Minimal prototype for generating a Zotero-ready Word draft about immunoglobulins in fibrosis.

## One-command demo

```bash
python3 tools/run_zotero_ready_demo.py --refresh-active-word
```

This regenerates the demo files, imports the three references into the currently selected Zotero target through Zotero's local connector, and asks Zotero's Mac Word integration endpoint to refresh the experimental active-field draft.

## Main outputs

- `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_draft.docx`: conservative draft with visible `[ZOTERO: ...]` placeholders.
- `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_active_field_experiment.docx`: experimental draft with generated `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_references.ris`: Zotero import file.
- `artifacts/immunoglobulins_fibrosis_demo/claim_support_report.md`: sentence-to-reference support map.
- `artifacts/immunoglobulins_fibrosis_demo/automation_summary.md`: latest run summary.

## Current validation status

The runner verifies that the experimental `.docx` contains four Zotero citation fields and one bibliography field, and Zotero accepted a Word `Refresh` request for that document. The remaining validation is inside Microsoft Word: confirm that Zotero can open an inserted citation with `Add/Edit Citation` and refresh the bibliography.
