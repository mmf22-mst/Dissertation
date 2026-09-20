"""
salient_term_pipeline.py — Salient-term extraction, coverage scoring,
genre coverage balance, and salient-assertion extraction.

Part of the dissertation evaluation battery:
    - Paper 1 §5.2a: salient-term coverage (co-primary outcome)
    - Paper 1 §5.2b: genre coverage balance (primary for H1b)
    - Paper 2 §5.2:  salient-assertion inventory (salience recall)
    - Part I §8, assets 2–3: frozen inventories

Dependencies:
    pip install spacy numpy
    python -m spacy download en_core_web_sm

Also requires:
    - embedding_utils.py (same directory or on PYTHONPATH)
    - A Wikipedia IDF table (built by build_wikipedia_idf.py)

Usage:
    from salient_term_pipeline import (
        extract_terms_from_corpus,
        build_salient_term_inventory,
        score_coverage,
        genre_coverage_balance,
        extract_assertions,
    )
"""

from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np

# Local imports — embedding_utils.py must be on the path
from embedding_utils import (
    match_terms_to_ontology,
    coverage_score,
    expand_aliases,
    embed_texts,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CandidateTerm:
    """A candidate domain term with scoring components."""
    surface: str                  # normalised surface form
    raw_forms: list[str]          # original forms seen in corpus
    frequency: int = 0            # corpus document frequency
    c_value: float = 0.0          # C-value score
    tfidf_score: float = 0.0     # TF-IDF against background corpus
    combined_score: float = 0.0  # final ranking score
    genre_sources: dict = field(default_factory=dict)  # {genre: doc_count}


@dataclass
class SalientTermInventory:
    """The frozen salient-term inventory (asset 2)."""
    terms: list[CandidateTerm]
    genre_inventories: dict[str, list[CandidateTerm]]  # per-genre
    parameters: dict              # extractor config for the manifest
    corpus_stats: dict            # document counts, genre proportions


@dataclass
class CoverageResult:
    """Coverage score for one ontology against the inventory."""
    whole_corpus_coverage: float
    per_genre_coverage: dict[str, float]
    genre_balance: float          # entropy-based
    matched_terms: int
    total_terms: int
    per_genre_matched: dict[str, int]
    per_genre_total: dict[str, int]


@dataclass
class Assertion:
    """A subject–predicate–object triple extracted from text."""
    subject: str
    predicate: str
    object: str
    sentence: str                 # source sentence
    doc_id: str = ""
    genre: str = ""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    # C-value
    "min_term_length": 2,         # minimum words in a multi-word term
    "max_term_length": 5,         # maximum words
    "min_frequency": 2,           # minimum corpus frequency to keep

    # TF-IDF
    "idf_missing_value": 15.0,    # IDF for terms not in Wikipedia (max salience)

    # Combined scoring
    "c_value_weight": 0.5,        # weight for C-value in combined score
    "tfidf_weight": 0.5,          # weight for TF-IDF in combined score
    "top_k_per_genre": 200,       # max terms kept per genre
    "top_k_whole_corpus": 500,    # max terms kept for whole-corpus inventory

    # Coverage
    "sim_threshold": 0.38,        # calibrate against your corpus
}


# ---------------------------------------------------------------------------
# NLP utilities
# ---------------------------------------------------------------------------

_nlp = None


def _get_nlp():
    """Load the spaCy model (cached)."""
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])
    return _nlp


def _extract_noun_phrases(text: str) -> list[str]:
    """Extract noun phrases from text using spaCy."""
    nlp = _get_nlp()
    doc = nlp(text)
    phrases = []
    for chunk in doc.noun_chunks:
        # Strip determiners and leading adjectives for cleaner terms
        tokens = [t for t in chunk if t.pos_ not in ("DET", "PRON", "NUM")]
        if tokens:
            phrase = " ".join(t.lemma_.lower() for t in tokens)
            phrase = phrase.strip()
            if phrase and len(phrase) > 2:
                phrases.append(phrase)
    return phrases


def _normalise_term(term: str) -> str:
    """Normalise a term for deduplication."""
    # Lowercase, strip extra whitespace, collapse hyphens
    term = term.lower().strip()
    term = re.sub(r"\s+", " ", term)
    return term


# ---------------------------------------------------------------------------
# C-value computation (Frantzi et al. 2000)
# ---------------------------------------------------------------------------

