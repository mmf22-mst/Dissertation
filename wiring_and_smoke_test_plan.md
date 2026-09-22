# Wiring & Smoke-Test Plan

Get the pipeline running on local hardware, validate each layer,
end with the determinism audit (Task 7).

**Estimated effort: 3–4 days** (days 5–6 of the Task 4 estimate,
plus 1 day for the determinism audit).

---

## 0. Environment setup (half day)

### 0.1 Python dependencies

```bash
pip install rdflib tiktoken numpy sentence-transformers requests
```

- `rdflib` — OWL parsing, graph manipulation, SPARQL
- `tiktoken` — token counting (match your model's tokeniser)
- `numpy` — embeddings, similarity
- `sentence-transformers` — embedding model (or swap for your own)
- `requests` — OOPS! REST client, LLM API client

### 0.2 Java dependencies

- **LogMap** — download the LogMap standalone matcher JAR:
  <https://github.com/ernestojimenezruiz/logmap-matcher>
  Put it somewhere stable; note the path.
- **AML** (optional audit) — download from
  <https://github.com/AgreementMakerLight/AML-Project>

Test that both run:
```bash
java -jar /path/to/logmap.jar --help
java -jar /path/to/aml.jar --help
```

### 0.3 Inference server

Start your local model server (vLLM, llama.cpp, etc.) and confirm it
responds:

```bash
curl http://localhost:8000/v1/completions \
  -d '{"model":"your-model","prompt":"Hello","max_tokens":5,"temperature":0}'
```

Record: model ID, revision hash, quantisation, context window, GPU
allocation, deterministic flags.  These go into `manifest.json`.

### 0.4 Token counter

Create a thin wrapper around your model's tokeniser:

```python
# wiring/token_counter.py
import tiktoken

# Replace with your model's tokeniser
_enc = tiktoken.encoding_for_model("gpt-4")  # or cl100k_base, etc.

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))
```

If your model uses a different tokeniser (e.g. Llama's sentencepiece),
wrap that instead.  The pipeline passes `token_counter` everywhere as
a callable; swap it once and everything follows.

### 0.5 Embedding function

```python
# wiring/embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np

_model = SentenceTransformer("all-MiniLM-L6-v2")  # or your pinned model

def embed(texts: list[str]) -> np.ndarray:
    return _model.encode(texts, normalize_embeddings=True)
```

Pin the model name in the manifest.  This function is passed as
`embed_fn` to windowing and salient-term matching.

---

## 1. Pin the allotments — the B2a fit test (half day)

The three prompt allotments must be set so B2a's full injection fits
alongside the window and the chunk within the context window.  B2b
(CCO) will be truncated within the same allotment — its full inventory
(~90K tokens) far exceeds B2a's (~12K).  This is the sizing exercise
that everything else depends on.

### 1.1 Measure the B2a and B2b injections

```python
from pipeline.injection import render_injection
from pipeline.ontology_model import GroundingLevel
from wiring.token_counter import count_tokens
from pathlib import Path

# B2a — the binding constraint for allotment sizing
result_b2a = render_injection(
    grounding=GroundingLevel.B2a,
    iof_core_path=Path("iof-core.rdf"),
    injection_allotment=99999,  # no truncation — measure full size
    token_counter=count_tokens,
)
print(f"B2a full injection: {result_b2a.token_count} tokens, "
      f"{result_b2a.entries_total} entries")

# B2b — will be truncated; measure full size for the record
result_b2b = render_injection(
    grounding=GroundingLevel.B2b,
    cco_merged_path=Path("CommonCoreOntologiesMerged.ttl"),
    injection_allotment=99999,
    token_counter=count_tokens,
)
print(f"B2b full injection: {result_b2b.token_count} tokens, "
      f"{result_b2b.entries_total} entries")
```

Do the same for B1 (`bfo-core.owl`).  B0 is 0 tokens.

### 1.2 Compute the allotments

```
CONTEXT_WINDOW         = <your model's context window>
SYSTEM_OVERHEAD        = ~800 tokens  (system prompt, markers, closing)
OUTPUT_RESERVE         = ~8000 tokens (model's generation budget)

AVAILABLE = CONTEXT_WINDOW - SYSTEM_OVERHEAD - OUTPUT_RESERVE

INJECTION_ALLOTMENT    = result_b2a.token_count  (or round up slightly)
REMAINING              = AVAILABLE - INJECTION_ALLOTMENT
WINDOW_ALLOTMENT       = REMAINING * 0.6     (most goes to the ontology)
CHUNK_ALLOTMENT        = REMAINING * 0.4     (rest to the corpus chunk)
```

Adjust the 60/40 split to taste.  The key constraints:
- `INJECTION_ALLOTMENT + WINDOW_ALLOTMENT + CHUNK_ALLOTMENT + SYSTEM_OVERHEAD + OUTPUT_RESERVE ≤ CONTEXT_WINDOW`
- All three are **fixed across B** — B0, B1, and B2b get the same window and chunk budgets as B2a.
- B2a may or may not fit without truncation; if not, truncation kicks in and you record the truncation point.
- B2b **will** be heavily truncated (full inventory ~6× larger than B2a's).  Record the truncation point and the truncation fraction for the methods section.

### 1.3 Verify

```python
# Build one construction prompt with all three allotments at max
from pipeline.prompt import build_construction_prompt

prompt = build_construction_prompt(
    injection_text="x " * INJECTION_ALLOTMENT,  # placeholder
    ontology_view="x " * WINDOW_ALLOTMENT,
    chunk_text="x " * CHUNK_ALLOTMENT,
    token_counter=count_tokens,
)
assert prompt.token_count <= CONTEXT_WINDOW - OUTPUT_RESERVE, \
    f"Prompt {prompt.token_count} exceeds budget"
```

Record all allotments in a `config.yaml` or constants file.

---

## 2. Wire the battery instruments (1 day)

Each instrument is a callable: `ManagedOntology → report`.
Create a `wiring/battery_instruments.py` that wraps your existing
implementations and returns the report types the Battery expects.

### 2.1 Reasoner

```python
# Wrap owlready2, or call HermiT/ELK via subprocess
from pipeline.battery import ReasonerReport

def run_reasoner(onto: ManagedOntology) -> ReasonerReport:
    # Option A: owlready2
    #   Save to temp file, load in owlready2, run HermiT,
    #   check consistency and collect unsatisfiable classes.
    #
    # Option B: subprocess to robot.jar or HermiT.jar
    #   robot reason --reasoner HermiT -i onto.owl -o reasoned.owl
    #   Parse the output for inconsistencies.
    #
    # Option C: stub for smoke test
    return ReasonerReport(
        consistent=True,
        unsatisfiable_classes=[],
        owl2dl_conformant=True,
        profile_violations=[],
    )
```

For the smoke test, the stub is fine.  Replace with the real thing
before the pilot.

**OWL 2 DL profile check:** rdflib doesn't do this natively.  Options:
- OWL API via Py4J
- `robot validate-profile`
- Write a heuristic check (punning, no meta-modelling)
- Stub for now, real implementation before pilot

### 2.2 OOPS!

You already have the OOPS! REST client in `structural_profile.py`.
Wrap it:

```python
from pipeline.battery import OOPSReport

def run_oops(onto: ManagedOntology) -> OOPSReport:
    owl_xml = onto.serialise("xml")
    # Call your existing OOPS! client
    pitfalls = call_oops_api(owl_xml)  # from structural_profile.py
    return OOPSReport(
        pitfalls=pitfalls,
        critical_count=sum(1 for p in pitfalls if p["severity"] == "critical"),
        important_count=sum(1 for p in pitfalls if p["severity"] == "important"),
        minor_count=sum(1 for p in pitfalls if p["severity"] == "minor"),
    )
```

**Smoke-test note:** OOPS! is a web service and may be slow or
unavailable.  For the smoke test, add a fallback that returns an
empty report with a warning.

### 2.3 OntoQA structural profile

You already have `structural_profile.py` with seven metrics.  Wrap it:

```python
from pipeline.battery import StructuralProfile

def run_structural(onto: ManagedOntology) -> StructuralProfile:
    # Call your existing structural_profile functions
    metrics = compute_ontoqa_metrics(onto.graph)  # from structural_profile.py
    return StructuralProfile(metrics=metrics)
```

### 2.4 Alignment rate

You already have `alignment_rate.sparql`.  Wrap it:

```python
from pipeline.battery import AlignmentReport

ALIGNMENT_QUERY = Path("alignment_rate.sparql").read_text()

def run_alignment(onto: ManagedOntology) -> AlignmentReport:
    results = onto.graph.query(ALIGNMENT_QUERY)
    # Parse the three rates from the query results
    # ...
    return AlignmentReport(
        bfo_aligned_rate=bfo_rate,
        iof_aligned_rate=iof_rate,
        unaligned_rate=unaligned_rate,
        total_domain_classes=total,
        contamination_flag=(unexpected > 0.05),
    )
```

### 2.5 Salient-term coverage

You already have `salient_term_pipeline.py`.  Wrap it:

```python
from pipeline.battery import CoverageReport

def run_coverage(onto: ManagedOntology) -> CoverageReport:
    # Call your existing coverage scoring
    result = score_coverage(onto, salient_term_inventory, embed_fn)
    return CoverageReport(
        salient_term_coverage=result.overall,
        genre_coverage_balance=result.entropy,
        missing_terms_by_genre=result.missing,
        per_genre_coverage=result.per_genre,
    )
```

**Dependency:** This needs the frozen salient-term inventory from Task 2.
For the smoke test, use the synthetic inventory from your Task 2 testing,
or compute a quick one from the test corpus.

### 2.6 CQ scorer (held out)

Not needed for the smoke test or the feedback loop — pass `cq_fn=None`
to the Battery constructor.  Wire it before the pilot, once the CQ set
is frozen (Task 1).

### 2.7 Assemble the Battery

```python
from pipeline.battery import Battery

battery = Battery(
    reasoner_fn=run_reasoner,
    oops_fn=run_oops,
    structural_fn=run_structural,
    alignment_fn=run_alignment,
    coverage_fn=run_coverage,
    cq_fn=None,  # held out; wire after Task 1 freezes the CQ set
)
```

---

## 3. Wire the LLM backend (half day)

### 3.1 Pick your backend

```python
from pipeline.llm import ChatBackend, OpenAICompatibleBackend

# For vLLM serve (completions API):
backend = OpenAICompatibleBackend(
    base_url="http://localhost:8000/v1",
    model="your-model-name",
    max_tokens=8192,  # OUTPUT_RESERVE from §1.2
)

# For chat-tuned models via vLLM or llama.cpp:
backend = ChatBackend(
    base_url="http://localhost:8000/v1",
    model="your-model-name",
    max_tokens=8192,
)
```

### 3.2 Sanity check

```python
from pipeline.llm import LLMCaller

caller = LLMCaller(backend)
result = caller.call("Respond with: Hello world")
print(result.raw_response)
print(f"Prompt tokens: {result.prompt_tokens}")
print(f"Response hash: {result.response_hash}")
```

### 3.3 Determinism pre-check

Run the same prompt three times.  If hashes match, greedy decoding
is working.  If not, check:
- `temperature=0` is being respected
- `seed` parameter is supported by your server
- Prefix caching is disabled
- Batch size is 1
- Deterministic CUDA flags are set

---

## 4. Wire LogMap (half day)

### 4.1 Test the subprocess

```python
from pipeline.integration import _run_logmap
from pipeline.ontology_model import ManagedOntology
from pathlib import Path

# Use two sub-ontologies from the bfo-core.owl as a test
onto1 = ManagedOntology.from_file(Path("bfo-core.owl"))
onto2 = ManagedOntology.from_file(Path("bfo-core.owl"))
# They're identical, so LogMap should find all-to-all alignment

aligns = _run_logmap(onto1, onto2, Path("/path/to/logmap.jar"), 0.5)
print(f"Alignments found: {len(aligns)}")
```

### 4.2 Adjust the subprocess call

The `_run_logmap` stub in `integration.py` has a generic command line.
You'll almost certainly need to adjust it to match LogMap's actual CLI.
Check LogMap's README for the exact invocation.  Common patterns:

```bash
# LogMap standalone
java -jar logmap-matcher.jar \
  file:///path/to/onto1.owl file:///path/to/onto2.owl \
  /output/dir/ true
```

Update the subprocess call and re-test.

### 4.3 If LogMap proves difficult

Stage 2 is optional for the smoke test — the pipeline handles
`logmap_jar=None` gracefully (Stage 1 label-normalisation-only
integration).  Get the rest working first, then come back to LogMap.

---

## 5. Wire the term extractor (quick)

The windowing module needs a term extractor for matching chunk terms
to ontology class labels.  Reuse the one from your salient-term
pipeline:

```python
# wiring/term_extractor.py
from salient_term_pipeline import extract_terms_from_text  # your existing fn

def extract_terms(text: str) -> list[str]:
    return extract_terms_from_text(text)
```

For the smoke test, the fallback in `windowing.py` (whitespace split)
works.  The real extractor matters for the pilot.

---

## 6. Smoke test 1: B0D0, R=2 (half day)

This is the minimum viable run: no injection, no integration, two
iteration rounds.  Tests the full loop without the complex D1 path.

### 6.1 Create a tiny test corpus

You don't want to burn real compute on the smoke test.  Make a tiny
corpus with 2–3 genres and 5–10 short documents per genre:

```
test_corpus/
  ncr/
    doc_001.txt     # 200-word fabricated NCR
    doc_002.txt
  fmea/
    doc_003.txt     # 200-word fabricated FMEA
    doc_004.txt
  command_media/
    doc_005.txt
```

### 6.2 Run it

```python
from pathlib import Path
from pipeline.campaign import CampaignConfig, CampaignRunner
from pipeline.ontology_model import Condition, GroundingLevel, DecompositionLevel
from wiring.token_counter import count_tokens
from wiring.embeddings import embed
from wiring.battery_instruments import battery  # assembled in §2.7

config = CampaignConfig(
    campaign_dir=Path("smoke_test_1"),
    corpus_dir=Path("test_corpus"),
    seeds=[0],
    conditions=[Condition(GroundingLevel.B0, DecompositionLevel.D0)],
    window_allotment=WINDOW_ALLOTMENT,
    chunk_allotment=CHUNK_ALLOTMENT,
    injection_allotment=INJECTION_ALLOTMENT,
    sim_threshold=0.5,          # placeholder; calibrate in Task 2
    fan_out_cap=10,
    r_max=2,                    # just 2 rounds for smoke test
    model_id="your-model",
    context_window=CONTEXT_WINDOW,
    embedding_model="all-MiniLM-L6-v2",
)

runner = CampaignRunner(
    config=config,
    backend=backend,            # from §3
    battery=battery,            # from §2.7
    token_counter=count_tokens,
    embed_fn=embed,
)

summary = runner.run()
```

### 6.3 Verify

```
smoke_test_1/
  manifest.json              ← campaign parameters, corpus stats
  runs/
    seed_00_B0D0/
      config.json            ← run config
      R00/
        ontology.owl         ← non-empty OWL file?
        battery.json         ← has scores?
        feedback_payload.txt ← non-empty feedback text?
        prompt_hash.txt      ← 64-char hex?
        response_hash.txt    ← 64-char hex?
      R01/
        ...                  ← scores differ from R00?
      R02/
        ...
      construction_log.jsonl ← one record per chunk?
      iteration_log.jsonl    ← one record per round?
      run_summary.json       ← wall time, class count?
```

Checklist:
- [ ] `ontology.owl` at each round is parseable RDF/XML
- [ ] `battery.json` has non-null values for all coupled instruments
- [ ] Class count grows from R00 (should start small on tiny corpus)
- [ ] Battery scores change between rounds (feedback is doing something)
- [ ] Construction log has one record per chunk, with token counts
- [ ] Iteration log has one record per round
- [ ] All hashes are 64-char hex strings
- [ ] No Python tracebacks in the log

### 6.4 Common failure modes

| Symptom | Likely cause |
|---|---|
| `ontology.owl` is empty or has 0 triples | OWL parser can't extract RDF/XML from model output — check `llm.py:extract_owl_from_response` against your model's actual output format |
| Battery scores are all null/zero | Instrument wrappers not returning real data |
| Same hash every round | Model not receiving different feedback; check that the prompt changes |
| `parse_success: false` every chunk | Model isn't outputting valid OWL — try the prompt manually, inspect raw output |
| Out of memory | Ontology serialisation is too large — check allotments |

---

## 7. Smoke test 2: B2aD1, R=2 (half day)

This tests the full D1 path: per-genre construction, integration,
defect routing, per-sub-ontology iteration.

### 7.1 Run it

Same test corpus.  Change the condition:

```python
config.conditions = [Condition(GroundingLevel.B2a, DecompositionLevel.D1)]
config.campaign_dir = Path("smoke_test_2")
```

### 7.2 Verify — same checklist as §6.3, plus:

```
runs/seed_00_B2aD1/
  R00/
    sub_ontologies/          ← one .owl per genre?
      ncr.owl
      fmea.owl
      command_media.owl
    integration_log.json     ← alignments found, IRIs redirected?
    iri_provenance.json      ← maps entities to source genres?
```

Additional checks:
- [ ] Sub-ontology files are each parseable and non-empty
- [ ] `integration_log.json` reports a nonzero redirect count (label
      normalisation should catch at least some overlapping terms)
- [ ] `iri_provenance.json` has entries with `sources` spanning
      multiple genres (proves cross-genre entities were detected)
- [ ] Iteration log has records for each sub-ontology AND an
      integration record per round
- [ ] Injection text is non-empty (B2a should have the IOF block)
- [ ] Defect routing produces both single-source and multi-source splits
      (check the routing log entry in `iteration_log.jsonl`)

---

## 7b. Smoke test 3: B2bD0, R=2 (quarter day)

This tests the CCO injection path — confirming the renderer parses
the TTL source, truncates correctly, and the model receives a
non-empty CCO injection block.

### 7b.1 Run it

```python
config.conditions = [Condition(GroundingLevel.B2b, DecompositionLevel.D0)]
config.campaign_dir = Path("smoke_test_3")
```

### 7b.2 Verify

- [ ] Injection text is non-empty and starts with the CCO header
- [ ] `injection.entries_total` ≈ 1,687 (full CCO inventory)
- [ ] `injection.truncated` is `True` (expected — allotment sized for B2a)
- [ ] `injection.entries_included` < `injection.entries_total` (confirms truncation)
- [ ] Truncation fraction logged — record for the methods section
- [ ] Generated ontology is parseable, non-empty, and has domain classes
- [ ] Alignment-rate query produces a non-empty result with at least
      some CCO-aligned classes (confirms the cco: cascade fires)

---

## 8. Determinism audit — Task 7 (1 day)

Three identical runs of one configuration under an identical seed.
Hashes compared.

### 8.1 Run

```python
for trial in range(3):
    config = CampaignConfig(
        campaign_dir=Path(f"determinism_trial_{trial}"),
        corpus_dir=Path("test_corpus"),  # same corpus
        seeds=[42],                      # same seed
        conditions=[Condition(GroundingLevel.B0, DecompositionLevel.D0)],
        # ... same allotments, same model, same everything
        r_max=2,
    )
    runner = CampaignRunner(config, backend, battery, count_tokens, embed)
    runner.run()
```

### 8.2 Compare

```python
from pathlib import Path
import json

def collect_hashes(campaign_dir: Path) -> list[str]:
    hashes = []
    run_dir = list((campaign_dir / "runs").iterdir())[0]
    for rd in sorted(run_dir.iterdir()):
        if rd.is_dir() and rd.name.startswith("R"):
            h = (rd / "response_hash.txt").read_text().strip()
            hashes.append(h)
    return hashes

h0 = collect_hashes(Path("determinism_trial_0"))
h1 = collect_hashes(Path("determinism_trial_1"))
h2 = collect_hashes(Path("determinism_trial_2"))

match = (h0 == h1 == h2)
print(f"Bitwise determinism: {'PASS' if match else 'FAIL'}")

if not match:
    for i, (a, b, c) in enumerate(zip(h0, h1, h2)):
        if not (a == b == c):
            print(f"  R{i:02d}: divergence — {a[:12]}... / {b[:12]}... / {c[:12]}...")
```

### 8.3 If hashes don't match

Per the spec (§4.5.4):
- Measure the divergence rate: at which round do responses first diverge?
- Check the prompt hashes — if prompts diverge, the non-determinism is
  upstream of the model (windowing, embedding, token counting).
- If prompts match but responses diverge: the model server is not
  deterministic.  Check CUDA deterministic flags, prefix caching,
  flash attention implementation.
- Document the divergence rate in the fallback section of the paper.

### 8.4 If hashes match

Task 7 is done.  Record the result in the seed register.

---

## 9. Summary — what's ready after this

| Layer | Validated by |
|---|---|
| Corpus + chunking | Smoke 1 (chunks produced, logged) |
| Injection rendering | Smoke 2 (B2a injection non-empty); Smoke 3 (B2b injection non-empty, truncation confirmed) |
| Windowing + patch-merge | Smoke 1 (windowing may or may not fire on tiny corpus — if not, run the windowing_spec test plan §7 separately) |
| LLM calling + OWL parsing | Smoke 1 (ontologies produced, parsed) |
| Integration + defect routing | Smoke 2 (sub-ontologies merged, defects routed) |
| Battery + feedback | Smoke 1+2 (scores produced, feedback rendered, scores change across rounds) |
| Checkpointing | Smoke 1+2 (all files written, loadable) |
| Determinism | Task 7 (hashes match or divergence documented) |

**After this you are ready for Task 5 (pilot):** 2 seeds, B0D0 + B2aD1 + B2bD1,
R=15, full battery, real corpus.

**Before the pilot, also wire:**
- The real reasoner (not the stub) — consistency and unsatisfiable
  classes are in the feedback loop
- The real term extractor (not the whitespace fallback) — windowing
  quality depends on it
- OOPS! with a timeout and retry (it's a web service)
- The real salient-term inventory from Task 2 (or a preliminary one)

**Not needed until after the pilot:**
- CQ scorer (Task 1 — needs the frozen CQ set)
- Community-structure pipeline (Task 6 — Paper 2)
- Population pipeline (Task 9 — Paper 2)
- Paper 3 mechanisms (Tasks 10–11)
