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
- recall metrics
- failure examples

## Required comparisons

| Test | Purpose | Status |
|---|---|---|
| Plain lexical RAG baseline | Shows whether RALG improves over a simple retrieval pipeline | Needed |
| Current RALG pipeline | Measures the actual project system | In progress |
| Domain technical-doc benchmark | Tests the target startup use case | Needed |
| Unsupported-question set | Measures abstention/refusal quality | Needed |
| False-premise set | Measures resistance to wrong assumptions | Needed |
| Latency and memory report | Shows practical deployability | Needed |

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
