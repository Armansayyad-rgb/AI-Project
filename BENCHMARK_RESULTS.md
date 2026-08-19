# Benchmark Results

This file records public benchmark runs for RALG Engine.

## Retrieval proof v1 — synthetic technical document sample

Date: 2026-08-19  
Command:

```powershell
python src\retrieval_proof_v1.py --dataset data\technical_doc_benchmark_v1.jsonl --knowledge-file data\technical_docs_sample.txt
```

Dataset:

- 5 total cases
- 3 supported technical-document questions
- 2 unsupported / false-premise questions
- synthetic sample corpus at `data/technical_docs_sample.txt`

Hardware/runtime:

- User local Windows environment
- Python virtual environment
- Corpus size: 4 chunks

## Summary

| System | Cases | Recall@1 | Recall@3 | Recall@5 | MRR | Unsupported rejection@5 | Accuracy@5 | Avg latency | P95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_v2 | 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.50 | 0.80 | 0.44 ms | 1.79 ms |
| ralg_v4 | 5 | 1.00 | 1.00 | 1.00 | 1.00 | 0.50 | 0.80 | 1.62 ms | 3.59 ms |

## Interpretation

This first benchmark proves that the evaluation runner works and that both retrieval paths can find relevant evidence in a small technical-document sample.

It does not yet prove that RALG is better than a plain baseline.

Current finding:

- baseline_v2 and ralg_v4 tie on accuracy and recall
- ralg_v4 is slower on this tiny sample
- unsupported rejection is only 50%, so false-premise/unsupported handling needs improvement

## Next benchmark milestone

The next target should be a 50-100 case technical-document benchmark with:

- more supported questions
- more unsupported questions
- more false-premise questions
- larger sample corpus
- failure-case analysis
- baseline-vs-RALG comparison

Minimum target before making strong claims:

- Accuracy@5 >= 0.85
- Unsupported rejection@5 >= 0.80
- RALG must beat baseline on at least one meaningful metric, or it should be described only as experimental.
