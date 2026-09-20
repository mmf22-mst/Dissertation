"""
embedding_utils.py — Shared embedding model for the dissertation pipeline.

Used by:
    - Salient-term coverage scoring (task 2 / Paper 1 §5.2a)
    - Windowing selection rule (task 4a / Part I §5)
    - Salient-assertion matching (task 2 / Paper 2 §5.2)

The same model instance and similarity function are shared across all
three consumers so that term-to-label distances are consistent between
"what the battery scores" and "what the window selects."

Dependencies:
    pip install sentence-transformers numpy

Pinning:
    Model weights are pinned by Hugging Face commit hash in EMBEDDING_CONFIG.
    The hash is recorded in the seed register (asset 10) and the model
    manifest (asset 7). Changing the model requires a new calibration of
    SIM_THRESHOLD.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Configuration — the single source of truth for the embedding model
# ---------------------------------------------------------------------------

EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "revision": "fa97f6e",          # pinned HF commit hash
    "dimensions": 384,
    "max_sequence_length": 256,     # model's native limit
    "deterministic": True,          # same input → same vector
    "seed_role": "S-HAR",           # governing seed (no-op: model is deterministic)
    "licence": "Apache-2.0",
}


# ---------------------------------------------------------------------------
# Model loader (singleton)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_model():
    """Load the pinned embedding model. Cached so it's loaded once."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        EMBEDDING_CONFIG["model_name"],
        revision=EMBEDDING_CONFIG["revision"],
    )
    return model


def get_model():
    """Return the shared embedding model instance."""
    return _load_model()


# ---------------------------------------------------------------------------
# Embedding computation
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Embed a list of strings, returning an (N, 384) float32 array.

    Texts are truncated to max_sequence_length tokens by the model.
    Output vectors are L2-normalised (unit length), so cosine similarity
    reduces to a dot product.
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embeddings, dtype=np.float32)


def embed_single(text: str) -> np.ndarray:
    """Embed a single string, returning a (384,) float32 vector."""
    return embed_texts([text])[0]


# ---------------------------------------------------------------------------
# Similarity computation
# ---------------------------------------------------------------------------

def cosine_similarity_matrix(
    a: np.ndarray,
    b: np.ndarray,
) -> np.ndarray:
    """Compute pairwise cosine similarities between two sets of vectors.

    Parameters
    ----------
    a : (M, D) array of L2-normalised vectors.
    b : (N, D) array of L2-normalised vectors.

    Returns
    -------
    (M, N) float32 array where [i, j] is the cosine similarity
    between a[i] and b[j].
    """
    # Since vectors are L2-normalised, cosine similarity = dot product.
    return a @ b.T


def max_similarity(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
) -> float:
    """Return the maximum cosine similarity between one query and many candidates.

    This is the core matching function for both salient-term coverage
    and windowing:
        - Salient-term coverage: query = corpus term, candidates = ontology labels
        - Windowing: query = ontology class label, candidates = chunk terms
    """
    sims = query_embedding @ candidate_embeddings.T
    return float(np.max(sims))


def best_match(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    candidate_labels: list[str],
) -> tuple[str, float]:
    """Return the best-matching candidate label and its similarity score."""
    sims = query_embedding @ candidate_embeddings.T
    idx = int(np.argmax(sims))
    return candidate_labels[idx], float(sims[idx])


# ---------------------------------------------------------------------------
# Batch matching (the workhorse for coverage scoring)
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    """Result of matching one term against an ontology."""
    term: str
    best_match_label: str
    similarity: float
    above_threshold: bool


def match_terms_to_ontology(
    terms: list[str],
    ontology_labels: list[str],
    threshold: float,
    batch_size: int = 64,
) -> list[MatchResult]:
    """Match a list of corpus terms against ontology class/property labels.

    Parameters
    ----------
    terms : salient terms extracted from the corpus.
    ontology_labels : rdfs:label values from the ontology.
    threshold : similarity threshold (SIM_THRESHOLD from calibration).
    batch_size : encoding batch size.

    Returns
    -------
    One MatchResult per term, sorted by descending similarity.
    """
    if not terms or not ontology_labels:
        return []

    term_embeddings = embed_texts(terms, batch_size=batch_size)
    label_embeddings = embed_texts(ontology_labels, batch_size=batch_size)

    # (N_terms, N_labels) similarity matrix
    sim_matrix = cosine_similarity_matrix(term_embeddings, label_embeddings)

    results = []
    for i, term in enumerate(terms):
        best_idx = int(np.argmax(sim_matrix[i]))
        sim = float(sim_matrix[i, best_idx])
        results.append(MatchResult(
            term=term,
            best_match_label=ontology_labels[best_idx],
            similarity=round(sim, 6),
            above_threshold=sim >= threshold,
        ))

    results.sort(key=lambda r: -r.similarity)
    return results


