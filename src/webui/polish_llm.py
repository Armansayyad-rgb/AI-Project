"""Polish LLM wrapper for the webui.

Wraps a small instruct-tuned model (Qwen2.5-1.5B-Instruct by default) so it
can be used as the final "polish" step in the RAG pipeline. The polish
LLM takes either:

1. A retrieved context + raw answer draft and rewrites it into a clean,
   user-facing answer (the "lookup" branch).
2. A user question alone and generates an answer from scratch (the
   "generative" branch for open-ended questions like "design me an OS").
3. A combination of both for hybrid requests.

The module deliberately keeps no state on its own beyond the loaded
model + tokenizer; the caller decides which branch to invoke and passes
the relevant inputs.

Design constraints honored:

- Single model load at startup. Subsequent calls are just .generate().
- Works on CPU, GPU, or 6GB VRAM GPUs.
- Lazy imports so the rest of the webui loads even if transformers is
  not installed yet.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Project defaults; can be overridden by env vars or by passing values
# explicitly into ``load_polish_llm``.
#
# The default lives under the project root via the env-var-aware config
# so the same code works on Windows, Linux, and macOS without edits.
def _default_polish_model_dir() -> Path:
    """Resolve the default polish LLM directory from env vars or config."""
    override = os.environ.get("POLISH_LLM_DIR")
    if override:
        return Path(override).expanduser().resolve()
    try:
        # Defer import so this module is importable without webui's
        # sys.path bootstrap.
        from config import CHECKPOINTS_DIR  # type: ignore

        return Path(CHECKPOINTS_DIR) / "qwen2.5-1.5b-instruct"
    except Exception:
        # No config available - fall back to a sibling of this file.
        return (
            Path(__file__).resolve().parent.parent.parent
            / "checkpoints"
            / "qwen2.5-1.5b-instruct"
        )


DEFAULT_MODEL_DIR: Path = _default_polish_model_dir()

# Hardware detection happens here, once, at load time.
@dataclass
class PolishLLM:
    """Loaded model + tokenizer wrapper."""

    model: object
    tokenizer: object
    device: str
    dtype: object
    model_name: str
    max_new_tokens_default: int = 256

    def is_ready(self) -> bool:
        return self.model is not None and self.tokenizer is not None


def _pick_dtype_and_device() -> tuple[str, object, str]:
    """Choose torch dtype based on available hardware.

    Returns (device, dtype, device_label_for_logs).
    """
    import torch

    if torch.cuda.is_available():
        vram_gb = (
            torch.cuda.get_device_properties(0).total_memory
            / 1024 ** 3
        )
        if vram_gb >= 4.0:
            return "cuda", torch.float16, "cuda:0 (FP16)"
        # Tiny VRAM — fall back to CPU to avoid OOM
        return "cpu", torch.float32, "cpu (FP32, fallback)"
    return "cpu", torch.float32, "cpu (FP32)"


def load_polish_llm(
    model_dir: Optional[Path | str] = None,
    device: Optional[str] = None,
) -> PolishLLM:
    """Load Qwen2.5-1.5B-Instruct and return a PolishLLM instance.

    The first call takes a few seconds (model load); subsequent calls
    reuse the same process.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    target_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
    if not target_dir.exists():
        raise FileNotFoundError(
            f"Polish LLM not found at {target_dir}. "
            f"Download it first or pass model_dir=..."
        )

    chosen_device, chosen_dtype, label = _pick_dtype_and_device()
    if device is not None:
        chosen_device = device

    print(f"[polish_llm] loading from {target_dir} on {label}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(
        str(target_dir),
        trust_remote_code=False,
    )

    model = AutoModelForCausalLM.from_pretrained(
        str(target_dir),
        torch_dtype=chosen_dtype,
        low_cpu_mem_usage=True,
    ).to(chosen_device)

    model.eval()

    return PolishLLM(
        model=model,
        tokenizer=tokenizer,
        device=chosen_device,
        dtype=chosen_dtype,
        model_name=target_dir.name,
    )


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

_LOOKUP_SYSTEM = (
    "You are a careful assistant. You will be given a user question "
    "and a context passage retrieved from a knowledge base. Answer "
    "the question using ONLY facts that appear in the context. If the "
    "context does not contain the answer, say so explicitly. Be "
    "concise. Cite the relevant phrase in quotes when useful."
)

_GENERATIVE_SYSTEM = (
    "You are a helpful assistant. Answer the user's question using "
    "your general knowledge. Be clear, well-structured, and honest "
    "about uncertainty. If the question is speculative (for example, "
    "'design me an OS'), produce a thoughtful, organized response "
    "rather than refusing."
)

