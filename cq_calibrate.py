"""
CQ Pattern Calibration Pipeline
================================

Extracts label-match patterns from SPARQL queries in the CQ set, hit-tests
them against the real corpus, expands synonyms via embedding similarity to
the salient-term inventory, and produces a calibration report with suggested
SPARQL patches.

Usage
-----
    python cq_calibrate.py \
        --cq-file    cq_set_draft.md \
        --corpus-dir /path/to/corpus \
        --genre-map  genre_map.json \
        --terms-dir  /path/to/salient_term_inventories \
        --out        cq_calibration_report.json \
        --threshold  0.72 \
        --model      all-MiniLM-L6-v2

Inputs
------
cq-file     Markdown file containing CQ blocks with fenced SPARQL code.
corpus-dir  Directory of plain-text corpus files (one file per document,
            or pre-extracted text from each source system).
genre-map   JSON mapping filename → genre label (one of the 11 genre codes).
            If absent, genre is inferred from parent directory name.
terms-dir   Directory of per-genre salient-term inventories, one JSON per
            genre (output of salient_term_pipeline.py).  Each file is a
            list of {"term": str, "score": float}.  If absent, step 3
            (embedding expansion) is skipped and only corpus hit counts
            are reported.
threshold   Embedding cosine-similarity threshold for synonym expansion.
            Same parameter as SIM_THRESHOLD in the windowing spec; default
            0.72 is a starting point — calibrate from the distribution.
model       Sentence-transformer model name.  Must match EMBEDDING_MODEL
            in the project manifest.

Outputs
-------
A JSON report with, per CQ:
  - cq_id, question text, genre tags, question type
  - per pattern: the regex string, corpus hit count by genre, total hits
  - suggested expansions: term, similarity score, genre source
  - a flag if zero patterns hit the corpus (needs manual review)
  - patched SPARQL with expansions folded in

Also prints a human-readable summary to stdout.

Dependencies
------------
  - sentence-transformers (for embedding expansion; optional)
  - numpy
  - Standard library only for the core pipeline
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ------------------------------------------------------------------ Step 1
# Parse CQ blocks and extract label patterns from SPARQL


# Matches the REGEX(..., "pattern") or CONTAINS(..., "pattern") calls
# in our grounding-agnostic SPARQL.
_SPARQL_PATTERN_RE = re.compile(
    r"""(?:REGEX|CONTAINS)\s*\(\s*
        LCASE\s*\(\s*STR\s*\(\s*\?\w+\s*\)\s*\)\s*,\s*
        "([^"]+)"
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Matches a CQ block: **CQ-XXX-Y-NN.** question text, followed by a
# fenced code block with SPARQL.
_CQ_BLOCK_RE = re.compile(
    r"""\*\*(?P<cq_id>CQ-[A-Z]{3}-[ERMD]-\d{2})\.\*\*\s*
        (?:\[(?P<genres>[^\]]+)\]\s*)?
        (?P<question>[^\n]+)\n+
        ```[^\n]*\n
        (?P<sparql>.*?)
        ```""",
    re.VERBOSE | re.DOTALL,
)

# Genre code → full name mapping
GENRE_CODES = {
    "DPB": "DPBPS",
    "CMD": "Command Media",
    "PRC": "Process Maps",
    "FME": "FMEAs",
    "NCR": "NCRs",
    "CAR": "Corrective Action Reports",
    "STR": "Strategic Documents",
    "JIR": "Jira Issues",
    "ERP": "ERP",
    "MES": "MES",
    "ARM": "Active Risk Management",
    "XGN": "Cross-genre",
}

# Question type codes
QTYPE_CODES = {"E": "existential", "R": "relational", "M": "multi-hop", "D": "definitional"}


@dataclass
class CQPattern:
    """One label-match pattern extracted from a SPARQL query."""
    raw: str                          # the regex/contains string as written
    alternates: list[str]             # individual terms after splitting on |
    hits_by_genre: dict[str, int] = field(default_factory=dict)
    total_hits: int = 0


@dataclass
class CQRecord:
    """One competency question with its patterns and calibration data."""
    cq_id: str
    question: str
    genre_tags: list[str]
    qtype: str
    sparql: str
    patterns: list[CQPattern] = field(default_factory=list)
    expansions: list[dict] = field(default_factory=list)   # suggested new terms
    zero_hit: bool = False
    patched_sparql: str = ""


