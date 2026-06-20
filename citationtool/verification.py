from __future__ import annotations

import difflib
import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .builder import year_from_ref


NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF_BASE = "https://api.crossref.org/works"
TOOL_NAME = "CitationTool"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "may",
    "of",
    "on",
    "or",
    "rather",
    "that",
    "the",
    "their",
    "this",
    "through",
    "to",
    "with",
}


@dataclass(frozen=True)
class VerificationPaths:
    json: Path
    report: Path


def verification_paths(out_dir: Path) -> VerificationPaths:
    return VerificationPaths(
        json=out_dir / "reference_verification.json",
        report=out_dir / "verification_report.md",
    )


def contact_email(explicit: str | None = None) -> str | None:
    return explicit or os.environ.get("CITATIONTOOL_CONTACT_EMAIL")


def normalize_doi(value: str | None) -> str:
    value = (value or "").strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    return value.lower()


def normalize_text(value: str | None) -> str:
    value = html.unescape(value or "").lower()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def first_author_family(ref: dict[str, Any]) -> str:
    authors = ref.get("author") or []
    if not authors:
        return ""
    return authors[0].get("family", "")


def year_from_parts(parts: list[Any]) -> str:
    if parts and isinstance(parts[0], list) and parts[0]:
        return str(parts[0][0])
    return ""


def xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def strip_markup(value: str | None) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def tokens(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if token not in STOPWORDS and len(token) > 2}


def title_similarity(expected: str, observed: str) -> float:
    expected_norm = normalize_text(expected)
    observed_norm = normalize_text(observed)
    if not expected_norm or not observed_norm:
        return 0.0
    if expected_norm == observed_norm:
        return 1.0
    return difflib.SequenceMatcher(a=expected_norm, b=observed_norm).ratio()


def best_candidate_snippets(claim: str, abstract: str, limit: int = 2) -> list[str]:
    claim_tokens = tokens(claim)
    if not claim_tokens:
        return []
    scored: list[tuple[float, str]] = []
    for sentence in split_sentences(abstract):
        sentence_tokens = tokens(sentence)
        if not sentence_tokens:
            continue
        overlap = len(claim_tokens & sentence_tokens)
        score = overlap / max(len(claim_tokens), 1)
        if score:
            scored.append((score, sentence))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [sentence for _, sentence in scored[:limit]]