_HYBRID_SYSTEM = (
    "You are a careful assistant. The user wants an answer that "
    "combines retrieved facts from a knowledge base with your own "
    "reasoning. Use the retrieved facts as ground truth for any "
    "concrete details, and add explanation, structure, or expansion "
    "where the user asked for more than just retrieval. Cite the "
    "retrieved phrase in quotes when you rely on it."
)


def _build_messages(
    system: str,
    user_prompt: str,
) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def polish_lookup_answer(
    llm: PolishLLM,
    question: str,
    context_chunks: list[str],
    *,
    max_new_tokens: Optional[int] = None,
) -> str:
    """Polish a retrieved-context answer for a lookup question."""
    if not llm or not llm.is_ready():
        raise RuntimeError("Polish LLM not loaded.")

    import torch

    context = "\n\n".join(
        f"[{i + 1}] {chunk.strip()}"
        for i, chunk in enumerate(context_chunks)
        if chunk and chunk.strip()
    )
    if not context:
        context = "(no retrieved context)"

    user_prompt = (
        f"Question:\n{question.strip()}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer based only on the context. If the context does not "
        "contain the answer, say 'I don't have enough information.'"
    )

    messages = _build_messages(_LOOKUP_SYSTEM, user_prompt)
    return _generate(llm, messages, max_new_tokens)


def polish_generative_answer(
    llm: PolishLLM,
    question: str,
    *,
    max_new_tokens: Optional[int] = None,
) -> str:
    """Generate an answer for a question the knowledge base cannot answer."""
    if not llm or not llm.is_ready():
        raise RuntimeError("Polish LLM not loaded.")

    messages = _build_messages(_GENERATIVE_SYSTEM, question.strip())
    return _generate(llm, messages, max_new_tokens)


def polish_hybrid_answer(
    llm: PolishLLM,
    question: str,
    context_chunks: list[str],
    *,
    max_new_tokens: Optional[int] = None,
) -> str:
    """Combine retrieved facts with the model's own reasoning."""
    if not llm or not llm.is_ready():
        raise RuntimeError("Polish LLM not loaded.")

    import torch

    context = "\n\n".join(
        f"[{i + 1}] {chunk.strip()}"
        for i, chunk in enumerate(context_chunks)
        if chunk and chunk.strip()
    )
    if not context:
        context = "(no retrieved context)"

    user_prompt = (
        f"Question:\n{question.strip()}\n\n"
        f"Retrieved facts:\n{context}\n\n"
        "Use the retrieved facts for concrete details, and add any "
        "explanation or expansion the user asked for. If the facts do "
        "not cover the question, fall back to your own knowledge and "
        "say so."
    )

    messages = _build_messages(_HYBRID_SYSTEM, user_prompt)
    return _generate(llm, messages, max_new_tokens)


# ---------------------------------------------------------------------------
# Generation core
# ---------------------------------------------------------------------------

def _generate(
    llm: PolishLLM,
    messages: list[dict],
    max_new_tokens: Optional[int] = None,
) -> str:
    """Run a chat-template generation and return the decoded text."""
    import torch

    cap = max_new_tokens or llm.max_new_tokens_default

    input_ids = llm.tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(llm.device)

    attention_mask = torch.ones_like(input_ids)

    with torch.no_grad():
        output_ids = llm.model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=cap,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=llm.tokenizer.eos_token_id,
        )

    # Slice off the prompt tokens; keep only the newly generated ones.
    new_token_ids = output_ids[0][input_ids.shape[-1]:]
    text = llm.tokenizer.decode(
        new_token_ids, skip_special_tokens=True
    ).strip()
    return text


# ---------------------------------------------------------------------------
# Streaming variants
# ---------------------------------------------------------------------------
#
# The non-streaming helpers above return the full text once generation
# finishes. The streaming variants below yield decoded chunks as they
# come off the GPU, so the Gradio UI can render partial output instead
# of waiting 5-10s for the polish LLM to finish.
#
# Implementation uses HuggingFace's ``TextIteratorStreamer`` running
# in a background thread — the canonical streaming pattern. The
# streamer is exposed as a Python iterator; we drain it on the main
# thread and yield each decoded chunk to the caller. A ``try/finally``
# joins the worker thread so we never leak it.

