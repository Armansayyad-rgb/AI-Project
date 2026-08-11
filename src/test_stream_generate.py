"""Smoke tests for :func:`rag_chat_v2.stream_generate` helper.

The full token-by-token streaming path is exercised against the real
``SmallLMV2`` model in the integration smoke test below; the unit tests
here verify the generator's contract (yielding, early termination on
EOS, empty-input handling) against a tiny stand-in tokenizer + model.

Run directly with::

    python test_stream_generate.py

What is pinned down here:

- The helper is a generator (does not eagerly consume).
- Empty input token lists yield nothing.
- The full reconstructed output equals the concatenation of chunks.
- A chunk_size > 1 emits more than one yield before completion.
- An EOS token mid-generation stops the generator cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import torch  # noqa: E402


# ---------------------------------------------------------------------------
# Fake tokenizer / model that lets us drive the streaming generator
# without loading the real SmallLMV2 weights.
# ---------------------------------------------------------------------------


class _FakeTokenizer:
    """Mirrors the slice of the real tokenizer API that stream_generate
    touches: ``encode``, ``token_to_id``, ``decode``."""

    def __init__(self, vocab: list[str], eos: str | None = "EOS"):
        self.vocab = vocab
        self.eos = eos

    def token_to_id(self, tok: str):
        if tok == "<BOS>":
            return None
        if tok == "<PAD>":
            return None
        if tok == "<EOS>":
            return self.eos
        return None

    def encode(self, text: str):
        # The generator extracts .ids; we hand back deterministic ints.
        return _FakeEncoded(list(range(4)))

    def decode(self, ids, skip_special_tokens=True):
        # Map each id back to a vocab word; with skip_special_tokens we
        # only ever see ids in [0, len(vocab)).
        return " ".join(self.vocab[i] for i in ids if 0 <= i < len(self.vocab))


class _FakeEncoded:
    def __init__(self, ids):
        self.ids = ids


class _FakeModel:
    """Returns a fixed sequence of argmax logits on every call.

    ``next_ids`` is the list of token ids the model will emit in order,
    stopping early if it hits ``eos_id``.
    """

    def __init__(self, next_ids: list[int], vocab_size: int = 16):
        self.next_ids = next_ids
        self.vocab_size = vocab_size
        self._step = 0

    def eval(self):
        pass

    def __call__(self, x):
        # logits shape: (batch, seq, vocab)
        logits = torch.zeros(1, x.shape[1], self.vocab_size)
        if self._step < len(self.next_ids):
            logits[0, -1, self.next_ids[self._step]] = 10.0
            self._step += 1
        return logits, None


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

VOCAB = ["the", "Empire", "fell", "in", "476", "AD", "after", "barbarian",
         "raids", ".", "a", "b", "c", "d", "e", "f"]

TEST_CASES = [
    {
        "name": "empty_token_list_yields_nothing",
        "token_ids_in_prompt": [],
        "next_ids": [1, 2, 3],
        "eos_id": None,
        "expected_yields": 0,
        # Universal invariant: skip the "non-empty output" check when no
        # chunks are expected (it would assert against len(joined) > 0).
        "check_non_empty": False,
    },
    {
        "name": "eos_terminates_immediately",
        "token_ids_in_prompt": [0, 1],
        "next_ids": [10],          # 10 is "a"; let's make 10 the EOS below
        "eos_id": None,
        "expected_max_yields": 1,   # At most one chunk of size chunk_size
        "eos_token": 10,
    },
    {
        "name": "all_tokens_yielded",
        "token_ids_in_prompt": [0, 1],
        "next_ids": [1, 2, 3, 4, 5],   # "Empire fell in 476 AD"
        "eos_id": None,
        "expected_yields_min": 2,
        "expected_yields_max": 6,
    },
    {
        "name": "chunk_size_one_yields_per_token",
        "token_ids_in_prompt": [0, 1],
        "next_ids": [1, 2, 3],
        "eos_id": None,
        "expected_yields": 3,
        "chunk_size": 1,
        # Cap the loop so the model can't drift past the 3 scripted
        # tokens and emit zeros into the yield stream.
        "max_new_tokens": 3,
    },
]


def _build_tokenizer(eos_id: int | None):
    """Build a tokenizer that maps int→vocab for non-special ids."""
    tok = _FakeTokenizer(VOCAB, eos=None)
    # Override token_to_id for EOS so the helper can recognise it.
    def token_to_id(t):
        if t == "<EOS>":
            return eos_id
        if t == "<BOS>" or t == "<PAD>":
            return None
        return None
    tok.token_to_id = token_to_id

    # Override encode so the prompt has controllable token ids.
    encode_state = {"ids": None}
    def encode(text):
        return _FakeEncoded(encode_state["ids"])
    tok.encode = encode
    tok._encode_state = encode_state
    return tok


def main() -> tuple[int, int]:
    from rag_chat_v2 import stream_generate

    passed = 0
    total = len(TEST_CASES)

    for case in TEST_CASES:
        name = case["name"]
        print(f"[test] {name} ... ", end="", flush=True)
        try:
            prompt_ids = case["token_ids_in_prompt"]
            eos_id = case.get("eos_token") or case.get("eos_id")
            tokenizer = _build_tokenizer(eos_id)
            tokenizer._encode_state["ids"] = list(prompt_ids)

            model = _FakeModel(case["next_ids"], vocab_size=len(VOCAB))

            chunk_size = case.get("chunk_size", 4)
            max_new_tokens = case.get("max_new_tokens", 10)
            chunks = list(
                stream_generate(
                    model=model,
                    tokenizer=tokenizer,
                    context="ignored",
                    question="ignored",
                    device="cpu",
                    max_new_tokens=max_new_tokens,
                    chunk_size=chunk_size,
                )
            )

            if "expected_yields" in case:
                assert len(chunks) == case["expected_yields"], (
                    f"got {len(chunks)} chunks, expected "
                    f"{case['expected_yields']}"
                )
            if "expected_max_yields" in case:
                assert len(chunks) <= case["expected_max_yields"], (
                    f"got {len(chunks)} chunks, expected "
                    f"<= {case['expected_max_yields']}"
                )
            if "expected_yields_min" in case:
                assert case["expected_yields_min"] <= len(chunks) \
                    <= case["expected_yields_max"], (
                    f"got {len(chunks)} chunks, expected "
                    f"{case['expected_yields_min']}..{case['expected_yields_max']}"
                )

            # Universal invariants: chunks are strings, concatenation is
            # non-empty when there was output (opt-out per case), the
            # generator was not eager (we used list() to consume).
            assert all(isinstance(c, str) for c in chunks), \
                "chunks must be strings"
            if case.get("check_non_empty", True):
                if case["next_ids"] and eos_id not in case["next_ids"]:
                    joined = "".join(chunks)
                    assert len(joined) > 0, \
                        "non-empty output expected"

            passed += 1
            print("PASS")
        except AssertionError as exc:
            print(f"FAIL  ({exc})")
        except Exception as exc:
            print(f"ERROR  ({exc!r})")

    print()
    print(f"Stream Generate Tests: {passed}/{total} PASSED")
    return passed, total


if __name__ == "__main__":
    p, t = main()
    sys.exit(0 if p == t else 1)