# CitationTool Project Spec

Use a JSON project spec as the boundary between LLM drafting and deterministic Word/Zotero generation.

## Required Fields

- `slug`: file-safe project id.
- `title`: Word document title.
- `subtitle` or `active_subtitle`: short document subtitle.
- `paragraphs`: list of paragraphs. Each paragraph is a list of chunks:
  - `{"text": "..."}`
  - `{"cite": "reference-id"}`
- `references` or `reference_source`: CSL JSON references. Prefer `reference_source` when references are shared with another artifact.

## Strongly Recommended Fields

- `claims`: claim-support map with `claim`, `support`, `level`, and `note`.
- `zotero_tags`: tags applied during Zotero connector import.
- `zotero_note`: note attached to the Zotero import session.
- `placeholders`: fallback placeholder text for each reference id.
- `output_dir`: repo-relative artifact directory.

## Minimal Shape

```json
{
  "slug": "topic_demo",
  "title": "Topic: Zotero-Active Draft",
  "active_subtitle": "Generated Zotero-active Word fields",
  "output_dir": "artifacts/topic_demo",
  "references": [
    {
      "id": "smith-2024",
      "type": "article-journal",
      "title": "Example verified article",
      "container-title": "Example Journal",
      "container-title-short": "Example J",
      "author": [{"family": "Smith", "given": "Alex"}],
      "issued": {"date-parts": [[2024]]},
      "volume": "1",
      "issue": "1",
      "page": "1-10",
      "DOI": "10.0000/example",
      "PMID": "12345678",
      "URL": "https://doi.org/10.0000/example"
    }
  ],
  "paragraphs": [
    [
      {"text": "A precise claim that is supported by the cited article "},
      {"cite": "smith-2024"},
      {"text": "."}
    ]
  ],
  "claims": [
    {
      "claim": "A precise claim that is supported by the cited article.",
      "support": "smith-2024",
      "level": "Supported",
      "note": "Verified by DOI/PMID metadata and source content."
    }
  ]
}
```

## Drafting Guidance

- Keep citation-bearing chunks narrow: one citation should support the immediately preceding claim.
- Prefer review articles for broad background claims and primary papers or consensus statements for specific mechanistic, diagnostic, or clinical claims.
- If a claim is not clearly supported, either remove it, soften it, or mark it as weak in the claim report.
- Use numbered citations by default for biomedical grant/paper introductions.
