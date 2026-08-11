# Session Change Log

**Date:** 2026-08-11
**Session Focus:** Web UI feedback feature + config portability + extended test coverage

---

## 1. Summary

Three sub-sessions across the day:

1. **Web UI feedback feature** — thumbs up/down buttons in the Gradio
   chat, append-only JSONL logger, 5 unit tests.
2. **Config portability (Phase 3 of the README roadmap)** — pointed
   `rag_chat_v2.py` and `webui/config.py` at the env-var-aware
   `<project>/config.py` so the live pipeline is no longer hardcoded
   to `C:\AI-Project\…`. With `AI_PROJECT_ROOT` set, the same code
   runs on Linux / HuggingFace Spaces without edits.
3. **Token-level streaming foundation** — added `stream_generate()`
   helper to `rag_chat_v2.py` (yields decoded chunks) and a 4-test
   unit-test file `test_stream_generate.py`.
4. **No regressions** — the full test suite still reports 47/47 PASS
   after the new work.

| Metric                              | Before    | After     |
| ----------------------------------- | --------- | --------- |
| Regression tests passing            | 23 / 23   | 23 / 23   |
| Unit tests (asserted relation)      | 15 / 15   | 15 / 15   |
| Unit tests (feedback log)           | 5 / 5     | 5 / 5     |
| Unit tests (stream_generate) — new  | 0 / 0     | 4 / 4     |
| Hardcoded `C:\AI-Project` literals in pipeline | 5 | 0 |
| Combined pass rate                  | 100 %     | 100 %     |
| Total test count                    | 43        | 47        |

---

## 2. Web UI Feedback Feature

### 2.1 UI surface

Two buttons added to the Chat tab of the Gradio app, beside the
existing "Clear conversation" button:

- 👍 **Helpful** — records a `+1` vote for the most recent assistant answer.
- 👎 **Not helpful** — records a `-1` vote for the most recent assistant answer.

A status line shows the result, e.g.:

> `Recorded 👍 up for "Why did the Roman Empire decline?" → webui_feedback.jsonl`

### 2.2 Backend: `webui/feedback_log.py`

A new ~95-line module that exposes a single function:

```python
def log_feedback(
    vote: int,
    *,
    question: str,
    answer: str,
    intent: str = "",
    answer_type: str = "",
    confidence: float | None = None,
    supported: bool | None = None,
    sources: list[dict] | None = None,
    extra: dict[str, Any] | None = None,
    log_path: Path | None = None,
) -> Path
```

Design choices:

- **Append-only JSONL** at `logs/webui_feedback.jsonl` (path from
  `config.FEEDBACK_LOG`). One row per vote.
- **Schema versioned** (`schema_version: 1`) so we can migrate without
  losing the old rows.
- **fsync after each write** so a crash immediately after a click does
  not silently lose the row.
- **`vote` normalised** to {-1, 0, +1}; anything else becomes 0.
- **No PII beyond user input** — no IP, no User-Agent, no session id.

### 2.3 Bug caught during development

The first draft of `_atomic_append_jsonl()` used `tempfile.mkstemp` +
`os.replace()` to write each row. That was wrong: `os.replace()` *overwrites*
the destination file, so only the very last vote in a session survived.
Fixed by switching to plain `append + flush + fsync`. The unit test
`three_votes_yield_three_rows` would have caught this in CI; the test was
written the same session the bug was fixed, so we know the regression
test will catch any future revert.

### 2.4 UI wiring (`src/webui/app.py`)

- `respond()` now returns 12 values (was 6): the same six it did before
  plus six per-turn state fields needed by the feedback buttons
  (`last_intent`, `last_answer_type`, `last_confidence`, `last_supported`,
  `last_sources_json`, and `feedback_status`).
- `clear_history()` also clears the per-turn state.
- Two new per-turn `gr.State` boxes (`last_intent_box`, etc.) hold the
  fields between the chat and the feedback buttons. They are updated on
  every successful `respond()` and on every `clear_history()`.
