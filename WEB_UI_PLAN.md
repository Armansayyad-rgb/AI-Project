# Web UI Plan: Gradio Interface for the AI Project

**Project:** AI Project RAG Chatbot
**Goal:** Replace the current CLI-only interface (`python -m rag_chat_v2`) with a browser-based Gradio UI so non-technical users can ask questions, see sources, manage documents, and tune behavior without touching the terminal.
**Audience:** End users who do not know Python or the command line.
**Author:** AI Project team
**Status:** Draft v1

---

## Table of Contents

1. [Why Gradio?](#1-why-gradio)
2. [Current State and Gap Analysis](#2-current-state-and-gap-analysis)
3. [Features to Build](#3-features-to-build)
4. [UI Layout Design](#4-ui-layout-design)
5. [Technical Implementation](#5-technical-implementation)
6. [Implementation Phases](#6-implementation-phases)
7. [Deployment Options](#7-deployment-options)
8. [Success Metrics](#8-success-metrics)
9. [Timeline](#9-timeline)
10. [Cost Estimate](#10-cost-estimate)
11. [Risks and Mitigations](#11-risks-and-mitigations)
12. [Next Steps](#12-next-steps)
13. [Appendix: Source Code References](#13-appendix-source-code-references)

---

## 1. Why Gradio?

Gradio is the right fit for this project for several concrete reasons:

- **Pure Python, no frontend skills required.** Gradio generates the entire HTML/CSS/JS layer. We keep the existing RAG stack (PyTorch, tokenizers, custom retrievers in `src/retriever_v4.py`, `src/query_planner_v1.py`, etc.) untouched and just wrap calls in Python callbacks.
- **Built-in chat components.** `gr.Chatbot`, `gr.Textbox`, `gr.File`, `gr.Accordion`, and `gr.Tabs` cover every interaction we need.
- **First-class ML/Demo hosting on HuggingFace Spaces.** A `git push` deploys the whole app — model checkpoint plus Gradio interface — with free HTTPS and a shareable URL. Perfect for a portfolio demo.
- **Streaming + async support.** Gradio 4.x supports generator functions, so we can stream tokens from `generate()` in `rag_chat_v2.py` (line 236) instead of waiting for the full answer.
- **Mobile-friendly out of the box.** Gradio ships responsive CSS, so phones and tablets work without extra effort.
- **Active maintenance and stable 4.x/5.x releases.** Lower long-term risk than rolling our own Flask + React app.

**Alternatives we considered and rejected:**

| Option | Why we said no |
|---|---|
| Streamlit | Chat history handling is weaker; reruns the whole script on every interaction, which is hostile to our expensive `initialize_pipeline()` call that loads a 200MB checkpoint. |
| Flask + React | Too much frontend work for a demo; doubles the maintenance burden. |
| FastAPI + HTMX | Workable, but we would still need to build every component from scratch. |

---

## 2. Current State and Gap Analysis

The CLI lives in `C:\AI-Project\src\rag_chat_v2.py`:

- `initialize_pipeline(verbose=True)` (line 1598) loads the BPE tokenizer from `C:\AI-Project\data\tokenizer_v2.json`, the `SmallLMV2` model from `C:\AI-Project\checkpoints\v2\reasoning_model_v1.pt`, and builds the retrieval index over `C:\AI-Project\data\wikitext_v2.txt` + `C:\AI-Project\data\knowledge_extra_v1.txt`. It returns a `dict` of artifacts. **Initialization is heavy (model load + index build) and must run exactly once per server.**
- `answer_question(pipeline, question, verbose=True)` (line 1885) wraps `_answer_question_impl()` (line 1910). It returns a result dictionary with keys including `answer`, `answer_type`, `supported`, `confidence`, `runtime_plan`, `canonical_question`, and `asserted_relation`. **This is the primary integration point for the UI.**
- `main()` (line 3492) is the read-eval-print loop: `input("You: ")` then `answer_question(...)` until `quit`/`exit`. It uses `print()` for all output, including confidence and routing info.

### Gap Summary

| Capability | CLI today | Web UI requirement |
|---|---|---|
| Ask question | `input()` prompt | Textbox + Send button |
| See answer | `print()` to stdout | Chat message bubble |
| Confidence | Printed as a number | Visual badge (0-1, color-coded) |
| Sources | Not exposed today | Expandable panel listing the chunk IDs/texts used |
| Clear conversation | `quit`/`exit` only | "Clear" button |
| Document upload | Not supported | `gr.File` for PDF/DOCX/TXT |
| Settings (threshold, max tokens) | Hardcoded in source | Sidebar with sliders |
| Multiple sessions | None | Session state in Gradio |
| Export history | None | Download as JSON/Markdown |
| Feedback | None | Thumbs up/down |
| Concurrent users | Not supported | Required for hosting |

The plan below closes each gap incrementally.

---

## 3. Features to Build

### 3.1 Core Features (MVP — Week 1)

Must-haves for the first usable build:

1. **Chat interface with message history.** Uses `gr.Chatbot(type="messages")` so user/assistant bubbles render correctly.
2. **Question input box.** `gr.Textbox` with submit-on-Enter and a "Send" button.
3. **Answer display inside the chat bubble.** The full `result["answer"]` text, with markdown rendering where the synthesizer returned markdown.
4. **Source citations.** Expandable `gr.Accordion` under each assistant message listing the chunk IDs, a 1-2 sentence preview, and a similarity score if available. **Gap to close:** today `answer_question()` does not return a structured `sources` list — we will either surface `result["support_chunks"]` if present, or extract it from the in-prompt context passed to the model (see Section 5.3).
5. **Confidence score display.** Numeric badge next to each assistant message, color-coded: green >= 0.7, yellow 0.4-0.7, red < 0.4. Pulls from `result["confidence"]` (float). When the answer is a system "I don't know" fallback (answer_type `system`, supported `False`), show an explicit "Unsupported" badge instead.
6. **Reset / Clear conversation button.** Wipes `gr.State` history and chat list.
7. **Streaming tokens.** Wrap the model `generate()` call in a generator so the user sees tokens appear as they are produced, instead of a 5-10 second blank screen.
8. **System health banner on load.** Shows device (CPU/CUDA), chunk count, and model checkpoint version, replacing today's `print_system_info()` (line 3412).

### 3.2 Advanced Features (Weeks 2-4)

9. **Document upload.** `gr.File` accepting `.pdf`, `.docx`, `.txt`. Files are saved to a working directory, parsed, chunked, and merged into the existing retrieval index. See Section 5.4.
10. **Knowledge base management UI.** Tab listing uploaded documents with: filename, chunk count, date added, "View" (preview first 5 chunks), "Remove" (drops them from the index).
11. **Settings panel.** Sidebar accordion with:
    - Confidence threshold (slider, default `CONFIDENCE_THRESHOLD` from `rag_chat_v2.py`)
    - `MAX_NEW_TOKENS` (slider, default 50)
    - `MAX_INPUT_TOKENS` (slider, default 480)
    - Top-k retrieval depth (slider)
    - Temperature for the reasoning model
    Settings are stored in `gr.State` and passed to the pipeline.
12. **Export conversation history.** "Export" button that downloads the current session as JSON (full result objects) or Markdown (just Q/A pairs).
13. **Multiple chat sessions.** `gr.Tabs` or a session dropdown, with each session holding its own history and settings.
14. **User feedback (thumbs up/down).** Persisted to a CSV/JSONL log so we can compute evaluation metrics later.
15. **System-intent routing transparency.** Show which intent the router chose (`runtime_plan["intent"]`, e.g. "comparison", "causal", "change", "effect", "structure", "summary", "entity_list") as a small label next to the confidence badge. Helps users understand why an answer looks the way it does.
16. **Unsupported answer explanation.** When the system falls back to `unsupported_answer()` (line 608) or `comparison_unsupported_answer()` (line 637), surface the reason inline ("not enough reliable evidence about X").

### 3.3 Out of Scope (for now)

- Authentication / multi-tenant user accounts
- Voice input/output
- Realtime collaborative editing
- Building a fine-tuning UI (separate project)

---

## 4. UI Layout Design

### 4.1 ASCII Mockup (Desktop)

```
+----------------------------------------------------------------+
|  AI Project - RAG Chatbot                       [v0.1] [Help]   |
|  Device: CUDA | Chunks: 12,438 | Model: reasoning_model_v1     |
+----------------------------------------------------------------+
| [Upload Docs] [Knowledge Base] [Settings] [Export] [Clear]    |
+----------------------------------+-----------------------------+
|                                  |  Answer Details             |
|  Conversation                   |  ----------------------     |
|  ================================|  Intent:   causal           |
|                                  |  Type:     reasoning_model  |
|  You                             |  Supported: yes             |
|  Why did the Roman Empire        |  Confidence: [####----] 0.87|
|  decline?                       |                             |
|                                  |  Sources                    |
|  Assistant                       |  [1] knowledge_extra_v1.txt |
|  The Roman Empire declined due   |      "Political instability |
|  to a combination of factors...  |       and barbarian..."     |
|                                  |      score: 0.81            |
|  Confidence: 0.92  [thumbs][thumbs]|  [2] wikitext_v2.txt      |
|  Sources: [1] [2] [3]            |      "Economic troubles..." |
|                                  |      score: 0.74            |
|  You                             |                             |
|  How was the Roman army          |  Settings                   |
|  organized?                      |  ----------------------     |
|                                  |  Conf threshold  [====]0.60 |
|  Assistant                       |  Max new tokens [======] 50 |
|  The Roman army was organized    |  Top-k            [==]   5  |
|  into legions of 5,000...        |  Temperature     [===] 0.7 |
|  Confidence: 0.87                |  [Apply]                    |
|                                  |                             |
+----------------------------------+-----------------------------+
| Type your question here...                         [Send >]    |
+----------------------------------------------------------------+
```

### 4.2 Mobile Layout

Gradio automatically stacks the two columns. On mobile the right-hand panel collapses below the chat. We will use `gr.Tabs` (Conversation / Details / Settings) for the narrow breakpoint.

```
+--------------------------------+
| AI Project - RAG Chatbot       |
| Device: CUDA | Chunks: 12,438  |
+--------------------------------+
| [Tabs: Chat | Details | Set]   |
+--------------------------------+
| (Chat tab content here)        |
|                                |
| User: Why did the Roman...     |
|                                |
| Bot: The Roman Empire...       |
| Confidence: 0.92               |
| Sources: [1][2][3]             |
|                                |
+--------------------------------+
| Type your question...  [Send]  |
+--------------------------------+
```

### 4.3 Component Map

| Component | Gradio widget | Purpose |
|---|---|---|
| Header | `gr.Markdown` | Title, device/chunk/model status |
| Tab bar | `gr.Tabs` / top toolbar buttons | Switch between views |
| Chat history | `gr.Chatbot(type="messages")` | Conversation display |
| Message input | `gr.Textbox` + `gr.Button` | Ask questions |
| Answer details panel | `gr.Accordion` group | Intent, type, confidence, sources |
| Confidence bar | `gr.Slider` (read-only) or custom HTML | Visualize 0-1 score |
| Sources list | `gr.Dataframe` or `gr.JSON` | Table of chunk ID, preview, score |
| Settings | `gr.Slider` x N inside `gr.Accordion` | Tunable parameters |
| Document upload | `gr.File(file_types=[".pdf",".docx",".txt"])` | Add to knowledge base |
| Knowledge base | `gr.Dataframe` | List uploaded documents |
| Feedback | `gr.Button("thumbs up")`, `gr.Button("thumbs down")` | Per-message feedback |
| Export | `gr.DownloadButton` | Save conversation JSON/MD |
| Clear | `gr.Button("Clear Chat")` | Reset session |

---

## 5. Technical Implementation

### 5.1 Files to Create

All new files live under `C:\AI-Project\src\webui\` (a new package). This keeps the existing CLI driver (`rag_chat_v2.py`) intact.

```
C:\AI-Project\src\webui\
    __init__.py
    app.py                # Main Gradio Blocks app, demo.launch()
    chat_handler.py       # Wraps answer_question(); normalizes result for the UI
    ui_components.py      # Reusable builders for panels, headers, source lists
    document_processor.py # PDF/DOCX/TXT parsing + chunking + index merge
    session.py            # In-memory session store (history, settings, feedback)
    feedback_log.py       # Append thumbs up/down to a JSONL log
    config.py             # UI-specific constants (default port, theme, paths)
```

A second entry point — `C:\AI-Project\src\webui_launcher.py` — is a thin wrapper that calls `initialize_pipeline()` once and then runs the Gradio demo, so users can launch with `python -m webui_launcher`.

### 5.2 Dependencies

Add to `C:\AI-Project\requirements.txt` (or a new `requirements-webui.txt` so the CLI build doesn't pull Gradio):

```
# Web UI stack
gradio>=4.44.0
PyPDF2>=3.0.1
python-docx>=1.1.2
chromadb>=0.5.5          # Optional: persistent vector store for uploaded docs
pydantic>=2.8.0          # Already used transitively; pin for typed session state
```

Notes:
- `gradio` pulls in `gradio-client`, `fastapi`, `uvicorn`, `httpx` transitively — no need to pin them.
- `chromadb` is only required for **persistent** uploaded-doc storage. If we choose to keep uploaded docs in memory only (re-uploaded per session), drop `chromadb` and use plain `dict` storage.
- All ML deps (`torch`, `tokenizers`, `numpy`, `huggingface_hub`) are already in `requirements.txt` and remain required.

### 5.3 Bridging `answer_question()` to the UI

`answer_question()` returns a result dictionary with these keys (from inspection of `rag_chat_v2.py`):

```
answer, answer_type, supported, confidence,
route, mode, retriever, runtime_plan, canonical_question,
asserted_relation
```

What the UI needs, mapped from the result:

| UI field | Source |
|---|---|
| Chat bubble text | `result["answer"]` |
| Intent label | `result["runtime_plan"]["intent"]` |
| Confidence number | `result["confidence"]` (float, may be `None` for some intents) |
| Supported flag | `result["supported"]` |
| Answer type | `result["answer_type"]` (e.g. `reasoning_model`, `extractor`, `system`, `comparison`, `causal`, `change`, `effect`, `structure`, `summary`, `entity_list`) |
| Sources | **Currently not in the result dict.** Needs to be added. |

**Source-citation gap (must be closed).** Today `_answer_question_impl()` builds a `context` string from retrieved chunks but does not expose the chunk objects back to the caller. Two options:

1. **Lightweight patch to `rag_chat_v2.py`.** Add `result["sources"] = top_k_chunks` (a list of `{id, text, score}` dicts) at every early-return and at the final return in `_answer_question_impl()`. This is the right long-term fix and ~10 lines of code. We will create a `result["sources"]` field once, populated in the helper functions that already have chunk context (`retrieve_for_extractor`, `retrieve_for_reasoning`, the comparison/causal/change/effect/synthesis branches).
2. **Wrapper-layer reconstruction.** Without touching `rag_chat_v2.py`, re-run retrieval inside `chat_handler.py` using the same retrievers. Adds duplicate work and risks drift if the retriever code changes.

We choose option 1. The patch is well-scoped:

- Each branch that has access to a `top_chunks` list adds:
  ```
  result["sources"] = [
      {"id": c.get("id"), "preview": c.get("text", "")[:200], "score": c.get("score")}
      for c in top_chunks
  ]
  ```
- Branches without retrievable chunks (e.g. `unsupported_answer()` early-returns) set `result["sources"] = []`.

This is the single most important backend change for the UI and is tracked as a Phase 0 task.

### 5.4 Document Upload Pipeline

`document_processor.py` will:

1. Accept a list of uploaded files from `gr.File`.
2. Route by extension:
   - `.txt` → read with `Path.read_text(encoding="utf-8", errors="ignore")`
   - `.pdf` → `PyPDF2.PdfReader` per page, concatenate text
   - `.docx` → `python-docx`, iterate `paragraphs`
3. Reuse the existing chunker from `src/retriever_v2.py` (`load_chunks` / chunking logic) so uploaded docs use the same chunk size and overlap as the static knowledge base.
4. Re-build the retrieval index incrementally:
   - Option A (simple, fine for a demo): append new chunks to the in-memory `chunks` list and rebuild `retrieval_index` + `document_frequency` via `build_index_v2()`. Rebuild takes ~1-2 seconds for thousands of chunks.
   - Option B (optional): persist to `chromadb` so uploads survive a server restart.
5. Expose `add_documents(pipeline, files)` and `remove_documents(pipeline, doc_ids)` to `chat_handler.py`.

We start with option A; promote to B only if we need persistence.

### 5.5 Streaming

Wrap the generator call:

```python
def stream_answer(pipeline, question):
    """Yield tokens from the reasoning model as they are produced."""
    # Direct passthrough to rag_chat_v2.generate(...) is not possible today
    # because answer_question() returns the full string. Workaround:
    #
    # 1. Run plan + retrieval up front (fast, ~50ms).
    # 2. Call model.generate() with a streaming hook OR call answer_question()
    #    with verbose=False and yield the final result as a single chunk.
    #
    # Phase 1 ships single-chunk streaming; Phase 3 introduces true token
    # streaming once we add a hook into generate().
    result = answer_question(pipeline, question, verbose=False)
    yield format_for_chat(result)
```

For true token-level streaming we add a `stream_generate()` helper to `rag_chat_v2.py` (mirrors `generate()` but yields one token at a time). This is a Phase 3 task.

### 5.6 Code Structure (skeleton)

`src/webui/app.py`:

```python
import gradio as gr

from rag_chat_v2 import initialize_pipeline, answer_question
from webui.chat_handler import chat_turn, format_sources
from webui.ui_components import (
    build_header,
    build_chat_panel,
    build_details_panel,
    build_settings_panel,
)
from webui.session import SessionStore
from webui.config import WEBUI_CONFIG


def build_demo(pipeline):
    with gr.Blocks(
        title=WEBUI_CONFIG["title"],
        theme=WEBUI_CONFIG["theme"],
    ) as demo:
        # ---------------- Header ----------------
        build_header(pipeline)

        # ---------------- State -----------------
        session = gr.State(SessionStore())

        # ---------------- Layout ----------------
        with gr.Row():
            with gr.Column(scale=3):
                chatbot, msg, send_btn, clear_btn = build_chat_panel()
            with gr.Column(scale=1):
                details = build_details_panel()
                settings = build_settings_panel()

        # ---------------- Wiring ----------------
        send_btn.click(
            chat_turn,
            inputs=[msg, chatbot, session, settings],
            outputs=[chatbot, msg, details],
            api_name="chat",
        )
        msg.submit(
            chat_turn,
            inputs=[msg, chatbot, session, settings],
            outputs=[chatbot, msg, details],
        )
        clear_btn.click(
            lambda s: (s.clear(), [], None),
            inputs=[session],
            outputs=[chatbot, details],
        )

    return demo


def main():
    pipeline = initialize_pipeline(verbose=False)
    demo = build_demo(pipeline)
    demo.queue(default_concurrency_limit=4).launch(
        server_name=WEBUI_CONFIG["host"],
        server_port=WEBUI_CONFIG["port"],
        show_error=True,
    )


if __name__ == "__main__":
    main()
```

`src/webui/chat_handler.py`:

```python
def chat_turn(message, history, session, settings):
    """
    Process one user message.

    history is a list of {"role": "user"|"assistant", "content": "..."} dicts
    in Gradio 4.x "messages" format.

    Returns: (new_history, cleared_input, details_dict)
    """
    pipeline = session.pipeline
    result = answer_question(
        pipeline,
        message,
        verbose=False,
    )

    formatted = format_for_chat(result)
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": formatted},
    ]

    details = {
        "intent": result.get("runtime_plan", {}).get("intent", "general"),
        "answer_type": result.get("answer_type", "unknown"),
        "confidence": result.get("confidence"),
        "supported": result.get("supported", False),
        "sources": format_sources(result.get("sources", [])),
    }

    session.append(message, result)
    return new_history, "", details
```

`src/webui/document_processor.py`:

```python
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from retriever_v2 import load_chunks as load_chunks_v2, build_index as build_index_v2


SUPPORTED_EXTS = {".txt", ".pdf", ".docx"}


def parse_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        doc = DocxDocument(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")


def add_documents(pipeline, file_paths):
    new_texts = [parse_file(Path(p)) for p in file_paths]
    new_chunks = load_chunks_v2(_paths_from_texts(new_texts))
    pipeline["chunks"].extend(new_chunks)
    pipeline["retrieval_index"], pipeline["document_frequency"] = build_index_v2(
        pipeline["chunks"]
    )
    return len(new_chunks)
```

### 5.7 Theming and Branding

Use Gradio's built-in `gr.themes.Soft()` as the base, override with a minimal palette:

- Primary: `#1f6feb` (matches HuggingFace accent)
- Secondary: `#3fb950` (success/green for high confidence)
- Neutral: `#0d1117` background, `#c9d1d9` text (GitHub-dark inspired)

This keeps the demo neutral enough to be accepted by reviewers without conflicting with branding.

---

## 6. Implementation Phases

### Phase 0 — Backend Preparation (Days 1-2, prerequisite for Phase 1)

**Goal:** Make `answer_question()` return everything the UI needs.

- [ ] Add `result["sources"]` to `_answer_question_impl()` in `C:\AI-Project\src\rag_chat_v2.py`. Populate from the chunk lists already in scope at each early-return and at the final return.
- [ ] Add `result["top_k_chunks"]` if richer info is needed.
- [ ] Confirm `result["confidence"]` is a `float | None`, not a dict, for every answer type. If any branch returns a dict, normalize.
- [ ] Add a `stream_generate()` helper that yields one token at a time (optional, enables streaming).
- [ ] Write a unit test in `regression_tests_v2.py` that asserts `result["sources"]` is present and non-empty for a known-good question.

### Phase 1 — Basic Chat (Week 1)

**Goal:** A runnable Gradio app that talks to the existing pipeline.

- [ ] Create `C:\AI-Project\src\webui\` package skeleton.
- [ ] Add `requirements-webui.txt` with `gradio>=4.44.0`.
- [ ] Implement `chat_handler.py` and `app.py` per Section 5.6.
- [ ] Wire up chat panel + answer details panel (intent, type, confidence, supported flag).
- [ ] Wire up the "Clear" button.
- [ ] Local launch test on `http://localhost:7860` against the existing `rag_chat_v2.py`.
- [ ] Smoke-test with 10 representative questions (factual, causal, comparison, unsupported).

**Exit criteria:** A user can ask any question the CLI handles today, see the answer plus intent/confidence/supported label, and reset the chat. No document upload yet.

### Phase 2 — Document Upload (Week 2)

**Goal:** Users can add their own PDFs/DOCX/TXT to the knowledge base without restarting.

- [ ] Implement `document_processor.py` (parsing + chunking + index merge).
- [ ] Add an `Upload` tab with `gr.File(file_count="multiple")`.
- [ ] Add a "Knowledge Base" tab listing uploaded documents (filename, chunk count, added date, remove button).
- [ ] Confirm retrieval returns uploaded content for queries that target it.
- [ ] Add a hard cap (e.g. 50 MB total, 5,000 chunks) to prevent OOM.

**Exit criteria:** User uploads a Wikipedia article PDF, asks a question about it, gets an answer sourced from the PDF.

### Phase 3 — Enhanced Features (Week 3)

**Goal:** Quality-of-life features.

- [ ] Settings panel (confidence threshold, max new tokens, top-k, temperature) with `Apply` button.
- [ ] Conversation history export (`gr.DownloadButton` producing `.json` and `.md`).
- [ ] Multiple sessions (`gr.Tabs` with `+` to add a session).
- [ ] User feedback buttons (thumbs up/down) per message, logged to `feedback_log.jsonl`.
- [ ] True token-level streaming via the `stream_generate()` hook from Phase 0.
- [ ] Unsupported-answer reason inline.
- [ ] System status refresh button (re-runs `print_system_info()` logic).

**Exit criteria:** A reviewer can spend 10 minutes in the app without hitting a rough edge.

### Phase 4 — Polish and Deploy (Week 4)

**Goal:** Production-ready demo.

- [ ] Error handling: every external call wrapped in try/except with user-friendly messages. No raw tracebacks in the UI.
- [ ] Loading states: `gr.Progress` while the model runs.
- [ ] Empty-state copy and example questions in the chat.
- [ ] Mobile layout verification on iPhone/Android Safari + Chrome.
- [ ] Accessibility: keyboard navigation, focus indicators, sufficient contrast.
- [ ] README updates: how to run locally, how to deploy.
- [ ] Deploy to HuggingFace Spaces (see Section 7.1).
- [ ] Optional: custom domain via Spaces settings.

**Exit criteria:** A non-technical friend can visit a public URL, ask a question, and get a useful answer without any hand-holding.

---

## 7. Deployment Options

### 7.1 Option A — HuggingFace Spaces (Recommended)

**Why:** Free, public, HTTPS by default, designed for exactly this use case.

**Steps:**

1. Create a new Space at `https://huggingface.co/new-space`, SDK = Gradio, hardware = CPU basic (free) or T4 small ($0.60/hr if we need GPU).
2. Create `C:\AI-Project\webui_space\` mirroring the app:
   ```
   app.py                # Gradio entry point
   requirements.txt      # gradio, torch, tokenizers, PyPDF2, python-docx
   packages.txt          # (optional) system deps like poppler for PDFs
   README.md             # HF Space front-matter
   ```
3. Copy the model checkpoint (`reasoning_model_v1.pt`), tokenizer (`tokenizer_v2.json`), and knowledge files (`wikitext_v2.txt`, `knowledge_extra_v1.txt`) into the Space's repo or load them via `huggingface_hub` at startup.
4. `git push` to the Space.
5. Public URL: `https://huggingface.co/spaces/<user>/<space-name>`.

**Cost:** $0 on CPU basic. $0.60/hr on T4 small. Estimate < $5/month for a demo with light traffic.

**Caveat:** CPU inference for our `SmallLMV2` is acceptable for a demo (sub-3s answers), but if latency becomes an issue, switch the Space hardware to T4 small. Avoid L4/A10G for this checkpoint size — overkill.

### 7.2 Option B — Local Server

For development and trusted-network use:

```powershell
python -m webui_launcher
# or
cd src
python webui/app.py
```

Open `http://localhost:7860`. Suitable for showing a colleague on the same LAN by setting `server_name="0.0.0.0"`.

**Cost:** $0.

### 7.3 Option C — Cloud VPS

If we outgrow HF Spaces or want full control:

- **DigitalOcean Droplet** ($6/month basic, $12/month recommended).
- **AWS Lightsail** ($5/month).
- **Hetzner** (EU, $4/month).

Setup: Ubuntu 22.04, Python 3.11, `nginx` reverse proxy, `systemd` service, Let's Encrypt SSL. Roughly half a day of DevOps work.

**Cost:** $5-20/month.

### 7.4 Recommendation

Ship on **HuggingFace Spaces (CPU basic)** for the public demo, keep the local server as the dev workflow. Add a VPS only if we need authentication or expect heavy traffic.

---

## 8. Success Metrics

We measure success in three buckets.

### 8.1 Functional

- [ ] User can ask any of the 100 questions in `regression_tests_v2.py` and get an answer that matches the CLI output.
- [ ] Answer detail panel shows intent, type, confidence, and supported flag for every answer.
- [ ] Source list is populated and clickable for every answer that uses retrieved chunks.
- [ ] Clear button resets the chat and the detail panel.
- [ ] Settings panel changes take effect on the next question without restarting.

### 8.2 Performance

- [ ] First-token latency < 3 s on CPU basic (HF Spaces).
- [ ] End-to-end answer < 10 s for `MAX_NEW_TOKENS=50`.
- [ ] App boots in < 30 s on a fresh Space container.
- [ ] 10 concurrent users with no degradation (Gradio queue handles this; verify with `demo.queue(max_size=20)`).
- [ ] No memory leak over a 1-hour session (heap stays under 2 GB on CPU basic).

### 8.3 User Experience

- [ ] Mobile layout verified at 375 px width (iPhone SE) and 768 px (iPad).
- [ ] All interactive elements keyboard-accessible.
- [ ] No uncaught exceptions in the Gradio log over a 30-minute session with 50 questions.
- [ ] Thumbs up/down feedback is logged for >= 50% of answers.
- [ ] First-time user can complete a Q&A without instructions (verified via 3 test users).

### 8.4 Instrumentation

Add lightweight telemetry to `feedback_log.py`:

- Per question: timestamp, session id, question text, answer_type, confidence, latency_ms, feedback (-1/0/+1).
- Aggregate dashboard (later): `feedback.csv` summary table.

---

## 9. Timeline

```
Week 0 (Days 1-2)   Phase 0  - Backend preparation (sources field in rag_chat_v2.py)
Week 1              Phase 1  - Basic chat MVP
Week 2              Phase 2  - Document upload
Week 3              Phase 3  - Settings, export, sessions, feedback, streaming
Week 4              Phase 4  - Polish, mobile, deploy to HF Spaces

Total: ~4 weeks to a public, polished demo.
```

Buffer: keep 1-2 days per phase for unexpected issues (CUDA/CPU differences, Gradio API quirks, file-upload edge cases).

---

## 10. Cost Estimate

| Item | Cost |
|---|---|
| Development time | ~80 hours (4 weeks x 20 hrs/week part-time) |
| Gradio | Free (Apache 2.0) |
| HuggingFace Spaces CPU basic | $0 |
| HuggingFace Spaces T4 small (optional) | ~$5/month if we need GPU |
| VPS (optional, fallback) | $5-20/month |
| Custom domain (optional) | $10-15/year |
| **Total** | **$0 - $25/month** |

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `answer_question()` is slow on CPU (5-10s) | High | Medium | Add streaming so the UI feels responsive; cap `MAX_NEW_TOKENS` at 50; offer T4 Space as fallback. |
| Source list is missing from result dict | High (today) | High | Phase 0 patch is mandatory before Phase 1. Block Phase 1 on this. |
| Uploaded docs balloon index size and slow retrieval | Medium | High | Hard cap on total chunks (5,000) and total bytes (50 MB). Show clear errors. |
| Gradio version drift | Medium | Low | Pin `gradio>=4.44.0,<5.0` until we're ready to migrate. |
| Concurrent users cause OOM | Low | High | Gradio queue with `max_size=20`, `default_concurrency_limit=4`. |
| PDF parsing produces garbage text (scanned PDFs) | High | Medium | Detect empty pages and warn the user. Do not ship OCR in v1. |
| HF Spaces LFS quota exceeded by 200MB checkpoint | Medium | Low | Store checkpoint on HF Hub (datasets or model repo), load at runtime via `huggingface_hub.hf_hub_download`. |
| Session history grows unbounded | Medium | Low | Cap history at 50 turns per session, summarize older turns. |
| Windows path assumptions break on Linux (HF Spaces) | Medium | Medium | All paths in `rag_chat_v2.py` use `Path(...)` already; verify with `pathlib` only. Avoid `os.path.join` in new code. |

---

## 12. Next Steps

**Immediate (this week):**

1. Install Gradio in the existing `.venv`:
   ```powershell
   cd C:\AI-Project
   .venv\Scripts\Activate.ps1
   pip install "gradio>=4.44.0"
   ```
2. Land the Phase 0 patch: add `result["sources"]` to `_answer_question_impl()` in `C:\AI-Project\src\rag_chat_v2.py`.
3. Create `C:\AI-Project\src\webui\` skeleton with `app.py` containing only the chat panel and the "Clear" button.
4. Run `python -m webui.app` and confirm a localhost:7860 page loads with the existing pipeline.

**This sprint:**

5. Add the answer details panel (intent, type, confidence, supported, sources).
6. Add the settings panel.
7. Run smoke tests against `regression_tests_v2.py` questions.

**Next sprint:**

8. Implement document upload (PDF/DOCX/TXT).
9. Add feedback and export.
10. Polish UI, error messages, mobile layout.

**Deploy:**

11. Create HuggingFace Space, push code + checkpoint, share URL.
12. Share with first 5 users, collect feedback, iterate.

---

## 13. Appendix: Source Code References

These are the key locations in the existing codebase that the UI will integrate with. All paths are absolute on Windows.

| Concern | File | Line(s) | Notes |
|---|---|---|---|
| Pipeline init | `C:\AI-Project\src\rag_chat_v2.py` | 1598 | `initialize_pipeline(verbose)` — load tokenizer, model, chunks, retrieval index. Call once at app startup. |
| Question answering | `C:\AI-Project\src\rag_chat_v2.py` | 1885 | `answer_question(pipeline, question, verbose)` — primary UI integration point. |
| Result dictionary shape | `C:\AI-Project\src\rag_chat_v2.py` | 2010-2042, 3382-3405 | Keys: `answer`, `answer_type`, `supported`, `confidence`, `route`, `mode`, `retriever`, `runtime_plan`, `canonical_question`, `asserted_relation`. |
| Confidence threshold | `C:\AI-Project\src\rag_chat_v2.py` | (constant) | `CONFIDENCE_THRESHOLD` — exposed via settings panel. |
| Token limits | `C:\AI-Project\src\rag_chat_v2.py` | 98-100 | `MAX_INPUT_TOKENS=480`, `MAX_NEW_TOKENS=50` — exposed via settings panel. |
| Knowledge files | `C:\AI-Project\src\rag_chat_v2.py` | 89-96 | `wikitext_v2.txt`, `knowledge_extra_v1.txt`. |
| Tokenizer path | `C:\AI-Project\src\rag_chat_v2.py` | 81-83 | `C:\AI-Project\data\tokenizer_v2.json`. |
| Model checkpoint | `C:\AI-Project\src\rag_chat_v2.py` | 85-87 | `C:\AI-Project\checkpoints\v2\reasoning_model_v1.pt`. |
| Retriever (v2) | `C:\AI-Project\src\rag_chat_v2.py` | 26-30 | `retrieve_v2`, `build_index_v2`, `load_chunks_v2` — what we extend for uploads. |
| Retriever (v4) | `C:\AI-Project\src\rag_chat_v2.py` | 32-34 | `retrieve_v4` — used in reasoning path. |
| Unsupported answer fallback | `C:\AI-Project\src\rag_chat_v2.py` | 608 | `unsupported_answer()` — surface reason in UI. |
| Comparison unsupported | `C:\AI-Project\src\rag_chat_v2.py` | 637 | `comparison_unsupported_answer()` — surfaced when intent=comparison and one side lacks evidence. |
| CLI driver | `C:\AI-Project\src\rag_chat_v2.py` | 3492 | `main()` — the loop we are replacing. |
| System info banner | `C:\AI-Project\src\rag_chat_v2.py` | 3412 | `print_system_info()` — replaced by Gradio header. |
| Retriever chunk loader | `C:\AI-Project\src\retriever_v2.py` | (function `load_chunks`) | Reused by `document_processor.py`. |
| Index builder | `C:\AI-Project\src\retriever_v2.py` | (function `build_index`) | Reused to rebuild index after uploads. |
| Query planner | `C:\AI-Project\src\query_planner_v1.py` | (function `build_queries`) | Source of `runtime_plan["intent"]`. |
| CLI launch command | (today) | — | `cd src && python rag_chat_v2.py`. |
| UI launch command | (after this plan) | — | `cd src && python -m webui.app` or `python webui_launcher.py`. |
| Existing requirements | `C:\AI-Project\requirements.txt` | 1-19 | torch, tokenizers, numpy, datasets, huggingface_hub already pinned. |

---

*End of plan. Last updated 2026-08-10.*