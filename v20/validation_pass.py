"""
Validation pass — Paper 2 §4.4, §5.4, and the RQ2.4 contingencies.

Consistency of each populated KG against its own generating ontology,
under a pinned wall-clock timeout per KG, with a pre-registered
scalability contingency:

  * Primary instrument: an OWL 2 DL reasoner (pluggable, DLReasonerHook).
  * If classification times out on ANY KG, the check falls back — for
    EVERY KG in the campaign, so the instrument is identical across
    cells — to the OWL 2 RL rule-based checker below.  The fallback is
    sound but incomplete: it detects disjointness, domain/range,
    functional-property and type clashes and misses inconsistencies that
    need full DL reasoning.  The instrument actually used is recorded,
    and the proportion of KGs on which the DL reasoner completed within
    the timeout is reported.

RQ2.4 floor contingency (fixed order):
  (i)  near-violation counts — assertions satisfying the antecedent of a
       constraint but escaping it through missing type information;
  (ii) punning (same IRI used as class and individual) and type-assertion
       anomaly rates;
  (iii) a declared null.
Both (i) and (ii) are computed here on every KG regardless, so the
contingency needs no re-run.

The RL checker assumes the unique name assumption for individuals the
pipeline minted (they are distinct by construction — kg_model mints one
IRI per resolved mention) and states so; a DL reasoner would not.

Dependencies: rdflib.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Set, Tuple

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .kg_model import PopulatedKG


# ── Hooks ───────────────────────────────────────────────────────────


@dataclass
class ReasonerOutcome:
    instrument: str                # "owl2dl" | "owl2rl"
    completed: bool                # False on timeout
    consistent: Optional[bool]     # None if not completed
    violations: int = 0            # RL: violation count; DL: explanations if available
    violation_types: Dict[str, int] = field(default_factory=dict)
    wall_seconds: float = 0.0
    detail: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return {"instrument": self.instrument, "completed": self.completed, "consistent": self.consistent,
                "violations": self.violations, "violation_types": self.violation_types,
                "wall_seconds": round(self.wall_seconds, 3), "detail": self.detail}


class DLReasonerHook(Protocol):
    """Wrap HermiT / Openllet / a reasoner service.  Must return within
    the timeout or raise TimeoutError; the runner also enforces the
    timeout with a thread guard for hooks that cannot."""

    def check(self, kg: Graph, ontology: Graph, timeout_s: float) -> ReasonerOutcome: ...


def run_with_timeout(fn, timeout_s: float):
    """Thread guard: returns (result, timed_out)."""
    box: Dict[str, object] = {}
    def target():
        try:
            box["r"] = fn()
        except BaseException as exc:  # noqa: BLE001
            box["e"] = exc
    t = threading.Thread(target=target, daemon=True)
    t.start(); t.join(timeout_s)
    if t.is_alive():
        return None, True
    if "e" in box:
        raise box["e"]  # type: ignore[misc]
    return box.get("r"), False


# ── OWL 2 RL rule-based checker ─────────────────────────────────────


def _closure_up(g: Graph, cls: URIRef, cache: Dict[URIRef, Set[URIRef]]) -> Set[URIRef]:
    if cls in cache:
        return cache[cls]
    seen: Set[URIRef] = set()
    stack = [cls]
    while stack:
        c = stack.pop()
        if c in seen or not isinstance(c, URIRef):
            continue
        seen.add(c)
        stack.extend(o for o in g.objects(c, RDFS.subClassOf) if isinstance(o, URIRef))
    cache[cls] = seen
    return seen


def _disjoint_pairs(ont: Graph) -> Set[Tuple[URIRef, URIRef]]:
    pairs: Set[Tuple[URIRef, URIRef]] = set()
    for a, b in ont.subject_objects(OWL.disjointWith):
        if isinstance(a, URIRef) and isinstance(b, URIRef):
            pairs.add((a, b)); pairs.add((b, a))
    for adc in ont.subjects(RDF.type, OWL.AllDisjointClasses):
        members = [m for m in _rdf_list(ont, next(iter(ont.objects(adc, OWL.members)), None)) if isinstance(m, URIRef)]
        for i in members:
            for j in members:
                if i != j:
                    pairs.add((i, j))
    return pairs


def _rdf_list(g: Graph, head) -> List:
    out = []
    while head is not None and head != RDF.nil:
        first = next(iter(g.objects(head, RDF.first)), None)
        if first is not None:
            out.append(first)
        head = next(iter(g.objects(head, RDF.rest)), None)
    return out


@dataclass
class RLReport:
    outcome: ReasonerOutcome
    near_violations: Dict[str, int]
    punning: Dict[str, int]
    type_anomalies: Dict[str, int]

    def as_dict(self) -> Dict[str, object]:
        return {"reasoner": self.outcome.as_dict(), "near_violations": self.near_violations,
                "punning": self.punning, "type_anomalies": self.type_anomalies}


def owl2rl_check(kg: Graph, ontology: Graph) -> RLReport:
    """
    Sound-but-incomplete consistency check plus the RQ2.4 contingency
    counts.  Violation types:
      disjoint_types      an individual asserted (or inferred via domain/range
                          and subclass closure) to be in two disjoint classes
      functional          a functional property with two distinct values
      inverse_functional  an inverse-functional property shared by two subjects
      irreflexive         x p x for an irreflexive property
      asymmetric          x p y and y p x for an asymmetric property
    Near-violations (contingency i):
      untyped_domain / untyped_range   a domain (range) constraint whose
                          subject (object) has no asserted class at all, so
                          no clash could have been detected
    Punning and type anomalies (contingency ii):
      class_as_individual  an ontology class IRI used as an individual
      individual_as_class  a minted individual used as a class / type
      type_not_in_ontology an individual typed with a class the ontology
                          does not declare
      property_as_type    an individual typed with a property IRI
    """
    t0 = time.monotonic()
    up: Dict[URIRef, Set[URIRef]] = {}
    disjoint = _disjoint_pairs(ontology)
    ont_classes = {c for c in ontology.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)}
    ont_props = {p for t in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty)
                 for p in ontology.subjects(RDF.type, t) if isinstance(p, URIRef)}
    domain = {p: [o for o in ontology.objects(p, RDFS.domain) if isinstance(o, URIRef)] for p in ont_props}
    range_ = {p: [o for o in ontology.objects(p, RDFS.range) if isinstance(o, URIRef)] for p in ont_props}
    functional = {p for p in ontology.subjects(RDF.type, OWL.FunctionalProperty)}
    inv_functional = {p for p in ontology.subjects(RDF.type, OWL.InverseFunctionalProperty)}
    irreflexive = {p for p in ontology.subjects(RDF.type, OWL.IrreflexiveProperty)}
    asymmetric = {p for p in ontology.subjects(RDF.type, OWL.AsymmetricProperty)}

    individuals = {s for s in kg.subjects(RDF.type, OWL.NamedIndividual)}
    asserted: Dict[URIRef, Set[URIRef]] = {}
    for s, _, c in kg.triples((None, RDF.type, None)):
        if c == OWL.NamedIndividual or not isinstance(c, URIRef):
            continue
        asserted.setdefault(s, set()).add(c)

    violations: Dict[str, int] = {}
    near: Dict[str, int] = {"untyped_domain": 0, "untyped_range": 0}
    punning = {"class_as_individual": 0, "individual_as_class": 0}
    anomalies = {"type_not_in_ontology": 0, "property_as_type": 0}

    def bump(d, k):
        d[k] = d.get(k, 0) + 1

    # inferred types via domain/range (RL prp-dom / prp-rng)
    inferred: Dict[URIRef, Set[URIRef]] = {s: set(v) for s, v in asserted.items()}
    for s, p, o in kg:
        if p == RDF.type or not isinstance(p, URIRef):
            continue
        for d in domain.get(p, ()):
            if s not in asserted:
                near["untyped_domain"] += 1
            inferred.setdefault(s, set()).add(d)
        if isinstance(o, URIRef):
            for r in range_.get(p, ()):
                if o not in asserted:
                    near["untyped_range"] += 1
                inferred.setdefault(o, set()).add(r)

    # disjointness over the closure of inferred types
    for ind, types in inferred.items():
        closure: Set[URIRef] = set()
        for t in types:
            closure |= _closure_up(ontology, t, up)
        for a in closure:
            for b in closure:
                if a != b and (a, b) in disjoint:
                    bump(violations, "disjoint_types")
                    break
            else:
                continue
            break

    # functional / inverse-functional / irreflexive / asymmetric
    for p in functional:
        seen: Dict[URIRef, Set] = {}
        for s, o in kg.subject_objects(p):
            seen.setdefault(s, set()).add(o)
        violations["functional"] = violations.get("functional", 0) + sum(1 for v in seen.values() if len(v) > 1)
    for p in inv_functional:
        seen: Dict[object, Set] = {}
        for s, o in kg.subject_objects(p):
            seen.setdefault(o, set()).add(s)
        violations["inverse_functional"] = violations.get("inverse_functional", 0) + sum(1 for v in seen.values() if len(v) > 1)
    for p in irreflexive:
        violations["irreflexive"] = violations.get("irreflexive", 0) + sum(1 for s, o in kg.subject_objects(p) if s == o)
    for p in asymmetric:
        pairs = set(kg.subject_objects(p))
        violations["asymmetric"] = violations.get("asymmetric", 0) + sum(1 for s, o in pairs if (o, s) in pairs and s != o)

    # punning and type anomalies
    for ind in individuals:
        if ind in ont_classes:
            punning["class_as_individual"] += 1
    for c in {c for _, _, c in kg.triples((None, RDF.type, None)) if isinstance(c, URIRef)} | \
             {c for c in kg.subjects(RDF.type, OWL.Class)}:
        # a minted individual used as a type; ontology classes used as
        # individuals are counted once, above, not again here
        if c in individuals and c != OWL.NamedIndividual and c not in ont_classes:
            punning["individual_as_class"] += 1
    for ind, types in asserted.items():
        for t in types:
            if t in ont_props:
                anomalies["property_as_type"] += 1
            elif t not in ont_classes and t != OWL.NamedIndividual:
                anomalies["type_not_in_ontology"] += 1

    total = sum(v for v in violations.values())
    outcome = ReasonerOutcome(
        instrument="owl2rl", completed=True, consistent=(total == 0), violations=total,
        violation_types={k: v for k, v in sorted(violations.items()) if v},
        wall_seconds=time.monotonic() - t0,
        detail={"individuals": len(individuals), "assumes_una": True},
    )
    return RLReport(outcome, near, punning, anomalies)


# ── Campaign-level runner with the uniform fallback ─────────────────


@dataclass
class ValidationRecord:
    kg_id: str
    dl: Optional[ReasonerOutcome]       # attempted DL outcome (None if not attempted)
    rl: RLReport                         # always computed (contingency counts)
    instrument_used: str                 # "owl2dl" or "owl2rl" — the reported inconsistency instrument

    def inconsistency_flag(self) -> Optional[bool]:
        if self.instrument_used == "owl2dl" and self.dl is not None and self.dl.completed:
            return not bool(self.dl.consistent)
        return not bool(self.rl.outcome.consistent)

    def as_dict(self) -> Dict[str, object]:
        return {"kg_id": self.kg_id, "instrument_used": self.instrument_used,
                "inconsistent": self.inconsistency_flag(),
                "dl": self.dl.as_dict() if self.dl else None, "rl": self.rl.as_dict()}


def run_validation(
    items: Sequence[Tuple[str, PopulatedKG, Graph]],   # (kg_id, kg, generating ontology graph)
    dl_hook: Optional[DLReasonerHook],
    timeout_s: float,
) -> Tuple[List[ValidationRecord], Dict[str, object]]:
    """
    Apply the pre-registered rule.  DL is attempted on every KG (so the
    completion rate is reported); if any KG times out — or no DL hook is
    configured — the reported instrument is OWL 2 RL for every KG.
    """
    records: List[ValidationRecord] = []
    timed_out = 0
    dl_attempted = dl_hook is not None
    for kg_id, kg, ont in items:
        rl = owl2rl_check(kg.graph, ont)
        dl: Optional[ReasonerOutcome] = None
        if dl_hook is not None:
            t0 = time.monotonic()
            res, to = run_with_timeout(lambda: dl_hook.check(kg.graph, ont, timeout_s), timeout_s)
            if to or res is None or not res.completed:
                timed_out += 1
                dl = ReasonerOutcome("owl2dl", False, None, wall_seconds=time.monotonic() - t0)
            else:
                dl = res
        records.append(ValidationRecord(kg_id, dl, rl, "owl2dl"))
    fallback = (not dl_attempted) or timed_out > 0
    if fallback:
        for r in records:
            r.instrument_used = "owl2rl"
    summary = {
        "n_kgs": len(records),
        "dl_attempted": dl_attempted,
        "dl_timeouts": timed_out,
        "dl_completion_rate": (1 - timed_out / len(records)) if (dl_attempted and records) else None,
        "timeout_s": timeout_s,
        "instrument_reported": "owl2rl" if fallback else "owl2dl",
        "fallback_triggered": fallback,
        "inconsistent_share": (sum(1 for r in records if r.inconsistency_flag()) / len(records)) if records else None,
    }
    return records, summary
