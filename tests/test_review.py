from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from citationtool.review import apply_review, candidate_from_safer_claim


def sample_project():
    return {
        "slug": "demo",
        "title": "Demo",
        "output_dir": "artifacts/demo",
        "references": [
            {
                "id": "smith-2024",
                "type": "article-journal",
                "title": "Example",
                "author": [{"family": "Smith", "given": "A"}],
                "issued": {"date-parts": [[2024]]},
                "DOI": "10.1000/example",
                "PMID": "123456",
            }
        ],
        "paragraphs": [
            [
                {"text": "Old broad claim about fibrosis and disease causality "},
                {"cite": "smith-2024"},
                {"text": "."},
            ]
        ],
        "claims": [
            {
                "claim": "Old broad claim about fibrosis and disease causality.",
                "support": "smith-2024",
                "level": "Supported",
                "note": "Original note.",
            }
        ],
    }


class ApplyReviewTests(unittest.TestCase):
    def test_candidate_from_safer_claim_extracts_sentence(self):
        result = candidate_from_safer_claim("Candidate safer wording: B cells are associated with inflammation")

        self.assertEqual(result, "B cells are associated with inflammation.")

    def test_apply_review_rewrites_claim_and_paragraph(self):
        project = sample_project()
        verification = {
            "overallStatus": "warnings",
            "paths": {"json": "reference_verification.json"},
            "claims": [
                {
                    "claim": "Old broad claim about fibrosis and disease causality.",
                    "evidence": [
                        {
                            "support": "smith-2024",
                            "status": "partially_supported",
                            "confidence": "low",
                            "reason": "The abstract supports a narrower wording.",
                            "saferClaim": "Candidate safer wording: Fibrosis is associated with extracellular matrix accumulation.",
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            result = apply_review(
                raw_project=project,
                loaded_project=project,
                verification_result=verification,
                out_spec=Path(tmp) / "reviewed.json",
                report_path=Path(tmp) / "apply_review_report.md",
            )

            self.assertTrue(result.out_spec.exists())
            self.assertTrue(result.report.exists())

        revised = result.project
        self.assertEqual(revised["slug"], "demo_reviewed")
        self.assertEqual(
            revised["claims"][0]["claim"],
            "Fibrosis is associated with extracellular matrix accumulation.",
        )
        self.assertEqual(
            revised["paragraphs"][0][0]["text"],
            "Fibrosis is associated with extracellular matrix accumulation ",
        )
        self.assertEqual(result.actions[0]["action"], "claim_and_paragraph_rewritten")
        self.assertIn("original claim", revised["claims"][0]["note"])

    def test_apply_review_flags_not_assessable_without_rewrite(self):
        project = sample_project()
        verification = {
            "overallStatus": "warnings",
            "paths": {"json": "reference_verification.json"},
            "claims": [
                {
                    "claim": "Old broad claim about fibrosis and disease causality.",
                    "evidence": [
                        {
                            "support": "smith-2024",
                            "status": "not_assessable",
                            "confidence": "none",
                            "reason": "No abstract was available.",
                            "saferClaim": "Inspect the full text manually, replace the citation with one that has an abstract, or soften/remove the claim.",
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            result = apply_review(
                raw_project=project,
                loaded_project=project,
                verification_result=verification,
                out_spec=Path(tmp) / "reviewed.json",
                report_path=Path(tmp) / "apply_review_report.md",
            )

        revised = result.project
        self.assertEqual(revised["claims"][0]["claim"], "Old broad claim about fibrosis and disease causality.")
        self.assertEqual(revised["paragraphs"][0][0]["text"], "Old broad claim about fibrosis and disease causality ")
        self.assertEqual(result.actions[0]["action"], "flagged_no_rewrite")
        self.assertIn("not_assessable", revised["claims"][0]["level"])


if __name__ == "__main__":
    unittest.main()