class MetadataClient:
    def __init__(self, email: str | None = None, timeout: float = 20):
        self.email = email
        self.timeout = timeout

    def _user_agent(self) -> str:
        if self.email:
            return f"{TOOL_NAME}/0.3 (mailto:{self.email})"
        return f"{TOOL_NAME}/0.3"

    def _request_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": self._user_agent()})
        with urlopen(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def _request_json(self, url: str) -> dict[str, Any]:
        return json.loads(self._request_text(url))

    def _ncbi_params(self, params: dict[str, str]) -> str:
        payload = {"tool": TOOL_NAME, **params}
        if self.email:
            payload["email"] = self.email
        return urlencode(payload)

    def fetch_pubmed_by_pmid(self, pmid: str) -> dict[str, Any] | None:
        pmid = (pmid or "").strip()
        if not pmid:
            return None
        url = f"{NCBI_BASE}/efetch.fcgi?{self._ncbi_params({'db': 'pubmed', 'id': pmid, 'retmode': 'xml'})}"
        body = self._request_text(url)
        return parse_pubmed_xml(body)

    def fetch_pubmed_by_doi(self, doi: str) -> dict[str, Any] | None:
        doi = normalize_doi(doi)
        if not doi:
            return None
        query = f"{doi}[AID]"
        url = f"{NCBI_BASE}/esearch.fcgi?{self._ncbi_params({'db': 'pubmed', 'term': query, 'retmode': 'json'})}"
        data = self._request_json(url)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return None
        return self.fetch_pubmed_by_pmid(ids[0])

    def fetch_crossref_by_doi(self, doi: str) -> dict[str, Any] | None:
        doi = normalize_doi(doi)
        if not doi:
            return None
        url = f"{CROSSREF_BASE}/{quote(doi, safe='')}"
        if self.email:
            url = f"{url}?{urlencode({'mailto': self.email})}"
        try:
            data = self._request_json(url)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        return parse_crossref_work(data.get("message", {}))


def parse_pubmed_xml(body: str) -> dict[str, Any] | None:
    root = ET.fromstring(body)
    article = root.find(".//PubmedArticle")
    if article is None:
        return None

    article_ids: dict[str, str] = {}
    for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        id_type = (article_id.get("IdType") or "").lower()
        if id_type:
            article_ids[id_type] = xml_text(article_id)

    authors = []
    for author in article.findall(".//AuthorList/Author"):
        family = xml_text(author.find("LastName"))
        given = xml_text(author.find("ForeName")) or xml_text(author.find("Initials"))
        if family or given:
            authors.append({"family": family, "given": given})

    abstract_parts = []
    for abstract_text in article.findall(".//Abstract/AbstractText"):
        part = xml_text(abstract_text)
        label = abstract_text.get("Label")
        if part and label:
            part = f"{label}: {part}"
        if part:
            abstract_parts.append(part)

    year = xml_text(article.find(".//JournalIssue/PubDate/Year")) or xml_text(article.find(".//ArticleDate/Year"))
    if not year:
        medline_date = xml_text(article.find(".//JournalIssue/PubDate/MedlineDate"))
        match = re.search(r"\d{4}", medline_date)
        year = match.group(0) if match else ""

    pmid = xml_text(article.find(".//MedlineCitation/PMID")) or article_ids.get("pubmed", "")
    return {
        "source": "PubMed",
        "pmid": pmid,
        "doi": article_ids.get("doi", ""),
        "pmcid": article_ids.get("pmc", ""),
        "title": xml_text(article.find(".//Article/ArticleTitle")),
        "journal": xml_text(article.find(".//Journal/Title")),
        "journal_short": xml_text(article.find(".//Journal/ISOAbbreviation")),
        "year": year,
        "authors": authors,
        "abstract": " ".join(abstract_parts),
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def parse_crossref_work(message: dict[str, Any]) -> dict[str, Any] | None:
    if not message:
        return None
    authors = [
        {"family": author.get("family", ""), "given": author.get("given", "")}
        for author in message.get("author", [])
        if author.get("family") or author.get("given")
    ]
    title = (message.get("title") or [""])[0]
    journal = (message.get("container-title") or [""])[0]
    year = year_from_parts(message.get("issued", {}).get("date-parts", []))
    doi = message.get("DOI", "")
    return {
        "source": "Crossref",
        "doi": doi,
        "title": title,
        "journal": journal,
        "journal_short": journal,
        "year": year,
        "authors": authors,
        "abstract": strip_markup(message.get("abstract", "")),
        "url": message.get("URL", f"https://doi.org/{doi}" if doi else ""),
    }


def safe_call(label: str, lookup, notes: list[str]) -> dict[str, Any] | None:
    try:
        return lookup()
    except (HTTPError, URLError, TimeoutError, OSError, ET.ParseError, json.JSONDecodeError) as exc:
        notes.append(f"{label} lookup error: {exc}")
        return {"source": label, "error": str(exc)}


def verify_reference(ref: dict[str, Any], client: MetadataClient) -> dict[str, Any]:
    expected_doi = normalize_doi(ref.get("DOI"))
    expected_pmid = str(ref.get("PMID", "")).strip()
    notes: list[str] = []
    warnings: list[str] = []
    problems: list[str] = []

    if not expected_doi and not expected_pmid:
        problems.append("Reference has neither DOI nor PMID.")

    pubmed = None
    if expected_pmid:
        pubmed = safe_call("PubMed", lambda: client.fetch_pubmed_by_pmid(expected_pmid), notes)
        if pubmed is None:
            problems.append(f"PMID {expected_pmid} was not found in PubMed.")
    elif expected_doi:
        pubmed = safe_call("PubMed", lambda: client.fetch_pubmed_by_doi(expected_doi), notes)

    crossref = None
    if expected_doi:
        crossref = safe_call("Crossref", lambda: client.fetch_crossref_by_doi(expected_doi), notes)
        if crossref is None:
            problems.append(f"DOI {expected_doi} was not found in Crossref.")

    if isinstance(pubmed, dict) and pubmed.get("error"):
        problems.append(f"PubMed lookup failed for `{ref['id']}`.")
    if isinstance(crossref, dict) and crossref.get("error"):
        problems.append(f"Crossref lookup failed for `{ref['id']}`.")

    found_sources = [
        source for source in [pubmed, crossref] if isinstance(source, dict) and not source.get("error")
    ]
    if not found_sources and (expected_doi or expected_pmid):
        problems.append("No metadata source resolved this reference.")

    if expected_pmid and isinstance(pubmed, dict) and not pubmed.get("error"):
        observed_pmid = str(pubmed.get("pmid", "")).strip()
        if observed_pmid and observed_pmid != expected_pmid:
            problems.append(f"PubMed returned PMID {observed_pmid}, expected {expected_pmid}.")

    if expected_doi and isinstance(crossref, dict) and not crossref.get("error"):
        observed_doi = normalize_doi(crossref.get("doi"))
        if observed_doi and observed_doi != expected_doi:
            problems.append(f"Crossref returned DOI {observed_doi}, expected {expected_doi}.")

    if expected_doi and isinstance(pubmed, dict) and not pubmed.get("error"):
        observed_doi = normalize_doi(pubmed.get("doi"))
        if observed_doi and observed_doi != expected_doi:
            problems.append(f"PubMed record DOI {observed_doi} does not match expected DOI {expected_doi}.")
        elif not observed_doi:
            warnings.append("PubMed record did not expose a DOI for cross-checking.")

    expected_title = ref.get("title", "")
    title_scores = [
        title_similarity(expected_title, source.get("title", ""))
        for source in found_sources
        if source.get("title")
    ]
    best_title_score = max(title_scores) if title_scores else 0.0
    if expected_title and found_sources and best_title_score < 0.86:
        problems.append(f"Best title match was low ({best_title_score:.2f}).")
    elif expected_title and found_sources and best_title_score < 0.95:
        warnings.append(f"Title match is close but not exact ({best_title_score:.2f}).")

    expected_year = year_from_ref(ref)
    observed_years = {source.get("year", "") for source in found_sources if source.get("year")}
    if expected_year and observed_years and expected_year not in observed_years:
        warnings.append(f"Expected year {expected_year}; observed {', '.join(sorted(observed_years))}.")

    expected_author = normalize_text(first_author_family(ref))
    observed_authors = {
        normalize_text(first_author_family({"author": source.get("authors", [])}))
        for source in found_sources
        if source.get("authors")
    }
    if expected_author and observed_authors and expected_author not in observed_authors:
        warnings.append(
            f"Expected first author `{first_author_family(ref)}`; observed {', '.join(sorted(observed_authors))}."
        )

    if problems and not found_sources:
        status = "not_found"
    elif problems:
        status = "mismatch"
    elif warnings:
        status = "partial"
    else:
        status = "verified"

    return {
        "id": ref["id"],
        "status": status,
        "expected": {
            "doi": expected_doi,
            "pmid": expected_pmid,
            "title": ref.get("title", ""),
            "year": expected_year,
            "firstAuthor": first_author_family(ref),
        },
        "sources": {
            "pubmed": pubmed,
            "crossref": crossref,
        },
        "bestTitleSimilarity": round(best_title_score, 3),
        "warnings": warnings,
        "problems": problems,
        "notes": notes,
    }


def claim_support_ids(claim: dict[str, Any]) -> list[str]:
    support = claim.get("support")
    if support is None:
        return []
    if isinstance(support, list):
        return [str(item) for item in support]
    return [str(support)]


def abstract_record(reference_result: dict[str, Any]) -> dict[str, Any] | None:
    sources = reference_result.get("sources", {})
    for key in ["pubmed", "crossref"]:
        source = sources.get(key)
        if isinstance(source, dict) and source.get("abstract") and not source.get("error"):
            return source
    return None


def verify_claims(project: dict[str, Any], reference_results: dict[str, dict[str, Any]], depth: str) -> list[dict[str, Any]]:
    claim_results = []
    for claim in project.get("claims", []):
        support_ids = claim_support_ids(claim)
        evidence = []
        for support_id in support_ids:
            ref_result = reference_results.get(support_id)
            if not ref_result:
                evidence.append(
                    {
                        "support": support_id,
                        "status": "not_assessable",
                        "reason": "Citation key was not found in references.",
                    }
                )
                continue
            if depth != "abstract":
                evidence.append(
                    {
                        "support": support_id,
                        "status": "not_assessed",
                        "reason": "Run with --depth abstract or --verify abstract for abstract evidence.",
                    }
                )
                continue
            abstract_source = abstract_record(ref_result)
            if not abstract_source:
                evidence.append(
                    {
                        "support": support_id,
                        "status": "not_assessable",
                        "reason": "No abstract was available from PubMed or Crossref.",
                    }
                )
                continue
            abstract = abstract_source.get("abstract", "")
            evidence.append(
                {
                    "support": support_id,
                    "status": "needs_llm_review",
                    "reason": "Abstract fetched; semantic support classification should be performed by the harness/LLM.",
                    "source": abstract_source.get("source"),
                    "url": abstract_source.get("url"),
                    "title": abstract_source.get("title"),
                    "abstract": abstract,
                    "candidateSnippets": best_candidate_snippets(claim.get("claim", ""), abstract),
                }
            )
        claim_results.append(
            {
                "claim": claim.get("claim", ""),
                "support": support_ids,
                "declaredLevel": claim.get("level", "Not assessed"),
                "declaredNote": claim.get("note", ""),
                "evidence": evidence,
            }
        )
    return claim_results


def overall_status(reference_results: list[dict[str, Any]], claim_results: list[dict[str, Any]], depth: str) -> str:
    failed = {"mismatch", "not_found", "error"}
    if any(result.get("status") in failed for result in reference_results):
        return "failed"
    if depth == "abstract":
        for claim in claim_results:
            for evidence in claim.get("evidence", []):
                if evidence.get("status") == "not_assessable":
                    return "warnings"
    if any(result.get("status") == "partial" for result in reference_results):
        return "warnings"
    return "passed"


def md_escape(value: Any) -> str:
    return str(value if value is not None else "").replace("\n", " ").replace("|", "\\|")


def write_markdown_report(result: dict[str, Any], path: Path):
    lines = [
        "# Reference Verification Report",
        "",
        f"Project: `{result['project']}`",
        f"Depth: `{result['depth']}`",
        f"Overall status: `{result['overallStatus']}`",
        "",
        "## References",
        "",
        "| Key | Status | Sources | Notes |",
        "|---|---|---|---|",
    ]
    for ref in result["references"]:
        sources = []
        source_data = ref.get("sources", {})
        pubmed = source_data.get("pubmed")
        crossref = source_data.get("crossref")
        if isinstance(pubmed, dict) and not pubmed.get("error"):
            sources.append(f"PubMed PMID {pubmed.get('pmid', '')}".strip())
        if isinstance(crossref, dict) and not crossref.get("error"):
            sources.append(f"Crossref DOI {normalize_doi(crossref.get('doi'))}".strip())
        if not sources:
            sources.append("none")
        notes = ref.get("problems", []) + ref.get("warnings", []) + ref.get("notes", [])
        lines.append(
            f"| `{md_escape(ref['id'])}` | `{md_escape(ref['status'])}` | "
            f"{md_escape('; '.join(sources))} | {md_escape('; '.join(notes) or 'OK')} |"
        )

    if result.get("claims"):
        lines.extend(["", "## Claims", "", "| Claim | Citation key | Evidence status | Notes |", "|---|---|---|---|"])
        for claim in result["claims"]:
            for evidence in claim.get("evidence", []):
                snippets = evidence.get("candidateSnippets") or []
                note = evidence.get("reason", "")
                if snippets:
                    note = f"{note} Candidate snippet: {snippets[0]}"
                lines.append(
                    f"| {md_escape(claim.get('claim', ''))} | `{md_escape(evidence.get('support', ''))}` | "
                    f"`{md_escape(evidence.get('status', ''))}` | {md_escape(note)} |"
                )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `metadata` verification checks DOI/PMID existence and basic bibliographic consistency.",
            "- `abstract` verification fetches abstract evidence packets for harness/LLM review.",
            "- CLI abstract mode does not make final semantic support judgments by keyword overlap alone.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_project(
    project: dict[str, Any],
    out_dir: Path,
    depth: str = "metadata",
    email: str | None = None,
    client: MetadataClient | None = None,
) -> dict[str, Any]:
    if depth not in {"metadata", "abstract"}:
        raise ValueError("Verification depth must be `metadata` or `abstract`.")

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = verification_paths(out_dir)
    client = client or MetadataClient(contact_email(email))

    references = [verify_reference(ref, client) for ref in project.get("references", [])]
    reference_results = {ref["id"]: ref for ref in references}
    claims = verify_claims(project, reference_results, depth)
    result = {
        "project": project["slug"],
        "depth": depth,
        "generatedAtUnix": int(time.time()),
        "overallStatus": overall_status(references, claims, depth),
        "references": references,
        "claims": claims,
        "paths": {
            "json": str(paths.json),
            "report": str(paths.report),
        },
    }
    paths.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown_report(result, paths.report)
    return result
