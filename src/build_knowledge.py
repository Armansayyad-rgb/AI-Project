import json
import re
from pathlib import Path

DATA_FILE = Path(r"C:\AI-Project\data\train.txt")
OUTPUT_FILE = Path(r"C:\AI-Project\indexes\knowledge.json")

CHUNK_WORDS = 120
OVERLAP_WORDS = 25


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_chunks(text):
    words = text.split()

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))

        chunk_text = " ".join(words[start:end])

        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "start_word": start,
            "end_word": end,
        })

        chunk_id += 1

        if end == len(words):
            break

        start += CHUNK_WORDS - OVERLAP_WORDS

    return chunks


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(DATA_FILE)

    text = DATA_FILE.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    text = clean_text(text)

    chunks = make_chunks(text)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("Characters:", len(text))
    print("Words:", len(text.split()))
    print("Chunks:", len(chunks))
    print("Saved:", OUTPUT_FILE)

    print("\nExample chunk:")
    print("-" * 60)
    print(chunks[0]["text"])


if __name__ == "__main__":
    main()