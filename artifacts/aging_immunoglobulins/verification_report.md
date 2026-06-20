# Reference Verification Report

Project: `aging_immunoglobulins`
Depth: `abstract`
Overall status: `passed`

## References

| Key | Status | Sources | Notes |
|---|---|---|---|
| `blomberg-2013` | `verified` | PubMed PMID 24203437; Crossref DOI 10.1007/s12026-013-8440-9 | OK |
| `frasca-2016` | `verified` | PubMed PMID 27108193; Crossref DOI 10.1016/j.vaccine.2016.04.023 | OK |
| `kristic-2014` | `verified` | PubMed PMID 24325898; Crossref DOI 10.1093/gerona/glt190 | OK |
| `kyle-2006` | `verified` | PubMed PMID 16571879; Crossref DOI 10.1056/nejmoa054494 | OK |

## Claims

| Claim | Citation key | Evidence status | Notes |
|---|---|---|---|
| Aging is linked to reduced immunoglobulin class switching, lower activation-induced cytidine deaminase, and impaired affinity maturation in mouse and human B-cell biology. | `blomberg-2013` | `needs_llm_review` | Abstract fetched; semantic support classification should be performed by the harness/LLM. Candidate snippet: These include decreases in immunoglobulin (Ig) class switch (e.g., IgM to IgG), decreases in the enzyme AID (activation-induced cytidine deaminase) and decreases in the transcription factor E47. |
| After repeated influenza immunizations, elderly adults can maintain memory B-cell generation while the antibody response is not maintained. | `frasca-2016` | `needs_llm_review` | Abstract fetched; semantic support classification should be performed by the harness/LLM. Candidate snippet: We have previously shown that the in vivo antibody response to a new influenza vaccine, the ex vivo plasmablast response, the in vitro B cell function, measured by AID (activation-induced cytidine deaminase), and the transcription factor E47, are significantly associated and decreased in elderly individuals. |
| IgG N-glycan profiles can serve as biomarkers of chronological and biological age. | `kristic-2014` | `needs_llm_review` | Abstract fetched; semantic support classification should be performed by the harness/LLM. Candidate snippet: Several IgG glycans (including FA2B, FA2G2, and FA2BG2) changed considerably with age and the combination of these three glycans can explain up to 58% of variance in chronological age, significantly more than other markers of biological age like telomere lengths. |
| Monoclonal gammopathy of undetermined significance reflects a circulating monoclonal immunoglobulin state whose prevalence increases with age. | `kyle-2006` | `needs_llm_review` | Abstract fetched; semantic support classification should be performed by the harness/LLM. Candidate snippet: BACKGROUND: The prevalence of monoclonal gammopathy of undetermined significance (MGUS), a premalignant plasma-cell disorder, among persons 50 years of age or older has not been accurately determined. |

## Interpretation

- `metadata` verification checks DOI/PMID existence and basic bibliographic consistency.
- `abstract` verification fetches abstract evidence packets for harness/LLM review.
- CLI abstract mode does not make final semantic support judgments by keyword overlap alone.
