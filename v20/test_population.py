"""Tests for the task 9 scaffolding (real rdflib, fake LLM/NLI/reasoner)."""
import json, shutil, sys, time
from pathlib import Path
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef

sys.path.insert(0, ".")
from pipeline.ontology_model import ManagedOntology
from pipeline.corpus import CorpusDocument, Genre
from pipeline.kg_model import Schema, ExtractedTriple, assemble_kg, PopulatedKG
from pipeline.population_extract import populate_state, parse_extraction_response, ExtractionStats
from pipeline.triple_sampler import stratified_sample, wilson, proportional_allocation, half_width_at
from pipeline.nli_verifier import (LexicalOverlapNLI, verify_sample, make_injection_set, calibrate,
                                   threshold_sweep, class_labels_for, STYLE_B1, STYLE_B2)
from pipeline.validation_pass import owl2rl_check, run_validation, ReasonerOutcome
from pipeline.population_run import (PopulationConfig, populate_one, validate_all, utilisation, s_pop, s_har,
                                     write_manifest)

EX = Namespace("http://example.org/onto#")
tc = lambda s: len(s.split())

# ── Generating ontology ──
def ontology():
    g = Graph()
    def cls(i, lab, parent=None):
        g.add((i, RDF.type, OWL.Class)); g.add((i, RDFS.label, Literal(lab)))
        if parent is not None: g.add((i, RDFS.subClassOf, parent))
    def prop(i, lab, dom, rng, kind=OWL.ObjectProperty, extra=()):
        g.add((i, RDF.type, kind)); g.add((i, RDFS.label, Literal(lab)))
        g.add((i, RDFS.domain, dom)); g.add((i, RDFS.range, rng))
        for e in extra: g.add((i, RDF.type, e))
    cls(EX.NCR, "Non-Conformance Report"); cls(EX.Part, "Part"); cls(EX.Machine, "Machine")
    cls(EX.Person, "Person"); cls(EX.Defect, "Defect"); cls(EX.Unused, "Unused Class")
    g.add((EX.Part, OWL.disjointWith, EX.Machine)); g.add((EX.Person, OWL.disjointWith, EX.Machine))
    prop(EX.reports, "reports", EX.NCR, EX.Defect)
    prop(EX.affects, "affects", EX.Defect, EX.Part)
    prop(EX.producedOn, "produced on", EX.Part, EX.Machine, extra=(OWL.FunctionalProperty,))
    prop(EX.raisedBy, "raised by", EX.NCR, EX.Person)
    prop(EX.severity, "severity", EX.NCR, RDFS.Literal, kind=OWL.DatatypeProperty)
    prop(EX.unusedProp, "unused property", EX.NCR, EX.Part)
    return ManagedOntology(g)

onto = ontology()
schema = Schema.from_ontology(onto)
assert schema.class_count == 6 and schema.property_count == 6
print("schema render:\n" + schema.render()[:300] + "\n...")

# ── Corpus ──
docs = []
for gi, g_ in enumerate([Genre.NCR, Genre.FMEA, Genre.JIRA]):
    for i in range(3):
        docs.append(CorpusDocument(doc_id=f"{g_.value}_{i}", genre=g_,
            text=(f"NCR-{gi}{i} reports a solder bridge. The solder bridge affects Board B{gi}{i}. "
                  f"Board B{gi}{i} was produced on Reflow Oven {gi}. NCR-{gi}{i} was raised by Alice Chen. "
                  f"Severity of NCR-{gi}{i} is high. ") * 3))

