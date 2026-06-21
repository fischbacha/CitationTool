# Abstract Support Review

Use this rubric after running:

```bash
python3 -m citationtool.cli verify <spec.json> --depth abstract
```

The CLI writes `abstract_support_review.md` automatically. Read that file together with `reference_verification.json`. For each `claims[]` entry, inspect the cited evidence abstract, candidate snippets, automatic support label, and safer-claim suggestion.

## Labels

- `supported`: the abstract visibly supports the claim as written.
- `partially_supported`: the abstract supports the general direction, but the claim is broader, stronger, or more specific than the visible evidence.
- `unsupported`: the abstract contradicts the claim or does not support it.
- `not_assessable`: no abstract is available, the citation key is wrong, or support requires full text/methods/tables.
- `metadata_only`: metadata was checked, but abstract-depth review was not requested.

## Output

Confirm that `abstract_support_review.md` contains:

- project slug
- statement that the review is abstract-level only
- table columns for claim, citation key, support status, confidence, evidence pointer, and safer claim/action
- brief overall summary

If any claim is `partially_supported`, `unsupported`, `not_assessable`, or `metadata_only`, either revise the JSON spec/draft and rerun CitationTool, or report the limitation clearly.

Do not treat automatic token overlap as final support. Candidate snippets are evidence pointers, and the harness/LLM should still make the final judgment before a claim is presented as supported.
