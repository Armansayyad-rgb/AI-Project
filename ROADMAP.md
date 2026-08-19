# Roadmap

This roadmap is focused on making RALG credible as a technical proof, not just a demo.

## Near-term priorities

1. Fix retrieval reliability
   - improve top-k evidence quality
   - reduce irrelevant retrieved chunks
   - track Recall@1, Recall@3, Recall@5, and MRR
   - first runner: `src/retrieval_proof_v1.py`

2. Build a fair baseline
   - plain lexical RAG
   - same dataset
   - same hardware
   - same scoring rules
   - first baseline included in `src/retrieval_proof_v1.py`

3. Create a technical-document benchmark
   - manuals
   - SOPs
   - maintenance instructions
   - safety documents
   - unsupported questions
   - seed dataset: `data/technical_doc_benchmark_v1.jsonl`

4. Publish benchmark results
   - accuracy
   - support/grounding
   - recall
   - latency
   - RAM/VRAM
   - failure cases

5. Package developer-facing demo
   - Docker quickstart
   - API endpoint
   - sample documents
   - repeatable eval command
   - API contract: `docs/api_demo.md`

## Commercial-readiness priorities

- define one narrow customer use case
- create a private pilot demo
- prepare deployment notes
- document limitations honestly
- separate public open-source code from private product/IP strategy

## Not a priority yet

- broad consumer chatbot UI
- exaggerated marketing
- many unrelated features
- unsupported superiority claims
- expensive always-on model paths

## Suggested first target market

Manufacturing and industrial technical-document intelligence.

Reason:

- high value per answer
- privacy matters
- documents are often dense and hard to search
- usage can be occasional but valuable
- grounded answers matter more than open-ended chat
