<div align="center">

# 🧠 RALG

### Retrieval-Augmented Learning & Generation

**A local-first, hardware-efficient retrieval + reasoning architecture built to achieve more with less compute.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Local First](https://img.shields.io/badge/AI-Local--First-blueviolet)
![Hardware](https://img.shields.io/badge/Compute-Hardware%20Efficient-orange)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)

**⚡ Lightweight · 🔎 Evidence-Grounded · 🧩 Conditional Multi-Hop · 🖥️ Local-First**

</div>

---

## 🌟 Overview

**RALG** is an experimental retrieval-augmented learning and generation system designed around one central principle:

> **Increase capability through better retrieval, routing, grounding, and reasoning — not simply by adding larger models and more hardware.**

RALG combines lightweight query routing, lexical retrieval, factual extraction, evidence grounding, false-premise rejection, compact reasoning, and conditional multi-hop retrieval in a single local-first pipeline.

Normal questions stay on a cheap execution path. Additional computation is activated only when the query appears to require it.

> 🚧 **Project status:** RALG is under active research and engineering development. Public source code and reproducible project structure are included in this repository. Private/local model checkpoints and sensitive development artifacts are intentionally excluded.

---

## ✨ Core Capabilities

| Capability | Description |
|---|---|
| 🖥️ **Local-First Inference** | Designed to operate without depending on a hosted LLM API. |
| 🧭 **Lightweight Routing** | Separates factual/extractive work from reasoning-oriented queries. |
| 🔎 **Retrieval-Augmented Answering** | Searches the local knowledge corpus before producing evidence-dependent answers. |
| 🎯 **Grounded Factual QA** | Factual candidates are checked against retrieved evidence before acceptance. |
| 🛡️ **False-Premise Rejection** | Unsupported or contradictory questions can be rejected instead of confidently hallucinated. |
| 🧩 **Conditional Multi-Hop Retrieval** | Ordinary queries use one retrieval pass; detected multi-hop queries may use one additional pass. |
| 🧠 **Compact Reasoning Path** | Uses the existing small reasoning model for questions that require synthesis. |
| 📚 **Document Ingestion** | PDF, DOCX, and TXT documents can extend the live knowledge base through the web interface. |
| 🌐 **Gradio Interface** | Includes chat, document upload, answer details, feedback, and export tooling. |
| ⚙️ **CPU / CUDA Support** | Supports execution according to available compute hardware. |
| 🐳 **Docker Support** | Includes container configuration for local/self-hosted deployment. |

---

## 💡 Why RALG?

Many AI systems improve capability by increasing model size, adding more models, introducing neural rerankers, or spending more compute on every request.

RALG explores a different direction.

<div align="center">

### **Do the cheap thing by default. Spend extra compute only when necessary.**

</div>

The architecture prioritizes:

- ⚡ low compute overhead
- 💾 low RAM / VRAM pressure
- 🧠 minimal always-loaded model count
- 🔎 one retrieval pass for ordinary queries
- 🧩 conditional extra retrieval only for harder queries
- 🚫 no separate verifier LLM
- 🚫 no always-on neural reranker
- ♻️ reuse of corpus/index state
- 🎯 evidence grounding before factual acceptance
- 🛑 abstention when reliable evidence is unavailable

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │    User Question     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Routing / Intent     │
                         │ + Premise Handling   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Retrieval       │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌──────────────────────┐        ┌──────────────────────┐
        │ Factual / Extractive │        │    Reasoning Path    │
        │        Path          │        │                      │
        ├──────────────────────┤        ├──────────────────────┤
        │ Direct extraction    │        │ Compact reasoning    │
        │ Evidence grounding   │        │ Intent synthesis     │
        │ Support validation   │        │ Conditional multi-hop│
        │ Answer / abstain     │        │ evidence merging     │
        └──────────┬───────────┘        └──────────┬───────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │ Grounded Response    │
                         │ + Evidence           │
                         └──────────────────────┘
```

The core implementation lives under `src/`, including the RAG pipeline, retrieval layers, routing, extraction, confidence/support logic, reasoning components, and evaluation tooling.

---

## ⚙️ Execution Strategy

### 🔹 Normal factual query

```text
Question
   ↓
Lightweight factual detection
   ↓
Single retrieval pass
   ↓
Factual extraction
   ↓
Cheap evidence grounding
   ↓
Answer OR abstain
```

### 🔹 Normal reasoning query

```text
Question
   ↓
Single retrieval pass
   ↓
Compact reasoning path
   ↓
Answer
```

### 🔹 Detected multi-hop query

```text
Question
   ↓
Lightweight multi-hop detection
   ↓
Simple decomposition
   ↓
Base retrieval
   +
Maximum one extra retrieval pass
   ↓
Evidence merge
   ↓
Existing reasoning model
   ↓
Answer
```

---

## 🚀 Hardware-Efficient by Design

RALG deliberately operates under a constrained compute budget.

| Resource / Component | Current Design |
|---|---|
| 🧠 Always-loaded reasoning models | **1** |
| 🔎 Default retrieval passes | **1** |
| 🧩 Maximum detected multi-hop passes | **2** |
| 🤖 Separate verifier LLM | **None** |
| 📊 Heavy neural reranker | **None** |
| 🔁 Per-query index rebuilding | **No** |
| 📚 Corpus/index reuse | **Yes** |
| 💻 CPU compatibility | **Yes** |
| 🎮 CUDA compatibility | **Yes** |

These constraints are intentional. RALG attempts to gain capability primarily from **architecture and information flow**, rather than brute-force compute.

---

## 📂 Project Structure

```text
RALG/
│
├── src/                    # Core retrieval, reasoning and evaluation code
├── data/                   # Local knowledge data (where applicable)
├── indexes/                # Retrieval/index artifacts
├── config.py               # Runtime configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Local container deployment
├── README.md               # Project documentation
└── LICENSE                 # MIT License
```

> Some local/private artifacts may not appear in the public repository because they are intentionally excluded from version control.

---

## 🛠️ Quick Start

### 1️⃣ Clone the repository

```powershell
git clone https://github.com/Armansayyad-rgb/RALG-Retrieval-Augmented-Learning-Generation..git
cd RALG-Retrieval-Augmented-Learning-Generation.
```

### 2️⃣ Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3️⃣ Install dependencies

```powershell
pip install -r requirements.txt
```

### 4️⃣ Configure local artifacts

The project expects required local knowledge, tokenizer, and model artifacts to be configured through `config.py` or supported environment variables.

> 🔐 Model checkpoints and other private artifacts are intentionally excluded from the public repository.

---

## 🐳 Docker

Docker deployment files are included:

```text
Dockerfile
docker-compose.yml
```

The container is intended for local/self-hosted deployment. Private model checkpoints should remain outside Git and be mounted or supplied locally when required.

---

## 🔧 Configuration

Runtime settings are centralized in `config.py` and may include:

- 📁 project root
- 🧠 reasoning-model checkpoint path
- 🔤 tokenizer path
- 📚 knowledge files
- 📏 input/output token limits
- 🎯 confidence and support thresholds
- 🌐 web UI host and port

Never commit credentials, private keys, model weights, or private runtime configuration.

---

## 📊 Evaluation & Benchmarking

RALG includes internal evaluation and regression tooling designed to measure behavior across multiple question classes.

Current evaluation areas include:

| Area | Evaluated |
|---|:---:|
| Causal reasoning | ✅ |
| Comparison | ✅ |
| Structure | ✅ |
| Summary | ✅ |
| Significance | ✅ |
| Factual QA | ✅ |
| Unsupported questions | ✅ |
| False-premise / adversarial cases | ✅ |
| Multi-hop behavior | ✅ |
| Latency / resource behavior | ✅ |

Benchmarking is treated as an **engineering instrument**, not a marketing shortcut.

Production logic should remain general. Benchmark-specific answers, entities, expected fragments, or routes must not be hardcoded into the system.

---

## 🔬 Current Research Focus

RALG is actively being improved in several areas:

1. 🎯 Improve factual extraction without increasing model size.
2. 🛡️ Strengthen grounding, evidence validation, and abstention.
3. 🧩 Improve lightweight multi-hop reasoning within the two-pass retrieval budget.
4. 🔎 Improve retrieval relevance and retrieval-quality measurement.
5. 🧪 Expand reproducible regression and benchmark coverage.
6. ⚡ Profile and reduce latency, RAM, and VRAM requirements.
7. 🧱 Preserve successful behavior while new capabilities are introduced.

---

## 🗺️ Development Direction

```text
Current RALG
    │
    ├── Better factual extraction
    ├── Stronger evidence grounding
    ├── Better retrieval quality
    ├── Lightweight multi-hop reasoning
    ├── Reproducible benchmarks
    ├── Resource profiling
    └── Production-oriented reliability
            │
            ▼
   Compact, measurable and
   hardware-efficient RAG system
```

The long-term engineering direction is to make the system increasingly **reliable, measurable, reproducible, integrable, and resource-efficient** without abandoning its compact architecture.

---

## 🚫 What RALG Is Not

RALG is **not** intended to be:

- ❌ a hosted frontier-model replacement
- ❌ a giant multi-agent architecture
- ❌ an always-online cloud assistant
- ❌ a collection of many always-loaded models
- ❌ a system that improves accuracy only by demanding more hardware

Instead, RALG explores how far a compact retrieval + reasoning architecture can be pushed through better system design.

---

## 🔐 Repository Safety

The public repository intentionally excludes common sensitive or unnecessary local artifacts:

- 🔑 `.env` files and credentials
- 🧠 model checkpoints / weights
- 🔐 private keys and certificates
- 📝 logs and runtime state
- 📦 virtual environments and caches
- 💼 private business/commercialization material
- 🔬 private internal research artifacts

See `.gitignore` for the active exclusion rules.

---

## 🤝 Contributing

Contributions are welcome when they preserve the core design principle:

> **Capability improvements should not substantially increase compute requirements for every query.**

Prefer changes that are:

- 📏 measurable
- 🌍 general rather than benchmark-specific
- ⚡ resource-efficient
- 🔄 backwards-compatible where practical
- 🧪 independently testable
- 📚 clearly documented

---

## 📜 License

This project is released under the **MIT License**.

See `LICENSE` for details.

---

<div align="center">

### 🧠 RALG

**Retrieval-Augmented Learning & Generation**

*Better architecture. Better evidence. Less unnecessary compute.*

⭐ If you find the project interesting, consider starring the repository.

</div>
