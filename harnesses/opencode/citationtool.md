# CitationTool OpenCode Adapter

OpenCode can use CitationTool as a native project-local skill through:

```text
.opencode/skills/citationtool/SKILL.md
```

OpenCode discovers project-local skills from `.opencode/skills/<name>/SKILL.md`. The `citationtool` skill mirrors the Codex and Claude Code workflows but uses OpenCode-compatible frontmatter and avoids Codex-specific `$skill` syntax.

## Usage

From the CitationTool repo root, start OpenCode and ask for the skill:

```text
Use the citationtool skill to draft a 900-word introduction on B cells in NASH with high-depth reference checking.
```

Or use the included custom command:

```text
/citationtool Draft a short introduction on aging and immunoglobulins with high-depth support checking.
```

The command file lives at:

```text
.opencode/commands/citationtool.md
```

## Expected Workflow

OpenCode should:

1. Create or update a CitationTool JSON project spec.
2. Run metadata verification with `python3 -m citationtool.cli run <spec.json> --no-zotero-import --verify metadata`.
3. Run abstract-depth verification when requested.
4. Run `apply-review` when weak claims have safer wording.
5. Build the Zotero-active Word draft.
6. Report generated files, verification status, support-review status, and any claims that still need full-text or human review.

Keep the original spec and reviewed spec separate so the user can compare the initial draft with the automatically revised draft.
