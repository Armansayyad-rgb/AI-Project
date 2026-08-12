# AI Project

A self-hosted, local-first question-answering system with a custom-trained reasoning model and retrieval over a knowledge base.

**100% local. Your data never leaves your machine.** Runs on a laptop, a Raspberry Pi, or a VPS.

---

## What it does

Ask a question in natural language. The system:

1. **Classifies intent** — causal, comparison, structure, factual, etc.
2. **Retrieves** relevant chunks from a knowledge base (Wikipedia + your uploads).
3. **Validates the premise** — refuses to answer impossible questions like *"How did photosynthesis create Roman law?"*
4. **Synthesizes an answer** with citations to the supporting evidence.

```
Q: Why did the Roman Empire decline?
A: The Roman Empire declined due to a combination of internal and external
   pressures, including economic troubles, overreliance on mercenary
   armies, political instability, and barbarian invasions ...
   Sources: chunk #1287, chunk #3412, chunk #8891
```

---

## Quick start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/<your-username>/ai-project.git
cd ai-project
docker compose up
```

Open http://localhost:7860.

First run takes ~2 minutes (model + index load). Subsequent runs are fast (~5 seconds).

### Option 2: Local Python

```bash
git clone https://github.com/<your-username>/ai-project.git
cd ai-project
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m webui_launcher
```

---

## What works

- **12 question types**: causal, change-over-time, effect, structure, process, summary, significance, features, entity-list, comparison, adversarial, negative.
- **Strong false-premise rejection** — refuses to confidently answer impossible questions.
- **Multi-source evidence** — surfaces the chunks that support an answer.
- **Document upload** — drop your own PDFs, DOCX, or TXT files in via the web UI; they become part of the searchable knowledge base.
- **Configurable confidence threshold** — you decide how confident an answer needs to be to be returned.
- **Web UI (Gradio)** — chat interface, no Python knowledge required.
- **Self-hosted** — runs entirely on your hardware; no external API calls.

---

## What it doesn't do (yet)

- Use a state-of-the-art LLM. The reasoning model is **20M parameters**, intentionally small to fit on low-end hardware. Quality on subtle multi-hop reasoning is lower than GPT-4 / Claude. For factual Q&A over a knowledge base, retrieval does most of the work and the model quality gap is smaller than you'd think.
- Train itself. The bundled model is from a fixed training run; re-training requires the original training scripts (included in `src/build_*` and `src/finetune_*`).
- Multi-user authentication out of the box. The current build assumes one trusted user per instance. If you want multi-tenant auth, you'd add it on top.

---

## Architecture

```
                +-----------------------+
                |   User question       |
                +----------+------------+
                           |
                           v
                +----------+------------+
                |  Query planner        |  intent classification,
                |  (intent + subject)   |  subject extraction,
                +----------+------------+  canonicalization
                           |
                           v
                +----------+------------+
                |  Premise validator    |  reject impossible claims
                |  (false-premise gate) |
                +----------+------------+
                           |
                           v
                +----------+------------+
                |  Retriever             |  lexical index over
                |  (~107K chunks)        |  WikiText + uploaded docs
                +----------+------------+
                           |
                           v
                +----------+------------+
                |  Synthesizer           |  intent-specific
                |  (causal / comparison  |  answer construction
                |   / structure / etc.)  |
                +----------+------------+
                           |
                           v
                +----------+------------+
                |  Confidence check      |  threshold gate; fall
                |                        |  back to "I don't know"
                +----------+------------+
                           |
                           v
                Answer + supporting evidence
```

Each component is a separate Python module under `src/` and can be tested independently. See `src/evaluation_suite_v3.py` for the end-to-end test harness.

---

## Hardware

| Setup | Works? | Speed |
|---|---|---|
| Modern laptop (any OS) | Yes | 1–3 s/question |
| Desktop with NVIDIA GPU + CUDA | Yes | 0.5–1 s/question |
| Raspberry Pi 5 (8 GB) | Yes | 10–30 s/question |
| Cheap VPS ($5/mo, 4 GB RAM) | Yes | 1–5 s/question |
| HuggingFace Spaces (free tier) | Yes | fast |

Disk: ~200 MB for the image, ~80 MB for the bundled model + tokenizer, ~60 MB for the default knowledge base.

GPU is **not required**. The CPU-only Docker image is the default.

---

## Configuration

All paths and runtime settings are env-var-overridable. See `config.py` for the full list.

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROJECT_ROOT` | platform-dependent | Project root |
| `TOKENIZER_FILE` | `<root>/data/tokenizer_v2.json` | BPE tokenizer |
| `MODEL_FILE` | `<root>/checkpoints/v2/reasoning_model_v1.pt` | Model weights |
| `KNOWLEDGE_FILES` | wikitext + knowledge_extra | Knowledge corpus |
| `MAX_INPUT_TOKENS` | 480 | Max context fed to model |
| `MAX_NEW_TOKENS` | 50 | Max tokens generated |
| `CONFIDENCE_THRESHOLD` | 0.80 | Min confidence for accepted answer |
| `WEBUI_HOST` | 127.0.0.1 | Web UI bind address |
| `WEBUI_PORT` | 7860 | Web UI port |

---

## Development

```bash
# Run the evaluation suite
python evaluation_suite_v3.py

# Run the regression tests
python regression_tests_v2.py

# Run unit tests
python test_asserted_relation.py
python test_feedback_log.py
```

Training scripts live in `src/build_*.py` and `src/finetune_*.py`. Tokenizer training in `src/train_tokenizer_v2.py`. Embeddings in `src/train_embeddings.py`.

See `docs/` for design notes (added over time as the project matures).

---

## Why this exists

Most AI products today either:
- Send your data to a third party (privacy concerns, API costs).
- Require a beefy GPU to run locally (hardware barrier).
- Are closed-source black boxes (no transparency).

This project is an attempt at a different point in the design space:
- Runs on the computer you already own.
- Open source. Read the code, change the code, deploy the code.
- Quality is honest about its limits — strong on factual Q&A, weaker on open-ended generation.

It's not trying to compete with GPT-4. It's trying to be **the best Q&A system that runs on a Raspberry Pi and keeps your data local**.

---

## License

MIT. See `LICENSE`.
