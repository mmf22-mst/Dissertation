"""
Windowing selection rule — windowing_spec_v15.md §3.

When the accumulated ontology exceeds WINDOW_ALLOTMENT, the generator
sees a selected view rather than the whole ontology.  The selection
rule is deterministic and seed-independent.

Four phases:
  1. Extract terms from the current chunk.
  2. Match terms to ontology class labels by embedding similarity.
  3. Build the structural context: ancestor closure + siblings/children.
  4. Fill remaining budget by descending match score (IRI tiebreak).

Dependencies: rdflib (via ontology_model), numpy, sentence-transformers
              (or any embedding model behind the embed_fn interface)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from rdflib import RDFS, URIRef
from rdflib.namespace import SKOS  # v20 fix: SKOS.definition is used in _build_window_ontology

from .ontology_model import ManagedOntology


# ── Result types ────────────────────────────────────────────────────


@dataclass
class WindowResult:
    """The selected window and its metadata."""

    window: ManagedOntology          # subset ontology to show the model
    selected_classes: Set[URIRef]    # classes included in the window
    total_classes: int               # classes in the full ontology
    visibility_ratio: float          # len(selected) / total
    matched_terms: int               # chunk terms that matched a class
    ancestor_classes: int            # classes added by ancestor closure
    sibling_child_classes: int       # classes added by fan-out
    budget_fill_classes: int         # classes added by budget fill
    windowed: bool                   # True if windowing fired


@dataclass
class WindowStats:
    """Per-chunk logging record for windowing."""

    windowed: bool
    window_classes_shown: int
    window_classes_total: int
    visibility_ratio: float
    matched_terms: int
    ancestor_classes: int
    fan_out_classes: int
    budget_fill_classes: int


# ── Term extraction ─────────────────────────────────────────────────


def extract_terms(
    chunk_text: str,
    term_extractor: Optional[Callable[[str], List[str]]] = None,
) -> List[str]:
    """
    Extract noun phrases / terms from a corpus chunk.

    Uses the same extractor as the salient-term coverage instrument
    (for consistency).  Falls back to whitespace tokenisation if no
    extractor is provided.

    Parameters
    ----------
    chunk_text
        The corpus chunk text.
    term_extractor
        Callable that extracts terms from text.  If None, a simple
        fallback splits on whitespace (for testing only).
    """
    if term_extractor is not None:
        return term_extractor(chunk_text)

    # Fallback: naive word extraction (replace with real extractor)
    words = chunk_text.split()
    # Deduplicate, preserve order
    seen: Set[str] = set()
    terms: List[str] = []
    for w in words:
        w_lower = w.lower().strip(".,;:!?\"'()[]{}—–")
        if w_lower and w_lower not in seen and len(w_lower) > 2:
            seen.add(w_lower)
            terms.append(w_lower)
    return terms


# ── Similarity scoring ──────────────────────────────────────────────


def score_classes(
    chunk_terms: List[str],
    ontology: ManagedOntology,
    embed_fn: Callable[[List[str]], "NDArray"],
    sim_threshold: float,
) -> List[Tuple[URIRef, float]]:
    """
    Score each class by maximum embedding similarity to any chunk term.

    Parameters
    ----------
    chunk_terms
        Terms extracted from the current chunk.
    ontology
        The full accumulated ontology.
    embed_fn
        Callable: list of strings → numpy array of shape (n, dim).
    sim_threshold
        Minimum similarity to count as a match.

    Returns
    -------
    List of (class_uri, max_similarity) for classes above threshold,
    sorted by (-similarity, IRI) for determinism.
    """
    import numpy as np

    classes = sorted(ontology.classes(), key=str)
    if not classes or not chunk_terms:
        return []

    # Get labels
    labels: List[str] = []
    label_to_cls: List[URIRef] = []
    for cls in classes:
        lab = ontology.label(cls)
        if lab:
            labels.append(lab)
            label_to_cls.append(cls)

    if not labels:
        return []

    # Embed
    term_embeddings = embed_fn(chunk_terms)         # (T, dim)
    label_embeddings = embed_fn(labels)             # (L, dim)

    # Cosine similarity matrix: (L, T)
    # Normalise
    term_norms = term_embeddings / (
        np.linalg.norm(term_embeddings, axis=1, keepdims=True) + 1e-10
    )
    label_norms = label_embeddings / (
        np.linalg.norm(label_embeddings, axis=1, keepdims=True) + 1e-10
    )
    sim_matrix = label_norms @ term_norms.T  # (L, T)

    # Max similarity per class
    max_sims = sim_matrix.max(axis=1)  # (L,)

    scored: List[Tuple[URIRef, float]] = []
    for i, cls in enumerate(label_to_cls):
        if max_sims[i] >= sim_threshold:
            scored.append((cls, float(max_sims[i])))

    # Sort: highest similarity first, IRI tiebreak
    scored.sort(key=lambda x: (-x[1], str(x[0])))
    return scored


# ── Window builder ──────────────────────────────────────────────────


def select_window(
    ontology: ManagedOntology,
    chunk_text: str,
    window_allotment: int,
    sim_threshold: float,
    fan_out_cap: int,
    embed_fn: Callable[[List[str]], "NDArray"],
    token_counter: Callable[[str], int],
    term_extractor: Optional[Callable[[str], List[str]]] = None,
    injection_iris: Optional[Set[URIRef]] = None,
) -> WindowResult:
    """
    Build the windowed view of the ontology for the current chunk.

    Implements windowing_spec_v15.md §3:
      Phase 1: extract terms from chunk
      Phase 2: match terms to class labels above SIM_THRESHOLD
      Phase 3: ancestor closure + siblings/children (FAN_OUT_CAP)
      Phase 4: fill remaining budget by descending match score (IRI tiebreak)

    Parameters
    ----------
    ontology
        The full accumulated ontology.
    chunk_text
        Current corpus chunk.
    window_allotment
        Token budget for the ontology view.
    sim_threshold
        Embedding similarity threshold.
    fan_out_cap
        Max siblings + children added per matched class.
    embed_fn
        Embedding function: list[str] → ndarray.
    token_counter
        Callable: str → int (token count).
    term_extractor
        Optional term extractor (see extract_terms).
    injection_iris
        IRIs from the Factor B injection source — these are NOT part of
        the window budget (they are always present in full).

    Returns
    -------
    WindowResult with the selected subset ontology and metadata.
    """
    all_classes = ontology.classes()
    total_classes = len(all_classes)

    # Check if windowing is needed
    full_serial = ontology.serialise("xml")
    if token_counter(full_serial) <= window_allotment:
        return WindowResult(
            window=ontology,
            selected_classes=all_classes,
            total_classes=total_classes,
            visibility_ratio=1.0,
            matched_terms=0,
            ancestor_classes=0,
            sibling_child_classes=0,
            budget_fill_classes=0,
            windowed=False,
        )

    # Exclude injection IRIs from the window budget (they're always present)
    domain_classes = all_classes
    if injection_iris:
        domain_classes = all_classes - injection_iris

    # Phase 1: Extract terms
    terms = extract_terms(chunk_text, term_extractor)

    # Phase 2: Score classes
    scored = score_classes(terms, ontology, embed_fn, sim_threshold)
    matched_classes: Set[URIRef] = {cls for cls, _ in scored}

    # Phase 3: Structural context
    ancestor_added: Set[URIRef] = set()
    sibling_child_added: Set[URIRef] = set()

    for cls in list(matched_classes):
        # Ancestor closure
        ancestors = ontology.ancestor_closure(cls)
        ancestor_added |= (ancestors - matched_classes - ancestor_added)

        # Siblings and direct children, up to fan_out_cap
        fan_out_candidates = ontology.siblings(cls) | ontology.subclasses(cls)
        fan_out_candidates -= matched_classes
        fan_out_candidates -= ancestor_added
        # Sort for determinism, take up to cap
        fan_out_sorted = sorted(fan_out_candidates, key=str)[:fan_out_cap]
        sibling_child_added.update(fan_out_sorted)

    selected = matched_classes | ancestor_added | sibling_child_added

    # Phase 4: Budget fill
    # Build the window and check token budget
    budget_fill_added: Set[URIRef] = set()
    remaining_scored = [(cls, score) for cls, score in scored if cls not in selected]
    # Also add unmatched classes by IRI order as lowest-priority fill
    unmatched = sorted(domain_classes - selected, key=str)
    fill_candidates = [(cls, score) for cls, score in remaining_scored] + [
        (cls, 0.0) for cls in unmatched
    ]

    # Build window ontology from selected classes
    window_onto = _build_window_ontology(ontology, selected, injection_iris)

    # Check budget; add more if room
    current_tokens = token_counter(window_onto.serialise("xml"))

    for cls, _ in fill_candidates:
        if current_tokens >= window_allotment:
            break
        # Tentatively add
        test_triples = ontology.triples_about(cls)
        for t in test_triples:
            window_onto.add_triple(*t)
        new_tokens = token_counter(window_onto.serialise("xml"))
        if new_tokens <= window_allotment:
            selected.add(cls)
            budget_fill_added.add(cls)
            current_tokens = new_tokens
        else:
            # Undo
            for t in test_triples:
                window_onto.remove_triple(*t)
            break

    visibility = len(selected) / total_classes if total_classes > 0 else 1.0

    return WindowResult(
        window=window_onto,
        selected_classes=selected,
        total_classes=total_classes,
        visibility_ratio=visibility,
        matched_terms=len(terms),
        ancestor_classes=len(ancestor_added),
        sibling_child_classes=len(sibling_child_added),
        budget_fill_classes=len(budget_fill_added),
        windowed=True,
    )


def _build_window_ontology(
    full: ManagedOntology,
    selected_classes: Set[URIRef],
    injection_iris: Optional[Set[URIRef]] = None,
) -> ManagedOntology:
    """
    Build a subset ontology containing only the selected classes
    and their connecting structure.

    Includes:
    - All triples where both subject and object are in the selected set
      (or are injection IRIs)
    - Annotation triples (labels, definitions) for selected classes
    - Object/datatype properties whose domain is in the selected set
    """
    from rdflib import OWL, RDF, RDFS, Graph

    allowed = set(selected_classes)
    if injection_iris:
        allowed |= injection_iris

    window_graph = Graph()

    for s, p, o in full.graph:
        include = False

        # Always include rdf:type declarations for selected classes
        if p == RDF.type and s in allowed:
            include = True
        # Include subClassOf where both ends are in scope
        elif p == RDFS.subClassOf:
            if s in allowed and (isinstance(o, URIRef) and o in allowed):
                include = True
            elif s in allowed:
                include = True  # keep the axiom even if target is outside
        # Include annotations for selected entities
        elif s in allowed and p in (RDFS.label, RDFS.comment, SKOS.definition):
            include = True
        # Include property declarations where domain is in scope
        elif p in (RDFS.domain, RDFS.range) and isinstance(o, URIRef):
            if s in allowed or o in allowed:
                include = True
        # Include property type declarations
        elif (
            p == RDF.type
            and o in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty)
            and s in allowed
        ):
            include = True

        if include:
            window_graph.add((s, p, o))

    return ManagedOntology(window_graph)
