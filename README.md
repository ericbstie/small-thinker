# small-thinker

## Dataset preparation

Filters English Wikipedia (see [`docs/research/wikipedia-text-only-dataset.md`](docs/research/wikipedia-text-only-dataset.md)
for the dataset research) down to articles with at least 1000 words (a simple whitespace
split), writing them to a JSONL file. No target corpus size is enforced — every article
meeting the word-count filter is kept, so the resulting corpus may land above or below 10GB.

```
pip install -r requirements.txt
python scripts/prepare_dataset.py
```

Output: `data/wikipedia_min1000w.jsonl`, one JSON object per line with `id`, `url`, `title`,
and `text` fields.