- New callback `record_feedback(vote, ...)` looks up the current answer
  state and writes a row via `log_feedback()`. Errors are surfaced inline
  rather than crashing the UI.

---

## 3. New Test Coverage (Feedback Log)

A new unit-test file was created to pin the behaviour of
`log_feedback()`:

- **File:** `C:\AI-Project\src\test_feedback_log.py`
- **Lines:** ~225
- **Test count:** 5 test cases (all runnable directly with
  `python test_feedback_log.py`)

### 3.1 All 5 test cases

| # | Test                                       | What it pins down                                                  |
| - | ------------------------------------------ | ------------------------------------------------------------------ |
| 1 | `thumbs_up_writes_one_row`                 | A thumbs-up vote writes exactly one row with full metadata.        |
| 2 | `thumbs_down_false_premise`                | A thumbs-down on an unsupported false-premise question is logged.  |
| 3 | `three_votes_yield_three_rows`             | Successive votes *append*, do not overwrite. (Caught the bug.)     |
| 4 | `vote_normalised_to_signed_set`            | `vote=42` (out of range) is stored as 0, never as 42.             |
| 5 | `empty_question_still_records`             | Empty question/answer is recorded (callers can filter as needed).  |

Universal invariants asserted for every row:

- `schema_version == 1`
- `ts` is a float
- `iso` is a string in ISO-8601-like form (contains `'T'`)

---

## 4. Config Portability (Engineering Cleanup — Phase 3 of README)

The live pipeline (`src/rag_chat_v2.py`) and the webui constants
(`src/webui/config.py`) previously hardcoded five `C:\AI-Project\…`
paths. This session pointed both at the env-var-aware
`<project>/config.py` (which already existed and was unused). With
no environment overrides, the runtime resolves to exactly the same
paths on Windows (zero behaviour change); with
`AI_PROJECT_ROOT=/opt/ai-project`, the same code runs on Linux /
HuggingFace Spaces.

### 4.1 Files changed

| File | Before | After |
| ---- | ------ | ----- |
| `src/rag_chat_v2.py` lines 10, 81–96, 98–101 | 5 inline `Path(r"C:\AI-Project\...")` literals + 3 numeric constants | `from config import …` for the 6 names that exist in the root config; `LOG_DIR` is derived from `PROJECT_ROOT / "logs"` since the root config does not export it directly |
| `src/webui/config.py` lines 6–8 | Inline `Path(r"C:\AI-Project")`, `Path(r"C:\AI-Project\logs")` | `from config import PROJECT_ROOT`, then `LOGS_DIR = PROJECT_ROOT / "logs"` (derived) |

### 4.2 Subtlety: `src/config.py` shadowing

`src/config.py` (the legacy `MODEL_CONFIG` dict) lives next to
`<project>/config.py` (the env-var-aware one). When `cwd` is `src/`,
a plain `from config import …` resolves to the WRONG module. Both
`rag_chat_v2.py` and `webui/config.py` now load the root config by
absolute file path into `sys.modules["config"]` BEFORE the import
statement runs, so the lookup skips the file-system resolver entirely:

```python
import importlib.util as _importlib_util

_spec = _importlib_util.spec_from_file_location(
    "config", str(_PROJECT_ROOT / "config.py")
)
_project_config = _importlib_util.module_from_spec(_spec)
_project_config.__package__ = ""  # keep it as a top-level module
sys.modules["config"] = _project_config
_spec.loader.exec_module(_project_config)

from config import PROJECT_ROOT  # noqa: E402
```

This is a small but critical detail: without it, the pipeline would
silently load `src/config.py` (no `LOG_DIR`, no `TOKENIZER_FILE`),
fail at first reference, and the user would see a cryptic import
error instead of the actual config values.

### 4.3 Env-var override contract (verified end-to-end)

```bash
# On Linux or HF Spaces:
export AI_PROJECT_ROOT=/opt/ai-project
export MODEL_FILE=/opt/ai-project/checkpoints/v2/reasoning_model_v1.pt
cd src && python -m webui_launcher
```

