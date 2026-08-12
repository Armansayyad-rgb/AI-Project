import logging
import re
import sys
from pathlib import Path

import torch
from tokenizers import Tokenizer

from log_helper import setup_logging

# Resolve ``from config import ...`` to the env-var-aware config at
# ``<project>/config.py`` unambiguously. ``src/config.py`` would shadow
# this on a cwd==src/ run because it defines an unrelated
# ``MODEL_CONFIG`` dict. We load the root config by absolute path into
# ``sys.modules['config']`` BEFORE the import statement runs, so the
# lookup skips the file-system resolver entirely.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ROOT_CONFIG_PATH = _PROJECT_ROOT / "config.py"

import importlib.util as _importlib_util

_spec = _importlib_util.spec_from_file_location(
    "config", str(_ROOT_CONFIG_PATH)
)
if _spec is None or _spec.loader is None:
    raise ImportError(
        f"Could not load project config at {_ROOT_CONFIG_PATH}. "
        f"Expected an env-var-aware config.py at the project root."
    )
_project_config = _importlib_util.module_from_spec(_spec)
_project_config.__package__ = ""  # keep it as a top-level module
sys.modules["config"] = _project_config
_spec.loader.exec_module(_project_config)

from config import (  # noqa: E402
    LOGS_DIR,
    TOKENIZER_FILE,
    MODEL_FILE,
    KNOWLEDGE_FILES,
    MAX_INPUT_TOKENS,
    MAX_NEW_TOKENS,
    CONFIDENCE_THRESHOLD,
)

# Backwards-compatible alias: callers historically used ``LOG_DIR``.
LOG_DIR = LOGS_DIR

logger = setup_logging(
    log_dir=LOG_DIR,
    log_name="rag_chat",
)

from model_v2 import SmallLMV2
from extractor_v1 import extract_answer
from router_v1 import route_question
from confidence_v1 import extraction_confidence

from reasoning_confidence_v1 import (
    reasoning_support_confidence,
)

from retriever_v2 import (
    load_chunks as load_chunks_v2,
    build_index as build_index_v2,
    retrieve as retrieve_v2,
)

from retriever_v4 import (
    retrieve as retrieve_v4,
)

from query_planner_v1 import (
    build_queries,
)

from comparison_planner_v1 import (
    build_comparison_queries,
)

from comparison_retrieval_v1 import (
    retrieve_comparison,
)

from comparison_confidence_v1 import (
    score_comparison,
)

from comparison_synthesizer_v1 import (
    synthesize_comparison,
)

from causal_synthesizer_v1 import (
    synthesize_causal_answer,
)

from change_synthesizer_v1 import (
    synthesize_change_answer,
)

from effect_synthesizer_v1 import (
    synthesize_effect_answer,
)

from entity_list_synthesizer_v1 import (
    synthesize_entity_list_answer,
)

from structure_synthesizer_v1 import (
    synthesize_structure_answer,
)

from summary_synthesizer_v1 import (
    synthesize_summary_answer,
)


# All project paths and tunables are imported from the root config
# module (C:\AI-Project\config.py) at the top of this file. See
# ``from config import`` near the imports above.


# --------------------------------------------------
# General text helpers
# --------------------------------------------------

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "they",
    "their",
    "them",
    "he",
    "she",
    "his",
    "her",
    "what",
    "when",
    "where",
    "why",
    "how",
    "did",
    "does",
    "do",
    "has",
    "have",
    "had",
}


def normalize_text(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9']+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(text):
    return re.findall(
        r"[a-z0-9']+",
        text.lower(),
    )


def useful_terms(text):
    return [
        word
        for word in tokenize(
            text
        )
        if (
            word not in STOPWORDS
            and len(word) >= 3
        )
    ]


def split_sentences(text):
    if not text:
        return []

    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if sentence.strip()
    ]


def clean_relation_entity(text):
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    text = text.rstrip(
        "?.!"
    )

    text = re.sub(
        r"^(?:the process by which)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


# --------------------------------------------------
# Generation
# --------------------------------------------------

def generate(
    model,
    tokenizer,
    context,
    question,
    device,
):
    prompt = (
        "<RESULT>\n"
        f"{context}\n\n"
        "<ANSWER>\n"
        f"Question: {question}\n"
        "Answer:"
    )

    encoded = tokenizer.encode(
        prompt
    )

    token_ids = encoded.ids

    bos_id = tokenizer.token_to_id(
        "<BOS>"
    )

    eos_id = tokenizer.token_to_id(
        "<EOS>"
    )

    pad_id = tokenizer.token_to_id(
        "<PAD>"
    )

    special_ids = {
        token_id
        for token_id in [
            bos_id,
            eos_id,
            pad_id,
        ]
        if token_id is not None
    }

    token_ids = [
        token_id
        for token_id in token_ids
        if token_id not in special_ids
    ]

    token_ids = token_ids[
        -(MAX_INPUT_TOKENS - 1):
    ]

    if bos_id is not None:
        token_ids = (
            [bos_id]
            + token_ids
        )

    if not token_ids:
        return ""

    x = torch.tensor(
        [token_ids],
        dtype=torch.long,
        device=device,
    )

    generated = []

    model.eval()

    with torch.no_grad():

        for _ in range(
            MAX_NEW_TOKENS
        ):
            model_input = x[
                :,
                -MAX_INPUT_TOKENS:
            ]

            logits, _ = model(
                model_input
            )

            next_logits = logits[
                0,
                -1,
                :
            ]

            next_token = torch.argmax(
                next_logits,
                dim=-1,
            ).item()

            if (
                eos_id is not None
                and next_token == eos_id
            ):
                break

            generated.append(
                next_token
            )

            next_tensor = torch.tensor(
                [[next_token]],
                dtype=torch.long,
                device=device,
            )

            x = torch.cat(
                [
                    x,
                    next_tensor,
                ],
                dim=1,
            )

    if not generated:
        return ""

    answer = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )

    return answer.strip()


