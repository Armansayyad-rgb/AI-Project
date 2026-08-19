# Benchmark Results

This file records public benchmark runs for RALG Engine.

## Retrieval proof v1 — 50-case synthetic technical document benchmark

Date: 2026-08-19  
Command:

```powershell
python src\retrieval_proof_v1.py --dataset data\technical_doc_benchmark_v1.jsonl --knowledge-file data\technical_docs_sample.txt
```

Dataset:

- 50 total cases
- 41 supported technical-document questions
- 9 unsupported / false-premise questions
- synthetic sample corpus at `data/technical_docs_sample.txt`
- corpus size: 41 chunks

## Summary

| System | Cases | Recall@1 | Recall@3 | Recall@5 | MRR | Unsupported rejection@5 | Accuracy@5 | Avg latency | P95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_v2 | 50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.30 ms | 0.57 ms |
| ralg_v4 | 50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.93 ms | 6.53 ms |

## Interpretation

This benchmark proves the retrieval proof runner works on a larger synthetic technical-document set.

Current finding:

- baseline_v2 and ralg_v4 tie on accuracy, recall, MRR, and unsupported rejection
- ralg_v4 is slower than baseline on this benchmark
- this benchmark is still synthetic and mostly direct lookup, so it does not yet prove a RALG advantage

## Commercial meaning

This is a useful engineering checkpoint, not a commercial proof yet.

The project can now show:

- repeatable benchmark command
- baseline-vs-RALG comparison
- technical-document dataset structure
- supported and unsupported question scoring
- false-premise contradiction scoring

The project still needs:

- harder multi-hop questions
- larger/noisier corpus
- confusing near-match documents
- real or realistic manuals/SOPs
- a benchmark where query planning provides measurable value

## Next benchmark milestone

Create a harder v2 benchmark where plain lexical retrieval is expected to struggle.

Needed additions:

- distractor documents with similar terms
- questions that require two evidence chunks
- comparison questions across two procedures
- false-premise questions with subtle contradiction
- unsupported questions that share many keywords with real documents
- latency/accuracy tradeoff analysis

Minimum target before making strong claims:

- RALG must beat baseline on at least one meaningful metric, or it should be described only as experimental.


## Retrieval proof v1 — hard synthetic technical document benchmark

Date: 2026-08-19  
Command:

```powershell
python src\retrieval_proof_v1.py --dataset data\technical_doc_benchmark_hard_v1.jsonl --knowledge-file data\technical_docs_hard_sample.txt
```

Dataset:

- 50 total cases
- 39 supported technical-document questions
- 11 unsupported / false-premise questions
- distractor documents included
- comparison and multi-evidence cases included
- synthetic hard corpus at `data/technical_docs_hard_sample.txt`
- corpus size: 51 chunks

## Hard benchmark summary

| System | Cases | Recall@1 | Recall@3 | Recall@5 | MRR | Unsupported rejection@5 | Accuracy@5 | Avg latency | P95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_v2 | 50 | 0.9231 | 1.00 | 1.00 | 0.9615 | 1.00 | 1.00 | 0.34 ms | 0.62 ms |
| ralg_v4 | 50 | 0.9231 | 1.00 | 1.00 | 0.9615 | 1.00 | 1.00 | 2.19 ms | 5.55 ms |

## Hard benchmark interpretation

The hard benchmark is more useful than the first 50-case direct benchmark because Recall@1 dropped below 100%, meaning distractors are starting to matter.

Current finding:

- baseline_v2 and ralg_v4 still tie on all quality metrics
- ralg_v4 remains slower
- current query planning does not yet create a measurable retrieval advantage on this benchmark
- the next engineering task is to inspect the Recall@1 misses and design cases or retrieval improvements where planned multi-query retrieval beats plain lexical retrieval