def parse_cq_file(path: str) -> list[CQRecord]:
    """Parse the CQ markdown file and extract records with their patterns."""
    text = Path(path).read_text(encoding="utf-8")
    records = []

    for m in _CQ_BLOCK_RE.finditer(text):
        cq_id = m.group("cq_id")
        question = m.group("question").strip()
        sparql = m.group("sparql").strip()

        # Derive genre and question type from the ID
        parts = cq_id.split("-")          # ["CQ", "DPB", "E", "01"]
        genre_code = parts[1]
        qtype_code = parts[2]

        # Cross-genre CQs have explicit genre tags in brackets
        genre_tags_raw = m.group("genres")
        if genre_tags_raw:
            genre_tags = [t.strip() for t in genre_tags_raw.split("+")]
        else:
            genre_tags = [genre_code]

        # Extract all label patterns from the SPARQL
        patterns = []
        for pm in _SPARQL_PATTERN_RE.finditer(sparql):
            raw = pm.group(1)
            # Split REGEX alternations: (a|b|c) → [a, b, c]
            # Also handle patterns like "non-conform|nonconform|ncr"
            alts = _split_alternation(raw)
            patterns.append(CQPattern(raw=raw, alternates=alts))

        records.append(CQRecord(
            cq_id=cq_id,
            question=question,
            genre_tags=genre_tags,
            qtype=QTYPE_CODES.get(qtype_code, qtype_code),
            sparql=sparql,
            patterns=patterns,
        ))

    return records


def _split_alternation(pattern: str) -> list[str]:
    """Split a REGEX alternation pattern into its component terms.

    Handles patterns like:
      "(work instruction|procedure|sop)"  → ["work instruction", "procedure", "sop"]
      "failure mode"                       → ["failure mode"]
      "(non-conform|nonconform|ncr)"       → ["non-conform", "nonconform", "ncr"]
      "(severity|occurrence|detection).*(rating|score|rank)"
        → ["severity", "occurrence", "detection", "rating", "score", "rank"]
    """
    # Remove regex metacharacters that aren't alternation
    terms = set()
    # Find all parenthesised alternation groups
    groups = re.findall(r"\(([^)]+)\)", pattern)
    if groups:
        for group in groups:
            for alt in group.split("|"):
                alt = alt.strip()
                if alt and not _is_pure_metachar(alt):
                    terms.add(_clean_term(alt))
    elif "|" in pattern:
        for alt in pattern.split("|"):
            alt = alt.strip()
            if alt and not _is_pure_metachar(alt):
                terms.add(_clean_term(alt))
    else:
        cleaned = _clean_term(pattern)
        if cleaned:
            terms.add(cleaned)
    return sorted(terms)


def _clean_term(t: str) -> str:
    """Strip regex anchors/metacharacters, leaving readable search terms."""
    t = re.sub(r"[\^$]", "", t)
    t = re.sub(r"\.\*", " ", t)        # .* → space (as a separator)
    t = re.sub(r"\\.", lambda m: m.group()[1], t)  # unescape
    t = t.replace(".", " ").strip()     # lone dots → spaces
    return re.sub(r"\s+", " ", t).strip()


def _is_pure_metachar(s: str) -> bool:
    return bool(re.fullmatch(r"[.*+?^$\\()\[\]{}|]+", s))


# ------------------------------------------------------------------ Step 2
# Hit-test patterns against the corpus


def load_corpus(corpus_dir: str, genre_map: Optional[dict] = None) -> dict[str, list[str]]:
    """Load corpus texts organised by genre.

    Returns {genre_label: [doc_text, ...]}.
    If genre_map is provided, it maps filename → genre.
    Otherwise, the parent directory name is used as the genre label.
    """
    corpus: dict[str, list[str]] = defaultdict(list)
    corpus_path = Path(corpus_dir)

    for fpath in sorted(corpus_path.rglob("*.txt")):
        text = fpath.read_text(encoding="utf-8", errors="replace")
        if genre_map:
            genre = genre_map.get(fpath.name, genre_map.get(fpath.stem, "unknown"))
        else:
            genre = fpath.parent.name
        corpus[genre].append(text)

    # Also handle .csv, .md, .json if present (common for structured exports)
    for ext in ("*.csv", "*.md", "*.json"):
        for fpath in sorted(corpus_path.rglob(ext)):
            text = fpath.read_text(encoding="utf-8", errors="replace")
            if genre_map:
                genre = genre_map.get(fpath.name, genre_map.get(fpath.stem, "unknown"))
            else:
                genre = fpath.parent.name
            corpus[genre].append(text)

    return dict(corpus)


