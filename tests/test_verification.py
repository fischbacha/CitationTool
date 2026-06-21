from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from citationtool.verification import parse_pubmed_xml, verify_project, verify_reference


def sample_ref(**overrides):
    ref = {
        "id": "smith-2024",
        "type": "article-journal",
        "title": "B cells aggravate metabolic liver inflammation",
        "container-title": "Example Journal",
        "author": [{"family": "Smith", "given": "A"}],
        "issued": {"date-parts": [[2024]]},
        "DOI": "10.1000/example",
        "PMID": "123456",
    }
    ref.update(overrides)
    return ref


def pubmed_record(**overrides):
    record = {
        "source": "PubMed",
        "pmid": "123456",
        "doi": "10.1000/example",
        "title": "B cells aggravate metabolic liver inflammation",
        "journal": "Example Journal",
        "year": "2024",
        "authors": [{"family": "Smith", "given": "A"}],
        "abstract": "B cells aggravate metabolic liver inflammation in experimental disease.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
    }
    record.update(overrides)
    return record


def crossref_record(**overrides):
    record = {
        "source": "Crossref",
        "doi": "10.1000/example",
        "title": "B cells aggravate metabolic liver inflammation",
        "journal": "Example Journal",
        "year": "2024",
        "authors": [{"family": "Smith", "given": "A"}],
        "abstract": "",
        "url": "https://doi.org/10.1000/example",
    }
    record.update(overrides)
    return record


class StubClient:
    def __init__(self, pubmed_by_pmid=None, pubmed_by_doi=None, crossref_by_doi=None):
        self.pubmed_by_pmid = pubmed_by_pmid or {}
        self.pubmed_by_doi = pubmed_by_doi or {}
        self.crossref_by_doi = crossref_by_doi or {}

    def fetch_pubmed_by_pmid(self, pmid):
        return self.pubmed_by_pmid.get(pmid)

    def fetch_pubmed_by_doi(self, doi):
        return self.pubmed_by_doi.get(doi.lower())

    def fetch_crossref_by_doi(self, doi):
        return self.crossref_by_doi.get(doi.lower())