def _compute_c_values(
    term_freqs: dict[str, int],
    min_length: int = 2,
) -> dict[str, float]:
    """Compute C-value for all candidate multi-word terms.

    C-value(t) = log2(|t|) * f(t)                     if t is not nested
    C-value(t) = log2(|t|) * (f(t) - 1/P(t) * Σf(b))  if t is nested

    where |t| = word count, f(t) = frequency, P(t) = number of longer
    terms containing t, Σf(b) = sum of their frequencies.
    """
    # Sort terms longest first for nesting detection
    sorted_terms = sorted(term_freqs.keys(), key=lambda t: -len(t.split()))

    # For each term, find which longer terms contain it
    nesting_info: dict[str, list[str]] = defaultdict(list)
    for i, term in enumerate(sorted_terms):
        for longer_term in sorted_terms[:i]:
            if term in longer_term and term != longer_term:
                nesting_info[term].append(longer_term)

    c_values = {}
    for term, freq in term_freqs.items():
        word_count = len(term.split())
        if word_count < min_length:
            continue

        log_length = math.log2(word_count) if word_count > 1 else 1.0

        containers = nesting_info.get(term, [])
        if not containers:
            # Not nested in any longer term
            c_values[term] = log_length * freq
        else:
            # Nested — subtract average frequency of containing terms
            container_freq_sum = sum(
                term_freqs.get(c, 0) for c in containers
            )
            p = len(containers)
            c_values[term] = log_length * (freq - container_freq_sum / p)

    return c_values


# ---------------------------------------------------------------------------
# IDF table loading
# ---------------------------------------------------------------------------

def load_idf_table(path: str | Path) -> dict[str, float]:
    """Load the Wikipedia IDF table.

    Accepts both gzipped and plain JSON.
    """
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    return data["idf"]


# ---------------------------------------------------------------------------
# Term extraction from a corpus
# ---------------------------------------------------------------------------

@dataclass
class CorpusDocument:
    """A single document in the corpus."""
    doc_id: str
    text: str
    genre: str


