<div align="center">

# 🧠 RALG
### Retrieval-Augmented Learning & Generation

**A lightweight local AI system that retrieves evidence and reasons over it without requiring large hardware.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-blue)

</div>

---

## 👋 What is RALG?

RALG is a local retrieval and reasoning project focused on getting useful AI capabilities from modest hardware.

Instead of sending every question through a large or expensive pipeline, RALG first retrieves useful information from its knowledge base and then chooses a lightweight answering or reasoning path.

The goal is straightforward: **better answers with less unnecessary compute.**

RALG is currently under active development, so some features and benchmarks are still being improved.

## ✨ Key Features

- 🔎 Retrieves relevant information from a local knowledge base
- 🧠 Uses a compact reasoning path when reasoning is needed
- 🎯 Checks factual answers against retrieved evidence
- 🛡️ Can abstain when there is not enough reliable evidence
- 🧩 Supports lightweight multi-hop questions with at most one extra retrieval pass
- 📄 Supports PDF, DOCX and TXT document ingestion
- 🌐 Includes a Gradio web interface
- 💻 Supports CPU and CUDA environments
- 🐳 Includes Docker support

## ⚙️ How It Works

```text
Question
   ↓
Retrieve relevant evidence
   ↓
Choose answer / reasoning path
   ↓
Check evidence when needed
   ↓
Answer or abstain
```

Normal questions use **one retrieval pass**. Harder multi-hop questions can use **up to two passes**. RALG does not require a separate verifier LLM or an always-on heavy reranker.

## 💡 Why RALG?

A common way to improve AI systems is to use larger models and more hardware. RALG is exploring another approach: improving the pipeline itself.

The project focuses on:

- low hardware requirements
- local execution
- efficient retrieval
- evidence-grounded answers
- compact reasoning
- extra computation only when needed

This makes hardware efficiency a design constraint rather than an afterthought.

## 📊 Evaluation

RALG includes evaluation and regression tools for areas such as factual QA, causal reasoning, comparison, unsupported questions, false-premise rejection and multi-hop behavior.

Benchmarks are used as engineering tools while the system is developed. Results should come from actual runs rather than benchmark-specific hardcoding.

## 🚀 Getting Started

```powershell
git clone https://github.com/Armansayyad-rgb/RALG-Retrieval-Augmented-Learning-Generation..git
cd RALG-Retrieval-Augmented-Learning-Generation.

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

RALG also requires the appropriate local knowledge, tokenizer and model artifacts. Model checkpoints and private development files are intentionally not stored in the public repository.

## 📁 Main Project Files

```text
src/                 Core RALG code
data/                Local knowledge data
indexes/             Retrieval/index data
config.py            Project configuration
requirements.txt     Python dependencies
Dockerfile           Docker configuration
docker-compose.yml   Local container setup
```

## 🔬 Current Status

RALG is an active research and engineering project. Current work is focused on improving factual extraction, evidence grounding, retrieval quality, lightweight multi-hop reasoning, benchmarking and resource efficiency.

The project is intentionally being kept compact: improvements should provide measurable value without making every query more expensive to run.

## 🔐 Public Repository

Private model checkpoints, credentials, logs, local runtime files and internal development material are excluded from version control. See `.gitignore` for the repository rules.

## 🤝 Contributing

Contributions are welcome. Changes should ideally be measurable, general rather than benchmark-specific, and consistent with RALG's low-resource design.

## 📜 License

MIT License. See `LICENSE` for details.

---

<div align="center">

**RALG — useful retrieval and reasoning without unnecessary compute.**

</div>
