# RALG — Retrieval-Augmented Learning & Generation

RALG is a **local-first, hardware-efficient retrieval + reasoning system** designed to answer questions from a local knowledge base while keeping compute requirements low.

The project combines lightweight routing, retrieval, extractive answering, a compact reasoning path, evidence grounding, false-premise rejection, and **conditional multi-hop retrieval**. The design goal is simple: **use one cheap path for normal questions and spend extra compute only when the question actually needs it.**

> RALG is an active research/engineering project. The public repository contains the source code and reproducible project structure, while model checkpoints and other private/local artifacts are intentionally not committed.

---

## Current capabilities

- **Local-first inference** — designed to run without a hosted LLM API.
- **Lightweight question routing** — separates extractive/factual work from reasoning-oriented queries.
- **Grounded factual QA** — factual candidates are checked against retrieved evidence before being accepted.
- **False-premise rejection** — unsupported or contradictory questions can be rejected instead of answered confidently.
- **Conditional multi-hop reasoning** — normal queries keep the standard single retrieval path; detected multi-hop queries can use at most one additional retrieval pass.
- **Evidence-aware answering** — retrieved context is used to support answer generation and extraction.
- **Document ingestion** — PDF, DOCX, and TXT uploads can extend the live knowledge base through the web UI.
- **Gradio web interface** — chat, document upload, answer details, feedback, and export tooling.
- **CPU and CUDA support** — the pipeline can select CPU or CUDA depending on the environment.
- **Docker support** — containerized local deployment is included.

---

## Design philosophy

RALG is intentionally **not** built as a large multi-model or multi-agent stack.

The project prioritizes:

- low RAM / VRAM pressure
- minimal always-on model count
- one retrieval pass for ordinary queries
- conditional extra work only for harder queries
- no separate verifier LLM
- no always-on neural reranker
- no per-query index rebuilding
- evidence grounding before accepting factual answers
- abstention when reliable evidence is unavailable

The intended execution pattern is:

```text
Normal factual query
    ↓
lightweight question detection
    ↓
single retrieval pass
    ↓
factual extraction
    ↓
cheap evidence grounding
    ↓
answer / abstain

Normal reasoning query
    ↓
single retrieval pass
    ↓
existing reasoning path
    ↓
answer

Detected multi-hop query
    ↓
lightweight decomposition
    ↓
base retrieval + at most one extra retrieval
    ↓
merge compact evidence
    ↓
existing reasoning model
    ↓
answer
```

---

## Architecture

At a high level:

```text
User question
    ↓
Query routing / intent handling
    ↓
Premise validation
    ↓
Retrieval
    ↓
┌───────────────────────────────┐
│ Factual / extractive path     │
│ - direct extraction           │
│ - cheap grounding check       │
│ - abstain if unsupported      │
└───────────────────────────────┘
               or
┌───────────────────────────────┐
│ Reasoning path                │
│ - compact reasoning model     │
│ - intent-specific synthesis   │
│ - optional lightweight        │
│   multi-hop second retrieval  │
└───────────────────────────────┘
    ↓
Answer + supporting evidence
```

Core implementation lives under `src/`.

Important modules include the main RAG pipeline, retrieval layers, extraction, routing, confidence/support logic, and the evaluation suites.

---

## Hardware-efficiency constraints

The current architecture is designed around the following limits:

- **No additional always-loaded LLM** for factual verification.
- **No separate verifier model.**
- **No separate heavy reranker model.**
- **Default retrieval count: 1.**
- **Detected multi-hop retrieval count: maximum 2.**
- **Corpus/index state is reused** rather than rebuilt per query.
- **The main model is loaded once** during pipeline initialization.

These constraints are deliberate. RALG aims to improve capability primarily through routing, retrieval strategy, extraction, grounding, and compact reasoning rather than brute-force compute.

---

## Quick start

### Local Python

```powershell
# Windows PowerShell
git clone https://github.com/Armansayyad-rgb/RALG-Retrieval-Augmented-Learning-Generation..git
cd RALG-Retrieval-Augmented-Learning-Generation.

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The project expects local data/tokenizer/model artifacts configured through `config.py` or environment variables.

Model checkpoints are intentionally excluded from the public repository by `.gitignore`.

Once the required local artifacts are available, run the project using the existing launcher for your environment.

### Docker

Docker support is included through:

- `Dockerfile`
- `docker-compose.yml`

The container is designed for local/self-hosted use. Private model checkpoints remain local and should be mounted/provided separately rather than committed to GitHub.

---

## Configuration

Runtime paths and settings are centralized in `config.py` and can be overridden by environment variables where supported.

Typical configuration includes:

- project root
- tokenizer path
- reasoning-model checkpoint path
- knowledge files
- input/output token limits
- confidence/support thresholds
- web UI host/port

Do not commit real credentials or private local configuration. `.env`, checkpoint files, keys, logs, and private/internal material are excluded by the repository's `.gitignore`.

---

## Evaluation

RALG includes internal evaluation and regression tooling under `src/`.

The current development process evaluates areas such as:

- causal questions
- comparison
- structure
- summary
- significance
- factual QA
- unsupported questions
- adversarial / false-premise cases
- multi-hop behavior
- latency and resource usage

Evaluation is treated as a development instrument, not a marketing claim. Benchmark-specific answers, entities, or routes should not be hardcoded into the production system.

---

## Current development focus

The current engineering priorities are:

1. Improve factual extraction without increasing model size.
2. Strengthen evidence grounding and abstention.
3. Improve lightweight multi-hop reasoning while keeping the maximum retrieval budget small.
4. Preserve strong behavior on already-working question categories.
5. Improve retrieval-quality measurement and reproducible evaluation.
6. Continue profiling RAM, VRAM, and latency so capability gains remain hardware-efficient.

---

## What RALG is not

RALG is not intended to be:

- a hosted frontier-LLM replacement
- a large multi-agent system
- an always-online cloud assistant
- a project that improves accuracy simply by adding more models and hardware

The goal is a **compact retrieval + reasoning architecture that remains useful on modest hardware**.

---

## Repository safety

The public repository intentionally excludes common sensitive/private artifacts, including:

- `.env` files and credentials
- model checkpoints / weights
- private keys and certificates
- logs and local runtime state
- virtual environments and caches
- private business / commercialization material
- internal research artifacts that are not intended for publication

See `.gitignore` for the current rules.

---

## Contributing

Contributions should preserve the project's main design constraint: **capability improvements should not substantially increase compute requirements for every query.**

When proposing a change, prefer solutions that are:

- measurable
- general rather than benchmark-specific
- resource-efficient
- backwards-compatible where practical
- testable with independent questions

---

## License

MIT. See `LICENSE`.
