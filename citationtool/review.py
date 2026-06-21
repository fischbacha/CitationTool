from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .verification import md_escape, tokens


DEFAULT_APPLY_STATUSES = {"partially_supported", "unsupported"}
WEAK_STATUSES = {"partially_supported", "unsupported", "not_assessable", "metadata_only"}


@dataclass(frozen=True)
class ApplyReviewResult:
    project: dict[str, Any]
    actions: list[dict[str, Any]]
    out_spec: Path
    report: Path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_reviewed_slug(slug: str, suffix: str) -> str:
    suffix = suffix.strip("_")
    if not suffix:
        return slug
    return slug if slug.endswith(f"_{suffix}") else f"{slug}_{suffix}"


def default_reviewed_output_dir(output_dir: str | None, slug: str, suffix: str) -> str:
    suffix = suffix.strip("_")
    if output_dir:
        return output_dir if output_dir.endswith(f"_{suffix}") else f"{output_dir}_{suffix}"
    return f"artifacts/{default_reviewed_slug(slug, suffix)}"


def candidate_from_safer_claim(value: str | None) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if not value:
        return ""
    prefixes = [
        "Candidate safer wording:",
        "Replace the source or use a narrower claim visible in the abstract:",
        "Narrow the claim toward the abstract evidence:",
        "Replace or substantially narrow the claim; the closest abstract sentence is:",
    ]
    for prefix in prefixes:
        if value.lower().startswith(prefix.lower()):
            value = value[len(prefix) :].strip()
            break
    if value.lower().startswith("run with ") or value.lower().startswith("inspect the full text"):
        return ""
    return sentence_text(value)


def sentence_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return ""
    return value if value[-1] in ".!?" else f"{value}."


def chunk_claim_text(value: str) -> str:
    value = sentence_text(value)
    return value.rstrip(".!?").strip() + " "


def replacement_for_text_chunk(text: str, replacement: str) -> tuple[str, str]:
    replacement_chunk = chunk_claim_text(replacement)
    leading = re.match(r"^(\s*[.;:!?]\s+)(.*)$", text, flags=re.S)
    if leading:
        return f"{leading.group(1)}{replacement_chunk}", leading.group(2)

    boundaries = list(re.finditer(r"(?<=[.!?])\s+", text))
    if boundaries:
        cut = boundaries[-1].end()
        return f"{text[:cut]}{replacement_chunk}", text[cut:]

    return replacement_chunk, text