def stream_generate(
    model,
    tokenizer,
    context,
    question,
    device,
    max_new_tokens: int | None = None,
    chunk_size: int = 4,
):
    """Streaming variant of :func:`generate`.

    Yields the answer one chunk at a time (default 4 tokens per chunk)
    so callers — typically the Gradio UI — can render partial output
    without waiting for the full answer to finish.

    The generation loop is identical to ``generate()``; the only
    difference is that each decoded chunk is yielded as soon as it is
    produced. ``chunk_size`` controls how many tokens to accumulate
    before yielding; a small chunk size gives finer-grained updates
    at the cost of more Python overhead per step.

    Stops early on EOS, on empty input, or after ``max_new_tokens``
    tokens (defaults to the module-level ``MAX_NEW_TOKENS``).
    """
    cap = max_new_tokens if max_new_tokens is not None else MAX_NEW_TOKENS

    prompt = (
        "<RESULT>\n"
        f"{context}\n\n"
        "<ANSWER>\n"
        f"Question: {question}\n"
        "Answer:"
    )

    encoded = tokenizer.encode(prompt)
    token_ids = encoded.ids

    bos_id = tokenizer.token_to_id("<BOS>")
    eos_id = tokenizer.token_to_id("<EOS>")
    pad_id = tokenizer.token_to_id("<PAD>")

    special_ids = {
        token_id
        for token_id in [bos_id, eos_id, pad_id]
        if token_id is not None
    }

    token_ids = [
        token_id
        for token_id in token_ids
        if token_id not in special_ids
    ]
    token_ids = token_ids[-(MAX_INPUT_TOKENS - 1):]

    if bos_id is not None:
        token_ids = [bos_id] + token_ids

    if not token_ids:
        return

    x = torch.tensor([token_ids], dtype=torch.long, device=device)

    buffer: list[int] = []

    model.eval()

    with torch.no_grad():
        for _ in range(cap):
            model_input = x[:, -MAX_INPUT_TOKENS:]
            logits, _ = model(model_input)
            next_logits = logits[0, -1, :]
            next_token = torch.argmax(next_logits, dim=-1).item()

            if eos_id is not None and next_token == eos_id:
                break

            buffer.append(next_token)

            if len(buffer) >= chunk_size:
                yield tokenizer.decode(
                    buffer, skip_special_tokens=True
                )
                buffer = []

            next_tensor = torch.tensor(
                [[next_token]], dtype=torch.long, device=device,
            )
            x = torch.cat([x, next_tensor], dim=1)

    if buffer:
        yield tokenizer.decode(buffer, skip_special_tokens=True)


# --------------------------------------------------
# Extracted-answer formatting
# --------------------------------------------------

