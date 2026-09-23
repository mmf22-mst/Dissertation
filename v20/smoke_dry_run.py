"""Smoke harness: real rdflib, fake LLM, stub instruments.

Runs the orchestrator end to end for B0D0 (R=2) and B1D1 (R=3) on a tiny
corpus with a small window allotment so that windowing fires, then checks
the v20 mechanics: feedback allotment fields, entity deltas, checkpoint
rounds + sub_battery.json, label normalisation on real graphs.
"""
import hashlib, json, re, sys, time
from pathlib import Path
import numpy as np
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef

sys.path.insert(0, ".")
from pipeline.orchestrator import RunOrchestrator
from pipeline.checkpoint import CheckpointStore, RunConfig, checkpoint_rounds_for
from pipeline.battery import (Battery, ReasonerReport, OOPSReport, StructuralProfile,
                              AlignmentReport, CoverageReport)
from pipeline.feedback_payload import FeedbackCaps
from pipeline.corpus import CorpusDocument, Genre
from pipeline.injection import render_injection
from pipeline.llm import LLMResult
from pipeline.ontology_model import Condition, DecompositionLevel, GroundingLevel, ManagedOntology
from pipeline.label_normalisation import (scoring_copy, rewrite_cq_query,
                                          normalisation_only_hit_share, normalise_scoring_label)

EX = Namespace("http://example.org/onto#")
tc = lambda s: len(s.split())


def embed_fn(texts):
    out = np.zeros((len(texts), 16), dtype=float)
    for i, t in enumerate(texts):
        h = hashlib.sha256(t.lower().encode()).digest()
        v = np.frombuffer(h[:16], dtype=np.uint8).astype(float)
        out[i] = v / (np.linalg.norm(v) or 1.0)
    return out


