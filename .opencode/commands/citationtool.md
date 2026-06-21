---
description: Generate a Zotero-active cited Word draft with CitationTool
agent: build
---

Use the `citationtool` skill for this request.

User request:

$ARGUMENTS

Run the CitationTool workflow from the repository root. Create or update a JSON project spec, verify DOI/PMID metadata, use abstract-depth checking when requested, apply reviewed safer-claim rewrites when appropriate, and build a Zotero-active Word draft. Report the generated files, verification status, support-review status, and any claims that still need full-text or human review.
