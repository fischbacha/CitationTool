---
name: citationtool
description: Generate Zotero-active Word drafts from LLM-written biomedical or grant/paper introduction text. Use when the user asks CitationTool/Citation Tool to draft a Word introduction with Zotero-editable citations, build a Zotero import library, verify DOI/PMID metadata, run abstract-level citation support checks, or produce claim-support reports using the local CitationTool CLI.
---

# CitationTool

Microsoft Word plus the Zotero Word plugin is the primary validation path. LibreOffice is optional for users who have Zotero's LibreOffice plugin or want LibreOffice-based visual export.

## Core Rule

Do not invent references. Write claims first, then attach only verified sources with DOI/PMID metadata and an explicit claim-support mapping.

## Repo Root

Run all CLI commands from the CitationTool repo root. Prefer the current workspace if it contains `citationtool/cli.py`; otherwise use `$CITATIONTOOL_HOME`; otherwise try `/Users/afischbach/Documents/CitationTool`. If no repo is found, ask the user for the path.

## Workflow

1. Search PubMed/Crossref for a small, defensible reference set with DOI/PMID metadata. Prefer 3-5 references for a demo draft.
2. Draft concise introduction text with narrow citation-bearing claims.
3. Build or update a CitationTool JSON project spec. For the required shape, read `references/project-spec.md`.
4. Build the draft with deterministic metadata verification:

```bash
python3 -m citationtool.cli run <spec.json> --no-zotero-import --verify metadata
```

5. For high-depth checking, fetch abstract evidence and generate `abstract_support_review.md`. Read `references/support-review.md` for how to interpret and revise weak claims.

```bash
python3 -m citationtool.cli verify <spec.json> --depth abstract
```

6. Inspect the generated active DOCX:

```bash
python3 -m citationtool.cli inspect <active.docx>
unzip -t <active.docx>
```

7. Visually render the active DOCX if the environment supports it:

```bash
python3 -m citationtool.cli run <spec.json> --no-zotero-import --verify none --render auto
```

On macOS, `auto` tries Quick Look first; otherwise it tries LibreOffice. If rendering is skipped or fails, state the reason and continue with field/archive validation.
8. When the user explicitly wants live Zotero/Word handoff, run:

```bash
python3 -m citationtool.cli run <spec.json> --refresh-word
```

This imports references through Zotero's local connector unless `--no-zotero-import` is passed, then asks Zotero's Mac Word integration endpoint to refresh the active Word draft.

## Expected Outputs

- Zotero-active `.docx` with `ADDIN ZOTERO_ITEM` citation fields and one `ADDIN ZOTERO_BIBL` bibliography field.
- Placeholder fallback `.docx`.
- RIS and CSL JSON reference files.
- `claim_support_report.md`.
- `reference_verification.json`.
- `verification_report.md`.
- `abstract_support_review.md` for high-depth runs.
- `automation_summary.md`.

## Validation Bar

Before calling the result done, confirm:

- active DOCX contains the expected number of `ADDIN ZOTERO_ITEM` fields and one `ADDIN ZOTERO_BIBL` field
- DOCX archive integrity passes with `unzip -t`
- claim report maps every substantive claim to a citation key
- reference metadata includes DOI or PMID where available
- `verification_report.md` has no failed metadata checks, or failures are reported clearly
- abstract-depth support labels and safer-claim suggestions are reviewed by the harness/LLM when the user requests high-depth support checking
- Word/Zotero refresh succeeds or any blocker is reported clearly
- visual render succeeds, is skipped intentionally, or any renderer blocker is reported clearly
