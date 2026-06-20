# Abstract Support Review

Use this rubric after running:

```bash
python3 -m citationtool.cli verify <spec.json> --depth abstract
```

Read `reference_verification.json`. For each `claims[]` entry, inspect the cited evidence abstract and candidate snippets.

## Labels

- `Supported`: the abstract directly supports the claim as written.
- `Partially supported`: the abstract supports the general direction, but the claim is broader, stronger, or more specific than the abstract.
- `Unsupported`: the abstract contradicts the claim or does not support it.
- `Not assessable`: no abstract is available, the citation key is wrong, or support requires full text/methods/tables.

## Output

Write `abstract_support_review.md` beside the generated artifacts with:

- project slug
- statement that the review is abstract-level only
- table columns: `Claim`, `Citation key`, `LLM support judgment`, `Notes`
- brief overall summary

If any claim is `Partially supported`, `Unsupported`, or `Not assessable`, either revise the JSON spec/draft and rerun CitationTool, or report the limitation clearly.

Do not treat keyword overlap as final support. Candidate snippets are evidence pointers, not the judgment.
