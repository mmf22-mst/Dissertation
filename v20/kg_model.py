"""
Populated knowledge graph model — Paper 2 (overview v20 Part III §4).

A populated KG is an rdflib Graph plus one provenance record per extracted
assertion: which document, genre and chunk it came from and the evidence
sentence the extractor cited.  Provenance is what the NLI verifier checks
against (§5.1) and what the genre labels for community structure are
computed from (§5.6).

Entity resolution (§4.3) is applied uniformly to every KG: mentions are
resolved to IRIs by their normalised label (label_normalisation.py), so
"Reflow Oven 3" and "reflow oven 3" and "ReflowOven3" become one
individual.  It is deterministic and has no parameters to tune; a
mention that resolves to an existing ontology *class* label is treated
as an instance of that class (a "class mention"), which the punning check
in validation_pass.py counts, not as the class itself.

On-disk layout for one populated state (population_run.py):

    kg.nt                 the graph, N-Triples, sorted (deterministic hash)
    provenance.jsonl      one record per extracted assertion
    population_stats.json yield, conformance, parse failures, timing

Dependencies: rdflib.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .label_normalisation import normalise_scoring_label

KG = Namespace("http://dissertation.local/kg/")          # minted individuals
KGP = Namespace("http://dissertation.local/kg/prov#")    # provenance annotations


@dataclass
class ExtractedTriple:
    """One assertion as the extractor emitted it, before resolution."""

    subject: str          # mention text
    predicate: str        # property label (must be in the schema)
    obj: str              # mention text or literal value
    subject_type: str     # class label (must be in the schema)
    object_type: Optional[str]   # class label, or None for a literal object
    evidence: str         # the sentence the extractor cites
    doc_id: str
    genre: str
    chunk_index: int
    is_literal: bool = False

    def key(self) -> str:
        h = hashlib.sha256("\x1f".join([
            self.subject, self.predicate, self.obj, self.subject_type,
            self.object_type or "", self.doc_id, str(self.chunk_index)]).encode()).hexdigest()
        return h[:16]


@dataclass
class ProvenanceRecord:
    triple_key: str
    s: str
    p: str
    o: str
    o_is_literal: bool
    doc_id: str
    genre: str
    chunk_index: int
    evidence: str
    subject_mention: str
    object_mention: str
    predicate_label: str


@dataclass
class PopulatedKG:
    graph: Graph
    provenance: List[ProvenanceRecord] = field(default_factory=list)

    # ── size ──
    @property
    def assertion_count(self) -> int:
        return len(self.provenance)

    def individuals(self) -> set:
        return {s for s, _, o in self.graph.triples((None, RDF.type, OWL.NamedIndividual))}

    def genres_by_triple(self) -> Dict[str, str]:
        return {r.triple_key: r.genre for r in self.provenance}

    # ── persistence ──
    def save(self, directory: Path) -> Tuple[Path, Path]:
        directory.mkdir(parents=True, exist_ok=True)
        nt_path = directory / "kg.nt"
        lines = sorted(self.graph.serialize(format="nt").splitlines())
        nt_path.write_text("\n".join(l for l in lines if l.strip()) + "\n", encoding="utf-8")
        prov_path = directory / "provenance.jsonl"
        with prov_path.open("w", encoding="utf-8") as fh:
            for r in self.provenance:
                fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        return nt_path, prov_path

    @classmethod
    def load(cls, directory: Path) -> "PopulatedKG":
        g = Graph()
        g.parse(directory / "kg.nt", format="nt")
        prov = [ProvenanceRecord(**json.loads(l)) for l in
                (directory / "provenance.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        return cls(graph=g, provenance=prov)

    def sha256(self) -> str:
        lines = sorted(self.graph.serialize(format="nt").splitlines())
        return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# ── Schema view of the generating ontology ──────────────────────────


@dataclass
class SchemaEntry:
    iri: URIRef
    label: str
    norm_label: str
    definition: str = ""
    domain: Optional[URIRef] = None
    range: Optional[URIRef] = None
    is_datatype_property: bool = False


@dataclass
class Schema:
    """What the extractor is constrained to: the generating ontology's
    classes and properties, keyed by normalised label."""

    classes: Dict[str, SchemaEntry]      # norm_label → entry
    properties: Dict[str, SchemaEntry]   # norm_label → entry
    class_count: int
    property_count: int

    @classmethod
    def from_ontology(cls, ontology) -> "Schema":
        g = ontology.graph if hasattr(ontology, "graph") else ontology
        classes: Dict[str, SchemaEntry] = {}
        props: Dict[str, SchemaEntry] = {}
        for c in sorted(set(g.subjects(RDF.type, OWL.Class))):
            if not isinstance(c, URIRef):
                continue
            lab = _label(g, c)
            if not lab:
                continue
            classes.setdefault(normalise_scoring_label(lab), SchemaEntry(c, lab, normalise_scoring_label(lab), _definition(g, c)))
        for ptype, is_dt in ((OWL.ObjectProperty, False), (OWL.DatatypeProperty, True)):
            for p in sorted(set(g.subjects(RDF.type, ptype))):
                if not isinstance(p, URIRef):
                    continue
                lab = _label(g, p)
                if not lab:
                    continue
                dom = next(iter(g.objects(p, RDFS.domain)), None)
                rng = next(iter(g.objects(p, RDFS.range)), None)
                props.setdefault(normalise_scoring_label(lab), SchemaEntry(
                    p, lab, normalise_scoring_label(lab), _definition(g, p),
                    dom if isinstance(dom, URIRef) else None,
                    rng if isinstance(rng, URIRef) else None, is_dt))
        return cls(classes, props, len(classes), len(props))

    def render(self, max_definition_chars: int = 160) -> str:
        """Deterministic text rendering for the extraction prompt: every
        class and property, sorted by label, one line each."""
        lines = ["## Classes"]
        for e in sorted(self.classes.values(), key=lambda e: e.norm_label):
            d = (" — " + e.definition[:max_definition_chars]) if e.definition else ""
            lines.append(f"- {e.label}{d}")
        lines.append("\n## Properties")
        for e in sorted(self.properties.values(), key=lambda e: e.norm_label):
            dom = _label_of(self, e.domain) or "any"
            rng = _label_of(self, e.range) or ("literal" if e.is_datatype_property else "any")
            kind = "datatype" if e.is_datatype_property else "object"
            lines.append(f"- {e.label} ({kind}; domain: {dom}; range: {rng})")
        return "\n".join(lines)


def _label(g: Graph, e: URIRef) -> str:
    labels = [str(o) for o in g.objects(e, RDFS.label)]
    return sorted(labels)[0] if labels else ""


def _definition(g: Graph, e: URIRef) -> str:
    from .ontology_model import SKOS
    for p in (SKOS.definition, RDFS.comment):
        vals = [str(o) for o in g.objects(e, p)]
        if vals:
            return sorted(vals)[0]
    return ""


def _label_of(schema: Schema, iri: Optional[URIRef]) -> Optional[str]:
    if iri is None:
        return None
    for e in schema.classes.values():
        if e.iri == iri:
            return e.label
    return str(iri).rsplit("/", 1)[-1].rsplit("#", 1)[-1]


# ── Entity resolution and graph assembly ────────────────────────────


def mint_individual(norm_label: str) -> URIRef:
    """Deterministic IRI for a resolved mention."""
    return KG["i_" + hashlib.sha1(norm_label.encode("utf-8")).hexdigest()[:16]]


def assemble_kg(
    triples: Iterable[ExtractedTriple],
    schema: Schema,
) -> Tuple[PopulatedKG, Dict[str, int]]:
    """
    Resolve mentions and build the graph.  Only schema-conforming
    assertions are kept: predicate and subject type must be schema labels,
    and the object type must be a schema label for object properties.
    Returns the KG and a conformance tally.
    """
    g = Graph()
    g.bind("kg", KG)
    prov: List[ProvenanceRecord] = []
    tally = {"kept": 0, "unknown_predicate": 0, "unknown_subject_type": 0,
             "unknown_object_type": 0, "literal_for_object_property": 0,
             "class_mentions": 0, "duplicates": 0}
    seen: set = set()

    for t in triples:
        p_entry = schema.properties.get(normalise_scoring_label(t.predicate))
        if p_entry is None:
            tally["unknown_predicate"] += 1
            continue
        s_cls = schema.classes.get(normalise_scoring_label(t.subject_type))
        if s_cls is None:
            tally["unknown_subject_type"] += 1
            continue
        s_norm = normalise_scoring_label(t.subject)
        s_iri = mint_individual(s_norm)
        if s_norm in schema.classes:
            tally["class_mentions"] += 1
        g.add((s_iri, RDF.type, OWL.NamedIndividual))
        g.add((s_iri, RDF.type, s_cls.iri))
        g.add((s_iri, RDFS.label, Literal(t.subject)))

        if t.is_literal or p_entry.is_datatype_property:
            if not p_entry.is_datatype_property:
                tally["literal_for_object_property"] += 1
                continue
            o_node = Literal(t.obj)
            o_norm = t.obj
        else:
            o_cls = schema.classes.get(normalise_scoring_label(t.object_type or ""))
            if o_cls is None:
                tally["unknown_object_type"] += 1
                continue
            o_norm = normalise_scoring_label(t.obj)
            o_node = mint_individual(o_norm)
            if o_norm in schema.classes:
                tally["class_mentions"] += 1
            g.add((o_node, RDF.type, OWL.NamedIndividual))
            g.add((o_node, RDF.type, o_cls.iri))
            g.add((o_node, RDFS.label, Literal(t.obj)))

        triple = (s_iri, p_entry.iri, o_node)
        if triple in seen:
            tally["duplicates"] += 1
        seen.add(triple)
        g.add(triple)
        tally["kept"] += 1
        prov.append(ProvenanceRecord(
            triple_key=t.key(), s=str(s_iri), p=str(p_entry.iri), o=str(o_node),
            o_is_literal=isinstance(o_node, Literal), doc_id=t.doc_id, genre=t.genre,
            chunk_index=t.chunk_index, evidence=t.evidence, subject_mention=t.subject,
            object_mention=t.obj, predicate_label=p_entry.label,
        ))
    return PopulatedKG(g, prov), tally
