from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import generate_immunoglobulins_fibrosis_demo as demo


CONNECTOR_BASE = "http://127.0.0.1:23119"
IMPORT_LOG = demo.OUT_DIR / "zotero_import_result.json"
SUMMARY = demo.OUT_DIR / "automation_summary.md"
DEFAULT_TAGS = ["CitationTool", "Immunoglobulins fibrosis demo"]
MAC_WORD_AGENT = "MacWord16"
MAC_WORD_TEMPLATE_VERSION = 2


def request_json(path: str, payload: dict | None = None, timeout: float = 15):
    data = None
    headers = {
        "X-Zotero-Connector-API-Version": "3",
        "X-Zotero-Version": "9.0.4",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(CONNECTOR_BASE + path, data=data, headers=headers)
    with urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        if not body:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return json.loads(body)
        return body


def ping_zotero() -> bool:
    try:
        response = urlopen(CONNECTOR_BASE + "/connector/ping", timeout=3)
        body = response.read().decode("utf-8", errors="replace")
        return response.status == 200 and "Zotero is running" in body
    except (HTTPError, URLError, TimeoutError):
        return False


def current_target() -> dict:
    data = request_json("/connector/getSelectedCollection", {})
    if not isinstance(data, dict):
        raise RuntimeError("Zotero returned an unexpected selected-collection response")

    if data.get("id") is not None:
        target_id = f"C{data['id']}"
    else:
        target_id = f"L{data['libraryID']}"

    return {
        "target": target_id,
        "name": data.get("name") or data.get("libraryName") or target_id,
        "libraryID": data.get("libraryID"),
        "libraryName": data.get("libraryName"),
        "editable": data.get("editable"),
    }


def import_log_matches() -> bool:
    if not IMPORT_LOG.exists():
        return False
    try:
        data = json.loads(IMPORT_LOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    expected_dois = sorted(ref["doi"].lower() for ref in demo.REFERENCES)
    logged_dois = sorted(item.get("DOI", "").lower() for item in data.get("items", []))
    return data.get("imported") is True and logged_dois == expected_dois


def import_ris_into_zotero(force: bool = False, dry_run: bool = False) -> dict:
    if not ping_zotero():
        raise RuntimeError(
            "Zotero is not reachable on http://127.0.0.1:23119. Open Zotero and rerun this command."
        )

    target = current_target()
    if target.get("editable") is False:
        raise RuntimeError(f"Selected Zotero target is not editable: {target['name']}")

    if import_log_matches() and not force:
        return {
            "imported": False,
            "skipped": True,
            "reason": "References were already imported by this workspace. Use --force-zotero-import to import again.",
            "target": target,
            "items": json.loads(IMPORT_LOG.read_text(encoding="utf-8")).get("items", []),
        }

    if dry_run:
        return {
            "imported": False,
            "skipped": True,
            "reason": "Dry run: Zotero reachable; import was not performed.",
            "target": target,
            "items": [],
        }

    session = f"citationtool-{uuid.uuid4().hex}"
    ris_path = demo.OUT_DIR / "immunoglobulins_fibrosis_zotero_references.ris"
    req = Request(
        f"{CONNECTOR_BASE}/connector/import?session={session}",
        data=ris_path.read_bytes(),
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "X-Zotero-Connector-API-Version": "3",
            "X-Zotero-Version": "9.0.4",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        if response.status != 201:
            raise RuntimeError(f"Zotero import failed with HTTP {response.status}: {body}")
        items = json.loads(body)

    request_json(
        "/connector/updateSession",
        {
            "sessionID": session,
            "target": target["target"],
            "tags": DEFAULT_TAGS,
            "note": (
                "<p>Imported by CitationTool demo. Replace the matching placeholders in "
                "the Word draft with Zotero Word plugin citations.</p>"
            ),
        },
    )

    result = {
        "imported": True,
        "skipped": False,
        "sessionID": session,
        "target": target,
        "tags": DEFAULT_TAGS,
        "items": items,
        "importedAtUnix": int(time.time()),
    }
    IMPORT_LOG.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def inspect_active_docx_fields() -> dict:
    with zipfile.ZipFile(demo.EXPERIMENTAL_ACTIVE_DOCX) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    return {
        "citationFields": document_xml.count("ADDIN ZOTERO_ITEM"),
        "bibliographyFields": document_xml.count("ADDIN ZOTERO_BIBL"),
        "hasCSLCitationMarker": "CSL_CITATION" in document_xml,
        "hasCSLBibliographyMarker": "CSL_BIBLIOGRAPHY" in document_xml,
    }


def repo_path(path: Path) -> str:
    return str(path.relative_to(demo.ROOT))


def write_summary(import_result: dict, field_check: dict, refresh_result: dict | None = None):
    lines = [
        "# Automation Summary",
        "",
        f"Placeholder Word draft: `{repo_path(demo.PLACEHOLDER_DOCX)}`",
        f"Experimental active-field Word draft: `{repo_path(demo.EXPERIMENTAL_ACTIVE_DOCX)}`",
        f"RIS: `{repo_path(demo.OUT_DIR / 'immunoglobulins_fibrosis_zotero_references.ris')}`",
        f"CSL JSON: `{repo_path(demo.OUT_DIR / 'immunoglobulins_fibrosis_zotero_references.csl.json')}`",
        f"Claim report: `{repo_path(demo.OUT_DIR / 'claim_support_report.md')}`",
        "",
        "## Zotero",
        "",
    ]
    if import_result.get("imported"):
        lines.append(
            f"Imported {len(import_result.get('items', []))} references into "
            f"`{import_result['target']['name']}` and tagged them with `{', '.join(DEFAULT_TAGS)}`."
        )
    elif import_result.get("skipped"):
        lines.append(f"Skipped Zotero import: {import_result.get('reason')}")
    else:
        lines.append("Zotero import was not requested.")

    lines.extend(
        [
            "",
            "## Remaining Word Step",
            "",
            "The Word plugin step is still intentionally not faked. Open the draft, search each `[ZOTERO: ...]` placeholder, and use Zotero `Add/Edit Citation`. Then use `Add/Edit Bibliography` under the References heading.",
            "",
            "## Experimental Active-Field Draft",
            "",
            "The active-field experiment contains generated `ADDIN ZOTERO_ITEM` and `ADDIN ZOTERO_BIBL` Word fields with embedded CSL item data. Open it in Word and run Zotero `Refresh`; if Zotero can edit the citations and refresh the bibliography, this is the path toward full automation.",
            "",
            f"Field self-check: detected {field_check['citationFields']} citation fields and {field_check['bibliographyFields']} bibliography field.",
            "",
            "Opt-in refresh test: `python3 tools/run_zotero_ready_demo.py --refresh-active-word` asks Zotero's Mac Word integration endpoint to run `Refresh` on the experimental active-field draft.",
            "",
        ]
    )
    if refresh_result:
        lines.extend(
            [
                "Last refresh request: Zotero accepted a Mac Word `Refresh` request for the experimental active-field draft. This confirms endpoint handoff, but the final validation still needs Word/Zotero to show the citations as editable.",
                "",
            ]
        )
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def open_in_word(docx: Path):
    subprocess.run(["open", "-a", "Microsoft Word", str(docx)], check=False)


def request_zotero_word_refresh(docx: Path) -> dict:
    if not ping_zotero():
        raise RuntimeError(
            "Zotero is not reachable on http://127.0.0.1:23119. Open Zotero and rerun this command."
        )
    path = str(docx)
    url = (
        f"{CONNECTOR_BASE}/integration/macWordCommand"
        f"?agent={MAC_WORD_AGENT}"
        f"&command=refresh"
        f"&document={quote(path)}"
        f"&templateVersion={MAC_WORD_TEMPLATE_VERSION}"
    )
    with urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")
        if response.status != 200:
            raise RuntimeError(f"Zotero Word refresh request failed with HTTP {response.status}: {body}")
    return {
        "requested": True,
        "document": path,
        "agent": MAC_WORD_AGENT,
        "templateVersion": MAC_WORD_TEMPLATE_VERSION,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the immunoglobulins/fibrosis demo and automate Zotero reference import."
    )
    parser.add_argument(
        "--no-zotero-import",
        action="store_true",
        help="Generate files but do not import references into Zotero.",
    )
    parser.add_argument(
        "--force-zotero-import",
        action="store_true",
        help="Import references even if this workspace already recorded an import.",
    )
    parser.add_argument(
        "--dry-run-zotero-import",
        action="store_true",
        help="Check Zotero connectivity and target without importing.",
    )
    parser.add_argument(
        "--open-word",
        action="store_true",
        help="Open the conservative placeholder draft in Microsoft Word after generation/import.",
    )
    parser.add_argument(
        "--open-active-word",
        action="store_true",
        help="Open the experimental generated-Zotero-field draft in Microsoft Word.",
    )
    parser.add_argument(
        "--refresh-active-word",
        action="store_true",
        help="Ask Zotero's Mac Word integration endpoint to run Refresh on the experimental active-field draft.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    demo.main()
    field_check = inspect_active_docx_fields()

    import_result = {"imported": False, "skipped": False, "items": []}
    if not args.no_zotero_import:
        import_result = import_ris_into_zotero(
            force=args.force_zotero_import,
            dry_run=args.dry_run_zotero_import,
        )

    if args.open_word:
        open_in_word(demo.PLACEHOLDER_DOCX)
    if args.open_active_word:
        open_in_word(demo.EXPERIMENTAL_ACTIVE_DOCX)
    refresh_result = None
    if args.refresh_active_word:
        refresh_result = request_zotero_word_refresh(demo.EXPERIMENTAL_ACTIVE_DOCX)
        print(f"Requested Zotero Word refresh for: {refresh_result['document']}")

    write_summary(import_result, field_check, refresh_result)

    print(f"Generated placeholder draft: {demo.PLACEHOLDER_DOCX}")
    print(f"Generated experimental active-field draft: {demo.EXPERIMENTAL_ACTIVE_DOCX}")
    print(
        "Experimental field self-check: "
        f"{field_check['citationFields']} citation fields, "
        f"{field_check['bibliographyFields']} bibliography field"
    )
    if import_result.get("imported"):
        print(f"Imported {len(import_result.get('items', []))} references into Zotero target: {import_result['target']['name']}")
    elif import_result.get("skipped"):
        print(f"Zotero import skipped: {import_result.get('reason')}")
    else:
        print("Zotero import not requested.")
    print(f"Summary: {SUMMARY}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