def hit_test(records: list[CQRecord], corpus: dict[str, list[str]]) -> None:
    """Count corpus hits for each pattern in each CQ, mutating in place."""
    # Pre-build a lowercased, concatenated text per genre for fast scanning.
    # For very large corpora this should be replaced with an index, but for
    # calibration purposes the full concatenation is fine.
    genre_texts: dict[str, str] = {}
    for genre, docs in corpus.items():
        genre_texts[genre] = "\n".join(docs).lower()

    for rec in records:
        any_hit = False
        for pat in rec.patterns:
            pat.hits_by_genre = {}
            pat.total_hits = 0
            for genre, text in genre_texts.items():
                count = sum(
                    1 for alt in pat.alternates
                    if alt.lower() in text
                )
                # Count per-document hits for more precision
                doc_hits = 0
                for doc in corpus.get(genre, []):
                    doc_lower = doc.lower()
                    if any(alt.lower() in doc_lower for alt in pat.alternates):
                        doc_hits += 1
                pat.hits_by_genre[genre] = doc_hits
                pat.total_hits += doc_hits
            if pat.total_hits > 0:
                any_hit = True
        rec.zero_hit = not any_hit


# ------------------------------------------------------------------ Step 3
# Expand via salient-term inventory + embeddings


def load_salient_terms(terms_dir: str) -> dict[str, list[dict]]:
    """Load per-genre salient-term inventories.

    Returns {genre_label: [{"term": str, "score": float}, ...]}.
    """
    inventories: dict[str, list[dict]] = {}
    terms_path = Path(terms_dir)
    for fpath in sorted(terms_path.glob("*.json")):
        genre = fpath.stem  # e.g., "NCRs.json" → "NCRs"
        data = json.loads(fpath.read_text(encoding="utf-8"))
        if isinstance(data, list):
            inventories[genre] = data
        elif isinstance(data, dict) and "terms" in data:
            inventories[genre] = data["terms"]
    return inventories


