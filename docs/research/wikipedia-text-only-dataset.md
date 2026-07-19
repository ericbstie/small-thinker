# Wikipedia text-only dataset for ~10GB-of-tokens pretraining

Research question: what's the best text-only Wikipedia dataset/config to use as a **~10GB
text corpus** for pretraining a small language model? Every number below was pulled live
from a primary source (Wikimedia's own dump infrastructure, Hugging Face dataset cards, the
HF `datasets-server` API, or OpenAI's `tiktoken` repo) — no blog posts or secondary
write-ups were used for any figure. Research date: 2026-07-19.

## Comparison

| Option | Primary source | Config used | Size | Articles / rows | License tag | Status |
|---|---|---|---|---|---|---|
| **`wikimedia/wikipedia`** (modern, parquet-native) | [dataset card](https://huggingface.co/datasets/wikimedia/wikipedia) · [raw README](https://huggingface.co/datasets/wikimedia/wikipedia/raw/main/README.md) · [datasets-server size API](https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia&config=20231101.en) | `20231101.en` (Nov 1 2023 dump; 323 language configs exist, all dated 20231101 — no newer date family found) | **11,630,929,031 B ≈ 11.63 GB** compressed parquet download; **20,200,062,385 B ≈ 20.20 GB** raw decoded text (`dataset_size`) | 6,407,814 | `cc-by-sa-3.0`, `gfdl` (card tags) | Actively maintained; ready-to-use `id`/`url`/`title`/`text` columns, one-line `load_dataset` |
| `legacy-datasets/wikipedia` (old builder script) | [dataset card](https://huggingface.co/datasets/legacy-datasets/wikipedia) · [raw README](https://huggingface.co/datasets/legacy-datasets/wikipedia/raw/main/README.md) | `20220301.en` | 11,685,147,288 B ≈ 11.69 GB download; 20,275,516,160 B ≈ 20.28 GB raw text | 6,458,670 | `cc-by-sa-3.0`, `gfdl` (card tags) | Same order of magnitude as the modern dataset, just an older (Mar 2022) dump. No explicit "deprecated" banner found in the card text itself, but it lives under the separate `legacy-datasets` org, uses a Python loading script (`load_dataset("wikipedia", language=..., date=...)`) rather than Parquet, and per [HF's `load_dataset` docs](https://huggingface.co/docs/datasets/v3.1.0/en/package_reference/loading_methods) such script-based datasets require `trust_remote_code=True` — treat as superseded by `wikimedia/wikipedia` |
| Raw XML dump + [WikiExtractor](https://github.com/attardi/wikiextractor) | [dumps.wikimedia.org/enwiki/](https://dumps.wikimedia.org/enwiki/) → dated snapshot [enwiki/20260701/](https://dumps.wikimedia.org/enwiki/20260701/) | `enwiki-20260701-pages-articles-multistream.xml.bz2` (dump marked "Dump complete", recombine finished 2026-07-07) | **24.7 GB** compressed bz2 (raw wikitext markup, not plain text); no extracted-plain-text size is published anywhere in WikiExtractor's own README | Not stated on the dump status page itself | CC BY-SA + GFDL per Wikimedia's own dump docs (see License section) | Requires running WikiExtractor yourself; most manual/DIY path, no size guarantee for the output |
| `wikitext-103` | [Salesforce/wikitext card](https://huggingface.co/datasets/Salesforce/wikitext) · [raw README](https://huggingface.co/datasets/Salesforce/wikitext/raw/main/README.md) | `wikitext-103-raw-v1` | 315,466,397 B ≈ 315 MB download; 548,965,325 B ≈ 549 MB raw text | 1,801,350 train rows (line-level, not article-level); card states "over 100 million tokens" (**word-level** tokens, per the original construction — not BPE subword tokens) | "Creative Commons Attribution-ShareAlike License" (derived from Wikipedia, per card) | Curated Good/Featured-article subset only — not full Wikipedia, ~40x too small alone for a 10GB target |
| `wikitext-2` | [Salesforce/wikitext card](https://huggingface.co/datasets/Salesforce/wikitext) · [raw README](https://huggingface.co/datasets/Salesforce/wikitext/raw/main/README.md) | `wikitext-2-raw-v1` | 7,747,362 B ≈ 7.7 MB download; 13,526,093 B ≈ 13.5 MB raw text | 36,718 train rows | same | Toy-scale smoke-test dataset only |

A useful extra data point pulled from the same API/README for the "smaller-language-edition"
question below: **German, `20231101.de`** — 2,845,308 articles, 5,771,317,942 B ≈ 5.77 GB
parquet download, **9,622,925,305 B ≈ 9.62 GB raw decoded text** ([datasets-server size
API](https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia&config=20231101.de),
[raw README block](https://huggingface.co/datasets/wikimedia/wikipedia/raw/main/README.md)).

**A note on a confusing extra field:** the `datasets-server` `/size` API also returns
`num_bytes_memory` (e.g. `149,043,267,408` bytes ≈ 149 GB for `20231101.en`) — this is an
estimate of the size once loaded as an in-memory Arrow table, not a file size, and it is
roughly 7x larger than the on-disk decoded-text figure above. It is not a useful number for
planning disk footprint or token counts; the two figures that matter are `download_size`
(compressed parquet on disk) and `dataset_size` (decoded raw text bytes).

## Getting to ~10GB of tokens

**Step 1 — plain-text size of full English Wikipedia.** Per the `wikimedia/wikipedia`
dataset card's own `dataset_info` (config `20231101.en`, dump dated Nov 1 2023): the decoded
`text`+`title`+`url`+`id` fields total **20,200,062,385 bytes ≈ 20.20 GB** of raw text across
6,407,814 articles ([raw README](https://huggingface.co/datasets/wikimedia/wikipedia/raw/main/README.md)).
This is the number to use for token math — not the 11.63 GB *compressed parquet download*
size, which is ~1.74x smaller because Parquet compresses text well.

**Step 2 — bytes-to-tokens ratio.** No paper was found that states an exact bytes/token
ratio for Wikipedia specifically. The commonly-used rule of thumb comes from OpenAI's own
`tiktoken` library README, in its "What is BPE anyway?" section: *"[BPE] compresses the
text: the token sequence is shorter than the bytes corresponding to the original text. On
average, in practice, each token corresponds to about 4 bytes."* ([openai/tiktoken
README](https://github.com/openai/tiktoken)). This is presented there as a practical
rule of thumb, not a derived constant — treat the token counts below the same way.

**Step 3 — the math.**

```
Full English Wikipedia (20231101.en):  20,200,062,385 bytes / 4 bytes-per-token ≈ 5.05 billion tokens
~10GB text target:                     10,000,000,000 bytes / 4 bytes-per-token ≈ 2.5 billion tokens
```

**Step 4 — does ~10GB require the full corpus, a subset, or a smaller language?**

Full English Wikipedia's raw text (20.20 GB) is almost exactly **2x** the ~10GB target, so
hitting ~10GB of text requires roughly **half** of it, not the full corpus and not a full
truncation-free fit. Three concrete, primary-source-grounded ways to get there:

1. **Byte-budget cutoff on the English config** (recommended — precise, stays English):
   stream `20231101.en` and stop once ~10,000,000,000 bytes of `text` have been accumulated.
   This keeps roughly half of the 6.4M articles (~3.2M, though real article-length variance
   means it won't be exactly half) and yields ~2.5 billion tokens by the ratio above.
2. **Full German Wikipedia, zero truncation**: `20231101.de` is 9,622,925,305 bytes ≈ 9.62 GB
   of raw text (2,845,308 articles) — already almost exactly the 10GB target with no
   subsetting logic at all (~2.4 billion tokens by the same ratio). Only usable if a
   non-English corpus is acceptable for this project.
3. **Full English config as-is, if "10GB" means the on-disk/download footprint**: the
   compressed parquet download for `20231101.en` is 11.63 GB, which is already close to
   10GB — but note this is the *compressed* size; the actual text a tokenizer sees is still
   20.2 GB (~5.05B tokens), not 10GB, so this interpretation only applies if disk footprint
   of the *download*, not token count, is the actual constraint.

Raw dumps (24.7 GB compressed bz2, markup not plain text) and `wikitext-103`/`wikitext-2`
(≤ 0.55 GB) are not practical routes to ~10GB of plain text on their own — the former needs
a full WikiExtractor run with no guaranteed output size, the latter are ~20-1,500x too small.

## License and redistribution terms

The Wikimedia Foundation's Terms of Use, Section 7 ("Licensing of Content"), states the
license text contributors agree to:

> "you agree to license it under: Creative Commons Attribution-ShareAlike 4.0 International
> License ('CC BY-SA 4.0'), and GNU Free Documentation License ('GFDL')"
> — [foundation.wikimedia.org, Policy:Terms_of_Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)

Reusers may comply with either license. Key points from the same page:

- **Attribution is required.** Acceptable methods: a hyperlink/URL to the article and its
  edit history, a link to an alternate stable copy that itself meets attribution
  requirements, or a list of authors (excluding trivial edits).
- **No revocation.** Contributors "cannot unilaterally revoke or seek invalidation of any
  license... granted under these Terms of Use for text content," even after they stop
  contributing.

Wikimedia's own dump documentation corroborates the license for dump content specifically:
*"Text is available under the Creative Commons Attribution-ShareAlike License; additional
terms may apply"* ([meta.wikimedia.org/wiki/Data_dumps](https://meta.wikimedia.org/wiki/Data_dumps)).

**Version note (flagged honestly):** the `wikimedia/wikipedia` and `legacy-datasets/wikipedia`
HF dataset cards both tag the dataset `cc-by-sa-3.0` + `gfdl` (older version identifiers) in
their metadata, while the Foundation's current Terms of Use specify CC BY-SA **4.0** + GFDL
for text contributions. Both are genuine primary-source statements — the discrepancy is
between the dataset packaging's license tag and the Foundation's current ToU — so for a
new project it's safest to treat the content as CC BY-SA (at least 3.0, current policy 4.0)
+ GFDL dual-licensed, and to implement attribution accordingly if any text or close
derivative is redistributed downstream (model *weights* trained on the data are generally
not considered a "modification" requiring the same share-alike license, but that is a legal
question outside what these primary sources state — consult counsel if redistribution of
outputs is a concern).

## Concrete recipe

**Recommended — full English config via Hugging Face `datasets`:**

```python
from datasets import load_dataset

# 6,407,814 articles; 11.63 GB compressed parquet download,
# ~20.2 GB of raw text once decoded.
ds = load_dataset("wikimedia/wikipedia", "20231101.en")
```

**To land on ~10GB of raw text instead of the full ~20.2GB**, stream and stop once the byte
budget is hit (shuffling first avoids biasing the sample toward whatever order the rows are
stored in, e.g. page-creation order):

```python
from datasets import load_dataset

ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
ds = ds.shuffle(seed=42, buffer_size=10_000)

target_bytes = 10_000_000_000  # 10 GB decimal; use 10 * 1024**3 for 10 GiB
running = 0
kept_rows = []
for row in ds:
    n = len(row["text"].encode("utf-8"))
    if running + n > target_bytes:
        break
    kept_rows.append(row)
    running += n
```

**Zero-truncation alternative (smaller full language edition):**

```python
from datasets import load_dataset

# 2,845,308 articles, 9.62 GB raw text as-is — no subsetting needed
ds = load_dataset("wikimedia/wikipedia", "20231101.de")
```

**Alternative path — raw dump + WikiExtractor** (more manual, no plain-text size guarantee):

```bash
wget https://dumps.wikimedia.org/enwiki/20260701/enwiki-20260701-pages-articles-multistream.xml.bz2
# 24.7 GB compressed, per https://dumps.wikimedia.org/enwiki/20260701/ ("Dump complete")

pip install wikiextractor
python -m wikiextractor.WikiExtractor enwiki-20260701-pages-articles-multistream.xml.bz2 --json -o extracted/
```

No primary source states an expected download time or output text size for this path — only
the file sizes cited above are authoritative; plan bandwidth and disk space (24.7 GB
download + extracted output on top) accordingly.

## Recommendation

**Use `wikimedia/wikipedia`, config `20231101.en`, subset to ~10GB by streaming with a
byte-count cutoff** (recipe above).

- It's the actively maintained, parquet-native, plain-text option — no WikiExtractor step,
  no script-based loader, just `load_dataset(...)`.
- Full English Wikipedia is ~20.2 GB of raw text (~5.05 billion tokens at the ~4-bytes/token
  rule of thumb), almost exactly 2x the ~10GB target, so a simple byte-budget stream cutoff
  (shuffled first) gets to ~10GB / ~2.5 billion tokens with minimal code and no reliance on
  DIY dump processing.
- If a non-English corpus is acceptable, the full German config (`20231101.de`) is a strong
  zero-code-truncation alternative: 9.62 GB raw text, 2.85M articles, no subsetting logic
  required at all.
- Content is CC BY-SA (3.0 per the dataset's own tag, 4.0 per the Foundation's current Terms
  of Use) + GFDL — attribution is required if the text or close derivatives are
  redistributed; training model weights on it is not itself addressed by these primary
  sources and is a separate legal question if redistribution of outputs matters.
