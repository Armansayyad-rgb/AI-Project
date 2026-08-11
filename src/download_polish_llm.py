"""Download the Polish LLM weights into the expected checkpoint directory.

Targets ``Qwen/Qwen2.5-1.5B-Instruct`` on HuggingFace Hub and pulls
``model.safetensors`` (single 3.09 GB file, no sharding per the repo
snapshot) directly into the directory the loader expects:
``C:\\AI-Project\\checkpoints\\qwen2.5-1.5b-instruct\\``.

Why a script (not a one-liner):
- The download is ~3 GB; if interrupted, re-running this script picks
  up where it left off (hf_hub_download is resumable).
- We get a clear size check before and after, so any partial download
  is obvious.
- We deliberately download only the weights, not the tokenizer files
  (those are already present in the target directory).

Usage:
    python download_polish_llm.py

Side effects:
- Creates ``C:\\AI-Project\\checkpoints\\qwen2.5-1.5b-instruct\\`` if
  it does not exist.
- Writes ``model.safetensors`` (~3.09 GB) into that directory.
- Writes nothing else; the rest of the model card files (config.json,
  generation_config.json, tokenizer.json, etc.) are already in place.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ID = "Qwen/Qwen2.5-1.5B-Instruct"
FILENAME = "model.safetensors"
TARGET_DIR = Path(r"C:\AI-Project\checkpoints\qwen2.5-1.5b-instruct")
EXPECTED_BYTES = 3_090_000_000   # ~3.09 GB, allow some slack on the check


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    target_path = TARGET_DIR / FILENAME

    if target_path.exists():
        existing_bytes = target_path.stat().st_size
        print(f"[download] existing file: {target_path}")
        print(f"[download] existing size: {existing_bytes:,} bytes "
              f"({existing_bytes / 1024 ** 3:.2f} GB)")
        if existing_bytes >= EXPECTED_BYTES * 0.99:
            print("[download] size already looks complete; skipping.")
            return 0
        print("[download] existing file looks incomplete; "
              "hf_hub_download will resume it.")

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("ERROR: huggingface_hub is not installed. "
              "Run: pip install huggingface_hub", file=sys.stderr)
        return 1

    print(f"[download] repo:    {REPO_ID}")
    print(f"[download] file:    {FILENAME}")
    print(f"[download] target:  {target_path}")
    print(f"[download] expected ~{EXPECTED_BYTES / 1024 ** 3:.2f} GB")

    try:
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False,   # write a real file, not a symlink
            resume_download=True,
        )
    except Exception as exc:
        print(f"ERROR: download failed: {exc!r}", file=sys.stderr)
        print("Re-run this script to resume.", file=sys.stderr)
        return 1

    final_path = Path(downloaded_path)
    final_bytes = final_path.stat().st_size
    print()
    print(f"[download] DONE: {final_path}")
    print(f"[download] size: {final_bytes:,} bytes "
          f"({final_bytes / 1024 ** 3:.2f} GB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
