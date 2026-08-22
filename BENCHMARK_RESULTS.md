# Benchmark Results

This file records public benchmark runs for RALG Engine. Results below are engineering evidence, not commercial performance claims.

> **Important:** these runs were produced at different points in development. Do not treat values from different runs as one simultaneous result. The datasets are synthetic and hand-designed; independent or real-world validation is still required.

## Current interpretation

The public retrieval benchmarks currently establish three things:

1. the evaluation runner is repeatable on 50-case technical-document datasets;
2. RALG can match a simple lexical baseline on the direct synthetic benchmark; and
3. some historical hard-benchmark runs showed improved top-rank ordering, but that advantage has not yet been established as stable across subsequent versions.

Accordingly, the safe public claim is **not** that RALG is superior to conventional RAG. The safe claim is that RALG has a reproducible evaluation framework and has shown promising ranking behavior on synthetic distractor-heavy cases that still requires broader validation.

---

## Direct synthetic benchmark

**Date:** 2026-08-19  
**Command:**

```powershell
python src\retrieval_proof_v1.py --dataset data\technical_doc_benchmark_v1.jsonl --knowledge-file data\technical_docs_sample.txt
```

**Dataset:**

- 50 total cases
- 41 supported technical-document questions
- 9 unsupported / false-premise questions
- synthetic sample corpus at `data/technical_docs_sample.txt`
- corpus size: 41 chunks

| System | Cases | Recall@1 | Recall@3 | Recall@5 | MRR | Unsupported rejection@5 | Accuracy@5 | Avg latency | P95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_v2 | 50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.30 ms | 0.57 ms |
| ralg_v4 | 50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.93 ms | 6.53 ms |

### Interpretation

- baseline_v2 and ralg_v4 tie on accuracy, recall, MRR, and unsupported rejection;
- ralg_v4 is slower on this benchmark; and
- because the set is synthetic and mostly direct lookup, it does not demonstrate a RALG advantage.

---

## Hard synthetic benchmark

**Date:** 2026-08-19  
**Command:**

```powershell
python src\retrieval_proof_v1.py --dataset data\technical_doc_benchmark_hard_v1.jsonl --knowledge-file data\technical_docs_hard_sample.txt
```

**Dataset:**

- 50 total cases
- 39 supported technical-document questions
- 11 unsupported / false-premise questions
- distractor documents included
- comparison and multi-evidence cases included
- synthetic hard corpus at `data/technical_docs_hard_sample.txt`
- corpus size: 51 chunks

### Recorded hard-benchmark runs

| Run | baseline Recall@1 | RALG Recall@1 | baseline MRR | RALG MRR | Accuracy@5 | Notes |
|---|---:|---:|---:|---:|---:|---|
| Earlier V4 run | 0.9231 | 1.00 | 0.9615 | 1.00 | 1.00 both | First measured top-rank improvement on distractors |
| V4.2 rerun after `343ea0e` | 0.9231 | 0.9231 | not separately recorded | not separately recorded | 1.00 both | Earlier top-rank advantage was not preserved in this rerun |

For the earlier V4 run, latency was:

- baseline_v2 average: 0.32 ms
- ralg_v4 average: 2.27 ms
- ralg_v4 P95: 6.44 ms

### Interpretation

The hard benchmark is more useful than the direct benchmark because distractors affect first-rank retrieval. One historical V4 run placed the correct evidence first in cases where the lexical baseline left it at rank 2. A later V4.2 rerun did not preserve that Recall@1 advantage.

This means **there is promising evidence, but no stable superiority claim yet**.

---

## Reliability benchmark

End-to-end API reliability is tracked separately in [RELIABILITY_BENCHMARK.md](RELIABILITY_BENCHMARK.md). Retrieval metrics and end-to-end answer reliability should not be conflated: a correct document in the top-k does not guarantee a correct supported answer.

---

## Commercial meaning

These benchmarks are useful engineering checkpoints. They demonstrate:

- repeatable benchmark commands;
- baseline-vs-RALG comparison;
- supported and unsupported question scoring;
- false-premise testing;
- distractor, comparison, and multi-evidence cases; and
- measurable latency tradeoffs.

They do **not** yet establish production readiness or a general technical advantage.

## Next benchmark milestone

Before making stronger claims, evaluate on a larger and less hand-designed corpus with:

- realistic manuals and SOPs;
- confusing near-match documents;
- multi-hop questions requiring multiple evidence chunks;
- unsupported questions with strong lexical overlap;
- fixed datasets that are not tuned after seeing failures;
- memory and latency measurements; and
- ideally an external or held-out evaluation set.

A stronger claim should be made only if RALG consistently beats the baseline on a meaningful quality metric without unacceptable reliability or latency regressions.