def term_extractor(text):
    return sorted({w.lower() for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", text)})[:40]


# ── Fake LLM: regenerate the view, add a class per call, sometimes drop one ──
class FakeCaller:
    def __init__(self):
        self.n = 0

    def call(self, prompt: str) -> LLMResult:
        self.n += 1
        m = re.search(r"## Current Ontology\n\n(.*?)\n\n## (Source Text|Feedback on Current Ontology)\n\n(.*)", prompt, re.S)
        view_text, section, tail = m.group(1), m.group(2), m.group(3)
        onto = ManagedOntology() if view_text.startswith("## (Empty") else ManagedOntology.from_string(view_text, "xml")
        # add one class named after a word in the chunk/feedback
        words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", tail)
        word = words[self.n % max(1, len(words))] if words else f"Thing{self.n}"
        cls = EX[f"{word.title().replace('-', '')}Class{self.n}"]
        g = onto.graph
        g.add((cls, RDF.type, OWL.Class))
        g.add((cls, RDFS.label, Literal(f"{word.title().replace('-', ' ')} Reports")))
        # in iteration calls, drop one class to exercise removal logging
        if section.startswith("Feedback"):
            classes = sorted(onto.classes())
            if len(classes) > 3:
                onto.remove_entity(classes[-1])
        raw = onto.serialise("xml")
        return LLMResult(raw_response=raw, prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                         response_hash=hashlib.sha256(raw.encode()).hexdigest(),
                         prompt_tokens=tc(prompt), completion_tokens=tc(raw), wall_seconds=0.01,
                         parse_success=True, ontology=onto, parse_error=None)


# ── Stub instruments ──
def reasoner_fn(o):
    cls = sorted(str(c) for c in o.classes())
    return ReasonerReport(consistent=True, unsatisfiable_classes=cls[:3], owl2dl_conformant=True, profile_violations=[])

def oops_fn(o):
    cls = sorted(str(c) for c in o.classes())
    pits = [{"id": "P04", "name": "Unconnected element", "severity": "minor", "affected_elements": [c]} for c in cls]
    return OOPSReport(pits, 0, 0, len(pits))

structural_fn = lambda o: StructuralProfile({"RR": 0.5})
alignment_fn = lambda o: AlignmentReport(0.3, 0.2, 0.5, max(1, o.class_count), False)

def coverage_fn(o):
    labels = {normalise_scoring_label(o.label(c) or "") for c in o.classes()}
    missing = {g.value: [t for t in ["defect report", "solder joint", "root cause", "corrective action", "risk register"] if t not in labels] for g in Genre}
    return CoverageReport(0.4, 0.8, missing, {g.value: 0.4 for g in Genre})

coverage_by_genre_fn = lambda o, g: CoverageReport(0.5, 1.0, {g: []}, {g: 0.5})

battery = Battery(reasoner_fn, oops_fn, structural_fn, alignment_fn, coverage_fn, cq_fn=None,
                  feedback_caps=FeedbackCaps(unsatisfiable_classes=2, pitfalls=3, missing_terms_per_genre=2, routed_defects=3),
                  feedback_allotment=400, token_counter=tc, coverage_by_genre_fn=coverage_by_genre_fn)

# ── Tiny corpus ──
docs = []
for g in Genre:
    for i in range(2):
        text = (f"{g.value} document {i}. The solder joint failed inspection and a defect report was raised. "
                f"Root cause analysis pointed to the reflow oven profile. Corrective action assigned to the risk register. ") * 6
        docs.append(CorpusDocument(doc_id=f"{g.value}_{i}", genre=g, text=text))


def run(cond_label, B, D, r_max, campaign_dir):
    cond = Condition(B=B, D=D)
    cfg = RunConfig(seed=0, condition=cond, r_max=r_max, window_allotment=40, chunk_allotment=120,
                    injection_allotment=6000, sim_threshold=0.3, fan_out_cap=5, embedding_model="stub",
                    logmap_confidence=0.5, model_id="fake", context_window=32000, thinking_mode=False,
                    feedback_allotment=400, checkpoint_rounds=checkpoint_rounds_for(r_max))
    store = CheckpointStore(Path(campaign_dir))
    inj = render_injection(B, bfo_core_path=Path("/mnt/project/bfo-core.owl"), iof_core_path=Path("/mnt/project/iof-core.rdf"),
                           injection_allotment=6000, token_counter=tc)
    orch = RunOrchestrator(config=cfg, store=store, caller=FakeCaller(), battery=battery, documents=docs,
                           token_counter=tc, embed_fn=embed_fn, injection=inj, injection_iris=set(),
                           logmap_jar=None, term_extractor=term_extractor)
    t0 = time.time(); summary = orch.run(); print(f"{cond_label}: {summary['rounds_completed']} rounds, "
          f"{summary['final_class_count']} classes, {time.time()-t0:.1f}s, injection {inj.entries_included} entries")
    return Path(campaign_dir) / "runs" / cfg.run_id


def check(run_dir, r_max, d1):
    it = [json.loads(l) for l in (run_dir / "iteration_log.jsonl").read_text().splitlines()]
    co = [json.loads(l) for l in (run_dir / "construction_log.jsonl").read_text().splitlines()]
    calls = [r for r in it if r.get("phase") == "iterate"]
    assert all("feedback_tokens" in r for r in calls), "feedback fields missing on iteration calls"
    assert all(r["feedback_overflow_steps"] == 0 for r in calls), "overflow guard fired"
    assert all(r["feedback_tokens"] <= 400 for r in calls)
    assert all("patch_removed_entities" in r for r in calls), "entity deltas missing (iteration)"
    assert all("patch_removed_entities" in r for r in co if r["parse_success"]), "entity deltas missing (construction)"
    windowed = sum(1 for r in co if r["windowed"]) + sum(1 for r in calls if r["windowed"])
    removed = [r["patch_removed_entities"] for r in calls]
    rounds = sorted(int(p.name[1:]) for p in run_dir.iterdir() if p.is_dir() and p.name.startswith("R"))
    subb = sorted(int(p.parent.name[1:]) for p in run_dir.glob("R*/sub_battery.json"))
    print(f"  rounds {rounds}; windowed calls {windowed}; removed entities per iteration call {removed}; "
          f"truncated items {sorted({i for r in calls for i in r['feedback_truncated_items']})}; sub_battery in {subb}")
    if d1:
        assert subb == list(checkpoint_rounds_for(r_max)), f"sub_battery rounds {subb} != {checkpoint_rounds_for(r_max)}"
        subs = [r for r in calls if r["target"].startswith("iterate_sub:")]
        assert subs and all(r["feedback_tokens"] > 0 for r in subs)
        fb = json.loads((run_dir / f"R0{r_max}" / "sub_battery.json").read_text())
        assert all("salient_term_coverage_genre" in v for v in fb.values())
        # per-sub-ontology payload starts with the routed section
        payload_ok = "Issues specific to this sub-ontology" in battery.render_feedback(
            battery.run(ManagedOntology.from_file(run_dir / "R00" / "ontology.owl")).reports, [], "ncr").text
        assert payload_ok
    else:
        assert subb == [], "sub_battery written under D0"
    r0 = (run_dir / "R00" / "feedback_payload.txt").read_text()
    assert r0.startswith("### 1. Reasoner Report") and "(omitted)" in r0
    manifest_cfg = json.loads((run_dir / "config.json").read_text())
    assert manifest_cfg.get("feedback_allotment") == 400 and manifest_cfg.get("checkpoint_rounds") == list(checkpoint_rounds_for(r_max))
    print("  checks passed")


base = Path("/home/claude/v20_support/harness/out")
rd0 = run("B0D0", GroundingLevel.B0, DecompositionLevel.D0, 2, base / "smoke1"); check(rd0, 2, False)
rd1 = run("B1D1", GroundingLevel.B1, DecompositionLevel.D1, 3, base / "smoke2"); check(rd1, 3, True)

# ── Label normalisation on a real ontology ──
onto = ManagedOntology.from_file(rd1 / "R03" / "ontology.owl")
g = scoring_copy(onto)
norm = URIRef("http://dissertation.local/scoring#normLabel")
pairs = sorted((str(onto.label(s)), str(o)) for s, o in g.subject_objects(norm))[:4]
print("scoring copy sample:", pairs)
target_raw, target_norm = pairs[0]          # e.g. ("Analysis Reports", "analysis report")
q = 'SELECT ?x WHERE { ?x a owl:Class ; rdfs:label ?l . FILTER(REGEX(LCASE(STR(?l)), "^%s$")) }' % target_norm
q = "PREFIX owl: <http://www.w3.org/2002/07/owl#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" + q
raw_hits = list(g.query(q)); norm_hits = list(g.query(rewrite_cq_query(q)))
print(f"pattern '{target_norm}': raw-label hits {len(raw_hits)}, normalised-label hits {len(norm_hits)}")
assert len(raw_hits) == 0 and len(norm_hits) >= 1
diag = normalisation_only_hit_share(g, {"cq1": q, "cq2": q.replace(target_norm, "no such label")})
print("diagnostic:", {k: v for k, v in diag.items() if k != "per_cq"})
assert diag["normalised_answerable"] >= 1 and diag["normalisation_only"] >= 1
print("ALL PASSED")
