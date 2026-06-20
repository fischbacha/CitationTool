# Automation Summary

Placeholder Word draft: `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_draft.docx`
Experimental active-field Word draft: `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_active_field_experiment.docx`
RIS: `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_references.ris`
CSL JSON: `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_references.csl.json`
Claim report: `artifacts/immunoglobulins_fibrosis_demo/claim_support_report.md`

## Zotero

Zotero import was not requested.

## Remaining Word Step

The Word plugin step is still intentionally not faked. Open the draft, search each `[ZOTERO: ...]` placeholder, and use Zotero `Add/Edit Citation`. Then use `Add/Edit Bibliography` under the References heading.

## Experimental Active-Field Draft

The active-field experiment contains generated `ADDIN ZOTERO_ITEM` and `ADDIN ZOTERO_BIBL` Word fields with embedded CSL item data. Open it in Word and run Zotero `Refresh`; if Zotero can edit the citations and refresh the bibliography, this is the path toward full automation.

Field self-check: detected 4 citation fields and 1 bibliography field.

Opt-in refresh test: `python3 tools/run_zotero_ready_demo.py --refresh-active-word` asks Zotero's Mac Word integration endpoint to run `Refresh` on the experimental active-field draft.