def format_extracted_answer(
    question,
    answer,
):
    q = question.lower().strip()

    a = (
        answer
        .strip()
        .replace(
            " - ",
            "-",
        )
    )

    a = re.sub(
        r"\s+",
        " ",
        a,
    )

    # ------------------------------------------
    # Birth
    # ------------------------------------------

    match = re.match(
        r"when was (.+?) born\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        if re.fullmatch(
            r"\d{4}",
            a,
        ):
            return (
                f"{subject} was born "
                f"in {a}."
            )

        return (
            f"{subject} was born on "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Founded
    # ------------------------------------------

    match = re.match(
        r"when was (.+?) founded\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        return (
            f"{subject} was founded in "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Established
    # ------------------------------------------

    match = re.match(
        r"when was (.+?) established\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        return (
            f"{subject} was established in "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Released
    # ------------------------------------------

    match = re.match(
        r"when was (.+?) released\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        return (
            f"{subject} was released in "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Published
    # ------------------------------------------

    match = re.match(
        r"when was (.+?) published\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        return (
            f"{subject} was published in "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Named after
    # ------------------------------------------

    match = re.match(
        r"(?:who or what|what|who) "
        r"was (.+?) named after\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        subject = (
            match.group(1)
            .strip()
        )

        return (
            f"{subject} was named after "
            f"{a.rstrip('.')}."
        )

    # ------------------------------------------
    # Why / causal
    # ------------------------------------------

    if q.startswith(
        "why "
    ):

        if a.lower().startswith(
            (
                "because ",
                "it was due to ",
                "it happened as a result of ",
            )
        ):
            return (
                a
                if a.endswith(".")
                else a + "."
            )

        match = re.match(
            r"why did (.+?) fall\??$",
            question,
            flags=re.IGNORECASE,
        )

        if match:
            subject = (
                match.group(1)
                .strip()
            )

            cause = a.rstrip(
                "."
            )

            if cause.lower().startswith(
                "first "
            ):
                cause = cause[6:]

            return (
                f"{subject} fell after "
                f"{cause}."
            )

    # ------------------------------------------
    # What caused X?
    # ------------------------------------------

    match = re.match(
        r"what caused (.+?)\??$",
        question,
        flags=re.IGNORECASE,
    )

    if match:
        event = (
            match.group(1)
            .strip()
        )

        return (
            f"{event} was caused by "
            f"{a.rstrip('.')}."
        )

    return (
        a
        if a.endswith(".")
        else a + "."
    )


# --------------------------------------------------
# Standard helpers
# --------------------------------------------------

def unsupported_answer():
    return (
        "I couldn't find enough reliable "
        "evidence in the current knowledge base."
    )


def build_system_result(
    result,
    answer=None,
):
    if answer is None:
        answer = unsupported_answer()

    result[
        "answer_type"
    ] = "system"

    result[
        "answer"
    ] = answer

    result[
        "supported"
    ] = False

    return result


def comparison_unsupported_answer(
    comparison_result,
    confidence,
):
    left_name = (
        comparison_result[
            "plan"
        ][
            "left_entity"
        ]
    )

    right_name = (
        comparison_result[
            "plan"
        ][
            "right_entity"
        ]
    )

    left_ok = (
        confidence[
            "left"
        ][
            "sufficient"
        ]
    )

    right_ok = (
        confidence[
            "right"
        ][
            "sufficient"
        ]
    )

    if (
        left_ok
        and not right_ok
    ):
        return (
            f"I found enough evidence about "
            f"{left_name}, but not enough "
            f"reliable evidence about "
            f"{right_name} in the current "
            f"knowledge base."
        )

    if (
        right_ok
        and not left_ok
    ):
        return (
            f"I found enough evidence about "
            f"{right_name}, but not enough "
            f"reliable evidence about "
            f"{left_name} in the current "
            f"knowledge base."
        )

    return (
        "I couldn't find enough reliable "
        "evidence for both sides of this "
        "comparison."
    )


# ==================================================
# ASSERTED RELATION / PREMISE VALIDATION
# ==================================================

RELATION_MARKERS = {
    "cause": [
        "cause",
        "caused",
        "causes",
        "because",
        "due to",
        "resulted in",
        "led to",
        "lead to",
    ],

    "create": [
        "create",
        "created",
        "creates",
        "produce",
        "produced",
        "produces",
        "generate",
        "generated",
        "generates",
        "form",
        "formed",
        "forms",
    ],

    "limit": [
        "limit",
        "limited",
        "limits",
        "restrict",
        "restricted",
        "restricts",
        "constrain",
        "constrained",
        "constrains",
    ],

    "function_as": [
        "functioned as",
        "functions as",
        "function as",
        "acted as",
        "acts as",
        "served as",
        "serves as",
    ],

    "structure_as": [
        "structured as",
        "structure as",
        "organized as",
        "organised as",
        "modeled as",
        "modelled as",
    ],

    # --------------------------------------------------
    # V3 cross-domain asserted actions
    # --------------------------------------------------

    "govern": [
        "govern",
        "governed",
        "governs",
        "governing",
    ],

    "organize": [
        "organize",
        "organized",
        "organizes",
        "organizing",
        "organise",
        "organised",
        "organises",
        "organising",
    ],

    "operate_as": [
        "operate as",
        "operated as",
        "operates as",
        "operating as",
    ],

    "replicate": [
        "replicate",
        "replicated",
        "replicates",
        "replicating",
        "replication",
    ],

    "separate": [
        "separate",
        "separated",
        "separates",
        "separating",
    ],

    "overthrow": [
        "overthrow",
        "overthrew",
        "overthrows",
        "overthrown",
        "overthrowing",
    ],

    "sign": [
        "sign",
        "signed",
        "signs",
        "signing",
    ],

    "invent": [
        "invent",
        "invented",
        "invents",
        "inventing",
    ],

    "perform": [
        "perform",
        "performed",
        "performs",
        "performing",
    ],

    "split": [
        "split",
        "splits",
        "splitting",
        "divide",
        "divided",
        "divides",
        "dividing",
    ],

    "describe_as": [
        " as ",
        "is a",
        "was a",
    ],
}


def extract_asserted_relation(
    question,
):
    """
    Detect a question that ASSERTS a relationship between
    two concepts.

    This is intentionally stricter than ordinary intent
    detection. The goal is to catch questions such as:

        "How did DNA create the Roman Empire?"
        "Explain how photosynthesis organized the Roman army."
        "Describe DNA as a political institution of the Roman Republic."

    Ordinary single-subject questions such as:

        "Why did the Roman Empire decline?"
        "How was the Roman army organized?"
        "How does photosynthesis work?"

    do not match and therefore do not require this extra gate.
    """

    q = re.sub(
        r"\s+",
        " ",
        question.strip(),
    )

    patterns = [
        # ------------------------------------------
        # Explicit cause
        # ------------------------------------------

        (
            "cause",
            r"^why did (.+?) cause "
            r"(.+?)[?.!]*$",
        ),

        (
            "cause",
            r"^how did (.+?) cause "
            r"(.+?)[?.!]*$",
        ),

        (
            "cause",
            r"^(?:explain|describe) how (.+?) caused "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Creation / production / generation
        # ------------------------------------------

        (
            "create",
            r"^how did (.+?) (?:create|produce|generate|form) "
            r"(.+?)[?.!]*$",
        ),

        (
            "create",
            r"^(?:explain|describe) how (.+?) "
            r"(?:create|creates|created|produce|produces|produced|"
            r"generate|generates|generated|form|forms|formed) "
            r"(.+?)[?.!]*$",
        ),

        (
            "create",
            r"^(?:explain|describe) the process by which "
            r"(.+?) (?:created|produced|generated|formed) "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Limitation / restriction
        # ------------------------------------------

        (
            "limit",
            r"^(?:describe|explain) how (.+?) "
            r"(?:limited|restricted|constrained) "
            r"(.+?)[?.!]*$",
        ),

        (
            "limit",
            r"^how did (.+?) "
            r"(?:limit|restrict|constrain) "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # X functioned / acted / served as Y
        # ------------------------------------------

        (
            "function_as",
            r"^(?:explain|describe) how (.+?) "
            r"(?:functioned|acted|served) as "
            r"(.+?)[?.!]*$",
        ),

        (
            "function_as",
            r"^how did (.+?) "
            r"(?:function|act|serve) as "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # X operated as Y
        # ------------------------------------------

        (
            "operate_as",
            r"^(?:explain|describe) how (.+?) "
            r"(?:operated|operates|operate) as "
            r"(.+?)[?.!]*$",
        ),

        (
            "operate_as",
            r"^how did (.+?) operate as "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Structure / identity-as assertions
        # ------------------------------------------

        (
            "structure_as",
            r"^(?:describe|explain) the structure of "
            r"(.+?) as (.+?)[?.!]*$",
        ),

        (
            "structure_as",
            r"^(?:describe|explain) how (.+?) was "
            r"(?:structured|organized|organised) as "
            r"(.+?)[?.!]*$",
        ),

        # Catches adversarial identity/metaphor claims such as
        # "Describe the Roman Empire as a stage of mitosis."
        # and "Describe DNA as a political institution ...".
        (
            "describe_as",
            r"^describe (.+?) as (.+?)[?.!]*$",
        ),

        (
            "describe_as",
            r"^explain (.+?) as (.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Governance / organization
        # ------------------------------------------

        (
            "govern",
            r"^(?:describe|explain) how (.+?) "
            r"(?:governed|governs|govern) "
            r"(.+?)[?.!]*$",
        ),

        (
            "govern",
            r"^how did (.+?) govern "
            r"(.+?)[?.!]*$",
        ),

        (
            "organize",
            r"^(?:describe|explain) how (.+?) "
            r"(?:organized|organised|organizes|organises|organize|organise) "
            r"(.+?)[?.!]*$",
        ),

        (
            "organize",
            r"^how did (.+?) "
            r"(?:organize|organise) "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Replication / separation
        # ------------------------------------------

        (
            "replicate",
            r"^(?:describe|explain) how (.+?) "
            r"(?:replicated|replicates|replicate) "
            r"(.+?)[?.!]*$",
        ),

        (
            "replicate",
            r"^how did (.+?) replicate "
            r"(.+?)[?.!]*$",
        ),

        (
            "separate",
            r"^(?:describe|explain) how (.+?) "
            r"(?:separated|separates|separate) "
            r"(.+?)[?.!]*$",
        ),

        (
            "separate",
            r"^how did (.+?) separate "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Overthrow / sign / invent / perform / split
        # ------------------------------------------

        (
            "overthrow",
            r"^why did (.+?) overthrow "
            r"(.+?)[?.!]*$",
        ),

        (
            "overthrow",
            r"^how did (.+?) overthrow "
            r"(.+?)[?.!]*$",
        ),

        (
            "overthrow",
            r"^what caused (.+?) to overthrow "
            r"(.+?)[?.!]*$",
        ),

        (
            "sign",
            r"^(?:why|how) did (.+?) sign "
            r"(.+?)[?.!]*$",
        ),

        (
            "invent",
            r"^(?:explain|describe) (?:why|how) (.+?) "
            r"(?:invented|invents|invent) "
            r"(.+?)[?.!]*$",
        ),

        (
            "perform",
            r"^(?:explain|describe) (?:why|how) (.+?) "
            r"(?:performed|performs|perform) "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^(?:explain|describe) how (.+?) "
            r"(?:split|splits) "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^how did (.+?) split "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^why did (.+?) divide "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^how did (.+?) divide "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^(?:explain|describe) how (.+?) "
            r"(?:divide|divides|divided) "
            r"(.+?)[?.!]*$",
        ),

        # ------------------------------------------
        # Additional why-form asserted relations
        # ------------------------------------------

        (
            "create",
            r"^why did (.+?) "
            r"(?:create|produce|generate|form) "
            r"(.+?)[?.!]*$",
        ),

        (
            "invent",
            r"^why did (.+?) "
            r"(?:invent|discover|develop) "
            r"(.+?)[?.!]*$",
        ),

        (
            "limit",
            r"^why did (.+?) "
            r"(?:limit|restrict|constrain) "
            r"(.+?)[?.!]*$",
        ),

        (
            "organize",
            r"^why did (.+?) "
            r"(?:organize|organise) "
            r"(.+?)[?.!]*$",
        ),

        (
            "split",
            r"^why did (.+?) split "
            r"(.+?)[?.!]*$",
        ),

        (
            "separate",
            r"^why did (.+?) separate "
            r"(.+?)[?.!]*$",
        ),

        (
            "replicate",
            r"^why did (.+?) replicate "
            r"(.+?)[?.!]*$",
        ),

        (
            "cause",
            r"^why did (.+?) "
            r"(?:lead|cause) "
            r"(.+?)[?.!]*$",
        ),
    ]

    for relation, pattern in patterns:
        match = re.fullmatch(
            pattern,
            q,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        source = clean_relation_entity(
            match.group(1)
        )

        target = clean_relation_entity(
            match.group(2)
        )

        if (
            not source
            or not target
        ):
            continue

        return {
            "relation":
                relation,

            "source":
                source,

            "target":
                target,
        }

    return None


def term_coverage(
    required_terms,
    sentence_terms,
):
    required_terms = set(
        required_terms
    )

    sentence_terms = set(
        sentence_terms
    )

    if not required_terms:
        return 0.0

    return (
        len(
            required_terms
            & sentence_terms
        )
        / len(
            required_terms
        )
    )


def relation_sentence_support(
    sentence,
    relation_info,
):
    sentence_normalized = normalize_text(
        sentence
    )

    sentence_terms = useful_terms(
        sentence
    )

    source_terms = useful_terms(
        relation_info[
            "source"
        ]
    )

    target_terms = useful_terms(
        relation_info[
            "target"
        ]
    )

    if (
        not source_terms
        or not target_terms
    ):
        return False

    source_coverage = term_coverage(
        source_terms,
        sentence_terms,
    )

    target_coverage = term_coverage(
        target_terms,
        sentence_terms,
    )

    # Require meaningful evidence for BOTH sides
    # of the asserted relation in the SAME sentence.
    # This prevents evidence about only one side from
    # being mistaken for evidence of the relationship.
    if source_coverage < 0.60:
        return False

    if target_coverage < 0.60:
        return False

    relation = relation_info[
        "relation"
    ]

    markers = RELATION_MARKERS.get(
        relation,
        [],
    )

    # "describe_as" uses the word "as" as a relational
    # bridge. normalize_text removes punctuation but keeps
    # spaces, so use token-aware checks rather than the
    # literal " as " marker stored above.
    if relation == "describe_as":
        words = sentence_normalized.split()

        if "as" not in words:
            return False

        return True

    marker_found = any(
        marker in sentence_normalized
        for marker in markers
    )

    return marker_found


def validate_asserted_relation(
    question,
    context,
):
    relation_info = (
        extract_asserted_relation(
            question
        )
    )

    # No asserted cross-concept relation:
    # no extra premise gate required.
    if relation_info is None:
        return {
            "required":
                False,

            "supported":
                True,

            "relation":
                None,

            "source":
                None,

            "target":
                None,

            "supporting_sentence":
                None,
        }

    for sentence in split_sentences(
        context
    ):
        if relation_sentence_support(
            sentence,
            relation_info,
        ):
            return {
                "required":
                    True,

                "supported":
                    True,

                "relation":
                    relation_info[
                        "relation"
                    ],

                "source":
                    relation_info[
                        "source"
                    ],

                "target":
                    relation_info[
                        "target"
                    ],

                "supporting_sentence":
                    sentence,
            }

    return {
        "required":
            True,

        "supported":
            False,

        "relation":
            relation_info[
                "relation"
            ],

        "source":
            relation_info[
                "source"
            ],

        "target":
            relation_info[
                "target"
            ],

        "supporting_sentence":
            None,
    }


# ==================================================
# INTENT-CANONICAL QUESTION HELPERS
# ==================================================

def canonical_question_for_intent(
    question,
    plan,
):
    """
    Return the canonical question produced by the
    query planner whenever possible.

    rag_chat_v2 should not independently reconstruct
    paraphrase normalization when query_planner_v1
    has already done that work.
    """

    if not plan:
        return question

    canonical_question = (
        plan.get(
            "canonical_question"
        )
        or ""
    ).strip()

    if canonical_question:
        return canonical_question

    intent = (
        plan.get(
            "intent",
            "general",
        )
        or "general"
    )

    subject = (
        plan.get(
            "subject",
            "",
        )
        or ""
    ).strip()

    if (
        not subject
        or intent == "general"
    ):
        return question

    if intent == "cause":
        return (
            f"Why did {subject} decline?"
        )

    if intent == "change":
        return (
            f"How did {subject} "
            f"change over time?"
        )

    if intent == "effect":
        return (
            f"What were the effects of "
            f"{subject}?"
        )

    if intent == "structure":
        return (
            f"What is the structure of "
            f"{subject}?"
        )

    if intent == "process":
        return (
            f"Explain how {subject} works."
        )

    if intent == "features":
        return (
            f"What were the main features "
            f"of {subject}?"
        )

    if intent == "significance":
        return (
            f"What is the significance of "
            f"{subject}?"
        )

    if intent == "entity_list":
        return (
            f"Who were the key figures of "
            f"{subject}?"
        )

    return question


# --------------------------------------------------
# Retrieval wrappers
# --------------------------------------------------

def retrieve_for_extractor(
    question,
    chunks,
    retrieval_index,
    document_frequency,
):
    results = retrieve_v2(
        question,
        chunks,
        retrieval_index,
        document_frequency,
    )

    if not results:
        return None

    return results[0]


def retrieve_for_reasoning(
    question,
    chunks,
    retrieval_index,
    document_frequency,
):
    retrieval = retrieve_v4(
        question,
        chunks,
        retrieval_index,
        document_frequency,
    )

    if not retrieval:
        return None

    if not retrieval.get(
        "results"
    ):
        return None

    return retrieval


# --------------------------------------------------
# Pipeline initialization
# --------------------------------------------------

def initialize_pipeline(
    verbose=True,
):
    logger.info(
        "Initializing rag_chat pipeline"
    )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    logger.info(
        "Pipeline device selected: %s",
        device,
    )

    if verbose:
        print(
            "Device:",
            device,
        )

    try:
        tokenizer = Tokenizer.from_file(
            str(
                TOKENIZER_FILE
            )
        )
    except Exception as exc:
        logger.error(
            "Failed to load tokenizer from %s",
            TOKENIZER_FILE,
            exc_info=True,
        )
        raise

    model = SmallLMV2().to(
        device
    )

    try:
        state_dict = torch.load(
            MODEL_FILE,
            map_location=device,
            weights_only=True,
        )
    except Exception as exc:
        logger.error(
            "Failed to load model checkpoint from %s",
            MODEL_FILE,
            exc_info=True,
        )
        raise

    model.load_state_dict(
        state_dict
    )

    model.eval()

    logger.info(
        "Reasoning V1 model loaded from %s",
        MODEL_FILE,
    )

    if verbose:
        print(
            "Reasoning V1 model loaded."
        )

    try:
        chunks = load_chunks_v2(
            KNOWLEDGE_FILES
        )
    except Exception as exc:
        logger.error(
            "Failed to load knowledge chunks",
            exc_info=True,
        )
        raise

    logger.info(
        "Loaded %d knowledge chunks",
        len(chunks),
    )

    try:
        (
            retrieval_index,
            document_frequency,
        ) = build_index_v2(
            chunks
        )
    except Exception as exc:
        logger.error(
            "Failed to build retrieval index",
            exc_info=True,
        )
        raise

    logger.info(
        "Retrieval index built (chunks=%d)",
        len(chunks),
    )

    logger.info(
        "Pipeline initialization complete"
    )

    return {
        "device":
            device,

        "tokenizer":
            tokenizer,

        "model":
            model,

        "chunks":
            chunks,

        "retrieval_index":
            retrieval_index,

        "document_frequency":
            document_frequency,
    }


# ==================================================
# RUNTIME INTENT PLANNING
# ==================================================

PLANNED_REASONING_INTENTS = {
    "cause",
    "change",
    "effect",
    "structure",
    "process",
    "features",
    "significance",
    "entity_list",
    "comparison",
}


def runtime_plan(
    question,
):
    """
    Build the semantic plan BEFORE the legacy router.

    This prevents route_question() from incorrectly
    sending recognized reasoning/paraphrase questions
    into the extractor route.
    """

    try:
        plan = build_queries(
            question
        )

    except Exception:
        plan = {
            "intent":
                "general",

            "subject":
                "",

            "canonical_question":
                None,

            "comparison_subjects":
                None,

            "queries":
                [question],
        }

    if not isinstance(
        plan,
        dict,
    ):
        plan = {
            "intent":
                "general",

            "subject":
                "",

            "canonical_question":
                None,

            "comparison_subjects":
                None,

            "queries":
                [question],
        }

    # --------------------------------------------------
    # Comparison planner is also allowed to upgrade
    # a query to comparison even when the general
    # query planner misses a wording variant.
    # --------------------------------------------------

    try:
        comparison_plan = (
            build_comparison_queries(
                question
            )
        )
    except Exception:
        comparison_plan = None

    if comparison_plan is not None:

        left = (
            comparison_plan.get(
                "left_entity"
            )
            or ""
        ).strip()

        right = (
            comparison_plan.get(
                "right_entity"
            )
            or ""
        ).strip()

        if left and right:
            plan[
                "intent"
            ] = "comparison"

            plan[
                "subject"
            ] = (
                f"{left} vs {right}"
            )

            plan[
                "comparison_subjects"
            ] = (
                left,
                right,
            )

            plan[
                "canonical_question"
            ] = (
                "What are the differences "
                f"between {left} and {right}?"
            )

    return plan


def should_force_reasoning(
    plan,
):
    if not plan:
        return False

    intent = (
        plan.get(
            "intent",
            "general",
        )
        or "general"
    )

    return (
        intent
        in PLANNED_REASONING_INTENTS
    )


# ==================================================
# SINGLE-QUESTION PROCESSOR
# ==================================================

def answer_question(
    pipeline,
    question,
    verbose=True,
):
    logger.info(
        "Question received: %s",
        question,
    )

    try:
        return _answer_question_impl(
            pipeline,
            question,
            verbose,
        )
    except Exception as exc:
        logger.error(
            "Unhandled error while answering question: %r",
            question,
            exc_info=True,
        )
        raise


def _answer_question_impl(
    pipeline,
    question,
    verbose=True,
):
    device = pipeline[
        "device"
    ]

    tokenizer = pipeline[
        "tokenizer"
    ]

    model = pipeline[
        "model"
    ]

    chunks = pipeline[
        "chunks"
    ]

    retrieval_index = pipeline[
        "retrieval_index"
    ]

    document_frequency = pipeline[
        "document_frequency"
    ]

    # ==================================================
    # SEMANTIC PLAN FIRST
    # ==================================================

    plan = runtime_plan(
        question
    )

    planned_intent = (
        plan.get(
            "intent",
            "general",
        )
        or "general"
    )

    canonical_question = (
        canonical_question_for_intent(
            question,
            plan,
        )
    )

    logger.debug(
        "Semantic plan: intent=%s subject=%r",
        planned_intent,
        plan.get("subject"),
    )

    # ==================================================
    # LEGACY ROUTER SECOND
    # ==================================================

    route = route_question(
        question
    )

    # If the semantic planner has positively identified
    # a reasoning intent, never allow the old router to
    # divert it into the extractor path.
    if should_force_reasoning(
        plan
    ):
        route = "model"

    logger.debug(
        "Routing decision: router=%s planned_intent=%s "
        "effective_route=%s",
        route,
        planned_intent,
        route,
    )

    if verbose:
        print(
            "\nRouter:",
            route,
        )

        print(
            "Planned intent:",
            planned_intent,
        )

        print(
            "Planned subject:",
            plan.get(
                "subject"
            ),
        )

        print(
            "Canonical question:",
            canonical_question,
        )

    result = {
        "question":
            question,

        "router":
            route,

        "mode":
            None,

        "retriever":
            None,

        "answer_type":
            None,

        "answer":
            None,

        "supported":
            False,

        "runtime_plan":
            plan,

        "canonical_question":
            canonical_question,
    }

    # ==================================================
    # ASSERTED RELATION DETECTION
    # ==================================================

    asserted_relation = (
        extract_asserted_relation(
            question
        )
    )

    result[
        "asserted_relation"
    ] = asserted_relation

    # ==================================================
    # EARLY PREMISE VALIDATION
    #
    # Critical fix:
    # Explicit cross-concept relations are checked
    # before extractor output can be accepted.
    # ==================================================

    if asserted_relation is not None:

        premise_retrieval = (
            retrieve_for_reasoning(
                question,
                chunks,
                retrieval_index,
                document_frequency,
            )
        )

        if premise_retrieval is None:
            result[
                "premise_validation"
            ] = {
                "required":
                    True,

                "supported":
                    False,

                "relation":
                    asserted_relation[
                        "relation"
                    ],

                "source":
                    asserted_relation[
                        "source"
                    ],

                "target":
                    asserted_relation[
                        "target"
                    ],

                "supporting_sentence":
                    None,
            }

            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nPremise validation: "
                    "UNSUPPORTED"
                )

                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        premise_context = (
            premise_retrieval.get(
                "context",
                "",
            )
            or ""
        )

        premise_validation = (
            validate_asserted_relation(
                question,
                premise_context,
            )
        )

        result[
            "premise_validation"
        ] = premise_validation

        if verbose:
            print(
                "\nAsserted relation:"
            )

            print(
                "Relation:",
                premise_validation.get(
                    "relation"
                ),
            )

            print(
                "Source:",
                premise_validation.get(
                    "source"
                ),
            )

            print(
                "Target:",
                premise_validation.get(
                    "target"
                ),
            )

            print(
                "Supported:",
                premise_validation.get(
                    "supported"
                ),
            )

        if not premise_validation[
            "supported"
        ]:
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

    # ==================================================
    # EXTRACTOR ROUTE
    # ==================================================

    if route == "extractor":

        best_result = (
            retrieve_for_extractor(
                question,
                chunks,
                retrieval_index,
                document_frequency,
            )
        )

        logger.debug(
            "Extractor retrieval: hits=%d",
            1 if best_result is not None else 0,
        )

        result[
            "retriever"
        ] = "V2"

        if best_result is None:
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        context = best_result[
            "chunk"
        ]

        result[
            "context"
        ] = context

        result[
            "retrieval_score"
        ] = best_result.get(
            "final_score",
            0.0,
        )

        if verbose:
            print(
                "\nRetriever: V2"
            )

            print(
                "\n--- Retrieved context ---\n"
            )

            print(
                context
            )

            print(
                "\nRetrieval score:",
                f"{result['retrieval_score']:.2f}",
            )

        extracted = extract_answer(
            question,
            context,
        )

        if not extracted:
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        confidence = (
            extraction_confidence(
                question,
                context,
                extracted,
            )
        )

        result[
            "confidence"
        ] = confidence

        if verbose:
            print(
                "\nExtraction confidence:",
                f"{confidence:.2f}",
            )

        if (
            confidence
            < CONFIDENCE_THRESHOLD
        ):
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        answer = format_extracted_answer(
            question,
            extracted,
        )

        result[
            "answer_type"
        ] = "extractor"

        result[
            "answer"
        ] = answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (extractor): %s",
            answer,
        )

        if verbose:
            print(
                "\nExtractor:",
                answer,
            )

        return result

    # ==================================================
    # COMPARISON ROUTE
    # ==================================================

    comparison_plan = None

    if planned_intent == "comparison":

        comparison_subjects = (
            plan.get(
                "comparison_subjects"
            )
        )

        if comparison_subjects:
            left, right = (
                comparison_subjects
            )

            comparison_plan = {
                "left_entity":
                    left,

                "right_entity":
                    right,

                "left_query":
                    left,

                "right_query":
                    right,
            }

        else:
            comparison_plan = (
                build_comparison_queries(
                    question
                )
            )

    if comparison_plan is not None:

        result[
            "mode"
        ] = "comparison"

        if verbose:
            print(
                "\nMode: comparison"
            )

        comparison_query = (
            canonical_question
            if canonical_question
            else question
        )

        comparison_result = (
            retrieve_comparison(
                comparison_query,
                chunks,
                retrieval_index,
                document_frequency,
            )
        )

        logger.debug(
            "Comparison retrieval: hits=%s",
            (
                "yes"
                if comparison_result is not None
                else "no"
            ),
        )

        if comparison_result is None:
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        comparison_confidence = (
            score_comparison(
                comparison_result
            )
        )

        result[
            "comparison_confidence"
        ] = comparison_confidence

        left_score = (
            comparison_confidence[
                "left"
            ][
                "score"
            ]
        )

        right_score = (
            comparison_confidence[
                "right"
            ][
                "score"
            ]
        )

        if verbose:
            print(
                "\nComparison confidence:"
            )

            print(
                "Left:",
                f"{left_score:.2f}",
            )

            print(
                "Right:",
                f"{right_score:.2f}",
            )

        if not comparison_confidence[
            "sufficient"
        ]:
            answer = (
                comparison_unsupported_answer(
                    comparison_result,
                    comparison_confidence,
                )
            )

            result = build_system_result(
                result,
                answer=answer,
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        comparison_context = (
            comparison_result[
                "context"
            ]
        )

        result[
            "context"
        ] = comparison_context

        if verbose:
            print(
                "\n--- Comparison evidence ---\n"
            )

            print(
                comparison_context
            )

        answer = synthesize_comparison(
            comparison_query,
            comparison_result,
        )

        if not answer:
            result = build_system_result(
                result
            )

            if verbose:
                print(
                    "\nSystem:",
                    result["answer"],
                )

            return result

        result[
            "answer_type"
        ] = "comparison"

        result[
            "answer"
        ] = answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (comparison): %s",
            answer,
        )

        if verbose:
            print(
                "\nComparison synthesizer:",
                answer,
            )

        return result

    # ==================================================
    # NORMAL REASONING ROUTE
    # ==================================================

    retrieval = retrieve_for_reasoning(
        question,
        chunks,
        retrieval_index,
        document_frequency,
    )

    result[
        "retriever"
    ] = "V4"

    retrieval_chunk_count = 0
    if (
        retrieval is not None
        and isinstance(
            retrieval.get("results"),
            list,
        )
    ):
        retrieval_chunk_count = len(
            retrieval["results"]
        )

    logger.debug(
        "Reasoning retrieval (V4): chunks=%d",
        retrieval_chunk_count,
    )

    if retrieval is None:
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    best_result = retrieval.get(
        "best"
    )

    reasoning_context = (
        retrieval.get(
            "context",
            "",
        )
        or ""
    )

    retrieval_plan = (
        retrieval.get(
            "plan",
            {}
        )
        or {}
    )

    # Prefer the plan computed before routing.
    #
    # Retriever V4's returned plan is retained for
    # diagnostics, but the runtime plan is the primary
    # semantic decision because it already prevented
    # incorrect extractor routing.

    effective_plan = (
        plan
        if (
            plan
            and plan.get(
                "intent",
                "general",
            ) != "general"
        )
        else retrieval_plan
    )

    result[
        "retrieval_plan"
    ] = effective_plan

    result[
        "retriever_plan_raw"
    ] = retrieval_plan

    if best_result is None:
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    result[
        "context"
    ] = reasoning_context

    result[
        "retrieval_score"
    ] = best_result.get(
        "merged_score",
        0.0,
    )

    if verbose:
        print(
            "\nRetriever: V4"
        )

        print(
            "\nIntent:",
            effective_plan.get(
                "intent"
            ),
        )

        print(
            "Subject:",
            effective_plan.get(
                "subject"
            ),
        )

        print(
            "\nBest retrieval score:",
            f"{result['retrieval_score']:.2f}",
        )

        print(
            "\n--- Aggregated evidence ---\n"
        )

        print(
            reasoning_context
        )

    if not reasoning_context.strip():
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    # ==================================================
    # SECOND PREMISE CHECK
    #
    # Defensive check before any deterministic
    # synthesizer can accept the question.
    # ==================================================

    premise_validation = (
        validate_asserted_relation(
            question,
            reasoning_context,
        )
    )

    result[
        "premise_validation"
    ] = premise_validation

    if (
        premise_validation[
            "required"
        ]
        and not premise_validation[
            "supported"
        ]
    ):
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nPremise validation: "
                "UNSUPPORTED"
            )

            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    # ==================================================
    # CANONICALIZE PARAPHRASED INTENT
    # ==================================================

    canonical_question = (
        canonical_question_for_intent(
            question,
            effective_plan,
        )
    )

    result[
        "canonical_question"
    ] = canonical_question

    intent = (
        effective_plan.get(
            "intent",
            "general",
        )
        or "general"
    )

    if verbose:
        if (
            canonical_question
            != question
        ):
            print(
                "\nCanonical question:",
                canonical_question,
            )

    # ==================================================
    # INTENT-FIRST DETERMINISTIC SYNTHESIS
    # ==================================================

    # ------------------------------------------
    # Causal
    # ------------------------------------------

    if intent == "cause":

        answer = synthesize_causal_answer(
            canonical_question,
            reasoning_context,
        )

        if answer:
            result[
                "answer_type"
            ] = "causal"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (causal): %s",
                answer,
            )

            if verbose:
                print(
                    "\nCausal synthesizer:",
                    answer,
                )

            return result

    # ------------------------------------------
    # Change
    # ------------------------------------------

    elif intent == "change":

        answer = synthesize_change_answer(
            canonical_question,
            reasoning_context,
        )

        if answer:
            result[
                "answer_type"
            ] = "change"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (change): %s",
                answer,
            )

            if verbose:
                print(
                    "\nChange synthesizer:",
                    answer,
                )

            return result

    # ------------------------------------------
    # Effect
    # ------------------------------------------

    elif intent == "effect":

        answer = synthesize_effect_answer(
            canonical_question,
            reasoning_context,
        )

        if answer:
            result[
                "answer_type"
            ] = "effect"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (effect): %s",
                answer,
            )

            if verbose:
                print(
                    "\nEffect synthesizer:",
                    answer,
                )

            return result

    # ------------------------------------------
    # Entity list
    # ------------------------------------------

    elif intent == "entity_list":

        answer = (
            synthesize_entity_list_answer(
                canonical_question,
                reasoning_context,
            )
        )

        if answer:
            result[
                "answer_type"
            ] = "entity_list"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (entity_list): %s",
                answer,
            )

            if verbose:
                print(
                    "\nEntity-list synthesizer:",
                    answer,
                )

            return result

    # ------------------------------------------
    # Structure
    # ------------------------------------------

    elif intent == "structure":

        answer = (
            synthesize_structure_answer(
                canonical_question,
                reasoning_context,
            )
        )

        if answer:
            result[
                "answer_type"
            ] = "structure"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (structure): %s",
                answer,
            )

            if verbose:
                print(
                    "\nStructure synthesizer:",
                    answer,
                )

            return result

    # ------------------------------------------
    # Process / significance / features
    #
    # These are handled by summary synthesizer.
    # ------------------------------------------

    elif intent in {
        "process",
        "significance",
        "features",
    }:

        answer = (
            synthesize_summary_answer(
                canonical_question,
                reasoning_context,
            )
        )

        if answer:
            result[
                "answer_type"
            ] = "summary"

            result[
                "answer"
            ] = answer

            result[
                "supported"
            ] = True

            logger.info(
                "Answer generated (summary): %s",
                answer,
            )

            if verbose:
                print(
                    "\nSummary synthesizer:",
                    answer,
                )

            return result

    # ==================================================
    # ORIGINAL-WORDING DETERMINISTIC FALLBACK
    #
    # Keeps compatibility with existing behavior.
    # ==================================================

    causal_answer = (
        synthesize_causal_answer(
            question,
            reasoning_context,
        )
    )

    if causal_answer:
        result[
            "answer_type"
        ] = "causal"

        result[
            "answer"
        ] = causal_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (causal-fallback): %s",
            causal_answer,
        )

        if verbose:
            print(
                "\nCausal synthesizer:",
                causal_answer,
            )

        return result

    change_answer = (
        synthesize_change_answer(
            question,
            reasoning_context,
        )
    )

    if change_answer:
        result[
            "answer_type"
        ] = "change"

        result[
            "answer"
        ] = change_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (change-fallback): %s",
            change_answer,
        )

        if verbose:
            print(
                "\nChange synthesizer:",
                change_answer,
            )

        return result

    effect_answer = (
        synthesize_effect_answer(
            question,
            reasoning_context,
        )
    )

    if effect_answer:
        result[
            "answer_type"
        ] = "effect"

        result[
            "answer"
        ] = effect_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (effect-fallback): %s",
            effect_answer,
        )

        if verbose:
            print(
                "\nEffect synthesizer:",
                effect_answer,
            )

        return result

    entity_list_answer = (
        synthesize_entity_list_answer(
            question,
            reasoning_context,
        )
    )

    if entity_list_answer:
        result[
            "answer_type"
        ] = "entity_list"

        result[
            "answer"
        ] = entity_list_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (entity_list-fallback): %s",
            entity_list_answer,
        )

        if verbose:
            print(
                "\nEntity-list synthesizer:",
                entity_list_answer,
            )

        return result

    structure_answer = (
        synthesize_structure_answer(
            question,
            reasoning_context,
        )
    )

    if structure_answer:
        result[
            "answer_type"
        ] = "structure"

        result[
            "answer"
        ] = structure_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (structure-fallback): %s",
            structure_answer,
        )

        if verbose:
            print(
                "\nStructure synthesizer:",
                structure_answer,
            )

        return result

    summary_answer = (
        synthesize_summary_answer(
            question,
            reasoning_context,
        )
    )

    if summary_answer:
        result[
            "answer_type"
        ] = "summary"

        result[
            "answer"
        ] = summary_answer

        result[
            "supported"
        ] = True

        logger.info(
            "Answer generated (summary-fallback): %s",
            summary_answer,
        )

        if verbose:
            print(
                "\nSummary synthesizer:",
                summary_answer,
            )

        return result

    # ==================================================
    # GENERIC REASONING SUPPORT GATE
    # ==================================================

    reasoning_support = (
        reasoning_support_confidence(
            question=question,
            context=reasoning_context,
            retrieval_score=result.get(
                "retrieval_score",
                0.0,
            ),
        )
    )

    if not isinstance(
        reasoning_support,
        dict,
    ):
        reasoning_support = {
            "score":
                0.0,

            "sufficient":
                False,

            "term_coverage":
                0.0,

            "supporting_sentences":
                0,

            "best_sentence_overlap":
                0.0,

            "matched_terms":
                [],
        }

    result[
        "reasoning_support"
    ] = reasoning_support

    support_score = reasoning_support.get(
        "score",
        0.0,
    )

    term_coverage = reasoning_support.get(
        "term_coverage",
        0.0,
    )

    supporting_sentences = (
        reasoning_support.get(
            "supporting_sentences",
            0,
        )
    )

    best_sentence_overlap = (
        reasoning_support.get(
            "best_sentence_overlap",
            0.0,
        )
    )

    matched_terms = reasoning_support.get(
        "matched_terms",
        [],
    )

    sufficient = bool(
        reasoning_support.get(
            "sufficient",
            False,
        )
    )

    if verbose:
        print(
            "\nReasoning fallback support:"
        )

        print(
            "Score:",
            f"{support_score:.2f}",
        )

        print(
            "Coverage:",
            f"{term_coverage:.2f}",
        )

        print(
            "Supporting sentences:",
            supporting_sentences,
        )

        print(
            "Best sentence overlap:",
            f"{best_sentence_overlap:.2f}",
        )

        print(
            "Matched terms:",
            matched_terms,
        )

    if not sufficient:
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    # ==================================================
    # GENERIC REASONING MODEL
    # ==================================================

    answer = generate(
        model,
        tokenizer,
        reasoning_context,
        question,
        device,
    )

    if not answer:
        result = build_system_result(
            result
        )

        if verbose:
            print(
                "\nSystem:",
                result["answer"],
            )

        return result

    result[
        "answer_type"
    ] = "reasoning_model"

    result[
        "answer"
    ] = answer

    result[
        "supported"
    ] = True

    logger.info(
        "Answer generated (reasoning_model): %s",
        answer,
    )

    if verbose:
        print(
            "\nReasoning model:",
            answer,
        )

    return result


# --------------------------------------------------
# Startup display
# --------------------------------------------------

def print_system_info():
    print(
        "\nHybrid retrieval enabled:"
    )

    print(
        "Extractor route -> Retriever V2"
    )

    print(
        "Reasoning route -> Retriever V4"
    )

    print(
        "Asserted relations -> "
        "early premise validation gate"
    )

    print(
        "Causal reasoning -> "
        "Retriever V4 + causal synthesizer"
    )

    print(
        "Change reasoning -> "
        "Retriever V4 + change synthesizer"
    )

    print(
        "Effect reasoning -> "
        "Retriever V4 + effect synthesizer"
    )

    print(
        "Entity-list reasoning -> "
        "Retriever V4 + entity-list synthesizer"
    )

    print(
        "Structure reasoning -> "
        "Retriever V4 + structure synthesizer"
    )

    print(
        "Summary reasoning -> "
        "Retriever V4 + summary synthesizer"
    )

    print(
        "Paraphrases -> "
        "V4 intent canonicalization"
    )

    print(
        "Comparison route -> "
        "adaptive dual retrieval "
        "+ confidence gate "
        "+ deterministic synthesizer"
    )

    print(
        "Generic reasoning fallback -> "
        "V4 support gate + reasoning model"
    )

    print(
        "\nKnowledge sources:"
    )

    for path in KNOWLEDGE_FILES:
        print(
            "-",
            path,
        )


# --------------------------------------------------
# Interactive main
# --------------------------------------------------

def main():
    pipeline = initialize_pipeline(
        verbose=True,
    )

    print_system_info()

    print(
        "\nSystem ready."
    )

    print(
        "Type 'quit' to exit."
    )

    while True:
        question = input(
            "\nYou: "
        ).strip()

        if question.lower() in {
            "quit",
            "exit",
        }:
            break

        if not question:
            continue

        answer_question(
            pipeline,
            question,
            verbose=True,
        )


if __name__ == "__main__":
    main()
    