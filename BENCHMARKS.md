# Benchmarks

This file tracks the evidence needed before RALG can make serious technical or commercial claims.

## Benchmark principle

RALG should not claim to beat normal RAG, larger systems, or commercial tools without fair, repeatable tests.

Every benchmark should report:

- dataset/domain
- number of questions
- baseline used
- RALG version/commit
- hardware
- latency
- RAM/VRAM usage
- accuracy
- support/grounding score
- Recall@1, Recall@3, Recall@5, and MRR
- failure examples

## New proof runner

A first lightweight retrieval proof runner is available:

```bash
python src/retrieval_proof_v1.py --dataset data/technical_doc_benchmark_v1.jsonl
```

It compares:

- `baseline_v2`: existing lexical retrieval path
- `ralg_v4`: query-planned RALG retrieval path

It writes JSON results to:

```text
logs/retrieval_proof_v1_results.json
```

This runner does not require the trained generation checkpoint. It tests retrieval quality first, because weak retrieval makes answer generation unreliable no matter how good the final answer layer is.

## Required comparisons

| Test | Purpose | Status |
|---|---|---|
| Plain lexical RAG baseline | Shows whether RALG improves over a simple retrieval pipeline | Added in `retrieval_proof_v1.py` |
| Current RALG pipeline | Measures the actual project retrieval path | Added in `retrieval_proof_v1.py` |
| Domain technical-doc benchmark | Tests the target startup use case | Seed JSONL added |
| Unsupported-question set | Measures abstention/refusal quality | Seed cases added |
| False-premise set | Measures resistance to wrong assumptions | Seed case added |
| Latency report | Shows practical deployability | Added |
| Memory report | Shows practical deployability | Still needed |

## Minimum public milestone

Before pitching this as a serious technical advantage, the repo should include at least one narrow benchmark where RALG shows:

- supported-answer accuracy of 80% or higher in the chosen domain
- clear improvement over a plain baseline
- acceptable latency on modest hardware
- examples of both successes and failures
- repeatable commands so another person can run the test

## Current caution

Current benchmark claims should be written carefully. If a test result is weak, publish it honestly and use it to guide the roadmap.

Bad claim:

> RALG is better than normal RAG.

Good claim:

> RALG is being evaluated against plain RAG. Current work is focused on retrieval quality, grounding, and domain-specific reliability.