class VerificationTests(unittest.TestCase):
    def test_doi_and_pmid_match(self):
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record()},
            crossref_by_doi={"10.1000/example": crossref_record()},
        )

        result = verify_reference(sample_ref(), client)

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["bestTitleSimilarity"], 1.0)

    def test_doi_pmid_mismatch(self):
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record(doi="10.1000/different")},
            crossref_by_doi={"10.1000/example": crossref_record()},
        )

        result = verify_reference(sample_ref(), client)

        self.assertEqual(result["status"], "mismatch")
        self.assertTrue(any("does not match" in problem for problem in result["problems"]))

    def test_doi_found_only_in_crossref(self):
        ref = sample_ref(PMID="")
        client = StubClient(crossref_by_doi={"10.1000/example": crossref_record()})

        result = verify_reference(ref, client)

        self.assertEqual(result["status"], "verified")
        self.assertIsNone(result["sources"]["pubmed"])
        self.assertEqual(result["sources"]["crossref"]["doi"], "10.1000/example")

    def test_pmid_found_only_in_pubmed(self):
        ref = sample_ref(DOI="")
        client = StubClient(pubmed_by_pmid={"123456": pubmed_record(doi="")})

        result = verify_reference(ref, client)

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["sources"]["pubmed"]["pmid"], "123456")
        self.assertIsNone(result["sources"]["crossref"])

    def test_missing_abstract_becomes_claim_warning(self):
        project = {
            "slug": "missing_abstract",
            "references": [sample_ref()],
            "paragraphs": [[{"text": "Claim "}, {"cite": "smith-2024"}, {"text": "."}]],
            "claims": [{"claim": "B cells aggravate inflammation.", "support": "smith-2024"}],
        }
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record(abstract="")},
            crossref_by_doi={"10.1000/example": crossref_record(abstract="")},
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = verify_project(project, Path(tmp), depth="abstract", client=client)

        self.assertEqual(result["overallStatus"], "warnings")
        self.assertEqual(result["claims"][0]["evidence"][0]["status"], "not_assessable")

    def test_abstract_evidence_packet_is_written(self):
        project = {
            "slug": "abstract_evidence",
            "references": [sample_ref()],
            "paragraphs": [[{"text": "Claim "}, {"cite": "smith-2024"}, {"text": "."}]],
            "claims": [{"claim": "B cells aggravate metabolic liver inflammation.", "support": "smith-2024"}],
        }
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record()},
            crossref_by_doi={"10.1000/example": crossref_record()},
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = verify_project(project, Path(tmp), depth="abstract", client=client)
            json_path = Path(result["paths"]["json"])
            report_path = Path(result["paths"]["report"])
            support_review_path = Path(result["paths"]["supportReview"])
            self.assertTrue(json_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(support_review_path.exists())
            saved = json.loads(json_path.read_text(encoding="utf-8"))

        evidence = saved["claims"][0]["evidence"][0]
        self.assertEqual(result["overallStatus"], "passed")
        self.assertEqual(evidence["status"], "supported")
        self.assertEqual(evidence["confidence"], "high")
        self.assertTrue(evidence["candidateSnippets"])
        self.assertTrue(evidence["scoredCandidateSnippets"])

    def test_metadata_depth_marks_claims_as_metadata_only(self):
        project = {
            "slug": "metadata_claims",
            "references": [sample_ref()],
            "paragraphs": [[{"text": "Claim "}, {"cite": "smith-2024"}, {"text": "."}]],
            "claims": [{"claim": "B cells aggravate metabolic liver inflammation.", "support": "smith-2024"}],
        }
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record()},
            crossref_by_doi={"10.1000/example": crossref_record()},
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = verify_project(project, Path(tmp), depth="metadata", client=client)

        evidence = result["claims"][0]["evidence"][0]
        self.assertEqual(evidence["status"], "metadata_only")
        self.assertNotIn("supportReview", result["paths"])

    def test_weak_abstract_support_gets_safer_claim_suggestion(self):
        project = {
            "slug": "weak_support",
            "references": [sample_ref()],
            "paragraphs": [[{"text": "Claim "}, {"cite": "smith-2024"}, {"text": "."}]],
            "claims": [
                {
                    "claim": "B cells drive liver fibrosis, cirrhosis, and hepatocellular carcinoma in human NASH.",
                    "support": "smith-2024",
                }
            ],
        }
        client = StubClient(
            pubmed_by_pmid={"123456": pubmed_record(abstract="B cells are associated with liver inflammation in NASH.")},
            crossref_by_doi={"10.1000/example": crossref_record()},
        )

        with tempfile.TemporaryDirectory() as tmp:
            result = verify_project(project, Path(tmp), depth="abstract", client=client)
            review = Path(result["paths"]["supportReview"]).read_text(encoding="utf-8")

        evidence = result["claims"][0]["evidence"][0]
        self.assertEqual(result["overallStatus"], "warnings")
        self.assertEqual(evidence["status"], "partially_supported")
        self.assertIn("Candidate safer wording", evidence["saferClaim"])
        self.assertIn("partially_supported", review)

    def test_pubmed_parser_prefers_journal_issue_year(self):
        xml = """<?xml version="1.0" ?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>1</PMID>
      <Article>
        <Journal>
          <JournalIssue>
            <PubDate><Year>2014</Year></PubDate>
          </JournalIssue>
          <Title>Example Journal</Title>
        </Journal>
        <ArticleTitle>Example title</ArticleTitle>
        <ArticleDate><Year>2013</Year></ArticleDate>
        <AuthorList>
          <Author><LastName>Smith</LastName><ForeName>A</ForeName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">1</ArticleId>
        <ArticleId IdType="doi">10.1000/example</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""

        parsed = parse_pubmed_xml(xml)

        self.assertEqual(parsed["year"], "2014")


if __name__ == "__main__":
    unittest.main()
