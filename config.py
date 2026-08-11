"""
Centralized configuration for the AI-Project RAG chat pipeline.

All paths and runtime settings live here so callers can override them
through environment variables without editing source files. This module
works the same on Windows, Linux, and macOS - only defaults vary.

Usage
-----
    # Use defaults (C:\\AI-Project\\... on Windows, ./AI-Project on others)
    from config import TOKENIZER_FILE, MODEL_FILE, KNOWLEDGE_FILES

    # Override per-process
    #   set AI_PROJECT_ROOT=/opt/ai-project
    #   set MODEL_FILE=C:\\models\\v2\\reasoning_model_v1.pt
"""

from __future__ import annotations

import os
from pathlib import Path


# ----------------------------------------------------------------------
# Project root resolution
# ----------------------------------------------------------------------

# Resolve the project root in this priority:
#   1. AI_PROJECT_ROOT environment variable (explicit override)
#   2. The parent of this file when it lives at <project>/config.py
#   3. The Windows default of C:\\AI-Project\\ (project's original home)
#
# On Linux/macOS the default differs from Windows so we pick the right one
# based on the current platform.

def _default_project_root() -> Path:
    """Pick a sensible default project root for the current platform."""
    if os.name == "nt":
        # Original Windows project home.
        return Path("C:/AI-Project")
    # POSIX - default to a sibling folder beside whatever sits at $HOME,
    # or fall back to a literal "AI-Project" if needed.
    return Path.home() / "AI-Project"


PROJECT_ROOT: Path = Path(
    os.environ.get(
        "AI_PROJECT_ROOT",
        str(_default_project_root()),
    )
).expanduser().resolve()


# ----------------------------------------------------------------------
# Data and checkpoint directory layout
# ----------------------------------------------------------------------
#
# We mirror the on-disk layout used by the project's build scripts:
#   <root>/data/         <- tokenizer and knowledge corpus text files
#   <root>/checkpoints/  <- trained model weights (.pt files)
#
# Both directories can also be overridden independently via env vars.

#: Directory holding tokenizer JSON files and knowledge corpus text files.
DATA_DIR: Path = Path(
    os.environ.get(
        "AI_PROJECT_DATA_DIR",
        str(PROJECT_ROOT / "data"),
    )
).expanduser().resolve()

#: Directory holding trained model checkpoints (.pt files).
CHECKPOINTS_DIR: Path = Path(
    os.environ.get(
        "AI_PROJECT_CHECKPOINTS_DIR",
        str(PROJECT_ROOT / "checkpoints"),
    )
).expanduser().resolve()


# ----------------------------------------------------------------------
# Logs directory
# ----------------------------------------------------------------------
#
# Single source of truth for where the project writes its rotating
# log files and other generated artifacts (feedback jsonl, exported
# chats, etc.). Derived from ``PROJECT_ROOT`` so it follows the same
# env-var override contract. Override with AI_PROJECT_LOGS_DIR.

LOGS_DIR: Path = Path(
    os.environ.get(
        "AI_PROJECT_LOGS_DIR",
        str(PROJECT_ROOT / "logs"),
    )
).expanduser().resolve()


# ----------------------------------------------------------------------
# Model and tokenizer artifacts
# ----------------------------------------------------------------------

#: Path to the BPE tokenizer JSON used by the reasoning model.
#: Override with TOKENIZER_FILE if you have trained a custom one.
TOKENIZER_FILE: Path = Path(
    os.environ.get(
        "TOKENIZER_FILE",
        str(DATA_DIR / "tokenizer_v2.json"),
    )
).expanduser().resolve()

#: Path to the trained PyTorch state-dict for the reasoning model.
#: Override with MODEL_FILE to point at a different checkpoint.
MODEL_FILE: Path = Path(
    os.environ.get(
        "MODEL_FILE",
        str(CHECKPOINTS_DIR / "v2" / "reasoning_model_v1.pt"),
    )
).expanduser().resolve()


# ----------------------------------------------------------------------
# Knowledge corpus
# ----------------------------------------------------------------------
#
# Multiple text files are supported so the corpus can be grown without
# touching code. Each entry below corresponds to one plain-text file
# loaded by retriever_v2.load_chunks().
#
# Paths can be overridden individually via the KNOWLEDGE_FILES environment
# variable as a comma-separated list, or each file can be set via its
# own environment variable (KNOWLEDGE_FILE_1, KNOWLEDGE_FILE_2, ...).

_DEFAULT_KNOWLEDGE_FILES = [
    DATA_DIR / "wikitext_v2.txt",
    DATA_DIR / "knowledge_extra_v1.txt",
]


def _resolve_knowledge_files() -> list[Path]:
    """Build the KNOWLEDGE_FILES list from environment overrides or defaults."""
    override = os.environ.get("KNOWLEDGE_FILES")
    if override:
        return [
            Path(p.strip()).expanduser().resolve()
            for p in override.split(os.pathsep)
            if p.strip()
        ]

    resolved: list[Path] = []
    for index, default_path in enumerate(_DEFAULT_KNOWLEDGE_FILES, start=1):
        env_name = f"KNOWLEDGE_FILE_{index}"
        raw = os.environ.get(env_name)
        if raw:
            resolved.append(Path(raw).expanduser().resolve())
        else:
            resolved.append(default_path.expanduser().resolve())
    return resolved


#: Ordered list of knowledge corpus text files used by the retriever.
KNOWLEDGE_FILES: list[Path] = _resolve_knowledge_files()


# ----------------------------------------------------------------------
# Generation and retrieval settings
# ----------------------------------------------------------------------
#
# Plain ints / floats are read via os.environ.get with a default. They can
# be overridden either with int(...) conversions or as strings - here we
# cast through int/float so the type contract is preserved.

#: Maximum number of input tokens fed to the model per generation call.
MAX_INPUT_TOKENS: int = int(
    os.environ.get(
        "MAX_INPUT_TOKENS",
        "480",
    )
)

#: Maximum number of new tokens the model is allowed to emit per call.
MAX_NEW_TOKENS: int = int(
    os.environ.get(
        "MAX_NEW_TOKENS",
        "50",
    )
)

#: Minimum extraction confidence (0.0-1.0) required to accept an answer.
CONFIDENCE_THRESHOLD: float = float(
    os.environ.get(
        "CONFIDENCE_THRESHOLD",
        "0.80",
    )
)


# ----------------------------------------------------------------------
# Convenience helpers (optional)
# ----------------------------------------------------------------------

def knowledge_files_str() -> str:
    """Return a printable summary of the configured knowledge files."""
    return ", ".join(str(p) for p in KNOWLEDGE_FILES)


if __name__ == "__main__":
    # Allow `python config.py` to print the resolved configuration.
    print("PROJECT_ROOT      :", PROJECT_ROOT)
    print("DATA_DIR          :", DATA_DIR)
    print("CHECKPOINTS_DIR   :", CHECKPOINTS_DIR)
    print("LOGS_DIR          :", LOGS_DIR)
    print("TOKENIZER_FILE    :", TOKENIZER_FILE)
    print("MODEL_FILE        :", MODEL_FILE)
    print("KNOWLEDGE_FILES   :", KNOWLEDGE_FILES)
    print("MAX_INPUT_TOKENS  :", MAX_INPUT_TOKENS)
    print("MAX_NEW_TOKENS    :", MAX_NEW_TOKENS)
    print("CONFIDENCE_THRESH :", CONFIDENCE_THRESHOLD)