# ── Fake extraction backend: reads the text, emits schema-conformant + some junk ──
class FakeBackend:
    def generate(self, prompt):
        text = prompt.split("# Text\n\n", 1)[1].split("\n\n# Facts")[0]
        import re
        lines = []
        for ncr, defect, board, oven in re.findall(r"(NCR-\d+) reports a (solder bridge)\. The solder bridge affects (Board B\d+)\. Board B\d+ was produced on (Reflow Oven \d)", text)[:1]:
            ev1 = f"{ncr} reports a {defect}."
            lines.append(json.dumps({"subject": ncr, "subject_type": "Non-Conformance Report", "predicate": "reports", "object": defect, "object_type": "Defect", "evidence": ev1}))
            lines.append(json.dumps({"subject": defect, "subject_type": "Defect", "predicate": "affects", "object": board, "object_type": "Part", "evidence": f"The {defect} affects {board}."}))
            lines.append(json.dumps({"subject": board, "subject_type": "Part", "predicate": "produced on", "object": oven, "object_type": "Machine", "evidence": f"{board} was produced on {oven}."}))
            lines.append(json.dumps({"subject": ncr, "subject_type": "Non-Conformance Report", "predicate": "raised by", "object": "Alice Chen", "object_type": "Person", "evidence": f"{ncr} was raised by Alice Chen."}))
            lines.append(json.dumps({"subject": ncr, "subject_type": "Non-Conformance Report", "predicate": "severity", "object": "high", "object_type": None, "evidence": f"Severity of {ncr} is high."}))
            # junk: unknown predicate, unknown type, malformed line
            lines.append(json.dumps({"subject": ncr, "subject_type": "Non-Conformance Report", "predicate": "caused by", "object": oven, "object_type": "Machine", "evidence": "x"}))
            lines.append(json.dumps({"subject": ncr, "subject_type": "Ticket", "predicate": "reports", "object": defect, "object_type": "Defect", "evidence": "x"}))
            lines.append('{"subject": "broken"')
        out = "```json\n" + "\n".join(lines) + "\n```"
        return out, tc(prompt), tc(out)

kg, stats = populate_state(onto, docs, FakeBackend(), tc, extraction_chunk_allotment=60)
print("extraction:", {k: v for k, v in stats.as_dict().items() if k in ("chunks", "calls", "emitted", "lines_malformed", "conformance", "yield_per_1000_tokens")})
assert stats.conformance["kept"] > 0 and stats.conformance["unknown_predicate"] > 0 and stats.conformance["unknown_subject_type"] > 0
assert stats.lines_malformed > 0
assert kg.assertion_count == stats.conformance["kept"]
assert len(kg.individuals()) > 0

# degenerate schema → empty KG, no error
empty_kg, empty_stats = populate_state(ManagedOntology(Graph()), docs, FakeBackend(), tc, 60)
assert empty_stats.degenerate_schema and empty_kg.assertion_count == 0

# ── Sampler + Wilson ──
alloc = proportional_allocation({"ncr": 500, "fmea": 300, "jira": 200, "arm": 3}, 100)
assert sum(alloc.values()) == 100 and alloc["arm"] >= 0, alloc
s = stratified_sample(kg.provenance, 10, seed=7)
s2 = stratified_sample(kg.provenance, 10, seed=7)
assert [r.triple_key for r in s.records] == [r.triple_key for r in s2.records] and s.n == 10
s_all = stratified_sample(kg.provenance, 100000, seed=7)
assert s_all.n == kg.assertion_count
w = wilson(1600, 2000)
print(f"wilson(1600/2000): {w.estimate:.3f} [{w.lower:.3f}, {w.upper:.3f}] half {w.half_width:.4f}; planning hw@2000,0.8 = {half_width_at(2000):.4f}")
assert 0.017 < w.half_width < 0.019 and wilson(0, 10).lower == 0.0 and wilson(10, 10).upper == 1.0

# ── NLI verification (lexical stand-in) ──
nli = LexicalOverlapNLI()
labels = class_labels_for(kg, schema)
ver = verify_sample(s_all, nli, threshold=0.6)
print("precision (lexical NLI, threshold 0.6):", ver.precision.as_dict(), "genres:", list(ver.per_genre))
assert ver.precision.trials == kg.assertion_count and ver.precision.estimate > 0.5

# ── Calibration by injection + style crossing ──
items = make_injection_set(kg, schema, seed=3, max_items=50)
n_pos = sum(1 for it in items if it.label); n_neg = len(items) - n_pos
assert n_pos > 0 and n_neg > 0, (n_pos, n_neg)
muts = {it.mutation for it in items if not it.label}
print(f"injection set: {n_pos} positives, {n_neg} negatives, mutations {sorted(muts)}")
cal = calibrate(items, nli, threshold=0.6, class_labels=labels)
for c in cal:
    print(f"  {c.style:5s} sens {c.sensitivity.estimate:.2f} spec {c.specificity.estimate:.2f} by-mutation {[(k, round(v.estimate,2)) for k, v in c.by_mutation.items()]}")
assert cal[0].sensitivity.estimate >= 0.9
sweep = threshold_sweep(items, nli, [0.3, 0.5, 0.7, 0.9])
assert len(sweep) == 4 and all("youden" in r for r in sweep)

