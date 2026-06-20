---
name: citationtool
description: Generate Zotero-active Word drafts from LLM-written biomedical or grant/paper introduction text, with verified references, RIS/CSL files, claim-support reports, and Zotero Word refresh validation using the local CitationTool CLI.
---

# CitationTool

Use this skill when the user wants a Word draft with Zotero-editable citations, a Zotero import library, or a claim-by-claim citation support report.

## Core Rule

Do not invent references. Write claims first, then attach only verified sources with DOI/PMID metadata and an explicit claim-support mapping.

## Workflow

1. Draft concise introduction text and split it into citation-bearing paragraph chunks.
2. Build or update a CitationTool JSON project spec. For the required shape, read `references/project-spec.md`.
3. Run the CLI from the repo root:

```bash
python3 -m citationtool.cli run <spec.json> --no-zotero-import
```

4. Inspect the generated active DOCX:

```bash
python3 -m citationtool.cli inspect <active.docx>
unzip -t <active.docx>
```

5. Visually render the active DOCX if the environment supports it. If LibreOffice fails, use a platform renderer such as Quick Look and state the fallback.
6. When the user wants live Zotero/Word handoff, run:

```bash
python3 -m citationtool.cli run <spec.json> --refresh-word
```

This imports references through Zotero's local connector unless `--no-zotero-import` is passed, then asks Zotero's Mac Word integration endpoint to refresh the active Word draft.

## Expected Outputs

- Zotero-active `.docx` with `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- Placeholder fallback `.docx`.
- RIS and CSL JSON reference files.
- `claim_support_report.md`.
- `automation_summary.md`.

## Validation Bar

Before calling the result done, confirm:

- active DOCX contains the expected number of `ADDIN ZOTERO_ITEM` fields and one `ADDIN ZOTERO_BIBL` field
- DOCX archive integrity passes with `unzip -t`
- claim report maps every substantive claim to a citation key
- reference metadata includes DOI or PMID where available
- Word/Zotero refresh succeeds or any blocker is reported clearly
