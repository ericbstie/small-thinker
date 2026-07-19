"""Filter English Wikipedia down to articles with >=1000 words, write JSONL."""
import json
from pathlib import Path

from datasets import load_dataset

MIN_WORDS = 1000
OUTPUT_PATH = Path("data/wikipedia_min1000w.jsonl")


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)

    seen = kept = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in ds:
            seen += 1
            if len(row["text"].split()) >= MIN_WORDS:
                f.write(json.dumps({
                    "id": row["id"],
                    "url": row["url"],
                    "title": row["title"],
                    "text": row["text"],
                }) + "\n")
                kept += 1
            if seen % 100_000 == 0:
                print(f"{seen} articles scanned, {kept} kept")

    print(f"Done: {kept}/{seen} articles kept -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