def extract_terms_from_corpus(
    documents: list[CorpusDocument],
    idf_table: dict[str, float],
    config: dict | None = None,
) -> SalientTermInventory:
    """Extract salient terms from a corpus, producing the frozen inventory.

    Parameters
    ----------
    documents : the corpus, with genre labels.
    idf_table : the Wikipedia IDF table (from load_idf_table).
    config : extraction parameters (defaults to DEFAULT_CONFIG).

    Returns
    -------
    SalientTermInventory ready to be frozen as asset 2.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    # ---------------------------------------------------------------
    # Step 1: Extract noun phrases from all documents
    # ---------------------------------------------------------------
    # Per-document term sets (for document frequency counting)
    doc_term_sets: list[tuple[str, set[str]]] = []  # (genre, {terms})
    raw_forms: dict[str, set[str]] = defaultdict(set)

    for doc in documents:
        phrases = _extract_noun_phrases(doc.text)
        normalised = set()
        for p in phrases:
            norm = _normalise_term(p)
            word_count = len(norm.split())
            if cfg["min_term_length"] <= word_count <= cfg["max_term_length"]:
                normalised.add(norm)
                raw_forms[norm].add(p)
        doc_term_sets.append((doc.genre, normalised))

    # ---------------------------------------------------------------
    # Step 2: Compute corpus document frequency
    # ---------------------------------------------------------------
    corpus_df: Counter = Counter()
    genre_df: dict[str, Counter] = defaultdict(Counter)

    for genre, terms in doc_term_sets:
        corpus_df.update(terms)
        genre_df[genre].update(terms)

    # Filter by minimum frequency
    corpus_df = {
        t: f for t, f in corpus_df.items()
        if f >= cfg["min_frequency"]
    }

    # ---------------------------------------------------------------
    # Step 3: C-value scoring
    # ---------------------------------------------------------------
    c_values = _compute_c_values(corpus_df, min_length=cfg["min_term_length"])

    # ---------------------------------------------------------------
    # Step 4: TF-IDF scoring against Wikipedia
    # ---------------------------------------------------------------
    n_docs = len(documents)
    tfidf_scores = {}
    for term, df in corpus_df.items():
        tf = df / n_docs  # normalised by corpus size

        # IDF: look up each word in the term, take the max
        # (the rarest word in the phrase determines domain-specificity)
        words = term.split()
        word_idfs = [
            idf_table.get(w, cfg["idf_missing_value"]) for w in words
        ]
        idf = max(word_idfs) if word_idfs else cfg["idf_missing_value"]

        tfidf_scores[term] = tf * idf

    # ---------------------------------------------------------------
    # Step 5: Combined scoring
    # ---------------------------------------------------------------
    # Normalise C-value and TF-IDF to [0, 1] before combining
    all_terms = set(c_values.keys()) | set(tfidf_scores.keys())

    c_max = max(c_values.values()) if c_values else 1.0
    t_max = max(tfidf_scores.values()) if tfidf_scores else 1.0

    candidates = {}
    for term in all_terms:
        c_norm = c_values.get(term, 0.0) / c_max if c_max > 0 else 0.0
        t_norm = tfidf_scores.get(term, 0.0) / t_max if t_max > 0 else 0.0
        combined = (
            cfg["c_value_weight"] * c_norm +
            cfg["tfidf_weight"] * t_norm
        )

        genre_sources = {}
        for genre, gdf in genre_df.items():
            if term in gdf:
                genre_sources[genre] = gdf[term]

        candidates[term] = CandidateTerm(
            surface=term,
            raw_forms=sorted(raw_forms.get(term, set())),
            frequency=corpus_df.get(term, 0),
            c_value=round(c_values.get(term, 0.0), 6),
            tfidf_score=round(tfidf_scores.get(term, 0.0), 6),
            combined_score=round(combined, 6),
            genre_sources=genre_sources,
        )

    # ---------------------------------------------------------------
    # Step 6: Rank and select top-k
    # ---------------------------------------------------------------
    ranked = sorted(
        candidates.values(),
        key=lambda t: -t.combined_score,
    )
    top_terms = ranked[:cfg["top_k_whole_corpus"]]

    # Per-genre inventories
    genres = sorted(set(g for g, _ in doc_term_sets))
    genre_inventories = {}
    for genre in genres:
        genre_terms = [
            t for t in ranked if genre in t.genre_sources
        ]
        genre_inventories[genre] = genre_terms[:cfg["top_k_per_genre"]]

    # ---------------------------------------------------------------
    # Step 7: Corpus statistics
    # ---------------------------------------------------------------
    genre_doc_counts = Counter(g for g, _ in doc_term_sets)
    corpus_stats = {
        "total_documents": n_docs,
        "genre_document_counts": dict(genre_doc_counts),
        "genre_proportions": {
            g: round(c / n_docs, 4) for g, c in genre_doc_counts.items()
        },
        "total_candidate_terms": len(candidates),
        "terms_after_top_k": len(top_terms),
    }

    return SalientTermInventory(
        terms=top_terms,
        genre_inventories=genre_inventories,
        parameters=cfg,
        corpus_stats=corpus_stats,
    )


# ---------------------------------------------------------------------------
# Coverage scoring
# ---------------------------------------------------------------------------

def score_coverage(
    inventory: SalientTermInventory,
    ontology_labels: list[str],
    threshold: float | None = None,
) -> CoverageResult:
    """Score an ontology's coverage of the salient-term inventory.

    Parameters
    ----------
    inventory : the frozen salient-term inventory.
    ontology_labels : rdfs:label values from the ontology.
    threshold : similarity threshold; defaults to inventory.parameters.

    Returns
    -------
    CoverageResult with whole-corpus and per-genre coverage plus genre balance.
    """
    sim_threshold = threshold or inventory.parameters.get(
        "sim_threshold", DEFAULT_CONFIG["sim_threshold"]
    )

    # Whole-corpus coverage
    term_surfaces = [t.surface for t in inventory.terms]
    match_results = match_terms_to_ontology(
        term_surfaces, ontology_labels, sim_threshold
    )
    whole_coverage = coverage_score(match_results)
    matched = sum(1 for r in match_results if r.above_threshold)

    # Per-genre coverage
    per_genre_coverage = {}
    per_genre_matched = {}
    per_genre_total = {}

    for genre, genre_terms in inventory.genre_inventories.items():
        genre_surfaces = [t.surface for t in genre_terms]
        if not genre_surfaces:
            per_genre_coverage[genre] = 0.0
            per_genre_matched[genre] = 0
            per_genre_total[genre] = 0
            continue

        genre_results = match_terms_to_ontology(
            genre_surfaces, ontology_labels, sim_threshold
        )
        per_genre_coverage[genre] = coverage_score(genre_results)
        per_genre_matched[genre] = sum(
            1 for r in genre_results if r.above_threshold
        )
        per_genre_total[genre] = len(genre_surfaces)

    # Genre coverage balance (entropy)
    balance = genre_coverage_balance(per_genre_coverage)

    return CoverageResult(
        whole_corpus_coverage=whole_coverage,
        per_genre_coverage=per_genre_coverage,
        genre_balance=balance,
        matched_terms=matched,
        total_terms=len(term_surfaces),
        per_genre_matched=per_genre_matched,
        per_genre_total=per_genre_total,
    )


# ---------------------------------------------------------------------------
# Genre coverage balance (Paper 1 §5.2b)
# ---------------------------------------------------------------------------

def genre_coverage_balance(per_genre_coverage: dict[str, float]) -> float:
    """Compute genre coverage balance as normalised entropy.

    Entropy over per-genre salient-term coverage values, normalised by
    log(G) so the result is in [0, 1]. A value of 1.0 means perfectly
    uniform coverage across genres; lower values indicate some genres
    are covered much better than others.

    This targets the predicted D0 failure mode: over-fitting to whichever
    genre dominates the token budget.
    """
    coverages = list(per_genre_coverage.values())
    g = len(coverages)

    if g <= 1:
        return 1.0  # one genre is trivially balanced

    total = sum(coverages)
    if total == 0:
        return 0.0  # no coverage at all

    # Normalise to a distribution
    probs = [c / total for c in coverages]

    # Shannon entropy
    entropy = -sum(p * math.log(p) if p > 0 else 0.0 for p in probs)

    # Normalise by max entropy (uniform distribution)
    max_entropy = math.log(g)
    if max_entropy == 0:
        return 1.0

    return round(entropy / max_entropy, 6)


# ---------------------------------------------------------------------------
# Salient-assertion extraction (Paper 2, asset 3)
# ---------------------------------------------------------------------------

def extract_assertions(
    documents: list[CorpusDocument],
) -> list[Assertion]:
    """Extract subject–predicate–object assertions from corpus text.

    Uses spaCy dependency parsing to extract (subject, verb, object)
    triples from each sentence. These form the salient-assertion
    inventory (asset 3) against which Paper 2's salience recall is
    computed.

    This is a distinct asset from the term inventory and is frozen
    on the same schedule.
    """
    nlp = _get_nlp()
    assertions = []

    for doc in documents:
        parsed = nlp(doc.text)
        for sent in parsed.sents:
            spo_triples = _extract_spo_from_sentence(sent)
            for subj, pred, obj in spo_triples:
                assertions.append(Assertion(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    sentence=sent.text.strip(),
                    doc_id=doc.doc_id,
                    genre=doc.genre,
                ))

    return assertions


def _extract_spo_from_sentence(sent) -> list[tuple[str, str, str]]:
    """Extract (subject, predicate, object) triples from a spaCy Span."""
    triples = []

    for token in sent:
        if token.dep_ == "ROOT" and token.pos_ == "VERB":
            # Find subject
            subjects = [
                child for child in token.children
                if child.dep_ in ("nsubj", "nsubjpass")
            ]
            # Find objects
            objects = [
                child for child in token.children
                if child.dep_ in ("dobj", "attr", "pobj")
            ]
            # Also check prepositional objects
            for child in token.children:
                if child.dep_ == "prep":
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            objects.append(grandchild)

            # Expand subjects and objects to their full noun phrases
            for subj in subjects:
                subj_text = _get_subtree_text(subj)
                for obj in objects:
                    obj_text = _get_subtree_text(obj)
                    if subj_text and obj_text:
                        triples.append((
                            subj_text,
                            token.lemma_.lower(),
                            obj_text,
                        ))

    return triples


def _get_subtree_text(token) -> str:
    """Get the text of a token's subtree (its full noun phrase)."""
    subtree = sorted(token.subtree, key=lambda t: t.i)
    # Filter out determiners and punctuation for cleaner output
    words = [
        t.text for t in subtree
        if t.pos_ not in ("DET", "PUNCT") and not t.is_space
    ]
    return " ".join(words).strip()