def coverage_score(results: list[MatchResult]) -> float:
    """Proportion of terms matched above threshold."""
    if not results:
        return 0.0
    matched = sum(1 for r in results if r.above_threshold)
    return round(matched / len(results), 6)


# ---------------------------------------------------------------------------
# Windowing support
# ---------------------------------------------------------------------------

def score_classes_against_chunk(
    class_labels: dict[str, str],
    chunk_terms: list[str],
    threshold: float,
    batch_size: int = 64,
) -> list[tuple[str, float]]:
    """Score ontology classes against a corpus chunk's terms.

    This is the Phase 1 scoring function for the windowing selection rule
    (windowing_spec_v15.md §3.2).

    Parameters
    ----------
    class_labels : {class_iri: rdfs_label} for all classes in the ontology.
    chunk_terms : extracted noun phrases from the current corpus chunk.
    threshold : SIM_THRESHOLD; classes below this are excluded from the
        seed set (but may enter via budget fill in Phase 4).

    Returns
    -------
    List of (class_iri, max_similarity) for classes at or above threshold,
    sorted descending by similarity with IRI tiebreaking.
    """
    if not class_labels or not chunk_terms:
        return []

    iris = list(class_labels.keys())
    labels = [class_labels[iri] for iri in iris]

    label_embeddings = embed_texts(labels, batch_size=batch_size)
    term_embeddings = embed_texts(chunk_terms, batch_size=batch_size)

    # For each class label, max similarity across all chunk terms
    sim_matrix = cosine_similarity_matrix(label_embeddings, term_embeddings)
    max_sims = sim_matrix.max(axis=1)  # (N_classes,)

    scored = []
    for i, iri in enumerate(iris):
        sim = float(max_sims[i])
        if sim >= threshold:
            scored.append((iri, round(sim, 6)))

    # Sort: descending similarity, IRI tiebreak (ascending)
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored


# ---------------------------------------------------------------------------
# Manifest entry
# ---------------------------------------------------------------------------

def manifest_entry() -> dict:
    """Return the model manifest entry for asset 7 / seed register."""
    return {
        "asset": "embedding_model",
        "model_name": EMBEDDING_CONFIG["model_name"],
        "revision": EMBEDDING_CONFIG["revision"],
        "dimensions": EMBEDDING_CONFIG["dimensions"],
        "max_sequence_length": EMBEDDING_CONFIG["max_sequence_length"],
        "deterministic": EMBEDDING_CONFIG["deterministic"],
        "seed_role": EMBEDDING_CONFIG["seed_role"],
        "licence": EMBEDDING_CONFIG["licence"],
        "used_by": [
            "salient-term coverage (Paper 1 §5.2a)",
            "windowing selection rule (Part I §5, task 4a)",
            "salient-assertion matching (Paper 2 §5.2)",
        ],
        "calibration_dependency": (
            "SIM_THRESHOLD must be recalibrated if this model changes"
        ),
    }


# ---------------------------------------------------------------------------
# CLI — quick smoke test
# ---------------------------------------------------------------------------

def main():
    """Smoke test: embed a few manufacturing terms and check similarity."""
    print("Loading model...")
    _ = get_model()
    print(f"Model: {EMBEDDING_CONFIG['model_name']}")
    print(f"Revision: {EMBEDDING_CONFIG['revision']}")
    print()

    # Quick sanity check with manufacturing domain terms
    ontology_labels = [
        "reflow soldering process",
        "solder paste",
        "tombstoning defect",
        "printed circuit board assembly",
        "surface mount technology",
        "bill of materials",
    ]
    chunk_terms = [
        "reflow profile",
        "solder joint",
        "tombstone",
        "PCB",
        "SMT placement",
    ]

    print("Ontology labels:", ontology_labels)
    print("Chunk terms:", chunk_terms)
    print()

    label_emb = embed_texts(ontology_labels)
    term_emb = embed_texts(chunk_terms)

    sim_matrix = cosine_similarity_matrix(term_emb, label_emb)

    print("Similarity matrix (chunk terms × ontology labels):")
    print(f"{'':>25s}", end="")
    for lbl in ontology_labels:
        print(f"  {lbl[:12]:>12s}", end="")
    print()
    for i, term in enumerate(chunk_terms):
        print(f"{term:>25s}", end="")
        for j in range(len(ontology_labels)):
            print(f"  {sim_matrix[i, j]:>12.4f}", end="")
        print()

    print()
    print("Manifest entry:")
    print(json.dumps(manifest_entry(), indent=2))


if __name__ == "__main__":
    main()
