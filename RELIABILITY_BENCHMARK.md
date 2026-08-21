# RALG End-to-End Reliability Benchmark

Run at: 2026-08-21 16:50:20
Target: current `/query` behavior of `src/api_server.py`
API: `http://127.0.0.1:8000` (top_k=5)

## Summary

- Total cases: 50
- Expected supported: 26 / Expected unsupported: 24
- Passed: 38 / Failed: 12
- Actual supported: 26 / Actual unsupported: 24

## Scores

- **Supported-answer correctness**: 65.4% (17/26)
- **Unsupported rejection rate**: 87.5% (21/24)
- **False-support rate**: 12.5% (3 cases)
- **False-rejection rate**: 11.5% (3 cases)
- **Average latency**: 858 ms (p50 944 ms, p95 1589 ms)
- **Runtime/API errors**: 0

## Targets

- `supported_correctness_ge_90`: FAIL
- `rejection_rate_ge_95`: FAIL
- `false_support_rate_le_5`: FAIL
- `false_rejection_rate_le_5`: FAIL
- `api_errors_zero`: PASS

## Failures by type

- **false_rejection** (3): sop_003, sop_005, sop_006
- **false_support** (3): mislead_003, mislead_004, mislead_007
- **wrong_content** (6): para_005, sop_001, sop_002, sop_004, rt_002, rt_003

## Per-category breakdown

| Category | Total | Passed | Failed | Supported | Unsupported |
|---|---|---|---|---|---|
| supported_factual | 8 | 8 | 0 | 8 | 0 |
| paraphrased | 5 | 4 | 1 | 5 | 0 |
| sop_procedure | 6 | 0 | 6 | 3 | 3 |
| unsupported | 8 | 8 | 0 | 0 | 8 |
| false_premise | 7 | 7 | 0 | 0 | 7 |
| misleading_keyword_overlap | 7 | 4 | 3 | 3 | 4 |
| runtime_ingested | 5 | 3 | 2 | 3 | 2 |
| existing_kb_regression | 4 | 4 | 0 | 4 | 0 |

## Failed cases (details)

| Test ID | Question | Expected | Actual answer | Supported | Answer type | Confidence | Top source score | Failure reason |
|---|---|---|---|---|---|---|---|---|
| para_005 | Describe the organization of the Roman army. | supported | The organization of the Roman army was organized around legions. Each legion was | True | structure | N/A | 26.54 | wrong_content |
| sop_001 | What must be done before starting compressor maintenance? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 52.02 | wrong_content |
| sop_002 | What are the restart steps after compressor maintenance? | supported | BEFORE STARTING - De-energize the compressor unit at the main disconnect. | True | api_extractive_fallback | 0.70 | 51.68 | wrong_content |
| sop_003 | How should belt tension be verified during inspection? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 23.44 | false_rejection |
| sop_004 | What oil should be used for compressor lubrication? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 58.11 | wrong_content |
| sop_005 | What must be checked during the inspection phase? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 31.50 | false_rejection |
| sop_006 | What should be done with the old oil when draining it? | supported | I couldn't find enough reliable evidence in the current knowledge base. | False | system | N/A | 31.44 | false_rejection |
| mislead_003 | What are the compressor lockout steps for DNA replication? | unsupported | The majority of eukaryotic genes are stored on a set of large , linear chromosom | True | api_extractive_fallback | 0.70 | 48.30 | false_support |
| mislead_004 | Describe the Magna Carta compressor maintenance procedure. | unsupported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1. | True | api_extractive_fallback | 0.70 | 58.15 | false_support |
| mislead_007 | What is the lockout procedure for the 38th Engineer Battalion's electr | unsupported | The 38th Engineer Battalion 's electrical group studied the batteries , the elec | True | api_extractive_fallback | 0.70 | 43.72 | false_support |
| rt_002 | What is the lockout/tagout procedure for compressor maintenance? | supported | STANDARD OPERATING PROCEDURE: COMPRESSOR MAINTENANCE 1 | True | factual | 0.60 | 78.89 | wrong_content |
| rt_003 | What oil specification is required for compressor lubrication? | supported | BEFORE STARTING - De-energize the compressor unit at the main disconnect. | True | api_extractive_fallback | 0.70 | 58.11 | wrong_content |