# ---------------------------------------------------------------------------
# Inventory serialisation (for freezing as project assets)
# ---------------------------------------------------------------------------

def save_inventory(
    inventory: SalientTermInventory,
    path: str | Path,
):
    """Save the salient-term inventory as JSON for freezing."""
    data = {
        "parameters": inventory.parameters,
        "corpus_stats": inventory.corpus_stats,
        "terms": [asdict(t) for t in inventory.terms],
        "genre_inventories": {
            genre: [asdict(t) for t in terms]
            for genre, terms in inventory.genre_inventories.items()
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_inventory(path: str | Path) -> SalientTermInventory:
    """Load a frozen salient-term inventory from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    terms = [CandidateTerm(**t) for t in data["terms"]]
    genre_inventories = {
        genre: [CandidateTerm(**t) for t in terms_list]
        for genre, terms_list in data["genre_inventories"].items()
    }

    return SalientTermInventory(
        terms=terms,
        genre_inventories=genre_inventories,
        parameters=data["parameters"],
        corpus_stats=data["corpus_stats"],
    )


def save_assertions(
    assertions: list[Assertion],
    path: str | Path,
):
    """Save the salient-assertion inventory as JSON for freezing."""
    data = [asdict(a) for a in assertions]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_assertions(path: str | Path) -> list[Assertion]:
    """Load a frozen salient-assertion inventory from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Assertion(**a) for a in data]


# ---------------------------------------------------------------------------
# Scoring record (for the battery output)
# ---------------------------------------------------------------------------

def scoring_record(result: CoverageResult) -> dict:
    """Return a flat dict for the battery scoring log."""
    rec = {
        "salient_term_coverage": result.whole_corpus_coverage,
        "genre_coverage_balance": result.genre_balance,
        "matched_terms": result.matched_terms,
        "total_terms": result.total_terms,
    }
    for genre, cov in result.per_genre_coverage.items():
        rec[f"coverage_{genre}"] = cov
    return rec


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Smoke test with synthetic data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Salient-term extraction and coverage scoring pipeline."
    )
    parser.add_argument(
        "--idf-table",
        help="Path to the Wikipedia IDF table (JSON or .json.gz)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a smoke test with synthetic manufacturing data",
    )
    args = parser.parse_args()

    if args.smoke_test:
        _run_smoke_test(args.idf_table)
    else:
        parser.print_help()


