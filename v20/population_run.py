"""
Population runner — Paper 2 §4, §5.5; the per-state driver for task 9.

For every checkpoint ontology-state (60 runs × the checkpoint rounds,
overview Part I §5), populate a KG from the frozen population sample (B),
validate it, verify a stratified sample of its triples, and compute the
utilisation outcomes.  Writes, under <population_dir>/<run_id>/R<nn>/:

    kg.nt, provenance.jsonl          the populated KG (kg_model)
    population_stats.json            extraction stats and conformance
    sample.json                      the drawn verification sample
    verification.json                precision with Wilson intervals
    utilisation.json                 RQ2.5 outcomes
    validation.json                  per-KG reasoner record (written by
                                     run_validation after the whole
                                     campaign, since the fallback rule is
                                     campaign-wide)

Seeds: S-POP is nested within S-GEN — derived deterministically from the
generation seed and the round, recorded per state — and S-HAR governs
the triple sample.  Decoding is greedy; the deterministic regime applies.

The community-structure instruments (task 6) consume kg.nt and
provenance.jsonl and are not part of this module.

Dependencies: rdflib; everything else is injected.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .corpus import CorpusDocument
from .kg_model import PopulatedKG, Schema
from .nli_verifier import NLIModel, STYLE_PLAIN, class_labels_for, verify_sample
from .ontology_model import ManagedOntology
from .population_extract import ExtractionStats, populate_state
from .triple_sampler import SAMPLE_N_DEFAULT, stratified_sample
from .validation_pass import DLReasonerHook, run_validation

log = logging.getLogger(__name__)


# ── Seeds ───────────────────────────────────────────────────────────


def s_pop(s_gen: int, round_num: int) -> int:
    """S-POP nested within S-GEN: deterministic, recorded, never chosen."""
    h = hashlib.sha256(f"S-POP|{s_gen}|{round_num}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def s_har(s_gen: int, round_num: int, har_master: int) -> int:
    """S-HAR for the triple sample of one state, from the campaign's HAR master seed."""
    h = hashlib.sha256(f"S-HAR|{har_master}|{s_gen}|{round_num}".encode()).digest()
    return int.from_bytes(h[:4], "big")


# ── Utilisation (RQ2.5) ─────────────────────────────────────────────


def utilisation(kg: PopulatedKG, ontology: ManagedOntology, stats: ExtractionStats) -> Dict[str, Any]:
    """
    Ontology utilisation rate (share of ontology classes / properties
    instantiated at least once), population yield per 1,000 corpus
    tokens, and orphan-instance rate (individuals with no assertion
    beyond their types and label).
    """
    g = kg.graph
    ont_classes = {c for c in ontology.classes() if isinstance(c, URIRef)}
    ont_props = {p for p in ontology.object_properties() | ontology.datatype_properties() if isinstance(p, URIRef)}
    used_classes = {c for _, _, c in g.triples((None, RDF.type, None)) if isinstance(c, URIRef) and c in ont_classes}
    used_props = {p for _, p, _ in g if p in ont_props}
    individuals = kg.individuals()
    orphan = 0
    for ind in individuals:
        has_assertion = any(p not in (RDF.type, RDFS.label) for _, p, _ in g.triples((ind, None, None))) or \
                        any(True for _ in g.triples((None, None, ind)))
        if not has_assertion:
            orphan += 1
    return {
        "class_utilisation": (len(used_classes) / len(ont_classes)) if ont_classes else 0.0,
        "property_utilisation": (len(used_props) / len(ont_props)) if ont_props else 0.0,
        "classes_used": len(used_classes), "classes_total": len(ont_classes),
        "properties_used": len(used_props), "properties_total": len(ont_props),
        "individuals": len(individuals),
        "assertions": kg.assertion_count,
        "orphan_instance_rate": (orphan / len(individuals)) if individuals else 0.0,
        "yield_per_1000_tokens": (1000.0 * kg.assertion_count / stats.corpus_tokens) if stats.corpus_tokens else 0.0,
        "degenerate_schema": stats.degenerate_schema,
    }


