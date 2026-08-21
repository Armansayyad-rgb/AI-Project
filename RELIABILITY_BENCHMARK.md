# RALG End-to-End Reliability Benchmark

> Baseline engineering report for the current RALG API. This document records measured behavior; it is not a marketing claim.

**Run timestamp:** 2026-08-21 16:50:20  
**Target:** current `/query` behavior in `src/api_server.py`  
**API:** `http://127.0.0.1:8000`  
**Retrieval setting:** `top_k=5`

## Executive Summary

RALG completed all 50 benchmark requests without a runtime or API error, which confirms that the current API path is operational and stable under this test set. However, the system did **not** meet the internal reliability gate for customer-demo readiness.

The strongest areas were ordinary factual QA, unsupported-query rejection, false-premise handling, and existing knowledge-base regression. The weakest area was procedural/SOP answering, where all 6 cases failed. The current extractive fallback also produced 3 false-support cases under adversarial keyword-overlap prompts.

### Overall Result

**Status: FAIL — reliability gate not yet met**

| Measure | Result |
|---|---:|
| Total test cases | 50 |
| Passed | 38 |
| Failed | 12 |
| Expected supported | 26 |
| Expected unsupported | 24 |
| Actual supported | 26 |
| Actual unsupported | 24 |
| Runtime/API errors | 0 |

## Reliability Metrics

| Metric | Measured result | Internal target | Status |
|---|---:|---:|---|
| Supported-answer correctness | **65.4%** (17/26) | >= 90% | **FAIL** |
| Unsupported rejection rate | **87.5%** (21/24) | >= 95% | **FAIL** |
| False-support rate | **12.5%** (3 cases) | <= 5% | **FAIL** |
| False-rejection rate | **11.5%** (3 cases) | <= 5% | **FAIL** |
| Runtime/API errors | **0** | 0 | **PASS** |

### Latency

| Metric | Result |
|---|---:|
| Average latency | 858 ms |
| p50 latency | 944 ms |
| p95 latency | 1589 ms |

Latency is recorded here as a baseline measurement only. This benchmark did not define an explicit latency pass/fail threshold.

## Category Breakdown

| Category | Total | Passed | Failed | Pass rate |
|---|---:|---:|---:|---:|
| Supported factual | 8 | 8 | 0 | 100% |
| Paraphrased | 5 | 4 | 1 | 80% |
| SOP / procedure | 6 | 0 | 6 | 0% |
| Unsupported | 8 | 8 | 0 | 100% |
| False premise | 7 | 7 | 0 | 100% |
| Misleading keyword overlap | 7 | 4 | 3 | 57.1% |
| Runtime ingested | 5 | 3 | 2 | 60% |
| Existing KB regression | 4 | 4 | 0 | 100% |

## Failure Summary

The 12 failures fall into three groups:

- **Wrong content (6):** `para_005`, `sop_001`, `sop_002`, `sop_004`, `rt_002`, `rt_003`
- **False rejection (3):** `sop_003`, `sop_005`, `sop_006`
- **False support (3):** `mislead_003`, `mislead_004`, `mislead_007`

### Primary Engineering Findings

1. **Procedural/SOP extraction is the largest weakness.** The retriever often finds the correct document with a strong source score, but the answer-selection layer returns a heading, the wrong procedural step, or abstains despite relevant evidence being present.
2. **Keyword overlap is currently too permissive for fallback support.** Three adversarial prompts were marked supported even though the requested relationship or procedure did not exist in the source material.
3. **Runtime ingestion works, but answer selection after ingestion is not yet reliable enough.** Three of five runtime-ingested cases passed; two returned incorrect content.
4. **Core regression behavior remains strong in this test set.** Supported factual, unsupported, false-premise, and existing-KB regression categories all achieved 100% pass rates.

These findings identify answer selection and grounding as the next engineering focus. They do not justify changing the benchmark or hardcoding benchmark-specific rules.

## Failed Cases

| Test ID | Category | Question | Expected | Actual answer | Supported | Answer type | Confidence | Top source score | Failure |
|---|---|---|---|---|---|---|---:|---:|---|
| `para_005` | paraphrased | Describe the organization of the Roman army. | supported | The organization of the Roman army was organized around legions. Each legion was | True | structure | N/A | 26.54 | wrong_content |
| `sop_001` | sop_procedure | What must be done before starting compressor maintenance? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 52.02 | wrong_content |
| `sop_002` | sop_procedure | What are the restart steps after compressor maintenance? | supported | BEFORE STARTING - De-energize the compressor unit at the main disconnect. | True | api_extractive_fallback | 0.70 | 51.68 | wrong_content |
| `sop_003` | sop_procedure | How should belt tension be verified during inspection? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 23.44 | false_rejection |
| `sop_004` | sop_procedure | What oil should be used for compressor lubrication? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 58.11 | wrong_content |
| `sop_005` | sop_procedure | What must be checked during the inspection phase? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 31.50 | false_rejection |
| `sop_006` | sop_procedure | What should be done with the old oil when draining it? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 31.44 | false_rejection |
| `mislead_003` | misleading_keyword_overlap | What are the compressor lockout steps for DNA replication? | unsupported | The majority of eukaryotic genes are stored on a set of large, linear chromosomes... | True | api_extractive_fallback | 0.70 | 48.30 | false_support |
| `mislead_004` | misleading_keyword_overlap | Describe the Magna Carta compressor maintenance procedure. | unsupported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 58.15 | false_support |
| `mislead_007` | misleading_keyword_overlap | What is the lockout procedure for the 38th Engineer Battalion's electrical group? | unsupported | The 38th Engineer Battalion's electrical group studied the batteries, the electrical... | True | api_extractive_fallback | 0.70 | 43.72 | false_support |
| `rt_002` | runtime_ingested | What is the lockout/tagout procedure for compressor maintenance? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1 | True | factual | 0.60 | 78.89 | wrong_content |
| `rt_003` | runtime_ingested | What oil specification is required for compressor lubrication? | supported | BEFORE STARTING - De-energize the compressor unit at the main disconnect. | True | api_extractive_fallback | 0.70 | 58.11 | wrong_content |

## Reliability Gate

The current build is **not yet approved as the first customer-demo candidate** under the internal reliability criteria.

Before promoting a future build past this gate, rerun the same benchmark and require all of the following:

- Supported-answer correctness >= 90%
- Unsupported rejection rate >= 95%
- False-support rate <= 5%
- False-rejection rate <= 5%
- Runtime/API errors = 0
- No regression in previously passing benchmark categories

## Recommended Next Engineering Work

The next iteration should remain narrow and measurable:

1. Improve procedural answer extraction so headings are not selected as answers when a more specific step or specification exists.
2. Strengthen grounding before applying `api_extractive_fallback`, especially for mixed-domain or relationship-mismatch prompts.
3. Preserve the current strong false-premise and unsupported-query behavior.
4. Rerun this exact 50-case benchmark after each production change.
5. Compare results against this report rather than replacing or weakening the benchmark.

## Benchmark Integrity

This benchmark is intended as an engineering regression instrument. Production code should not contain benchmark-specific answers, entity exceptions, test IDs, or rules designed only to make these cases pass.

Future improvements should be generalizable and validated with additional independent questions before being treated as product-level evidence.
