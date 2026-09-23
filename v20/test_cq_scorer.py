"""Tests for cq_scorer on real rdflib."""
import json, subprocess, sys
from pathlib import Path
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef

sys.path.insert(0, ".")
from pipeline.cq_scorer import CQSet, CQScorer, INJECTED_NAMESPACE_PREFIXES, _pattern_terms
from pipeline.ontology_model import ManagedOntology, BFO, IOF_CONSTR
from pipeline.battery import (Battery, ReasonerReport, OOPSReport, StructuralProfile,
                              AlignmentReport, CoverageReport)

EX = Namespace("http://example.org/onto#")
IOF = Namespace(str(IOF_CONSTR))

# ── A small B2-style ontology: injected IOF classes + constructed domain classes ──
def build_ontology():
    g = Graph()
    def cls(iri, label, parent=None):
        g.add((iri, RDF.type, OWL.Class)); g.add((iri, RDFS.label, Literal(label)))
        if parent is not None: g.add((iri, RDFS.subClassOf, parent))
    def prop(iri, label, dom, rng):
        g.add((iri, RDF.type, OWL.ObjectProperty)); g.add((iri, RDFS.label, Literal(label)))
        g.add((iri, RDFS.domain, dom)); g.add((iri, RDFS.range, rng))
    # injected (IOF namespace) — must NOT satisfy CQs by themselves
    cls(IOF.PlanSpecification, "plan specification")
    cls(IOF.ManufacturingProcess, "manufacturing process")
    prop(IOF.prescribes, "prescribes", IOF.PlanSpecification, IOF.ManufacturingProcess)
    # constructed domain classes, CamelCase / plural labels
    cls(EX.NonConformanceReports, "NonConformanceReports")
    cls(EX.SolderJoint, "Solder-Joints", IOF.ManufacturingProcess)   # path through an injected class
    cls(EX.ReworkProcedure, "rework procedures", IOF.PlanSpecification)
    prop(EX.documents, "documents", EX.NonConformanceReports, EX.SolderJoint)
    prop(EX.prescribesRework, "prescribes rework", EX.ReworkProcedure, EX.SolderJoint)
    return ManagedOntology(g)


CQ_MD = '''
# Test CQ set

**CQ-NCR-E-01.** Is there a class for non-conformance reports?
```sparql
SELECT ?c WHERE { ?c a owl:Class ; rdfs:label ?l . FILTER(REGEX(LCASE(STR(?l)), "^non conformance report$")) }
```

**CQ-NCR-R-01.** Which classes document solder joints?
```sparql
SELECT ?a ?b WHERE {
  ?a a owl:Class ; rdfs:label ?la . FILTER(REGEX(LCASE(STR(?la)), "^non conformance report$"))
  ?b a owl:Class ; rdfs:label ?lb . FILTER(REGEX(LCASE(STR(?lb)), "^solder joint$"))
  ?p a owl:ObjectProperty ; rdfs:domain ?a ; rdfs:range ?b .
}
```

**CQ-XGN-M-01.** [NCR+DPB] Which plan specifications prescribe manufacturing processes?
```sparql
SELECT ?a ?b WHERE {
  ?a a owl:Class ; rdfs:label ?la . FILTER(REGEX(LCASE(STR(?la)), "^plan specification$"))
  ?b a owl:Class ; rdfs:label ?lb . FILTER(REGEX(LCASE(STR(?lb)), "^manufacturing process$"))
  ?p a owl:ObjectProperty ; rdfs:domain ?a ; rdfs:range ?b .
}
```

**CQ-DPB-M-02.** Which rework procedures prescribe work on things that are manufacturing processes?
```sparql
SELECT ?a ?b WHERE {
  ?a a owl:Class ; rdfs:label ?la . FILTER(REGEX(LCASE(STR(?la)), "^rework procedure$"))
  ?b a owl:Class ; rdfs:label ?lb . FILTER(REGEX(LCASE(STR(?lb)), "^solder joint$"))
  ?p a owl:ObjectProperty ; rdfs:domain ?a ; rdfs:range ?b .
  ?b rdfs:subClassOf+ ?mp . ?mp rdfs:label ?lm . FILTER(REGEX(LCASE(STR(?lm)), "^manufacturing process$"))
}
```

**CQ-FME-D-01.** Is failure mode defined?
```sparql
SELECT ?c WHERE { ?c a owl:Class ; rdfs:label ?l ; skos:definition ?d . FILTER(REGEX(LCASE(STR(?l)), "^failure mode$")) }
```

**CQ-JIR-E-02.** Broken query on purpose
```sparql
SELECT ?c WHERE { ?c a owl:Class ; rdfs:label ?l . FILTER(REGEX(LCASE(STR(?l)), "^tickets$")) 
```
'''

