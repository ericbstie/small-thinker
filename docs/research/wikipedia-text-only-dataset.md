# Wikipedia Text-Only Dataset for ~10GB-of-Tokens Pretraining

Research question: what's the best text-only Wikipedia dataset to use as a ~10GB training
corpus for pretraining a small language model? All numbers below were pulled live from
primary sources (Wikimedia's own dump infrastructure, Hugging Face dataset cards, and the
HF `datasets-server` API) on 2026-07-19.

## Comparison

| Option | Source | Version/config | Size on disk | Rows / articles | License (as stated) | Status |
|---|---|---|---|---|---|---|
| **`wikimedia/wikipedia`** (modern) | [HF dataset card](https://huggingface.co/datasets/wikimedia/wikipedia) + [datasets-server size API](https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia&config=20231101.en) | `20231101.en` (Nov 1, 2023 dump; 323 language configs exist) | **11,630,929,031 bytes parquet ≈ 11.63 GB decimal (10.83 GiB)** | 6,407,814 | `cc-by-sa-3.0`, `gfdl` (per card tags) | Actively maintained, plain-text `text` column, one-line `load_dataset` |
| `legacy-datasets/wikipedia` (old builder script) | [HF dataset card](https://huggingface.co/datasets/legacy-datasets/wikipedia) | `20220301.en` | Download 11.69 GB + generated 20.28 GB = **31.96 GB total disk** | 6,458,670 | CC BY-SA 3.0 + GFDL (per card) | Dataset Viewer disabled on the card; effectively superseded by `wikimedia/wikipedia`, though still listed as loadable |
| Raw XML dump + [WikiExtractor](https://github.com/attardi/wikiextractor) | [dumps.wikimedia.org/enwiki](https://dumps.wikimedia.org/enwiki/) | `enwiki-20260701` (dump complete 2026-07-07) | Multistream bz2 (all articles, recombined) = **26,564,488,717 bytes ≈ 26.56 GB decimal (24.74 GiB) compressed**, per the dump's own [`dumpstatus.json`](https://dumps.wikimedia.org/enwiki/20260701/dumpstatus.json) | 7,210,872 articles per [en.wikipedia.org's own size page](https://en.wikipedia.org/wiki/Wikipedia:Size_of_Wikipedia) | CC BY-SA 4.0 + GFDL (per [Wikipedia:Copyrights](https://en.wikipedia.org/wiki/Wikipedia:Copyrights)) | Raw wikitext markup; requires running WikiExtractor yourself, no plain-text size figure is published by Wikimedia itself |
| `wikitext-103` | [HF Salesforce/wikitext card](https://huggingface.co/datasets/Salesforce/wikitext) | `wikitext-103-raw-v1` | 190.23–191.98 MB download, 549 MB generated, **741.41 MB total disk** | 1,801,350 train rows (line-level, not article-level); card states "over 100 million tokens" | Derived from Wikipedia (CC BY-SA) | Good/Featured-article subset only — a curation, not full Wikipedia |
| `wikitext-2` | [HF Salesforce/wikitext card](https://huggingface.co/datasets/Salesforce/wikitext) | `wikitext-2-raw-v1` | **18.26 MB total disk** (36,718 train rows) | tiny | same | Toy-scale only, ~1.8% the size of wikitext-103 |

## Getting to ~10GB of tokens

**Corpus chosen for this math:** `wikimedia/wikipedia`, config `20231101.en` (English Wikipedia, Nov 1 2023 dump snapshot).

- **Plain-text size:** the HF `datasets-server` size API reports this config's parquet data as
  `num_bytes_parquet_files: 11,630,929,031` and `num_bytes_original_files: 11,630,929,031`
  (both fields report the same figure since the dataset ships directly as Parquet) —
  i.e. **11.63 GB decimal / 10.83 GiB** on disk, across 6,407,814 article rows
  ([source](https://datasets-server.huggingface.co/size?dataset=wikimedia/wikipedia&config=20231101.en)).
  The same API call also reports `num_bytes_memory: 149,043,267,408` — the size once
  decompressed into an in-memory Arrow table (~149 GB), which matters if you plan to
  materialize the whole thing in RAM rather than stream it.

- **Token estimate and its basis:** OpenAI's own `tiktoken` README states the rule of thumb
  directly: *"[BPE] compresses the text: the token sequence is shorter than the bytes
  corresponding to the original text. On average, in practice, each token corresponds to
  about 4 bytes."* ([tiktoken README, "What is BPE anyway?"](https://github.com/openai/tiktoken)).
  Applying that ratio to the 11.63 GB (11,630,929,031 bytes) of text:

  ```
  11,630,929,031 bytes / 4 bytes-per-token ≈ 2.9 billion tokens
  ```

  This is a rule-of-thumb, not an exact count (actual BPE token counts depend on the specific
  vocabulary/tokenizer used), but it's the figure OpenAI's own tokenizer library states as typical.

- **Do you need truncation?** Practically, no meaningful truncation is required. At
  10.83 GiB / 11.63 GB, the full `20231101.en` config is *already* within a few percent of a
  "roughly 10GB" target — it doesn't need the full English Wikipedia's raw dump (24.7 GB
  compressed, and larger still once decompressed) or a smaller-language edition. If you want
  to land on an exact 10.0 GB (decimal) rather than 11.6 GB, stream the dataset and stop once
  you've accumulated 10 GB of UTF-8 text bytes (see recipe below) — this drops roughly the
  last ~1M of the 6.4M rows. No sampling tricks or non-English fallback are needed.

## License and redistribution terms

Wikipedia's own copyright policy page states plainly:

> "Permission is granted to copy, distribute and/or modify Wikipedia's text under the terms
> of the Creative Commons Attribution-ShareAlike 4.0 International License and, unless
> otherwise noted, the GNU Free Documentation License, unversioned, with no invariant
> sections, front-cover texts, or back-cover texts."
> — [Wikipedia:Copyrights](https://en.wikipedia.org/wiki/Wikipedia:Copyrights)

The Wikimedia Foundation's Terms of Use confirm the same current license for contributed text
(CC BY-SA 4.0), and add the redistribution mechanics — reusers must:

1. Provide attribution (e.g. a hyperlink/URL to the article or its history page, or a list of authors).
2. License any modifications/additions under CC BY-SA 4.0 (or later).
3. Indicate that the original has been modified, if it has been.

— [foundation.wikimedia.org, Policy:Terms_of_Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use)

Note: the `wikimedia/wikipedia` and `legacy-datasets/wikipedia` HF dataset cards still tag
the older `cc-by-sa-3.0` + `gfdl` combination; Wikipedia's own copyright page is the more
current and authoritative statement (CC BY-SA **4.0** + GFDL unversioned) and is what should
govern reuse.

## Recipe

**Recommended path — Hugging Face `datasets`:**

```python
from datasets import load_dataset

# ~11.6 GB decimal (10.83 GiB) on disk, 6,407,814 rows, columns: id, url, title, text
ds = load_dataset("wikimedia/wikipedia", "20231101.en")
```

To land on an exact ~10 GB by byte count instead of the full 11.6 GB, stream and cut off:

```python
from datasets import load_dataset

ds = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)

target_bytes = 10 * 1024**3  # 10 GiB; use 10_000_000_000 for 10 GB decimal
running = 0
kept_rows = []
for row in ds:
    n = len(row["text"].encode("utf-8"))
    if running + n > target_bytes:
        break
    kept_rows.append(row)
    running += n
```

Neither Hugging Face's dataset card nor the `datasets-server` API states an expected download
time — only the file-size figures cited above are authoritative; plan bandwidth/time
accordingly for an ~11.6 GB transfer.

**Alternative path — raw dump + WikiExtractor** (more work, no plain-text size guarantee):

```bash
wget https://dumps.wikimedia.org/enwiki/20260701/enwiki-20260701-pages-articles-multistream.xml.bz2
# 26,564,488,717 bytes ≈ 26.56 GB decimal (24.74 GiB) compressed, per dumpstatus.json

pip install wikiextractor
python -m wikiextractor.WikiExtractor enwiki-20260701-pages-articles-multistream.xml.bz2 --json -o extracted/
```

WikiExtractor's own README documents usage and output format (XML- or JSON-lines-wrapped
plain text, chunked into files, default 1MB/file) but does not state an expected output size
relative to the input dump ([attardi/wikiextractor README](https://github.com/attardi/wikiextractor)).
The closest primary-sourced proxy for "plain text size after full extraction" is the legacy
HF dataset card's own build stats — its "generated dataset" size for the March 2022 English
config was 20.28 GB (Arrow format, not raw `.txt`, and from an older/smaller dump) — see
[legacy-datasets/wikipedia](https://huggingface.co/datasets/legacy-datasets/wikipedia). This
raw-dump path is not recommended for this project given the ready-made `wikimedia/wikipedia`
option already fits the target size with a one-line load.

## Recommendation

**Use `load_dataset("wikimedia/wikipedia", "20231101.en")`.**

- It's the actively maintained, already-parsed, plain-text option (`id`/`url`/`title`/`text`
  columns) — no WikiExtractor step, no deprecated loading script.
- At **11.63 GB decimal (10.83 GiB)** across 6.4M articles, it lands almost exactly on the
  "~10GB" target with no truncation, language-swap, or sampling needed. At the standard
  ~4-bytes/token BPE rule of thumb, that's roughly **2.9 billion tokens** — comfortably
  enough scale for pretraining a small LM.
- If an exact 10.0 GB (rather than 11.6 GB) is wanted, stream and cut off at the byte target
  using the snippet above — this only trims the tail ~1M of 6.4M articles.
- Content is CC BY-SA 4.0 + GFDL per Wikipedia's own copyright page; using it for model
  training just requires normal attribution practices if the text or close derivatives are
  redistributed downstream.