def _run_smoke_test(idf_path: str | None = None):
    """Run a smoke test with synthetic manufacturing documents."""

    # Synthetic corpus
    docs = [
        CorpusDocument(
            "doc1", "The reflow soldering process requires careful "
            "temperature profiling. Solder paste is applied to the "
            "printed circuit board before component placement.",
            "process_spec"
        ),
        CorpusDocument(
            "doc2", "Tombstoning defects occur when one end of a "
            "surface mount component lifts during reflow. Root cause "
            "analysis shows uneven pad geometry or paste volume.",
            "defect_report"
        ),
        CorpusDocument(
            "doc3", "The automated optical inspection system detects "
            "solder bridge defects and missing components. Statistical "
            "process control charts track defect rates over time.",
            "inspection"
        ),
        CorpusDocument(
            "doc4", "Bill of materials specifies component types and "
            "quantities. Design for manufacturability review ensures "
            "the PCB layout is compatible with the assembly process.",
            "process_spec"
        ),
    ]

    # Load IDF table if provided
    idf_table = {}
    if idf_path:
        print(f"Loading IDF table from {idf_path}...")
        idf_table = load_idf_table(idf_path)
        print(f"  {len(idf_table):,} tokens loaded")

    # Extract terms
    print("\nExtracting terms...")
    inventory = extract_terms_from_corpus(docs, idf_table, config={
        "min_frequency": 1,  # low threshold for tiny corpus
        "top_k_per_genre": 50,
        "top_k_whole_corpus": 100,
    })

    print(f"  Total candidate terms: {inventory.corpus_stats['total_candidate_terms']}")
    print(f"  Terms in inventory: {len(inventory.terms)}")
    print(f"  Genres: {list(inventory.genre_inventories.keys())}")

    print("\nTop 10 terms by combined score:")
    for t in inventory.terms[:10]:
        print(f"  {t.combined_score:.4f}  {t.surface:30s}  "
              f"(freq={t.frequency}, c={t.c_value:.2f}, "
              f"tfidf={t.tfidf_score:.4f})")

    # Score against a mock ontology
    ontology_labels = [
        "reflow soldering process",
        "solder paste",
        "tombstoning defect",
        "printed circuit board",
        "surface mount component",
        "automated optical inspection",
        "bill of materials",
        "statistical process control",
    ]

    print(f"\nScoring against {len(ontology_labels)} ontology labels...")
    result = score_coverage(inventory, ontology_labels)
    print(f"  Whole-corpus coverage: {result.whole_corpus_coverage:.4f}")
    print(f"  Genre coverage balance: {result.genre_balance:.4f}")
    for genre, cov in sorted(result.per_genre_coverage.items()):
        print(f"    {genre:20s}: {cov:.4f} "
              f"({result.per_genre_matched[genre]}/{result.per_genre_total[genre]})")

    # Extract assertions
    print("\nExtracting SPO assertions...")
    assertions = extract_assertions(docs)
    print(f"  {len(assertions)} assertions extracted")
    for a in assertions[:5]:
        print(f"    ({a.subject} | {a.predicate} | {a.object})")

    print("\nScoring record:")
    print(json.dumps(scoring_record(result), indent=2))


if __name__ == "__main__":
    main()