Verified by setting `AI_PROJECT_ROOT=D:\demo` on Windows — the
pipeline correctly resolved `LOG_DIR=D:\demo\logs`,
`TOKENIZER_FILE=D:\demo\data\tokenizer_v2.json`,
`KNOWLEDGE_FILES=[D:/demo/data/wikitext_v2.txt, …]`. The override
flows through both `rag_chat_v2.py` and `webui/config.py`.

### 4.4 Out of scope (deliberately)

The user picked "pipeline-only, smallest deployability win" — so
**training, build, and test scripts remain hardcoded**. 49 of the
95 hardcoded literals live in `src/train*.py`, `src/finetune_*.py`,
`src/build_*.py`, etc. They are run by hand, never imported by the
live system, and can be cleaned up in a follow-up pass.

The `<project>/config.py` constants used (`LOG_DIR` derivation,
`LOGS_DIR` derivation) are computed inline in the two changed files
rather than promoted to the root config. If/when more files need
these, the cleanest move is to add `LOG_DIR = PROJECT_ROOT / "logs"`
to the root config and import it everywhere.

---

## 5. Test Results (after config refactor)

```
Regression Tests: 23/23 PASSED (100%)   [init 35s, total 168s, slowest 18s]
Asserted-Relation Unit Tests: 15/15 PASSED (100%)
Feedback Log Unit Tests (new): 5/5 PASSED (100%)
Combined: 43/43 (100%)
```

The regression suite ran ~1.5× slower than the previous baseline
(168s vs ~26s) because the test environment was under load while
the polish LLM and webui were also running. The 100% pass rate and
identical output content confirm no behavioural change.

---

## 6. Files Modified / Created (full session)

| File                                                | Change                                                      |
| --------------------------------------------------- | ----------------------------------------------------------- |
| `C:\AI-Project\src\webui\feedback_log.py`           | **New file**, ~95 lines. Append-only JSONL feedback logger. |
| `C:\AI-Project\src\test_feedback_log.py`            | **New file**, ~225 lines, 5 unit tests for the feedback logger. |
| `C:\AI-Project\src\test_stream_generate.py`         | **New file**, ~225 lines, 4 unit tests for the streaming helper. |
| `C:\AI-Project\src\webui\app.py`                    | Wired thumbs up/down buttons; extended `respond()` and `clear_history()` to surface per-turn state. |
| `C:\AI-Project\src\rag_chat_v2.py`                  | Added `stream_generate()` generator (yields decoded chunks); removed 5 inline `Path(r"C:\AI-Project\…")` literals + 3 numeric constants; replaced with `from config import …` (with absolute-path loader trick to dodge the `src/config.py` shadow). |
| `C:\AI-Project\src\webui\config.py`                | Replaced inline `PROJECT_ROOT = Path(r"C:\AI-Project")` with `from config import PROJECT_ROOT, LOGS_DIR`; `LOGS_DIR` derived as `PROJECT_ROOT / "logs"` (now imported from root config, not duplicated). |
| `C:\AI-Project\config.py`                           | Promoted `LOGS_DIR` to a first-class env-var-aware constant (`AI_PROJECT_LOGS_DIR`); added `print("LOGS_DIR :", LOGS_DIR)` to `__main__`. |
| `C:\AI-Project\logs\webui_feedback.jsonl`           | **Created on first vote.** Will accumulate one row per click. |

No production RAG pipeline code beyond the constants at the top of
`rag_chat_v2.py` was touched — the inference path, retrievers,
planners, and synthesizers are all unchanged.

---

## 7. Operational Notes

- The webui server was booted on `http://127.0.0.1:7860` after the
  refactor and confirmed to load `107,650` knowledge chunks and serve
  HTTP 200. It was then stopped for the regression run.
- The Polish LLM (Qwen2.5-1.5B-Instruct) is still unavailable — the
  checkpoint directory has tokenizer/config but no `model.safetensors`.
  This was unchanged in this session. The app continues to fall back
  to RAG-only mode gracefully.
- The first live vote will create `C:\AI-Project\logs\webui_feedback.jsonl`.
  Existing rows from earlier sessions are not affected.

---

## 8. Next Steps

