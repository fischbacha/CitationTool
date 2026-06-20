from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CONNECTOR_BASE = "http://127.0.0.1:23119"
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
    except (HTTPError, URLError, TimeoutError, PermissionError):
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


def expected_dois_from_csl(csl_json: Path) -> list[str]:
    refs = json.loads(csl_json.read_text(encoding="utf-8"))
    return sorted(ref.get("DOI", "").lower() for ref in refs if ref.get("DOI"))


def import_log_matches(import_log: Path, csl_json: Path) -> bool:
    if not import_log.exists():
        return False
    try:
        data = json.loads(import_log.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    logged_dois = sorted(item.get("DOI", "").lower() for item in data.get("items", []))
    return data.get("imported") is True and logged_dois == expected_dois_from_csl(csl_json)


def import_ris_into_zotero(
    ris_path: Path,
    csl_json: Path,
    import_log: Path,
    tags: list[str],
    note: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    if not ping_zotero():
        raise RuntimeError("Zotero is not reachable on http://127.0.0.1:23119. Open Zotero and rerun this command.")

    target = current_target()
    if target.get("editable") is False:
        raise RuntimeError(f"Selected Zotero target is not editable: {target['name']}")

    if import_log_matches(import_log, csl_json) and not force:
        return {
            "imported": False,
            "skipped": True,
            "reason": "References were already imported by this workspace. Use --force-zotero-import to import again.",
            "target": target,
            "items": json.loads(import_log.read_text(encoding="utf-8")).get("items", []),
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
            "tags": tags,
            "note": note,
        },
    )

    result = {
        "imported": True,
        "skipped": False,
        "sessionID": session,
        "target": target,
        "tags": tags,
        "items": items,
        "importedAtUnix": int(time.time()),
    }
    import_log.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def request_zotero_word_refresh(docx: Path) -> dict:
    if not ping_zotero():
        raise RuntimeError("Zotero is not reachable on http://127.0.0.1:23119. Open Zotero and rerun this command.")
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
