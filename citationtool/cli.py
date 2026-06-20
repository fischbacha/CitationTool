from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .builder import ROOT, build_project, inspect_docx_fields, load_project, project_out_dir
from .rendering import RenderResult, render_docx
from .verification import verify_project
from .zotero import import_ris_into_zotero, request_zotero_word_refresh


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_summary(
    project: dict,
    outputs,
    field_check: dict,
    import_result: dict,
    refresh_result: dict | None,
    render_result: RenderResult,
    verification_result: dict | None,
):
    summary = outputs.out_dir / "automation_summary.md"
    lines = [
        "# Automation Summary",
        "",
        f"Project: `{project['slug']}`",
        f"Active Zotero Word draft: `{repo_path(outputs.active_docx)}`",
        f"Placeholder fallback draft: `{repo_path(outputs.placeholder_docx)}`",
        f"RIS: `{repo_path(outputs.ris)}`",
        f"CSL JSON: `{repo_path(outputs.csl_json)}`",
        f"Claim report: `{repo_path(outputs.claim_report)}`",
        "",
        "## Field Self-Check",
        "",
        f"Detected {field_check['citationFields']} citation fields and {field_check['bibliographyFields']} bibliography field.",
        "",
        "## Reference Verification",
        "",
    ]
    if verification_result:
        report = verification_result.get("paths", {}).get("report")
        report_text = f" Report: `{repo_path(Path(report))}`." if report else ""
        lines.append(
            f"Verification depth `{verification_result['depth']}` finished with status "
            f"`{verification_result['overallStatus']}`.{report_text}"
        )
    else:
        lines.append("Skipped: verification was not requested.")

    lines.extend(
        [
            "",
            "## Zotero",
            "",
        ]
    )
    if import_result.get("imported"):
        lines.append(
            f"Imported {len(import_result.get('items', []))} references into "
            f"`{import_result['target']['name']}` and tagged them with `{', '.join(import_result.get('tags', []))}`."
        )
    elif import_result.get("skipped"):
        lines.append(f"Skipped Zotero import: {import_result.get('reason')}")
    else:
        lines.append("Zotero import was not requested.")

    if refresh_result:
        lines.extend(
            [
                "",
                "## Word Refresh",
                "",
                "Zotero accepted a Mac Word `Refresh` request for the active Zotero Word draft.",
            ]
        )

    lines.extend(["", "## Visual Render", ""])
    if render_result.skipped:
        lines.append(f"Skipped: {render_result.reason}")
    else:
        lines.append(f"Rendered with `{render_result.renderer}` to `{repo_path(render_result.output)}`.")

    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def open_in_word(docx: Path):
    subprocess.run(["open", "-a", "Microsoft Word", str(docx)], check=False)


def run_project(args) -> int:
    project = load_project(args.spec)
    out_dir = project_out_dir(project, args.out)
    verification_result = None
    if args.verify != "none":
        verification_result = verify_project(project, out_dir, depth=args.verify, email=args.contact_email)
        if verification_result["overallStatus"] == "failed" and not args.verify_warn_only:
            print(
                "Reference verification: "
                f"{verification_result['overallStatus']} ({verification_result['depth']})"
            )
            print(f"Verification report: {verification_result['paths']['report']}")
            return 2

    outputs = build_project(project, out_dir)
    field_check = inspect_docx_fields(outputs.active_docx)

    import_result = {"imported": False, "skipped": False, "items": []}
    if not args.no_zotero_import:
        import_result = import_ris_into_zotero(
            ris_path=outputs.ris,
            csl_json=outputs.csl_json,
            import_log=outputs.out_dir / "zotero_import_result.json",
            tags=project.get("zotero_tags", ["CitationTool", project["slug"]]),
            note=project.get("zotero_note", "<p>Imported by CitationTool.</p>"),
            force=args.force_zotero_import,
            dry_run=args.dry_run_zotero_import,
        )

    if args.open_word:
        open_in_word(outputs.active_docx)
    if args.open_placeholder_word:
        open_in_word(outputs.placeholder_docx)

    refresh_result = None
    if args.refresh_word:
        refresh_result = request_zotero_word_refresh(outputs.active_docx)
        print(f"Requested Zotero Word refresh for: {refresh_result['document']}")

    render_result = render_docx(outputs.active_docx, outputs.out_dir / "rendered", args.render)

    summary = write_summary(
        project,
        outputs,
        field_check,
        import_result,
        refresh_result,
        render_result,
        verification_result,
    )
    print(f"Generated active Zotero Word draft: {outputs.active_docx}")
    print(f"Generated placeholder fallback draft: {outputs.placeholder_docx}")
    print(f"Generated RIS: {outputs.ris}")
    print(f"Generated CSL JSON: {outputs.csl_json}")
    print(
        "Field self-check: "
        f"{field_check['citationFields']} citation fields, "
        f"{field_check['bibliographyFields']} bibliography field"
    )
    if verification_result:
        print(
            "Reference verification: "
            f"{verification_result['overallStatus']} ({verification_result['depth']})"
        )
    if import_result.get("imported"):
        print(f"Imported {len(import_result.get('items', []))} references into Zotero target: {import_result['target']['name']}")
    elif import_result.get("skipped"):
        print(f"Zotero import skipped: {import_result.get('reason')}")
    else:
        print("Zotero import not requested.")
    if render_result.skipped:
        print(f"Visual render skipped: {render_result.reason}")
    else:
        print(f"Visual render ({render_result.renderer}): {render_result.output}")
    print(f"Summary: {summary}")
    return 0