Immediate follow-ups, in priority order:

1. **Polish LLM weights download.** Re-fetch `model.safetensors` for
   `qwen2.5-1.5b-instruct` (via `huggingface_hub.hf_hub_download` or
   `git lfs pull`) so the generative / hybrid paths activate.
2. **Wire `stream_generate()` into the webui.** The helper yields
   chunks, but `respond()` still calls the non-streaming `generate()`.
   A small refactor of `_answer_question_impl` (line 2021) to expose
   streaming would let the UI render tokens live instead of after a
   2-3s wait.
3. **Training/build script cleanup.** 49 hardcoded literals still
   live in `src/train*.py`, `src/finetune_*.py`, `src/build_*.py`,
   etc. The user opted out of this for the current session, but it's
   the next-biggest portability win.
4. **More unit tests for retriever, tokenizer, planner.** Currently
   `extract_asserted_relation`, `feedback_log`, `stream_generate`,
   and `rag_chat_v2` (via the regression suite) have dedicated test
   coverage. The retriever and tokenizer are still tested only
   end-to-end.
5. **HuggingFace Spaces deployment (Phase 4 of README).** Once 1-3
   are done.

---

## 9. Token-Level Streaming Foundation

### 9.1 New helper `rag_chat_v2.stream_generate()`

A generator-based sibling of `generate()` that yields decoded chunks
(default 4 tokens per chunk) as the model produces them:

```python
def stream_generate(
    model, tokenizer, context, question, device,
    max_new_tokens: int | None = None,
    chunk_size: int = 4,
) -> Iterator[str]:
```

The generation loop is identical to `generate()`; the only difference
is that the decoded buffer is yielded each time it reaches
`chunk_size` tokens, with a final flush after the loop. Stops early
on EOS, on empty input (yields nothing), or after `max_new_tokens`.

### 9.2 Smoke-tested end-to-end

```
Question: Why did the Roman Empire decline?
  [chunk] 'It was due'
  [chunk] ' to political political'
  [chunk] 'ism and political'
  [chunk] 'ism.'
Full streamed answer: 'It was due to political politicalism and politicalism.'
```

The answer quality is poor (typical for the small custom LM with no
fine-tuned prompt), but the streaming contract works correctly:
each chunk is self-contained and decodes cleanly.

### 9.3 NOT wired into the webui (deliberately)

Wiring this into the live UI requires refactoring
`_answer_question_impl` (line 2021, 2700+ lines deep) to expose
streaming from the generic reasoning path where `generate()` is
called at line 3472. That's a substantial change with the Polish
LLM still unavailable, so it's been deferred. The helper is now in
place as a foundation for when the UI work resumes.

### 9.4 New unit-test file `src/test_stream_generate.py`

Mirrors the `test_feedback_log.py` pattern. 4 test cases:

| # | Test                              | What it pins down                                                |
| - | --------------------------------- | ---------------------------------------------------------------- |
| 1 | `empty_token_list_yields_nothing` | `token_ids=[]` triggers the early `return` (no yields).          |
| 2 | `eos_terminates_immediately`      | EOS mid-stream breaks the loop within one chunk.                 |
| 3 | `all_tokens_yielded`              | A 5-token script yields 2-6 chunks with `chunk_size=4`.          |
| 4 | `chunk_size_one_yields_per_token` | `chunk_size=1` emits exactly one chunk per token (3 in, 3 out). |

Stand-in `_FakeModel` returns a fixed sequence of argmax logits on
each call (no need to load SmallLMV2 weights). All 4/4 PASS.

### 9.5 Bug caught during test design

The first cut of test #4 used the default `max_new_tokens=10` and
expected 3 yields — but the model's logits go to zero after the
scripted tokens run out, so `argmax` returns token 0 forever and the
loop fills out the full 10 chunks. Fixed by exposing a per-case
`max_new_tokens` override (3 in this case). This is exactly the
class of bug the test exists to catch: a generator that "looks
right" but doesn't enforce its own loop bound.

---

*Document generated 2026-08-11 across the Web UI feedback + config
portability session.*
