# CitationTool Claude Code Adapter

Use this project as a deterministic backend for Zotero-active Word drafts.

## When To Use

Use CitationTool when the user asks for a grant/paper introduction, Word draft, Zotero-editable citations, RIS/CSL import files, or a claim-support citation audit.

Microsoft Word plus the Zotero Word plugin is the primary editable-citation target. LibreOffice remains optional for users who have Zotero's LibreOffice plugin or want LibreOffice-based rendering/export.

## Workflow

1. Write a focused introduction draft.
2. Break the draft into paragraph chunks with `text` and `cite` entries.
3. Build a JSON project spec. Follow `harnesses/codex/citationtool/references/project-spec.md`.
4. Run from the repo root:

```bash
python3 -m citationtool.cli run <spec.json> --no-zotero-import
```

5. Validate:

```bash
python3 -m citationtool.cli inspect <active.docx>
unzip -t <active.docx>
```

6. Optional visual QA:

```bash
python3 -m citationtool.cli run <spec.json> --no-zotero-import --render auto
```

7. For live Zotero/Word handoff:

```bash
python3 -m citationtool.cli run <spec.json> --refresh-word
```

## Rules

- Do not invent references.
- Every substantive claim needs a claim-support entry.
- Prefer DOI/PMID metadata.
- Report unsupported or weakly supported claims instead of hiding them.
- The active Word draft is the primary deliverable; the placeholder draft is fallback.
- Report whether rendering used Quick Look, LibreOffice, or was intentionally skipped.
