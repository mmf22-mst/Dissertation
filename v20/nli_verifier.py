"""
NLI triple verifier and its calibration harness — Paper 2 §5.1, §5.3.

Verification.  Each sampled assertion is verbalised from its schema
labels ("<subject> <predicate label> <object>.") and checked by an NLI
model against its source passage (the evidence sentence plus, optionally,
the surrounding chunk).  A triple is *verified* when the model's entailment
score for (passage ⇒ verbalisation) is at or above a pinned threshold.
Precision = verified / sampled, with a Wilson interval (triple_sampler).
Per-triple, no annotation.

Calibration by injection (§5.3).  The verifier is a heuristic instrument
with no oracle, so before it is used it is characterised on triples whose
truth is known by construction:

  * positives: assertions the pipeline extracted whose evidence sentence
    literally contains both mentions (a conservative proxy for correct),
    or hand-checked seeds if available;
  * negatives: the same assertions mutated — subject swapped for another
    individual of the same class, object swapped likewise, predicate
    swapped for another schema property with compatible domain/range —
    so every negative is schema-conformant and plausible.

Sensitivity = verified positives / positives; specificity = rejected
negatives / negatives; both with Wilson intervals.  Style crossing:
the same items are verbalised with a B1-style template (BFO-flavoured,
category-heavy) and a B2-style template (IOF-flavoured, domain terms),
and sensitivity/specificity are reported per style so any dependence of
verifier behaviour on schema richness is visible before it can confound
the B contrast.

The NLI model is pluggable (NLIModel protocol) so the pinned model and
its revision are recorded in the manifest, not hard-coded here.  A
deterministic lexical stand-in (LexicalOverlapNLI) exists for smoke
tests only.

Dependencies: none beyond the standard library (the NLI model is injected).
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Protocol, Sequence, Tuple

from .kg_model import PopulatedKG, ProvenanceRecord, Schema
from .triple_sampler import Proportion, TripleSample, wilson


# ── NLI model protocol ──────────────────────────────────────────────


class NLIModel(Protocol):
    def entailment_scores(self, pairs: Sequence[Tuple[str, str]]) -> List[float]:
        """For each (premise, hypothesis) return P(entailment) in [0, 1]."""
        ...


class LexicalOverlapNLI:
    """Smoke-test stand-in: fraction of hypothesis content words found in
    the premise.  Deterministic; not an instrument."""

    def entailment_scores(self, pairs: Sequence[Tuple[str, str]]) -> List[float]:
        out = []
        for premise, hyp in pairs:
            pw = set(re.findall(r"[a-z0-9]+", premise.lower()))
            hw = [w for w in re.findall(r"[a-z0-9]+", hyp.lower()) if len(w) > 2]
            out.append(sum(1 for w in hw if w in pw) / len(hw) if hw else 0.0)
        return out


# ── Verbalisation ───────────────────────────────────────────────────

STYLE_PLAIN = "plain"
STYLE_B1 = "b1"      # category-heavy: "<subject>, a <subject class>, <predicate> <object>, a <object class>."
STYLE_B2 = "b2"      # domain-flavoured: "<subject> (<subject class>) <predicate> <object> (<object class>)."


def verbalise(rec: ProvenanceRecord, schema: Optional[Schema] = None, style: str = STYLE_PLAIN,
              class_labels: Optional[Dict[str, str]] = None) -> str:
    s, p, o = rec.subject_mention, rec.predicate_label, rec.object_mention
    if style == STYLE_PLAIN or not class_labels:
        return f"{s} {p} {o}."
    sc = class_labels.get(rec.s, "")
    oc = class_labels.get(rec.o, "") if not rec.o_is_literal else ""
    if style == STYLE_B1:
        sc_t = f", a {sc}," if sc else ""
        oc_t = f", a {oc}" if oc else ""
        return f"{s}{sc_t} {p} {o}{oc_t}."
    if style == STYLE_B2:
        sc_t = f" ({sc})" if sc else ""
        oc_t = f" ({oc})" if oc else ""
        return f"{s}{sc_t} {p} {o}{oc_t}."
    raise ValueError(style)


def class_labels_for(kg: PopulatedKG, schema: Schema) -> Dict[str, str]:
    """individual IRI → its asserted class label (first by label order)."""
    from rdflib import URIRef
    from rdflib.namespace import RDF, OWL
    iri_to_label = {str(e.iri): e.label for e in schema.classes.values()}
    out: Dict[str, str] = {}
    for ind, _, cls in kg.graph.triples((None, RDF.type, None)):
        if cls == OWL.NamedIndividual or not isinstance(cls, URIRef):
            continue
        lab = iri_to_label.get(str(cls))
        if lab and (str(ind) not in out or lab < out[str(ind)]):
            out[str(ind)] = lab
    return out


# ── Verification ────────────────────────────────────────────────────


@dataclass
class VerificationResult:
    precision: Proportion
    per_genre: Dict[str, Proportion]
    threshold: float
    style: str
    scores: List[float] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {"precision": self.precision.as_dict(), "per_genre": {g: p.as_dict() for g, p in self.per_genre.items()},
                "threshold": self.threshold, "style": self.style}


def verify_sample(sample: TripleSample, nli: NLIModel, threshold: float, style: str = STYLE_PLAIN,
                  class_labels: Optional[Dict[str, str]] = None,
                  premise_fn: Optional[Callable[[ProvenanceRecord], str]] = None) -> VerificationResult:
    """Score every sampled triple against its evidence; precision with Wilson."""
    premise_fn = premise_fn or (lambda r: r.evidence)
    pairs = [(premise_fn(r), verbalise(r, style=style, class_labels=class_labels)) for r in sample.records]
    scores = nli.entailment_scores(pairs) if pairs else []
    verified = [s >= threshold for s in scores]
    by_genre: Dict[str, List[bool]] = {}
    for r, v in zip(sample.records, verified):
        by_genre.setdefault(r.genre, []).append(v)
    return VerificationResult(
        precision=wilson(sum(verified), len(verified)),
        per_genre={g: wilson(sum(v), len(v)) for g, v in sorted(by_genre.items())},
        threshold=threshold, style=style, scores=scores,
    )


# ── Calibration by injection ────────────────────────────────────────


@dataclass
class InjectedItem:
    record: ProvenanceRecord
    label: bool          # True = correct, False = mutated
    mutation: str        # "none" | "subject_swap" | "object_swap" | "predicate_swap"


def literal_support(rec: ProvenanceRecord) -> bool:
    """Conservative positive proxy: both mentions appear in the evidence."""
    ev = rec.evidence.lower()
    return rec.subject_mention.lower() in ev and rec.object_mention.lower() in ev


def make_injection_set(kg: PopulatedKG, schema: Schema, seed: int, max_items: int = 500,
                       positives: Optional[Sequence[ProvenanceRecord]] = None) -> List[InjectedItem]:
    """
    Build a labelled set: positives (literal support, or the supplied
    hand-checked seeds) and an equal number of schema-conformant mutations.
    """
    rng = random.Random(seed)
    pos_pool = list(positives) if positives is not None else [r for r in kg.provenance if literal_support(r)]
    pos_pool = sorted(pos_pool, key=lambda r: r.triple_key)
    rng.shuffle(pos_pool)
    pos = pos_pool[:max_items]
    labels = class_labels_for(kg, schema)
    # individuals by class label for same-class swaps
    by_class: Dict[str, List[Tuple[str, str]]] = {}
    for r in kg.provenance:
        for iri, mention in ((r.s, r.subject_mention), (r.o, r.object_mention)):
            c = labels.get(iri)
            if c and not (iri == r.o and r.o_is_literal):
                by_class.setdefault(c, []).append((iri, mention))
    by_class = {c: sorted(set(v)) for c, v in by_class.items()}
    props = sorted(schema.properties.values(), key=lambda e: e.norm_label)

    items: List[InjectedItem] = [InjectedItem(r, True, "none") for r in pos]
    for r in pos:
        choice = rng.choice(["subject_swap", "object_swap", "predicate_swap"])
        mutated = _mutate(r, choice, labels, by_class, props, rng)
        if mutated is None:   # fall back through the other operators
            for alt in ("object_swap", "subject_swap", "predicate_swap"):
                mutated = _mutate(r, alt, labels, by_class, props, rng)
                if mutated is not None:
                    choice = alt
                    break
        if mutated is not None:
            items.append(InjectedItem(mutated, False, choice))
    return items


def _mutate(r: ProvenanceRecord, op: str, labels, by_class, props, rng) -> Optional[ProvenanceRecord]:
    from dataclasses import replace
    if op == "subject_swap":
        c = labels.get(r.s)
        cands = [(i, m) for i, m in by_class.get(c, []) if i != r.s] if c else []
        if not cands:
            return None
        i, m = rng.choice(cands)
        return replace(r, s=i, subject_mention=m, triple_key=r.triple_key + ":ms")
    if op == "object_swap":
        if r.o_is_literal:
            return None
        c = labels.get(r.o)
        cands = [(i, m) for i, m in by_class.get(c, []) if i != r.o] if c else []
        if not cands:
            return None
        i, m = rng.choice(cands)
        return replace(r, o=i, object_mention=m, triple_key=r.triple_key + ":mo")
    if op == "predicate_swap":
        cands = [p for p in props if str(p.iri) != r.p and p.is_datatype_property == r.o_is_literal]
        if not cands:
            return None
        p = rng.choice(cands)
        return replace(r, p=str(p.iri), predicate_label=p.label, triple_key=r.triple_key + ":mp")
    return None


@dataclass
class CalibrationResult:
    style: str
    threshold: float
    sensitivity: Proportion
    specificity: Proportion
    by_mutation: Dict[str, Proportion]
    n_items: int

    def as_dict(self) -> Dict[str, object]:
        return {"style": self.style, "threshold": self.threshold, "n_items": self.n_items,
                "sensitivity": self.sensitivity.as_dict(), "specificity": self.specificity.as_dict(),
                "specificity_by_mutation": {k: v.as_dict() for k, v in self.by_mutation.items()}}


def calibrate(items: Sequence[InjectedItem], nli: NLIModel, threshold: float,
              styles: Sequence[str] = (STYLE_PLAIN, STYLE_B1, STYLE_B2),
              class_labels: Optional[Dict[str, str]] = None) -> List[CalibrationResult]:
    """Sensitivity/specificity per verbalisation style (style crossing)."""
    results = []
    for style in styles:
        pairs = [(it.record.evidence, verbalise(it.record, style=style, class_labels=class_labels)) for it in items]
        scores = nli.entailment_scores(pairs) if pairs else []
        pos = [(s >= threshold) for it, s in zip(items, scores) if it.label]
        neg = [(s < threshold) for it, s in zip(items, scores) if not it.label]
        by_mut: Dict[str, List[bool]] = {}
        for it, s in zip(items, scores):
            if not it.label:
                by_mut.setdefault(it.mutation, []).append(s < threshold)
        results.append(CalibrationResult(
            style=style, threshold=threshold,
            sensitivity=wilson(sum(pos), len(pos)), specificity=wilson(sum(neg), len(neg)),
            by_mutation={k: wilson(sum(v), len(v)) for k, v in sorted(by_mut.items())},
            n_items=len(items),
        ))
    return results


def threshold_sweep(items: Sequence[InjectedItem], nli: NLIModel, thresholds: Sequence[float],
                    style: str = STYLE_PLAIN, class_labels=None) -> List[Dict[str, float]]:
    """Youden-style table for pinning the threshold before the campaign."""
    pairs = [(it.record.evidence, verbalise(it.record, style=style, class_labels=class_labels)) for it in items]
    scores = nli.entailment_scores(pairs) if pairs else []
    rows = []
    for t in thresholds:
        sens = [s >= t for it, s in zip(items, scores) if it.label]
        spec = [s < t for it, s in zip(items, scores) if not it.label]
        se = sum(sens) / len(sens) if sens else float("nan")
        sp = sum(spec) / len(spec) if spec else float("nan")
        rows.append({"threshold": t, "sensitivity": se, "specificity": sp, "youden": se + sp - 1})
    return rows