# ── Per-state driver ────────────────────────────────────────────────


@dataclass
class PopulationConfig:
    population_dir: Path
    extraction_chunk_allotment: int
    sample_n: int = SAMPLE_N_DEFAULT
    har_master_seed: int = 0
    nli_threshold: float = 0.5
    nli_style: str = STYLE_PLAIN
    validation_timeout_s: float = 600.0
    nli_model_id: str = "unpinned"

    def manifest(self) -> Dict[str, Any]:
        return {"extraction_chunk_allotment": self.extraction_chunk_allotment, "sample_n": self.sample_n,
                "har_master_seed": self.har_master_seed, "nli_threshold": self.nli_threshold,
                "nli_style": self.nli_style, "validation_timeout_s": self.validation_timeout_s,
                "nli_model_id": self.nli_model_id}


@dataclass
class StateResult:
    run_id: str
    round_num: int
    kg: PopulatedKG
    ontology_graph: Graph
    stats: ExtractionStats
    sample: Dict[str, Any]
    verification: Dict[str, Any]
    utilisation: Dict[str, Any]
    out_dir: Path


def populate_one(
    run_id: str, s_gen: int, round_num: int, ontology: ManagedOntology,
    documents: Sequence[CorpusDocument], backend, token_counter: Callable[[str], int],
    nli: NLIModel, cfg: PopulationConfig,
) -> StateResult:
    out_dir = cfg.population_dir / run_id / f"R{round_num:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    kg, stats = populate_state(ontology, documents, backend, token_counter, cfg.extraction_chunk_allotment)
    kg.save(out_dir)
    schema = Schema.from_ontology(ontology)

    sample = stratified_sample(kg.provenance, cfg.sample_n, s_har(s_gen, round_num, cfg.har_master_seed))
    labels = class_labels_for(kg, schema)
    ver = verify_sample(sample, nli, cfg.nli_threshold, style=cfg.nli_style, class_labels=labels)
    util = utilisation(kg, ontology, stats)

    pop_stats = stats.as_dict()
    pop_stats.update({"run_id": run_id, "round": round_num, "s_gen": s_gen, "s_pop": s_pop(s_gen, round_num),
                      "kg_sha256": kg.sha256(), "wall_seconds_total": time.monotonic() - t0})
    (out_dir / "population_stats.json").write_text(json.dumps(pop_stats, indent=2), encoding="utf-8")
    (out_dir / "sample.json").write_text(json.dumps(sample.as_dict(), indent=2), encoding="utf-8")
    (out_dir / "verification.json").write_text(json.dumps(ver.as_dict(), indent=2), encoding="utf-8")
    (out_dir / "utilisation.json").write_text(json.dumps(util, indent=2), encoding="utf-8")
    return StateResult(run_id, round_num, kg, ontology.graph, stats, sample.as_dict(), ver.as_dict(), util, out_dir)


def validate_all(results: Sequence[StateResult], dl_hook: Optional[DLReasonerHook], cfg: PopulationConfig) -> Dict[str, Any]:
    """Campaign-wide validation with the uniform fallback; writes validation.json per state."""
    items = [(f"{r.run_id}/R{r.round_num:02d}", r.kg, r.ontology_graph) for r in results]
    records, summary = run_validation(items, dl_hook, cfg.validation_timeout_s)
    for r, rec in zip(results, records):
        (r.out_dir / "validation.json").write_text(json.dumps(rec.as_dict(), indent=2), encoding="utf-8")
    (cfg.population_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def write_manifest(cfg: PopulationConfig, extra: Optional[Dict[str, Any]] = None) -> Path:
    m = {"population": cfg.manifest()}
    if extra:
        m.update(extra)
    p = cfg.population_dir / "population_manifest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, indent=2), encoding="utf-8")
    return p