def _generate_stream(
    llm: PolishLLM,
    messages: list[dict],
    max_new_tokens: Optional[int] = None,
):
    """Yield decoded text chunks as the polish LLM generates them.

    Mirrors :func:`_generate` but uses ``TextIteratorStreamer`` so the
    caller can render partial output. The chunks yielded are arbitrary
    decode boundaries — typically multi-character strings but sometimes
    a single character, depending on the tokenizer's byte-pair merges.
    """
    # Imported lazily so the rest of polish_llm can be imported without
    # the heavy transformers dependency (see webui.app.main()).
    import torch
    from threading import Thread
    from transformers import TextIteratorStreamer

    if not llm or not llm.is_ready():
        raise RuntimeError("Polish LLM not loaded.")

    cap = max_new_tokens or llm.max_new_tokens_default

    input_ids = llm.tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(llm.device)

    attention_mask = torch.ones_like(input_ids)

    # The streamer accumulates text fragments as model.generate emits
    # token ids. We drain it from the main thread while generate runs
    # in the worker thread.
    streamer = TextIteratorStreamer(
        llm.tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )

    gen_kwargs = dict(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=cap,
        do_sample=False,
        temperature=None,
        top_p=None,
        pad_token_id=llm.tokenizer.eos_token_id,
        streamer=streamer,
    )

    thread = Thread(
        target=llm.model.generate,
        kwargs=gen_kwargs,
        daemon=True,
    )
    thread.start()

    try:
        for chunk in streamer:
            if chunk:
                yield chunk
    finally:
        # Always join so we don't leak a thread if the consumer bails
        # out mid-stream (e.g. user clicks Stop).
        thread.join(timeout=1)


def stream_polish_lookup_answer(
    llm: PolishLLM,
    question: str,
    context_chunks: list[str],
    *,
    max_new_tokens: Optional[int] = None,
):
    """Streaming variant of :func:`polish_lookup_answer`. Yields chunks."""
    context = "\n\n".join(
        f"[{i + 1}] {chunk.strip()}"
        for i, chunk in enumerate(context_chunks)
        if chunk and chunk.strip()
    )
    if not context:
        context = "(no retrieved context)"

    user_prompt = (
        f"Question:\n{question.strip()}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer based only on the context. If the context does not "
        "contain the answer, say 'I don't have enough information.'"
    )

    messages = _build_messages(_LOOKUP_SYSTEM, user_prompt)
    yield from _generate_stream(llm, messages, max_new_tokens)


def stream_polish_generative_answer(
    llm: PolishLLM,
    question: str,
    *,
    max_new_tokens: Optional[int] = None,
):
    """Streaming variant of :func:`polish_generative_answer`. Yields chunks."""
    messages = _build_messages(_GENERATIVE_SYSTEM, question.strip())
    yield from _generate_stream(llm, messages, max_new_tokens)


def stream_polish_hybrid_answer(
    llm: PolishLLM,
    question: str,
    context_chunks: list[str],
    *,
    max_new_tokens: Optional[int] = None,
):
    """Streaming variant of :func:`polish_hybrid_answer`. Yields chunks."""
    context = "\n\n".join(
        f"[{i + 1}] {chunk.strip()}"
        for i, chunk in enumerate(context_chunks)
        if chunk and chunk.strip()
    )
    if not context:
        context = "(no retrieved context)"

    user_prompt = (
        f"Question:\n{question.strip()}\n\n"
        f"Retrieved facts:\n{context}\n\n"
        "Use the retrieved facts for concrete details, and add any "
        "explanation or expansion the user asked for. If the facts do "
        "not cover the question, fall back to your own knowledge and "
        "say so."
    )

    messages = _build_messages(_HYBRID_SYSTEM, user_prompt)
    yield from _generate_stream(llm, messages, max_new_tokens)


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

# Lightweight heuristic router so the webui can pick the branch without
# needing the full RAG pipeline to know. For accurate routing we still
# defer to rag_chat_v2's runtime_plan; this is just a fast pre-filter.

_LOOKUP_HINTS = (
    "what is", "who is", "when did", "where is", "why did",
    "how many", "capital of", "define ", "explain ", "summarize ",
    "according to", "in the", "from the", "based on",
)

_GENERATIVE_HINTS = (
    "design me", "create a", "write me", "imagine", "invent",
    "write a ", "compose", "generate ", "make up", "come up with",
    "how would", "what would", "plan ", "outline a",
)


def quick_intent_guess(question: str) -> str:
    """Return one of 'lookup', 'generative', 'hybrid'.

    Cheap heuristic, not authoritative. The authoritative router is
    rag_chat_v2.runtime_plan.
    """
    q = (question or "").lower().strip()
    if not q:
        return "lookup"

    has_lookup = any(h in q for h in _LOOKUP_HINTS)
    has_generative = any(h in q for h in _GENERATIVE_HINTS)

    if has_generative and has_lookup:
        return "hybrid"
    if has_generative:
        return "generative"
    return "lookup"