# ── OWL 2 RL checker on crafted violations ──
bad = Graph()
for t in kg.graph: bad.add(t)
some_part = next(iter(kg.graph.subjects(RDF.type, EX.Part)))
some_machine = next(iter(kg.graph.subjects(RDF.type, EX.Machine)))
bad.add((some_part, RDF.type, EX.Machine))                       # disjoint types (Part ∧ Machine)
bad.add((some_part, EX.producedOn, EX.OtherOven))                # functional: second value
bad.add((EX.OtherOven, RDF.type, OWL.NamedIndividual))
bad.add((EX.Untyped, EX.affects, some_part))                     # domain constraint, subject untyped → near-violation
bad.add((EX.NCR, RDF.type, OWL.NamedIndividual))                 # punning: class used as individual
bad.add((some_machine, RDF.type, EX.NotInOntology))              # type not in ontology
bad.add((some_machine, RDF.type, EX.reports))                    # property as type
rl = owl2rl_check(bad, onto.graph)
print("RL violations:", rl.outcome.violation_types, "near:", rl.near_violations, "punning:", rl.punning, "anomalies:", rl.type_anomalies)
assert rl.outcome.consistent is False
assert rl.outcome.violation_types.get("disjoint_types", 0) >= 1 and rl.outcome.violation_types.get("functional", 0) >= 1
assert rl.near_violations["untyped_domain"] >= 1 and rl.punning["class_as_individual"] == 1 and rl.punning["individual_as_class"] == 0
assert rl.type_anomalies["type_not_in_ontology"] == 1 and rl.type_anomalies["property_as_type"] == 1
clean = owl2rl_check(kg.graph, onto.graph)
assert clean.outcome.consistent is True and clean.outcome.violations == 0

# ── DL hook with timeout → uniform fallback ──
class SlowDL:
    def check(self, kg_g, ont_g, timeout_s):
        time.sleep(timeout_s + 0.5); return ReasonerOutcome("owl2dl", True, True)
class FastDL:
    def check(self, kg_g, ont_g, timeout_s):
        return ReasonerOutcome("owl2dl", True, True, wall_seconds=0.01)
items3 = [("a", kg, onto.graph), ("b", PopulatedKG(bad, []), onto.graph)]
recs, summ = run_validation(items3, FastDL(), timeout_s=1.0)
assert summ["instrument_reported"] == "owl2dl" and not summ["fallback_triggered"] and summ["dl_completion_rate"] == 1.0
recs, summ = run_validation(items3, SlowDL(), timeout_s=0.2)
assert summ["fallback_triggered"] and all(r.instrument_used == "owl2rl" for r in recs) and summ["dl_completion_rate"] == 0.0
assert recs[1].inconsistency_flag() is True and recs[0].inconsistency_flag() is False
recs, summ = run_validation(items3, None, timeout_s=1.0)
assert summ["instrument_reported"] == "owl2rl" and summ["dl_completion_rate"] is None
print("validation summary (slow DL):", {k: summ[k] for k in ("dl_timeouts", "instrument_reported", "fallback_triggered", "inconsistent_share")})

# ── Utilisation ──
u = utilisation(kg, onto, stats)
print("utilisation:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in u.items()})
assert u["classes_used"] == 5 and u["classes_total"] == 6 and u["properties_used"] == 5 and u["properties_total"] == 6
assert 0.0 <= u["orphan_instance_rate"] <= 1.0

# ── Per-state driver and on-disk layout ──
base = Path("out_pop"); shutil.rmtree(base, ignore_errors=True)
cfg = PopulationConfig(population_dir=base, extraction_chunk_allotment=60, sample_n=20, har_master_seed=11,
                       nli_threshold=0.6, validation_timeout_s=1.0, nli_model_id="lexical-stub")
write_manifest(cfg, {"note": "test"})
results = [populate_one("seed_00_B0D0", 0, r, onto, docs, FakeBackend(), tc, nli, cfg) for r in (0, 3)]
summ = validate_all(results, FastDL(), cfg)
files = sorted(p.name for p in (base / "seed_00_B0D0" / "R00").iterdir())
print("state files:", files)
assert files == ["kg.nt", "population_stats.json", "provenance.jsonl", "sample.json", "utilisation.json", "validation.json", "verification.json"]
reloaded = PopulatedKG.load(base / "seed_00_B0D0" / "R00")
assert reloaded.assertion_count == results[0].kg.assertion_count and reloaded.sha256() == results[0].kg.sha256()
ps = json.loads((base / "seed_00_B0D0" / "R00" / "population_stats.json").read_text())
assert ps["s_pop"] == s_pop(0, 0) and s_pop(0, 0) != s_pop(0, 3) and s_har(0, 0, 11) != s_har(1, 0, 11)
assert (base / "validation_summary.json").exists() and (base / "population_manifest.json").exists()
print("ALL PASSED")
