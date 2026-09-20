"""
build_wikipedia_idf.py — Build a pinned IDF table from a Wikipedia dump.

Run once. Produces a gzipped JSON file mapping each lowercased token to its
IDF score, plus a metadata header for the environment manifest.

Dependencies:
    pip install wikiextractor   # for dump extraction
    pip install tqdm            # optional, for progress bars

Usage:
    # Step 1: Download a dump (once, ~22 GB compressed)
    wget https://dumps.wikimedia.org/enwiki/20260901/enwiki-20260901-pages-articles.xml.bz2

    # Step 2: Extract article text
    python -m wikiextractor.WikiExtractor enwiki-20260901-pages-articles.xml.bz2 \
        --output extracted/ --json --no-templates --processes 4

    # Step 3: Build the IDF table
    python build_wikipedia_idf.py \
        --input extracted/ \
        --output wikipedia_idf_20260901.json.gz \
        --min-df 5

    The output file is the pinned artefact for the dissertation manifest.

Approximate resource requirements:
    - Disk: ~22 GB for the dump, ~18 GB for extracted text, ~200-400 MB for
      the final IDF table. The dump and extracted text can be deleted after.
    - RAM: ~4 GB (streams documents, doesn't hold all text in memory).
    - Time: 2-4 hours depending on hardware and core count.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tokeniser — deliberately simple and reproducible
# ---------------------------------------------------------------------------

# Matches word-like tokens: letters, digits, hyphens within words.
# Lowercased. No stemming or lemmatisation — the salient-term extractor
# will handle morphological normalisation on the domain side.
_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]*[a-z0-9]|[a-z]", re.IGNORECASE)


def tokenise(text: str) -> set[str]:
    """Return the unique lowercased tokens in a text string.

    Returns a set (document-frequency counting needs presence, not count).
    """
    return {m.group().lower() for m in _TOKEN_RE.finditer(text)}


# ---------------------------------------------------------------------------
# Document iterator — reads wikiextractor JSON output
# ---------------------------------------------------------------------------

def iter_documents(input_dir: str | Path) -> Iterator[str]:
    """Yield article text strings from wikiextractor JSON output.

    wikiextractor with --json produces files like:
        extracted/AA/wiki_00
        extracted/AA/wiki_01
        ...
    Each file contains one JSON object per line with keys:
        {"id": "...", "url": "...", "title": "...", "text": "..."}
    """
    input_path = Path(input_dir)
    files = sorted(input_path.rglob("wiki_*"))
    log.info(f"Found {len(files)} wikiextractor output files")

    doc_count = 0
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    if text and len(text) > 50:  # skip stubs
                        yield text
                        doc_count += 1
                except json.JSONDecodeError:
                    continue

        if doc_count % 500_000 == 0 and doc_count > 0:
            log.info(f"  ... processed {doc_count:,} documents so far")

    log.info(f"Total documents: {doc_count:,}")


# ---------------------------------------------------------------------------
# IDF computation
# ---------------------------------------------------------------------------

def build_idf(
    input_dir: str | Path,
    min_df: int = 5,
) -> tuple[dict[str, float], dict]:
    """Build the IDF table from extracted Wikipedia articles.

    Parameters
    ----------
    input_dir : path to the wikiextractor output directory.
    min_df : minimum document frequency. Tokens appearing in fewer than
        this many documents are excluded (removes typos, OCR errors,
        and ultra-rare tokens that would inflate the table size without
        contributing to background frequency estimation).

    Returns
    -------
    idf_table : dict mapping lowercased token → IDF score.
    metadata : dict with provenance and statistics for the manifest.
    """
    doc_freq: Counter = Counter()
    n_docs = 0

    log.info("Pass 1: counting document frequencies...")
    for text in iter_documents(input_dir):
        tokens = tokenise(text)
        doc_freq.update(tokens)
        n_docs += 1

    log.info(f"Documents: {n_docs:,}")
    log.info(f"Unique tokens (before min_df filter): {len(doc_freq):,}")

    # Filter by min_df
    doc_freq = {tok: df for tok, df in doc_freq.items() if df >= min_df}
    log.info(f"Unique tokens (after min_df={min_df}): {len(doc_freq):,}")

    # Compute IDF: log(N / df) — standard smooth IDF
    # Using log base e; the absolute scale doesn't matter since this is
    # used for ranking, not for calibrated probabilities.
    idf_table = {}
    for tok, df in doc_freq.items():
        idf_table[tok] = round(math.log(n_docs / df), 6)

    metadata = {
        "source": "English Wikipedia dump",
        "dump_date": None,          # filled in by caller
        "n_documents": n_docs,
        "n_tokens_before_filter": None,  # could track but not critical
        "n_tokens_after_filter": len(idf_table),
        "min_df": min_df,
        "idf_formula": "ln(N / df)",
        "tokeniser": "regex [a-z][a-z0-9-]*[a-z0-9]|[a-z], lowercased, no stemming",
        "built_at": datetime.now(timezone.utc).isoformat(),
    }

    return idf_table, metadata


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_idf(
    idf_table: dict[str, float],
    metadata: dict,
    output_path: str | Path,
):
    """Save the IDF table as gzipped JSON with a metadata header.

    Format:
        {"metadata": {...}, "idf": {"token": score, ...}}
    """
    output_path = Path(output_path)
    payload = {"metadata": metadata, "idf": idf_table}

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True)

    # Compute file hash for the manifest
    h = hashlib.sha256()
    with open(output_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    log.info(f"Saved to {output_path} ({size_mb:.1f} MB)")
    log.info(f"SHA-256: {h.hexdigest()}")

    return h.hexdigest()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build a pinned IDF table from a Wikipedia dump "
                    "(wikiextractor output)."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to wikiextractor output directory (e.g. extracted/)",
    )
    parser.add_argument(
        "--output", required=True,
        help="Output path for the gzipped JSON IDF table",
    )
    parser.add_argument(
        "--dump-date", default=None,
        help="Wikipedia dump date for provenance (e.g. 20260901)",
    )
    parser.add_argument(
        "--min-df", type=int, default=5,
        help="Minimum document frequency (default: 5)",
    )
    args = parser.parse_args()

    idf_table, metadata = build_idf(args.input, min_df=args.min_df)
    metadata["dump_date"] = args.dump_date

    file_hash = save_idf(idf_table, metadata, args.output)

    # Print manifest entry
    print("\n--- Manifest entry ---")
    print(json.dumps({
        "artefact": "wikipedia_idf_table",
        "file": args.output,
        "sha256": file_hash,
        "dump_date": args.dump_date,
        "n_documents": metadata["n_documents"],
        "n_tokens": metadata["n_tokens_after_filter"],
        "min_df": args.min_df,
    }, indent=2))


if __name__ == "__main__":
    main()
