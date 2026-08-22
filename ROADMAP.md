# Roadmap

This roadmap is focused on making RALG credible as a technical proof and pilot-ready local document intelligence engine.

## Completed foundations

- local retrieval and answer pipeline
- document ingestion and live indexing
- Gradio web UI
- FastAPI demo endpoint
- Docker / Docker Compose packaging
- repeatable simple and hard synthetic retrieval benchmarks
- unsupported and false-premise evaluation coverage
- public benchmark reporting and CI sanity checks

## Current priority: reliability

1. Improve runtime-ingested document ranking
   - ensure newly ingested relevant chunks outrank unrelated static knowledge
   - reduce false support from high-overlap but irrelevant chunks
   - track exact failure cases instead of tuning only aggregate metrics

2. Reach a stable end-to-end reliability gate
   - supported-answer correctness >= 90%
   - unsupported rejection >= 95%
   - false-support rate <= 5%
   - false-rejection rate <= 5%
   - zero API/runtime errors in the reliability suite

3. Remove benchmark-specific behavior
   - generalize domain-specific retrieval rules
   - avoid hardcoded benchmark entities or answer-specific heuristics
   - rerun all retrieval and reliability tests after cleanup

## Validation priority

4. Build a held-out benchmark
   - do not tune production logic against the held-out set
   - include realistic manuals, SOPs, maintenance instructions, and safety documents
   - include distractors, paraphrases, multi-hop questions, unsupported questions, and false premises

5. Compare against a fair baseline
   - same corpus
   - same hardware
   - same query set
   - same scoring rules
   - report Recall@K, MRR, supported-answer accuracy, false-support rate, latency, and memory use

6. Verify evidence consistency
   - displayed sources must correspond to evidence actually used for the answer
   - document ingestion and API/UI paths should share the same retrieval semantics

## Engineering hardening

7. Keep the repository reproducible
   - CI compile and structure checks
   - deterministic benchmark commands where practical
   - clean configuration without machine-specific paths
   - Docker startup test

8. Separate runtime and research concerns
   - identify production runtime modules
   - classify training/data-build utilities
   - move or archive genuinely obsolete scripts only after dependency review

9. Manage large artifacts deliberately
   - document provenance for training/evaluation data
   - avoid committing unnecessary generated indexes or large replaceable corpora
   - keep proprietary checkpoints and private datasets outside the public repository

## Pilot-readiness

10. Package a narrow technical-document demo
    - sample manuals/SOPs
    - simple ingestion flow
    - API contract
    - repeatable evaluation command
    - limitations and security notes

11. Validate with realistic users and documents
    - manufacturing / maintenance workflows
    - measure answer usefulness and failure modes
    - collect pilot evidence before making broad commercial claims

## Not a priority yet

- broad consumer chatbot features
- unsupported superiority claims
- expensive always-on model paths
- cosmetic UI work that does not improve reliability or deployment

## Initial target market

Manufacturing and industrial technical-document intelligence, where privacy, grounded answers, and reliable retrieval are more important than open-ended chat.