def expand_patterns(
    records: list[CQRecord],
    salient_terms: dict[str, list[dict]],
    threshold: float = 0.72,
    model_name: str = "all-MiniLM-L6-v2",
) -> None:
    """Find salient-term synonyms for each CQ's concepts via embedding similarity.

    For each unique concept term in the CQ patterns, find salient terms within
    the similarity threshold that are NOT already covered by the existing patterns.
    Mutates records in place, adding to rec.expansions.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        print("WARNING: sentence-transformers not installed; skipping embedding expansion.",
              file=sys.stderr)
        return

    print(f"Loading embedding model: {model_name} ...", file=sys.stderr)
    model = SentenceTransformer(model_name)

    # Collect all unique concept terms from all CQ patterns
    all_concept_terms: set[str] = set()
    for rec in records:
        for pat in rec.patterns:
            all_concept_terms.update(pat.alternates)

    # Collect all unique salient terms across genres
    all_salient: list[dict] = []     # {"term", "score", "genre"}
    salient_texts: list[str] = []
    seen_terms: set[str] = set()
    for genre, terms in salient_terms.items():
        for entry in terms:
            t = entry["term"].lower().strip()
            if t not in seen_terms:
                seen_terms.add(t)
                all_salient.append({"term": entry["term"], "score": entry.get("score", 0), "genre": genre})
                salient_texts.append(t)

    if not salient_texts:
        print("WARNING: no salient terms loaded; skipping expansion.", file=sys.stderr)
        return

    # Embed everything once
    concept_list = sorted(all_concept_terms)
    print(f"Encoding {len(concept_list)} concept terms and {len(salient_texts)} salient terms ...",
          file=sys.stderr)
    concept_embs = model.encode(concept_list, show_progress_bar=False, normalize_embeddings=True)
    salient_embs = model.encode(salient_texts, show_progress_bar=False, normalize_embeddings=True)

    # Build a similarity matrix: concepts × salient terms
    sim_matrix = concept_embs @ salient_embs.T  # (n_concepts, n_salient)

    # Index for fast lookup
    concept_idx = {t: i for i, t in enumerate(concept_list)}

    for rec in records:
        # Gather all existing pattern terms for this CQ (lowered)
        existing = set()
        for pat in rec.patterns:
            for alt in pat.alternates:
                existing.add(alt.lower())

        # For each pattern's concept terms, find similar salient terms
        for pat in rec.patterns:
            for alt in pat.alternates:
                ci = concept_idx.get(alt)
                if ci is None:
                    continue
                sims = sim_matrix[ci]
                # Find all salient terms above threshold
                above = np.where(sims >= threshold)[0]
                for si in above:
                    candidate = all_salient[si]
                    candidate_lower = candidate["term"].lower().strip()
                    # Skip if already covered by existing patterns
                    if candidate_lower in existing:
                        continue
                    # Skip if it's a substring match of an existing pattern
                    if any(candidate_lower in ex or ex in candidate_lower for ex in existing):
                        continue
                    rec.expansions.append({
                        "source_concept": alt,
                        "suggested_term": candidate["term"],
                        "similarity": float(sims[si]),
                        "genre": candidate["genre"],
                        "salience_score": candidate["score"],
                    })
                    existing.add(candidate_lower)  # avoid duplicates within a CQ


# ------------------------------------------------------------------ Step 4
# Produce calibration report


def build_report(records: list[CQRecord]) -> dict:
    """Build the full calibration report as a dict."""
    summary = {
        "total_cqs": len(records),
        "zero_hit_cqs": sum(1 for r in records if r.zero_hit),
        "total_patterns": sum(len(r.patterns) for r in records),
        "total_expansions": sum(len(r.expansions) for r in records),
    }

    cq_details = []
    for rec in records:
        detail = {
            "cq_id": rec.cq_id,
            "question": rec.question,
            "genre_tags": rec.genre_tags,
            "qtype": rec.qtype,
            "zero_hit": rec.zero_hit,
            "patterns": [
                {
                    "raw": p.raw,
                    "alternates": p.alternates,
                    "hits_by_genre": p.hits_by_genre,
                    "total_hits": p.total_hits,
                }
                for p in rec.patterns
            ],
            "expansions": rec.expansions,
            "patched_sparql": rec.patched_sparql,
        }
        cq_details.append(detail)

    return {"summary": summary, "cqs": cq_details}


def print_summary(records: list[CQRecord]) -> None:
    """Print a human-readable summary to stdout."""
    total = len(records)
    zero_hit = [r for r in records if r.zero_hit]
    has_expansions = [r for r in records if r.expansions]

    print(f"\n{'='*70}")
    print(f"CQ Pattern Calibration Report")
    print(f"{'='*70}")
    print(f"Total CQs:              {total}")
    print(f"Zero-hit CQs:           {len(zero_hit)}  (need manual review)")
    print(f"CQs with expansions:    {len(has_expansions)}")
    print(f"Total expansions:       {sum(len(r.expansions) for r in records)}")

    if zero_hit:
        print(f"\n--- Zero-hit CQs (no pattern matched any corpus document) ---")
        for r in zero_hit:
            print(f"  {r.cq_id}: {r.question[:80]}...")
            for p in r.patterns:
                print(f"    pattern: {p.alternates}  →  0 hits")

    # Top expansions by frequency
    expansion_counts: dict[str, int] = defaultdict(int)
    for r in records:
        for exp in r.expansions:
            expansion_counts[exp["suggested_term"]] += 1
    if expansion_counts:
        print(f"\n--- Most suggested expansions (appear in multiple CQs) ---")
        for term, count in sorted(expansion_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  \"{term}\"  →  suggested for {count} CQs")

    # Per-genre hit coverage
    print(f"\n--- Pattern hit rate by genre ---")
    genre_stats: dict[str, dict] = defaultdict(lambda: {"total_patterns": 0, "hitting_patterns": 0})
    for r in records:
        for genre in r.genre_tags:
            for p in r.patterns:
                genre_stats[genre]["total_patterns"] += 1
                if p.hits_by_genre.get(genre, 0) > 0 or p.total_hits > 0:
                    genre_stats[genre]["hitting_patterns"] += 1
    for genre in sorted(genre_stats.keys()):
        s = genre_stats[genre]
        rate = s["hitting_patterns"] / s["total_patterns"] if s["total_patterns"] else 0
        print(f"  {genre:4s}: {s['hitting_patterns']:3d}/{s['total_patterns']:3d} patterns hit "
              f"({rate:.0%})")


# ------------------------------------------------------------------ Step 5
# Patch SPARQL with expansions


def patch_sparql(records: list[CQRecord]) -> None:
    """For each CQ, produce a patched SPARQL with expansions folded in.

    Strategy: for each expansion, find the REGEX or CONTAINS clause whose
    existing alternates include the expansion's source_concept, and widen
    the alternation to include the new term.

    Mutates rec.patched_sparql in place.
    """
    for rec in records:
        patched = rec.sparql

        # Group expansions by source concept
        by_source: dict[str, list[str]] = defaultdict(list)
        for exp in rec.expansions:
            by_source[exp["source_concept"]].append(exp["suggested_term"].lower())

        # For each pattern in the SPARQL, see if any of its alternates
        # have expansions, and widen the pattern.
        for pm in _SPARQL_PATTERN_RE.finditer(rec.sparql):
            original_pattern = pm.group(1)
            alts = _split_alternation(original_pattern)
            new_alts: list[str] = []
            for alt in alts:
                if alt in by_source:
                    new_alts.extend(by_source[alt])

            if new_alts:
                # Build the widened pattern.  If the original was a simple
                # string, wrap it in an alternation.  If it already had
                # alternation, extend it.
                new_terms = sorted(set(new_alts))
                if "|" in original_pattern or "(" in original_pattern:
                    # Find the last closing paren or last alternate and append
                    # We do a simple string extension: add new terms at the end
                    # of the outermost alternation group.
                    widened = _widen_regex(original_pattern, new_terms)
                else:
                    # Simple string → wrap in alternation
                    all_options = [original_pattern] + new_terms
                    widened = "(" + "|".join(all_options) + ")"

                patched = patched.replace(
                    f'"{original_pattern}"',
                    f'"{widened}"',
                    1,  # replace only the first occurrence
                )

        rec.patched_sparql = patched


def _widen_regex(original: str, new_terms: list[str]) -> str:
    """Add new alternation terms to an existing REGEX pattern.

    Tries to be minimally invasive: finds the primary alternation group
    and appends the new terms inside it.
    """
    # Find the outermost parenthesised group
    # Simple approach: find the last ) and insert before it
    last_paren = original.rfind(")")
    if last_paren > 0:
        addition = "|" + "|".join(new_terms)
        return original[:last_paren] + addition + original[last_paren:]
    else:
        # No parens — wrap everything
        all_options = [original] + new_terms
        return "(" + "|".join(all_options) + ")"


# ------------------------------------------------------------------ main


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate CQ SPARQL patterns against the real corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--cq-file", required=True,
                        help="Markdown file with CQ blocks and SPARQL")
    parser.add_argument("--corpus-dir", required=True,
                        help="Directory of corpus text files")
    parser.add_argument("--genre-map", default=None,
                        help="JSON file mapping filename → genre label")
    parser.add_argument("--terms-dir", default=None,
                        help="Directory of per-genre salient-term inventories (JSON)")
    parser.add_argument("--out", default="cq_calibration_report.json",
                        help="Output path for the JSON report")
    parser.add_argument("--threshold", type=float, default=0.72,
                        help="Embedding similarity threshold for synonym expansion")
    parser.add_argument("--model", default="all-MiniLM-L6-v2",
                        help="Sentence-transformer model for embeddings")
    args = parser.parse_args()

    # Step 1: parse CQ file
    print(f"Parsing CQ file: {args.cq_file}", file=sys.stderr)
    records = parse_cq_file(args.cq_file)
    print(f"  → {len(records)} CQs, "
          f"{sum(len(r.patterns) for r in records)} patterns extracted",
          file=sys.stderr)

    # Step 2: load corpus and hit-test
    genre_map = None
    if args.genre_map:
        genre_map = json.loads(Path(args.genre_map).read_text())

    print(f"Loading corpus from: {args.corpus_dir}", file=sys.stderr)
    corpus = load_corpus(args.corpus_dir, genre_map)
    for genre, docs in sorted(corpus.items()):
        print(f"  {genre}: {len(docs)} documents", file=sys.stderr)

    print("Hit-testing patterns against corpus ...", file=sys.stderr)
    hit_test(records, corpus)

    # Step 3: embedding expansion (if salient-term inventories provided)
    if args.terms_dir:
        print(f"Loading salient-term inventories from: {args.terms_dir}", file=sys.stderr)
        salient_terms = load_salient_terms(args.terms_dir)
        for genre, terms in sorted(salient_terms.items()):
            print(f"  {genre}: {len(terms)} terms", file=sys.stderr)

        expand_patterns(records, salient_terms, args.threshold, args.model)
    else:
        print("No --terms-dir provided; skipping embedding expansion.", file=sys.stderr)

    # Step 5: patch SPARQL
    patch_sparql(records)

    # Step 4: report
    print_summary(records)

    report = build_report(records)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nFull report written to: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
