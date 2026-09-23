"""
CQ label normalisation — overview v20, Part I §6.2(c).

Ontologies built under different grounding levels use different labelling
conventions (CamelCase against spaced words, singular against plural,
hyphenated against not).  An unnormalised CQ pattern would make part of
any grounding effect on the primary outcome a labelling artefact.

The rule (pinned before the CQ set is frozen; recorded in the campaign
manifest as LABEL_NORMALISATION_RULE):

    1. split CamelCase and underscores into words
    2. lower-case
    3. replace punctuation (hyphens, slashes, dots, ...) with spaces
    4. collapse whitespace
    5. singularise the head noun (last token) by a fixed suffix table

The scorer applies it to a *scoring copy* of the ontology, never to the
artefact: every entity with an rdfs:label gets a `scoring:normLabel`
triple, and the CQ SPARQL is rewritten to match that property instead of
rdfs:label (rewrite_cq_query).  The CQ set stays written against
rdfs:label, so nothing in the frozen asset changes.

Diagnostic: normalisation_only_hit_share() reports, per ontology, the
share of CQ pattern hits that arrive only through the normalised label
and not through the raw label — how far labelling conventions differ by
condition.

This module is stdlib-only except for the two functions that touch a
graph, which import rdflib lazily.

This is NOT the integration-time label normalisation in
deterministic_integration_spec (LABEL_NORMALISATION, casing/whitespace/
punctuation only, applied to the artefact during the D1 merge).  The two
rules are related but serve different steps and are pinned separately.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

LABEL_NORMALISATION_RULE = "v20.1"   # bump if the rule below changes
SCORING_NS = "http://dissertation.local/scoring#"
SCORING_NORMLABEL = SCORING_NS + "normLabel"
SCORING_RAWLABEL = SCORING_NS + "rawLabel"    # verbatim label, same entity set

_CAMEL_1 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_2 = re.compile(r"([a-z0-9])([A-Z])")
_PUNCT = re.compile(r"[^0-9a-z\s]")
_WS = re.compile(r"\s+")

# Head-noun singularisation.  A fixed, ordered suffix table — deliberately
# small so the rule is auditable.  Order matters: first match wins.
# (suffix, replacement, minimum stem length)
_SINGULAR_RULES: List[Tuple[str, str, int]] = [
    ("analyses", "analysis", 0),
    ("hypotheses", "hypothesis", 0),
    ("processes", "process", 0),
    ("statuses", "status", 0),
    ("indices", "index", 0),
    ("matrices", "matrix", 0),
    ("criteria", "criterion", 0),
    ("data", "data", 0),          # mass noun: unchanged
    ("series", "series", 0),
    ("species", "species", 0),
    ("ies", "y", 2),              # assemblies → assembly
    ("sses", "ss", 1),            # classes → class
    ("shes", "sh", 1),            # batches? (no) — finishes → finish
    ("ches", "ch", 1),            # batches → batch
    ("xes", "x", 1),              # boxes → box
    ("zes", "z", 1),
    ("ves", "f", 2),              # shelves → shelf (halves → half)
    ("ss", "ss", 0),              # process (already singular) unchanged
    ("us", "us", 0),              # status, bus unchanged
    ("is", "is", 0),              # axis, basis unchanged
    ("s", "", 2),                 # parts → part
]

# Words the suffix table would mangle; kept singular as-is.
_INVARIANT = {
    "bus", "gas", "lens", "chassis", "diagnosis", "prognosis", "basis",
    "axis", "news", "means", "series", "species", "data", "apparatus",
}


def singularise_head_noun(word: str) -> str:
    """Singularise one lower-case token by the pinned suffix table."""
    if not word or word in _INVARIANT or len(word) < 3:
        return word
    for suffix, repl, min_stem in _SINGULAR_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= min_stem:
            return word[: len(word) - len(suffix)] + repl
    return word


def split_camel(text: str) -> str:
    text = text.replace("_", " ")
    text = _CAMEL_1.sub(r"\1 \2", text)
    text = _CAMEL_2.sub(r"\1 \2", text)
    return text


def normalise_scoring_label(label: str) -> str:
    """
    Apply the pinned rule to one label.

    >>> normalise_scoring_label("NonConformanceReports")
    'non conformance report'
    >>> normalise_scoring_label("Non-Conformance Report")
    'non conformance report'
    >>> normalise_scoring_label("manufacturing_processes")
    'manufacturing process'
    """
    if label is None:
        return ""
    text = split_camel(str(label))
    text = text.lower()
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    if not text:
        return text
    words = text.split(" ")
    words[-1] = singularise_head_noun(words[-1])
    return " ".join(words)


# ── Scoring copy (rdflib) ───────────────────────────────────────────


def scoring_copy(
    ontology,
    exclude_iris: Optional[set] = None,
    exclude_prefixes: Iterable[str] = (),
) -> "object":
    """
    Return an rdflib Graph copy of the ontology's graph with, for every
    (entity, rdfs:label) whose entity is not excluded, a scoring:normLabel
    triple (normalised) and a scoring:rawLabel triple (verbatim).

    The artefact (ManagedOntology) is not modified.  Returns the copy so
    the CQ scorer can run rewritten queries against it.

    Exclusion (cq_scorer.py): injected entities — the Factor B scaffolding —
    receive no scoring label, so a CQ is answered only when the
    label-matched classes come from the constructed part of the ontology.
    Injected classes can still sit on the path between them.  rawLabel
    exists so the normalisation-only diagnostic compares like with like
    (same entity set, only the normalisation differs).
    """
    from rdflib import Graph, Literal, URIRef  # lazy: stdlib-only elsewhere
    from rdflib.namespace import RDFS

    g = Graph()
    src = ontology.graph if hasattr(ontology, "graph") else ontology
    for t in src:
        g.add(t)
    excl = set(str(x) for x in (exclude_iris or set()))
    prefixes = tuple(exclude_prefixes)
    norm = URIRef(SCORING_NORMLABEL)
    raw = URIRef(SCORING_RAWLABEL)
    for s_, o in src.subject_objects(RDFS.label):
        s_str = str(s_)
        if s_str in excl or any(s_str.startswith(p) for p in prefixes):
            continue
        g.add((s_, norm, Literal(normalise_scoring_label(str(o)))))
        g.add((s_, raw, Literal(str(o))))
    return g


_RDFS_LABEL_PREFIXED = re.compile(r"\brdfs:label\b")
_RDFS_LABEL_FULL = re.compile(r"<http://www\.w3\.org/2000/01/rdf-schema#label>")
_PREFIX_LINE = f"PREFIX scoring: <{SCORING_NS}>\n"


def rewrite_cq_query(sparql: str, target: str = "norm") -> str:
    """
    Rewrite a CQ query so its label matches run against the scoring label.
    Deterministic textual substitution: every rdfs:label (prefixed or full
    IRI) becomes scoring:normLabel (target="norm", the instrument) or
    scoring:rawLabel (target="raw", the diagnostic baseline), and the
    scoring prefix is declared if absent.  Nothing else in the query
    changes, so the object-property join structure the primary strata
    require is untouched.
    """
    prop = "scoring:normLabel" if target == "norm" else "scoring:rawLabel"
    full = SCORING_NORMLABEL if target == "norm" else SCORING_RAWLABEL
    out = _RDFS_LABEL_PREFIXED.sub(prop, sparql)
    out = _RDFS_LABEL_FULL.sub(f"<{full}>", out)
    if "PREFIX scoring:" not in out and prop in out:
        out = _PREFIX_LINE + out
    return out


# ── Diagnostic ──────────────────────────────────────────────────────


def normalisation_only_hit_share(
    graph,
    queries: Dict[str, str],
) -> Dict[str, object]:
    """
    For each CQ, run the query against raw rdfs:label (as written) and
    against scoring:normLabel (rewritten) on the same scoring copy, and
    report the share of CQs answerable only through normalisation.

    Returns {"raw_answerable": n, "normalised_answerable": n,
             "normalisation_only": n, "share": float, "per_cq": {...}}.
    Reported per condition as the labelling-convention diagnostic.
    """
    per_cq: Dict[str, Tuple[bool, bool]] = {}
    for cq_id, q in queries.items():
        raw = bool(list(graph.query(rewrite_cq_query(q, "raw"))))
        normed = bool(list(graph.query(rewrite_cq_query(q, "norm"))))
        per_cq[cq_id] = (raw, normed)
    raw_n = sum(1 for r, _ in per_cq.values() if r)
    norm_n = sum(1 for _, n in per_cq.values() if n)
    only = sum(1 for r, n in per_cq.values() if n and not r)
    return {
        "raw_answerable": raw_n,
        "normalised_answerable": norm_n,
        "normalisation_only": only,
        "share": (only / norm_n) if norm_n else 0.0,
        "per_cq": {k: {"raw": r, "normalised": n} for k, (r, n) in per_cq.items()},
    }


def check_pattern_terms(terms: Iterable[str]) -> List[Tuple[str, str]]:
    """
    For cq_calibrate: return (term, normalised) pairs for every CQ pattern
    term that is not already in normalised form.  A pattern written in
    plural or CamelCase would never match a normalised label, so the
    calibration report flags these before the CQ set is frozen.
    """
    out = []
    for t in terms:
        n = normalise_scoring_label(t)
        if n != t.strip().lower():
            out.append((t, n))
    return out
