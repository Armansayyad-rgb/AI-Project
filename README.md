<div align="center">

# RALG Engine
### Retrieval-Augmented Learning & Generation

A local, evidence-grounded AI engine for answering questions over private documents with efficient retrieval, compact reasoning, and clear abstention when support is weak.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-blue)

</div>

---

## What is RALG?

RALG, short for Retrieval-Augmented Learning & Generation, is an experimental local AI system that combines document retrieval, lightweight reasoning, and evidence-grounded answering.

The project is designed around a simple constraint: useful AI should not always require a large model, cloud inference, or heavy hardware. RALG explores how far a smaller local pipeline can go when retrieval, routing, grounding, and refusal behavior are treated as first-class parts of the system.

## Current focus

The current product direction is a private technical-document intelligence engine for teams that need answers from manuals, SOPs, maintenance notes, safety documents, policies, or internal knowledge bases.

The near-term goal is not broad general chat. The goal is reliable, cited answers in narrow domains where privacy, evidence, and compute efficiency matter.

## Key capabilities

- Local document retrieval from a knowledge base
- Evidence-grounded answer generation
- Lightweight reasoning path for selected questions
- False-premise and unsupported-question rejection
- Conditional multi-hop retrieval with a maximum extra pass
- PDF, DOCX, and TXT ingestion
- Gradio web interface
- CPU and CUDA support
- Docker and Docker Compose support
- Evaluation and regression tooling

## How it works

```text
User question
   ↓
Query planning and retrieval
   ↓
Evidence selection
   ↓
Answer / reasoning route
   ↓
Support check
   ↓
Cited answer or abstention
```

RALG uses extra computation only when the query appears to need it. Simple questions stay on the cheaper path; harder questions can trigger additional retrieval/reasoning logic.

## Why this matters

Many AI document systems improve quality by adding larger models, rerankers, hosted APIs, or expensive inference layers. RALG explores another path: improving the pipeline itself so that smaller local systems can become more useful and more trustworthy.

This makes the project relevant for:

- private enterprise document search
- technical support knowledge bases
- manufacturing and maintenance documentation
- safety and compliance document lookup
- local-first AI deployments
- low-resource AI reasoning experiments

## Current status

RALG is in active development. The system already includes a working local pipeline, web UI, document ingestion, Docker support, and evaluation scripts.

The most important work now is improving retrieval quality and publishing fair benchmark results against a plain RAG baseline. Claims about superiority should be treated as unproven until benchmarked.

See:

- [Benchmarks](BENCHMARKS.md)
- [Roadmap](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Use cases](docs/use_cases.md)
- [Security](SECURITY.md)
- [Commercial readiness](COMMERCIAL_READINESS.md)

## Quick start

### Local Python

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the web UI from the project source entrypoint used by your environment.

### Docker

```bash
docker compose up
```

Then open:

```text
http://localhost:7860
```

## Evaluation

Evaluation is part of the project, not an afterthought. The repo includes test suites for factual QA, unsupported questions, false-premise rejection, causal questions, comparisons, and multi-hop behavior.

The next required milestone is a fair comparison between:

- plain lexical RAG baseline
- current RALG pipeline
- domain-specific technical-document benchmark

Published metrics should include accuracy, support rate, recall, latency, RAM/VRAM usage, and failure examples.

## Limitations

RALG is not production-ready yet.

Known limitations:

- retrieval quality still needs improvement
- benchmark results are not yet strong enough for commercial claims
- current evaluation needs cleaner public reporting
- some paths are experimental
- domain-specific validation is still required before deployment

## License

This repository is currently released under the MIT License.

If the project becomes a commercial product, proprietary deployment code, customer integrations, datasets, benchmarks, and private strategy material should be kept outside the public repository.

## Positioning

A safe one-line description:

> RALG Engine is a local, evidence-grounded AI system for private technical-document question answering with efficient retrieval and compact reasoning.