def inspect_docx(args) -> int:
    result = inspect_docx_fields(args.docx)
    print(json.dumps(result, indent=2))
    return 0


def verify_references(args) -> int:
    project = load_project(args.spec)
    out_dir = project_out_dir(project, args.out)
    result = verify_project(project, out_dir, depth=args.depth, email=args.contact_email)
    print(f"Reference verification: {result['overallStatus']} ({result['depth']})")
    print(f"JSON: {result['paths']['json']}")
    print(f"Report: {result['paths']['report']}")
    if result["overallStatus"] == "failed" and not args.warn_only:
        return 2
    return 0


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Generate Zotero-active Word drafts from CitationTool project specs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Build a project spec and optionally import/refresh through Zotero.")
    run.add_argument("spec", type=Path, help="Path to a CitationTool JSON project spec.")
    run.add_argument("--out", type=Path, help="Override output directory.")
    run.add_argument("--no-zotero-import", action="store_true", help="Generate files but do not import references into Zotero.")
    run.add_argument("--force-zotero-import", action="store_true", help="Import references even if this workspace already recorded an import.")
    run.add_argument("--dry-run-zotero-import", action="store_true", help="Check Zotero connectivity and target without importing.")
    run.add_argument("--open-word", action="store_true", help="Open the generated active Zotero Word draft.")
    run.add_argument("--open-placeholder-word", action="store_true", help="Open the generated placeholder fallback draft.")
    run.add_argument("--refresh-word", action="store_true", help="Ask Zotero's Mac Word integration endpoint to refresh the active draft.")
    run.add_argument(
        "--verify",
        choices=["none", "metadata", "abstract"],
        default="metadata",
        help="Verify references before generation. Metadata checks DOI/PMID; abstract also fetches evidence for claim review.",
    )
    run.add_argument("--verify-warn-only", action="store_true", help="Continue generation even if verification fails.")
    run.add_argument(
        "--contact-email",
        help="Contact email for polite PubMed/Crossref API use. Can also use CITATIONTOOL_CONTACT_EMAIL.",
    )
    run.add_argument(
        "--render",
        choices=["none", "auto", "quicklook", "libreoffice"],
        default="none",
        help="Optionally render the active DOCX for visual QA. `auto` tries Quick Look on macOS and LibreOffice otherwise.",
    )
    run.set_defaults(func=run_project)

    inspect = subparsers.add_parser("inspect", help="Count generated Zotero field markers in a DOCX.")
    inspect.add_argument("docx", type=Path)
    inspect.set_defaults(func=inspect_docx)

    verify = subparsers.add_parser("verify", help="Verify DOI/PMID metadata and optionally fetch abstract evidence.")
    verify.add_argument("spec", type=Path, help="Path to a CitationTool JSON project spec.")
    verify.add_argument("--out", type=Path, help="Override output directory.")
    verify.add_argument("--depth", choices=["metadata", "abstract"], default="metadata", help="Verification depth.")
    verify.add_argument("--warn-only", action="store_true", help="Return success even if verification finds failures.")
    verify.add_argument(
        "--contact-email",
        help="Contact email for polite PubMed/Crossref API use. Can also use CITATIONTOOL_CONTACT_EMAIL.",
    )
    verify.set_defaults(func=verify_references)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