def citation_targets(project: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    targets: dict[str, list[dict[str, Any]]] = {}
    for paragraph_index, chunks in enumerate(project.get("paragraphs", [])):
        for chunk_index, chunk in enumerate(chunks):
            support = chunk.get("cite")
            if not support:
                continue
            previous_index = chunk_index - 1
            if previous_index < 0 or "text" not in chunks[previous_index]:
                continue
            targets.setdefault(str(support), []).append(
                {
                    "paragraphIndex": paragraph_index,
                    "textChunkIndex": previous_index,
                    "citeChunkIndex": chunk_index,
                    "text": chunks[previous_index].get("text", ""),
                }
            )
    return targets


def target_score(claim: str, text: str) -> float:
    claim_tokens = tokens(claim)
    text_tokens = tokens(text)
    if not claim_tokens or not text_tokens:
        return 0.0
    return len(claim_tokens & text_tokens) / len(claim_tokens)


def select_rewrite_target(
    project: dict[str, Any],
    targets: dict[str, list[dict[str, Any]]],
    support_id: str,
    claim_text: str,
    touched: set[tuple[int, int]],
) -> dict[str, Any] | None:
    available = [
        target
        for target in targets.get(support_id, [])
        if (target["paragraphIndex"], target["textChunkIndex"]) not in touched
    ]
    if not available:
        return None
    for target in available:
        chunks = project["paragraphs"][target["paragraphIndex"]]
        target["text"] = chunks[target["textChunkIndex"]].get("text", "")
        target["score"] = target_score(claim_text, target["text"])
    return max(available, key=lambda item: item["score"])


def support_ids_from_claim(claim: dict[str, Any]) -> list[str]:
    support = claim.get("support")
    if support is None:
        return []
    if isinstance(support, list):
        return [str(item) for item in support]
    return [str(support)]


def primary_evidence(claim_result: dict[str, Any], apply_statuses: set[str]) -> dict[str, Any] | None:
    evidence_items = claim_result.get("evidence", [])
    for evidence in evidence_items:
        if evidence.get("status") in apply_statuses and candidate_from_safer_claim(evidence.get("saferClaim")):
            return evidence
    for evidence in evidence_items:
        if evidence.get("status") in WEAK_STATUSES:
            return evidence
    return evidence_items[0] if evidence_items else None


def add_review_metadata(
    claim: dict[str, Any],
    evidence: dict[str, Any],
    original_claim: str,
    revised_claim: str | None,
    action: str,
):
    status = evidence.get("status", "unknown")
    support = evidence.get("support", "")
    claim["level"] = "Supported" if status == "supported" else f"Abstract triage: {status}"
    note_bits = [
        f"apply-review action: {action}",
        f"support `{support}` status `{status}`",
    ]
    if evidence.get("confidence"):
        note_bits.append(f"confidence `{evidence['confidence']}`")
    if revised_claim:
        note_bits.append(f"original claim: {original_claim}")
    if evidence.get("reason"):
        note_bits.append(evidence["reason"])
    claim["note"] = "; ".join(note_bits)


def apply_review(
    raw_project: dict[str, Any],
    loaded_project: dict[str, Any],
    verification_result: dict[str, Any],
    out_spec: Path,
    report_path: Path,
    suffix: str = "reviewed",
    apply_statuses: set[str] | None = None,
) -> ApplyReviewResult:
    apply_statuses = apply_statuses or DEFAULT_APPLY_STATUSES
    project = copy.deepcopy(raw_project)
    project["references"] = copy.deepcopy(loaded_project.get("references", raw_project.get("references", [])))
    project.pop("reference_source", None)
    project["slug"] = default_reviewed_slug(str(loaded_project.get("slug", project.get("slug", "citationtool_project"))), suffix)
    project["output_dir"] = default_reviewed_output_dir(
        loaded_project.get("output_dir") or raw_project.get("output_dir"),
        str(loaded_project.get("slug", project["slug"])),
        suffix,
    )

    targets = citation_targets(project)
    touched: set[tuple[int, int]] = set()
    actions: list[dict[str, Any]] = []
    verification_claims = verification_result.get("claims", [])

    for index, claim in enumerate(project.get("claims", [])):
        claim_result = verification_claims[index] if index < len(verification_claims) else {}
        evidence = primary_evidence(claim_result, apply_statuses)
        if not evidence:
            continue

        original_claim = claim.get("claim", "")
        status = evidence.get("status", "")
        support_id = str(evidence.get("support") or (support_ids_from_claim(claim) or [""])[0])
        revised_claim = candidate_from_safer_claim(evidence.get("saferClaim"))
        action = {
            "claimIndex": index,
            "support": support_id,
            "status": status,
            "originalClaim": original_claim,
            "revisedClaim": revised_claim,
            "action": "unchanged",
            "paragraphRewrite": None,
            "reason": evidence.get("reason", ""),
        }

        if status in apply_statuses and revised_claim:
            claim["claim"] = revised_claim
            target = select_rewrite_target(project, targets, support_id, original_claim, touched)
            if target:
                paragraph_index = target["paragraphIndex"]
                chunk_index = target["textChunkIndex"]
                old_text = project["paragraphs"][paragraph_index][chunk_index].get("text", "")
                new_text, replaced_fragment = replacement_for_text_chunk(old_text, revised_claim)
                project["paragraphs"][paragraph_index][chunk_index]["text"] = new_text
                touched.add((paragraph_index, chunk_index))
                action["action"] = "claim_and_paragraph_rewritten"
                action["paragraphRewrite"] = {
                    "paragraphIndex": paragraph_index,
                    "textChunkIndex": chunk_index,
                    "oldText": old_text,
                    "newText": new_text,
                    "replacedFragment": replaced_fragment,
                    "targetScore": target.get("score", 0.0),
                }
            else:
                action["action"] = "claim_rewritten_no_paragraph_target"
        elif status in WEAK_STATUSES:
            action["action"] = "flagged_no_rewrite"

        add_review_metadata(
            claim=claim,
            evidence=evidence,
            original_claim=original_claim,
            revised_claim=revised_claim if action["action"].startswith("claim") else None,
            action=action["action"],
        )
        actions.append(action)

    project["review_application"] = {
        "sourceVerification": verification_result.get("paths", {}).get("json", ""),
        "generatedAtUnix": int(time.time()),
        "appliedStatuses": sorted(apply_statuses),
        "weakStatuses": sorted(WEAK_STATUSES),
        "actions": actions,
    }

    out_spec.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_spec.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
    write_apply_report(project, actions, report_path)
    return ApplyReviewResult(project=project, actions=actions, out_spec=out_spec, report=report_path)


def write_apply_report(project: dict[str, Any], actions: list[dict[str, Any]], path: Path):
    lines = [
        "# Apply Review Report",
        "",
        f"Project: `{project.get('slug', '')}`",
        "",
        "| Claim | Citation key | Status | Action | Revised claim |",
        "|---|---|---|---|---|",
    ]
    for action in actions:
        lines.append(
            f"| {md_escape(action.get('originalClaim', ''))} | `{md_escape(action.get('support', ''))}` | "
            f"`{md_escape(action.get('status', ''))}` | `{md_escape(action.get('action', ''))}` | "
            f"{md_escape(action.get('revisedClaim') or '')} |"
        )

    rewrites = [action for action in actions if action.get("paragraphRewrite")]
    lines.extend(["", "## Paragraph Rewrites", ""])
    if not rewrites:
        lines.append("No paragraph text was rewritten.")
    else:
        for action in rewrites:
            rewrite = action["paragraphRewrite"]
            lines.extend(
                [
                    f"- Paragraph `{rewrite['paragraphIndex']}`, text chunk `{rewrite['textChunkIndex']}`",
                    f"  - Old: {md_escape(rewrite.get('oldText', ''))}",
                    f"  - New: {md_escape(rewrite.get('newText', ''))}",
                ]
            )

    skipped = [action for action in actions if action.get("action") == "flagged_no_rewrite"]
    lines.extend(["", "## Still Needs Review", ""])
    if not skipped:
        lines.append("No weak claims were left without a rewrite.")
    else:
        for action in skipped:
            lines.append(
                f"- `{md_escape(action.get('status', ''))}` for `{md_escape(action.get('support', ''))}`: "
                f"{md_escape(action.get('originalClaim', ''))}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