Path("cq_test.md").write_text(CQ_MD, encoding="utf-8")
cq = CQSet.from_markdown("cq_test.md")
assert len(cq.items) == 6 and cq.items[2].genre_tags == ("NCR", "DPB") and cq.items[3].qtype == "multi-hop"
print("parsed:", cq.stratum_counts(), "sha", cq.sha256[:12])

problems = cq.validate()
print("validate:", [(p["cq_id"], p["problem"][:60]) for p in problems])
ids = {p["cq_id"] for p in problems}
assert "CQ-JIR-E-02" in ids, "broken SPARQL not caught"          # parse error
assert any("normalised form" in p["problem"] and p["cq_id"] == "CQ-JIR-E-02" for p in problems)  # 'tickets' plural

onto = build_ontology()
scorer = CQScorer(cq)
rep, results = scorer.score_detailed(onto)
by = {r.cq_id: r for r in results}
print({k: (v.answered, v.answered_raw, v.error is not None) for k, v in by.items()})
assert by["CQ-NCR-E-01"].answered and not by["CQ-NCR-E-01"].answered_raw     # CamelCase+plural only via normalisation
assert by["CQ-NCR-R-01"].answered and not by["CQ-NCR-R-01"].answered_raw     # relational, via normalised labels
assert not by["CQ-XGN-M-01"].answered and by["CQ-XGN-M-01"].rows_injection_only >= 1   # IOF-only rows discarded
assert by["CQ-DPB-M-02"].answered                                            # path THROUGH an injected class is fine
assert not by["CQ-FME-D-01"].answered
assert by["CQ-JIR-E-02"].error is not None and not by["CQ-JIR-E-02"].answered
print(f"overall {rep.answerability:.3f}  primary {rep.primary_answerability}  ({rep.primary_answerable}/{rep.primary_total})  "
      f"strata {rep.per_stratum}  genres {rep.per_genre}  norm-only {rep.normalisation_only_share}  errors {rep.errors}")
assert rep.primary_total == 3 and rep.primary_answerable == 2
assert rep.normalisation_only_share == 1.0 and rep.errors == 1 and rep.injection_only_cqs == 1

# Without the rule the IOF-only CQ would be answered — shows why the floor exists
rep_noexcl = CQScorer(cq, exclude_prefixes=()).score(onto)
assert rep_noexcl.per_cq["CQ-XGN-M-01"] is True
print("without exclusion, IOF-only CQ answered:", rep_noexcl.per_cq["CQ-XGN-M-01"])

# Battery integration
b = Battery(lambda o: ReasonerReport(True, [], True, []), lambda o: OOPSReport([], 0, 0, 0),
            lambda o: StructuralProfile({}), lambda o: AlignmentReport(0.3, 0.3, 0.4, 5, False),
            lambda o: CoverageReport(0.5, 0.9, {}, {}), cq_fn=scorer)
res = b.run(onto)
assert res.scores["cq_answerability_primary"] == rep.primary_answerability
assert res.scores["cq_set_sha256"] == cq.sha256 and "cq_per_cq" in res.scores
assert "CQ" not in res.feedback_text and "answerab" not in res.feedback_text.lower()   # held out of feedback
print("battery scores keys:", sorted(k for k in res.scores if k.startswith("cq_")))

# Determinism
rep2 = scorer.score(onto)
assert rep2.per_cq == rep.per_cq

# CLI
onto.graph.serialize("test_onto.owl", format="xml")
out = subprocess.run([sys.executable, "-m", "pipeline.cq_scorer", "--cq-file", "cq_test.md", "--ontology", "test_onto.owl",
                      "--out", "cq_out.json"], capture_output=True, text=True)
assert out.returncode == 0, out.stderr
d = json.loads(Path("cq_out.json").read_text())
assert d["cq_answerability_primary"] == rep.primary_answerability and len(d["per_cq"]) == 6
v = subprocess.run([sys.executable, "-m", "pipeline.cq_scorer", "--cq-file", "cq_test.md", "--validate"], capture_output=True, text=True)
assert v.returncode == 1 and "CQ-JIR-E-02" in v.stdout
print("CLI ok")
print("ALL PASSED")
