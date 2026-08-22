# Commercial Readiness

This document describes the public readiness criteria for RALG without exposing private strategy, customer information, or valuation targets.

## Current stage

RALG is an early technical proof with a working local pipeline, document ingestion, web UI, API, Docker support, evaluation tooling, and a reproducible held-out commercial validation runner.

The latest validated checkpoint demonstrates correct retrieval and complete answers on 5 supported synthetic held-out cases, safe rejection on 5 unsupported cases, a 0% false-support rate on that small set, 23/23 regression passes, and a passing GitHub Actions sanity workflow on `master`.

These are engineering checkpoints, not production claims. RALG is **not yet production-ready** and should not be presented as having proven superiority over conventional RAG systems.

See [Customer Pilot Readiness](PILOT_READINESS.md) for the explicit release gates before an external pilot.

## What is already demonstrated

- local document ingestion and question answering
- evidence-oriented retrieval and answer generation
- unsupported / false-premise rejection paths
- repeatable synthetic retrieval benchmarks
- a hard benchmark with distractors and multi-evidence cases
- a small held-out commercial validation set with supported and unsupported cases
- runtime-ingested evidence tracking without hard-coded corpus-size assumptions
- end-to-end API reliability testing
- local web UI and Docker packaging
- GitHub Actions CI with manual dispatch support

## Required before customer pilots

The following should be treated as release gates rather than marketing goals:

- stable supported-answer accuracy in the chosen domain
- low false-support rate for unsupported questions
- runtime-ingested documents ranking correctly against the static knowledge base
- evidence returned to the user matching the evidence actually used for the answer
- repeatable installation on a clean machine
- passing CI and Docker startup checks
- latency and memory measurements on representative hardware
- clear handling of malformed or oversized document uploads
- documented security boundaries for local deployment
- a fixed held-out evaluation set that is not tuned after failures are observed
- a larger and more realistic evaluation set than the current small synthetic checkpoint

## Required before strong technical or investor claims

- larger, less hand-designed benchmark data
- realistic or independently sourced manuals/SOPs with clear usage rights
- baseline comparison performed under identical data and hardware conditions
- reproducible benchmark versions tied to commits
- evidence that any measured retrieval advantage survives subsequent code changes
- documented failure examples, not only aggregate scores
- provenance and licensing records for public training/evaluation data

## Safe positioning

> RALG Engine is a local, evidence-grounded AI system for private technical-document question answering with efficient retrieval and compact reasoning.

## Suggested target users

- manufacturing teams
- maintenance teams
- industrial documentation teams
- internal technical support teams
- organizations that prefer not to send private documents to hosted AI services

## Keep private

The following should not be stored in the public repository:

- valuation targets
- acquisition strategy
- investor negotiation notes
- private customer or prospect lists
- customer documents
- non-public benchmark data
- proprietary deployment code
- private model weights
- credentials, API keys, or access tokens

## Public-reporting rule

Benchmark reports should clearly distinguish **historical results**, **current verified results**, and **targets**. A synthetic or historical result should never be presented as current production performance without a fresh reproducible run.
