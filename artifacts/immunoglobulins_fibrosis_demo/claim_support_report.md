# Claim Support Report

Generated for the Zotero-ready immunoglobulins/fibrosis demo.

## Verification Summary

All three references were selected because PubMed metadata confirms the PMID, DOI, journal, year, volume, issue, and pages. The Nature Medicine DOI was also checked through Crossref during generation setup.

| Key | Zotero placeholder | Verified identifier | Reference |
|---|---|---|---|
| `wynn-2012` | `[ZOTERO: Wynn 2012]` | PMID `22772564`, DOI `10.1038/nm.2807` | Wynn and Ramalingam 2012. Mechanisms of fibrosis: therapeutic translation for fibrotic disease. Nat Med 18(7):1028-1040. doi:10.1038/nm.2807; PMID:22772564. |
| `stone-2012` | `[ZOTERO: Stone 2012]` | PMID `22316447`, DOI `10.1056/NEJMra1104650` | Stone et al. 2012. IgG4-related disease. N Engl J Med 366(6):539-551. doi:10.1056/NEJMra1104650; PMID:22316447. |
| `deshpande-2012` | `[ZOTERO: Deshpande 2012]` | PMID `22596100`, DOI `10.1038/modpathol.2012.72` | Deshpande et al. 2012. Consensus statement on the pathology of IgG4-related disease. Mod Pathol 25(9):1181-1192. doi:10.1038/modpathol.2012.72; PMID:22596100. |

## Claim Mapping

| Claim | Placeholder | Support level | Notes |
|---|---|---|---|
| Fibrosis is framed as a persistent wound-healing program involving immune activation, fibroblast activation, and extracellular matrix remodeling. | `[ZOTERO: Wynn 2012]` | Supported | Review article on mechanisms of fibrosis and therapeutic translation; appropriate for broad fibrosis framing. |
| Fibrotic tissue reflects ongoing crosstalk between inflammatory cells, stromal cells, and matrix-producing myofibroblasts. | `[ZOTERO: Wynn 2012]` | Supported | Used as mechanistic background, not as evidence for an IgG-specific mechanism. |
| IgG4-related disease is a useful immunoglobulin-associated example of fibroinflammatory organ disease. | `[ZOTERO: Stone 2012]` | Supported | NEJM review describes IgG4-related disease as a fibroinflammatory condition with multi-organ involvement. |
| The syndrome often includes dense lymphoplasmacytic infiltrates and increased IgG4-positive plasma cells. | `[ZOTERO: Stone 2012]` | Supported | Kept general and tied to the disease overview source. |
| Diagnostic tissue interpretation emphasizes dense lymphoplasmacytic infiltrate, storiform fibrosis, obliterative phlebitis, and increased IgG4-positive plasma cells. | `[ZOTERO: Deshpande 2012]` | Supported | Directly grounded in the pathology consensus statement. |

## Zotero Round Trip

Recommended automation:

```bash
python3 tools/run_zotero_ready_demo.py --open-active-word
```

That command regenerates both Word drafts, imports the references into the currently selected Zotero target via Zotero's local connector, and opens the experimental active-field draft. In Word, run Zotero `Refresh`; if Zotero can edit the citations and bibliography, this becomes the automated path.

Conservative placeholder workflow:

```bash
python3 tools/run_zotero_ready_demo.py --open-word
```

This opens the safe placeholder draft. The remaining manual step is to use the Zotero Word plugin to replace the placeholders with active citation fields.

Experimental automation output:

- `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_active_field_experiment.docx` contains generated Word ADDIN field codes using Zotero's `ZOTERO_ITEM` and `ZOTERO_BIBL` markers. Open it in Word and run Zotero `Refresh`; if the citations open in Zotero's edit dialog, this can become the automated path.
- `python3 tools/run_zotero_ready_demo.py --refresh-active-word` asks Zotero's Mac Word integration endpoint to run `Refresh` on `artifacts/immunoglobulins_fibrosis_demo/immunoglobulins_fibrosis_zotero_active_field_experiment.docx`.

Manual fallback:

1. Import `immunoglobulins_fibrosis_zotero_references.ris` or `immunoglobulins_fibrosis_zotero_references.csl.json` into Zotero.
2. Open `immunoglobulins_fibrosis_zotero_draft.docx` in Microsoft Word.
3. Replace each `[ZOTERO: ...]` placeholder with Zotero Word plugin `Add/Edit Citation`.
4. Under the References heading, use Zotero Word plugin `Add/Edit Bibliography`.
5. Save the result as a new Word file; that copy will contain active Zotero fields.

Important: the generated draft intentionally does not contain handcrafted Zotero field codes. The placeholders are plain text until the Zotero Word plugin replaces them.
