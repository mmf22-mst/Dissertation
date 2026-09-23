# Wiring & Smoke-Test Plan

Get the pipeline running on the 8×B200 platform, validate each layer,
end with the determinism audit (Task 7).

**v20 changes.** Four pinned allotments — the iteration payload now has
its own FEEDBACK allotment and per-item caps (`feedback_payload.py`),
pinned in §1.2 with the others.  The model regenerates the full view, so
§1.2's output reserve must be sized to the window allotment and §3.2 now
measures per-call latency at full output size (the term that sets the D0
run length).  The D1 sub-ontology battery runs at checkpoint rounds only
(`sub_battery.json`).  Entity-level patch deltas and feedback truncation
fields appear in the logs.  CQ scoring runs against a normalised scoring
copy (`label_normalisation.py`).  The pilot (task 5) runs four seeds.
New checks are collected in §7c.  A real-rdflib dry run of the v20 code
(fake LLM, stub instruments, tiny corpus, windowing forced) found and fixed
a latent crash in `windowing.py` — `SKOS` was used without being imported,
so the first windowed call would have raised `NameError`; the fixed file
ships with the v20 code.

**v19 changes.** Three grounding levels (B0, B1, B2 = IOF Core; no CCO) and
six genres.  Generator: gemma-4-26B-A4B-it, bf16, text-only, eight
single-GPU vLLM replicas with batch-invariant mode.  Execution is concurrent
(all runs at once; D1 genres in parallel), so the determinism checks now
cover batch size, replicas, concurrent load and prefix caching, not only
repeat runs.  The campaign reads the frozen construction sample (tasks
0c/0d), not the full collection.

**Estimated effort: 3–4 days** (days 5–6 of the Task 4 estimate,
plus 1 day for the determinism audit).

---

## 0. Environment setup (half day)

### 0.1 Python dependencies

```bash
pip install rdflib transformers numpy sentence-transformers requests
```

- `rdflib` — OWL parsing, graph manipulation, SPARQL
- `transformers` — the generator's own tokenizer, for token counting
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

### 0.3 Inference server — eight identical replicas

One vLLM server per B200, each with the same flags.  Check every flag
against the pinned vLLM version's documentation before recording it.

```bash
export VLLM_BATCH_INVARIANT=1
for gpu in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$gpu vllm serve google/gemma-4-26B-A4B-it \
    --revision <pinned-revision-hash> \
    --dtype bfloat16 \
    --tensor-parallel-size 1 \
    --max-model-len <CONTEXT_WINDOW> \
    --limit-mm-per-prompt '{"image":0,"video":0}' \
    --reasoning-parser gemma4 \
    --no-enable-prefix-caching \
    --seed 0 \
    --port $((8000 + gpu)) &
done
```

- **Text-only.** Disabling image and video inputs frees the vision
  encoder's memory for KV cache.
- **Reasoning parser.** With `gemma4`, any thinking output goes to
  `reasoning_content` instead of the answer.  The client also strips
  reasoning blocks, as a guard.
- **Prefix caching.** Off until the determinism audit (§8) shows identical
  hashes with it on and off; then it may be enabled on every replica.

Confirm each replica responds:

```bash
for port in $(seq 8000 8007); do
  curl -s http://localhost:$port/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"google/gemma-4-26B-A4B-it","messages":[{"role":"user","content":"Hello"}],
         "max_tokens":5,"temperature":0,"chat_template_kwargs":{"enable_thinking":false}}' | head -c 200; echo
done
```

Record in `manifest.json` (the campaign's `serving` field): model ID and
revision hash, dtype, vLLM version, `VLLM_BATCH_INVARIANT=1`, replicas × GPUs,
GPU type (B200), context window, prefix-caching setting, thinking mode.

### 0.4 Token counter

Use the generator's own tokenizer, so every allotment is in real tokens:

```python
# wiring/token_counter.py
from transformers import AutoTokenizer

_tok = AutoTokenizer.from_pretrained("google/gemma-4-26B-A4B-it", revision="<pinned>")

def count_tokens(text: str) -> int:
    return len(_tok.encode(text, add_special_tokens=False))
```

The pipeline passes `token_counter` everywhere as a callable; the census
and `saturation.py` use the same tokenizer.

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

Under concurrent execution many threads call `embed` at once.  If the
embedding model is not thread-safe on your setup, wrap the call in a
`threading.Lock`; it is fast next to generation, so the lock costs little.

### 0.6 Corpus samples (tasks 0c and 0d)

The smoke tests use a tiny fabricated corpus (§6.1).  The pilot and
campaign use the frozen construction sample A:

```python
from pipeline.corpus import census, draw_two_samples, write_sample, plan_summary
from wiring.token_counter import count_tokens

index = census(Path("/data/collection"), count_tokens)     # CPU, one pass
# T_A and floor come from saturation.py (task 0c)
plan = draw_two_samples(index, t_a=T_A, floor=FLOOR, seed_a=SEED_A, seed_b=SEED_B,
                        t_b=T_B_OR_FULL, linked_ncr_ids=LINKED, linked_ncr_min=MIN_LINKED)
write_sample(plan.sample_a, Path("/data/sample_A"), "A", {"plan": plan_summary(plan)})
write_sample(plan.sample_b, Path("/data/sample_B"), "B", {"plan": plan_summary(plan)})
# then: redact both, insert synthetic scenarios into B, leakage check,
# and re-run write_sample on the final directories to freeze the hashes.
```


---

## 1. Pin the allotments — the B2 fit test (half day)

The three prompt allotments must be set so B2's full injection (IOF Core
with its BFO layer, the largest inventory) fits alongside the window and
the chunk within the context window.  In v19 neither grounded condition is
truncated: `render_injection` raises if the allotment would truncate.

### 1.1 Measure the B1 and B2 injections

```python
from pipeline.injection import render_injection
from pipeline.ontology_model import GroundingLevel
from wiring.token_counter import count_tokens
from pathlib import Path

# B2 — the binding constraint for allotment sizing
result_b2 = render_injection(
    grounding=GroundingLevel.B2,
    iof_core_path=Path("iof-core.rdf"),     # Core.rdf with imports resolved
    injection_allotment=10**9,              # measure full size
    token_counter=count_tokens,
)
print(f"B2 full injection: {result_b2.token_count} tokens, "
      f"{result_b2.entries_total} entries")   # expect 174 entries

result_b1 = render_injection(
    grounding=GroundingLevel.B1,
    bfo_core_path=Path("bfo-core.owl"),
    injection_allotment=10**9,
    token_counter=count_tokens,
)
print(f"B1 full injection: {result_b1.token_count} tokens, "
      f"{result_b1.entries_total} entries")   # expect 76 entries
```

B0 is 0 tokens.

### 1.2 Compute the allotments

```
CONTEXT_WINDOW         = <pinned max-model-len>
SYSTEM_OVERHEAD        = ~800 tokens  (chat template, markers, closing)
OUTPUT_RESERVE         = ~8000 tokens (model's generation budget)

AVAILABLE = CONTEXT_WINDOW - SYSTEM_OVERHEAD - OUTPUT_RESERVE

INJECTION_ALLOTMENT    = result_b2.token_count, rounded up with a small margin
REMAINING              = AVAILABLE - INJECTION_ALLOTMENT
WINDOW_ALLOTMENT       = REMAINING * 0.6     (most goes to the ontology)
CHUNK_ALLOTMENT        = REMAINING * 0.4     (rest to the corpus chunk)
FEEDBACK_ALLOTMENT     = CHUNK_ALLOTMENT     (v20: the iteration payload occupies the
                                              fourth slot; equal to the chunk allotment
                                              unless the pilot shows systematic truncation)
FEEDBACK_CAPS          = FeedbackCaps(...)   (v20: per-item list caps, chosen so the
                                              worst-case payload fits FEEDBACK_ALLOTMENT)
```

**v20 — output reserve.** The model outputs the complete revised view, so
`OUTPUT_RESERVE` must be at least `WINDOW_ALLOTMENT` plus growth headroom,
not a fixed 8,000.  Budget it first, then split what remains.

Adjust the 60/40 split to taste.  The key constraints:
- `INJECTION_ALLOTMENT + max(WINDOW_ALLOTMENT + CHUNK_ALLOTMENT, WINDOW_ALLOTMENT + FEEDBACK_ALLOTMENT) + SYSTEM_OVERHEAD + OUTPUT_RESERVE ≤ CONTEXT_WINDOW`
- All four are **fixed across B** — B0 and B1 get the same window, chunk and feedback budgets as B2.
- Caps are pinned so that `feedback_overflow_steps` is 0 on every call in the pilot (§7c).
- Rendering B1 and B2 at the pinned `INJECTION_ALLOTMENT` must not raise (no truncation).
- Longer prompts raise per-call latency, and construction is latency-bound; record the chosen allotments with the throughput measurements from task 0c.

### 1.3 Verify

```python
# Build one construction prompt with the three construction allotments at max
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
is frozen (Task 1).  The scorer itself is done (`cq_scorer.py`, v20):

```python
from pipeline.cq_scorer import CQSet, CQScorer

cq_set = CQSet.from_markdown("assets/cq_set_frozen.md")
assert not cq_set.validate()            # parse errors, non-normalised terms, duplicate ids
cq_fn = CQScorer(cq_set, injection_iris=injection_iris_for_condition)
```

`injection_iris` is the condition's injection entity set (what
`campaign.py` computes as `_injection_iris[condition.B]`); the BFO/IOF/CCO
namespace floor applies even without it.  Before freezing, run
`python -m pipeline.cq_scorer --cq-file assets/cq_set_frozen.md --validate`
and require zero problems.  Check on a Smoke 2 R02 ontology that
`cq_injection_only_cqs` is non-zero under B2 for at least one CQ whose
label patterns name IOF classes — that is the rule working — and zero
under B0.

### 2.7 Assemble the Battery

```python
from pipeline.battery import Battery

from pipeline.feedback_payload import FeedbackCaps

battery = Battery(
    reasoner_fn=run_reasoner,
    oops_fn=run_oops,
    structural_fn=run_structural,
    alignment_fn=run_alignment,
    coverage_fn=run_coverage,
    cq_fn=None,  # held out; wire after Task 1 freezes the CQ set
    # v20: pinned feedback allotment and caps (also set by CampaignRunner
    # from CampaignConfig; pass here for standalone battery use)
    feedback_caps=FeedbackCaps(
        unsatisfiable_classes=20, profile_violations=10, pitfalls=15,
        pitfall_affected_elements=5, missing_terms_per_genre=15,
        routed_defects=20,
    ),
    feedback_allotment=FEEDBACK_ALLOTMENT,
    token_counter=count_tokens,
    # v20: sub-ontology coverage against that genre's inventory
    coverage_by_genre_fn=run_coverage_for_genre,
)
```

`run_coverage_for_genre(ontology, genre_key)` scores against the per-genre
inventory from Task 2.  It is only called at checkpoint rounds under D1.

**CQ scorer (v20).** When Task 1 lands, `cq_fn` must run every CQ against
`label_normalisation.scoring_copy(ontology)` with the query passed through
`label_normalisation.rewrite_cq_query`, and must report
`normalisation_only_hit_share` in the CQ record.  Never score against raw
`rdfs:label`.

---

## 3. Wire the LLM backend (half day)

### 3.1 Backend

```python
from pipeline.llm import ChatBackend

backend = ChatBackend(
    base_url=[f"http://localhost:{p}/v1" for p in range(8000, 8008)],  # 8 replicas
    model="google/gemma-4-26B-A4B-it",
    max_tokens=8192,           # OUTPUT_RESERVE from §1.2
    enable_thinking=False,     # pinned per campaign; must equal CampaignConfig.thinking_mode
)
```

Use `ChatBackend` for Gemma 4: the raw completions endpoint does not
apply the chat template.

### 3.2 Sanity check

```python
from pipeline.llm import LLMCaller

caller = LLMCaller(backend)          # optional: max_in_flight=<server max-num-seqs × 8>
result = caller.call("Respond with: Hello world")
print(result.raw_response)
print(f"Prompt tokens: {result.prompt_tokens}")
print(f"Response hash: {result.response_hash}")
```

### 3.3 Determinism pre-check

Take one real construction prompt and hash its response:

1. alone, three times;
2. alone on each of the eight replicas;
3. while 50 other, different prompts are in flight (concurrent threads).

All hashes must match.  If not, check:
- `VLLM_BATCH_INVARIANT=1` is set in every server's environment
- `temperature=0` is respected and the `seed` parameter is supported
- every replica has identical flags, vLLM version and model revision
- prefix caching is disabled
- the GPU is on the batch-invariance supported list for the pinned version

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
      iteration_log.jsonl    ← one record per round, plus feedback_render records?
      run_summary.json       ← wall time, class count?
```

Checklist:
- [ ] `ontology.owl` at each round is parseable RDF/XML
- [ ] (v20) every iteration record has `feedback_tokens`, `feedback_omitted`, `feedback_overflow_steps` (== 0)
- [ ] (v20) every construction and iteration record has `patch_added_entities` / `patch_removed_entities`
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

## 7. Smoke test 2: B2D1, R=2 (half day)

This tests the full D1 path: per-genre construction (in parallel),
integration, defect routing, per-sub-ontology iteration (in parallel).

### 7.1 Run it

Same test corpus.  Change the condition:

```python
config.conditions = [Condition(GroundingLevel.B2, DecompositionLevel.D1)]
config.campaign_dir = Path("smoke_test_2")
```

### 7.2 Verify — same checklist as §6.3, plus:

```
runs/seed_00_B2D1/
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
- [ ] Construction log has records for every genre, interleaved (genres
      ran in parallel); every JSONL line parses
- [ ] Injection text is non-empty (B2 should have the IOF block) and
      `injection.truncated` is `False`
- [ ] Defect routing produces both single-source and multi-source splits
      (check the routing log entry in `iteration_log.jsonl`)

---

## 7b. Smoke test 3: concurrency equivalence (quarter day)

This tests that concurrent execution produces the same artefacts as
sequential execution — the property the whole v19 execution model rests on.

### 7b.1 Run it twice

```python
jobs = dict(seeds=[0, 1], conditions=ALL_CONDITIONS, r_max=2)   # 12 runs

# (a) fully sequential
cfg_seq = CampaignConfig(campaign_dir=Path("smoke_seq"), max_concurrent_runs=1,
                         max_genre_workers=1, **common, **jobs)
# (b) fully concurrent
cfg_par = CampaignConfig(campaign_dir=Path("smoke_par"), max_concurrent_runs=None,
                         max_genre_workers=None, **common, **jobs)
```

### 7b.2 Verify

- [ ] Every `R*/ontology.owl` is byte-identical between `smoke_seq` and `smoke_par`
- [ ] Every run's set of response hashes is identical (sort the log
      records by genre, chunk_index, round and target before comparing)
- [ ] The campaign manifest lists runs in the same order in both
- [ ] `failed_runs` is empty in both

If artefacts differ, the cause is either the server (batch invariance not
holding — go back to §3.3) or shared mutable state in the pipeline
(embedding model, battery instruments) — check thread-safety.

---

## 7c. v20 checks (quarter day)

Run these on the Smoke 1 and Smoke 2 outputs before the determinism audit.

### 7c.1 Feedback allotment

```python
import json
recs = [json.loads(l) for l in open("smoke_test_2/runs/seed_00_B2D1/iteration_log.jsonl")]
fb = [r for r in recs if "feedback_tokens" in r]
assert fb, "no feedback records"
assert all(r["feedback_overflow_steps"] == 0 for r in fb), "caps not pinned to fit — raise caps or allotment"
assert all(r["feedback_tokens"] <= FEEDBACK_ALLOTMENT for r in fb)
print("truncated items seen:", sorted({i for r in fb for i in r["feedback_truncated_items"]}))
```

- [ ] `feedback_overflow_steps` is 0 on every call, both conditions
- [ ] Under D1 every `iterate_sub:*` record has its own feedback fields (per-sub-ontology render, not the global payload)
- [ ] `feedback_payload.txt` at R00 begins with `### 1. Reasoner Report` (global); a D1 sub-ontology call's payload begins with `### Issues specific to this sub-ontology`
- [ ] Rendering the same reports twice gives byte-identical text (determinism of ordering)

### 7c.2 Entity deltas (unintended deletions)

```python
rem = [r.get("patch_removed_entities", 0) for r in recs if r.get("phase") == "iterate"]
print("removed entities per iteration call:", rem)
```

- [ ] Fields present on every call, windowed or not
- [ ] Removal counts are plausible (a handful, not the whole view); a large count on a non-windowed call means the model dropped content when regenerating — the pilot reports this rate

### 7c.3 Checkpoint rounds and sub-ontology battery

```python
from pipeline.checkpoint import checkpoint_rounds_for
assert checkpoint_rounds_for(9) == (0, 3, 6, 9)
assert checkpoint_rounds_for(15) == (0, 5, 10, 15)
```

- [ ] `manifest.json` records `checkpoint_rounds`, `feedback_allotment`, `feedback_caps`, `few_shot_exemplars: 0`, `label_normalisation_rule`, `coverage_match_level`
- [ ] Smoke 2 (R = 2): `sub_battery.json` exists only in the checkpoint rounds for r_max = 2 — `checkpoint_rounds_for(2)` = (0, 1, 2), so all three — and has one entry per genre with `salient_term_coverage_genre`
- [ ] Re-run Smoke 2 with `r_max = 6` on the tiny corpus if time allows: `sub_battery.json` in R00, R02, R04, R06 only

### 7c.4 Label normalisation

```python
from pipeline.label_normalisation import normalise_scoring_label, rewrite_cq_query
assert normalise_scoring_label("NonConformanceReports") == "non conformance report"
assert normalise_scoring_label("Non-Conformance Report") == "non conformance report"
assert "scoring:normLabel" in rewrite_cq_query('?x rdfs:label ?l')
```

- [ ] Run `cq_calibrate.py` on the CQ draft: `non_normalised_term_cqs` should be 0 before the set is frozen
- [ ] On a Smoke 2 R02 ontology, `normalisation_only_hit_share` runs and returns a share in [0, 1]

### 7c.5 Output length (feeds task 0c)

- [ ] From `construction_log.jsonl`, plot `completion_tokens` against `ontology_tokens` (or chunk index): it should track the view size, not stay flat near 1,500
- [ ] Record per-call `wall_seconds` at the largest view seen; this is the latency figure the throughput benchmark must reproduce at the pinned window allotment before *T*<sub>A</sub> is set

---

## 8. Determinism audit — Task 7 (1 day)

Hashes compared under five conditions (overview Paper 1 §4.5.4), covering
construction, feedback and extraction prompts:

| # | Condition | How |
|---|---|---|
| 1 | Repeat runs | Three identical runs of one configuration under an identical seed |
| 2 | Batch size | The same prompt set sent one at a time versus at campaign concurrency |
| 3 | Replicas | The same prompt set sent to each replica |
| 4 | Concurrent load | Smoke test 3 (§7b) at realistic load, on real sample-A text |
| 5 | Prefix caching | Conditions 1–2 repeated with prefix caching on; enable it only if hashes match |

### 8.1 Run condition 1

```python
for trial in range(3):
    config = CampaignConfig(
        campaign_dir=Path(f"determinism_trial_{trial}"),
        corpus_dir=Path("/data/sample_A"),   # frozen construction sample
        seeds=[42],
        conditions=[Condition(GroundingLevel.B2, DecompositionLevel.D1)],
        # ... same allotments, same model, same serving flags
        r_max=2,
    )
    CampaignRunner(config, backend, battery, count_tokens, embed).run()
```

### 8.2 Compare

```python
from pathlib import Path

def collect_hashes(campaign_dir: Path) -> list[str]:
    hashes = []
    run_dir = sorted((campaign_dir / "runs").iterdir())[0]
    for rd in sorted(run_dir.iterdir()):
        if rd.is_dir() and rd.name.startswith("R"):
            hashes.append((rd / "ontology.owl").read_bytes())
    return hashes

h = [collect_hashes(Path(f"determinism_trial_{t}")) for t in range(3)]
print(f"Bitwise determinism: {'PASS' if h[0] == h[1] == h[2] else 'FAIL'}")
```

For conditions 2, 3 and 5, send a fixed list of real prompts through
`LLMCaller` under each setting and compare the `response_hash` lists.

### 8.3 If hashes don't match

The fallback is pre-registered (overview Paper 1 §4.5.4):
- If conditions 1–4 fail, Paper 1 construction reverts to batch size 1
  (`max_concurrent_runs=1`, `max_genre_workers=1`, and one request in
  flight per replica).  Population and RCA stay batched; divergence is
  measured on a replicate subset and reported.
- If only condition 5 fails, prefix caching stays disabled.
- Diagnose first: if prompt hashes diverge, the cause is upstream of the
  model (windowing, embedding, token counting); if prompts match but
  responses diverge, the server is not batch-invariant.

### 8.4 If hashes match

Task 7 is done.  Record the result, the vLLM version and the serving flags
in the seed register.

---

## 9. Summary — what's ready after this

| Layer | Validated by |
|---|---|
| Corpus + chunking | Smoke 1 (chunks produced, logged) |
| Injection rendering | §1 (B1 and B2 render untruncated at the pinned allotment); Smoke 2 (B2 injection non-empty) |
| Concurrency | Smoke 3 (concurrent artefacts identical to sequential) |
| Windowing + patch-merge | Smoke 1 (windowing may or may not fire on tiny corpus — if not, run the windowing_spec test plan §7 separately) |
| LLM calling + OWL parsing | Smoke 1 (ontologies produced, parsed) |
| Integration + defect routing | Smoke 2 (sub-ontologies merged, defects routed) |
| Battery + feedback | Smoke 1+2 (scores produced, feedback rendered, scores change across rounds); §7c.1 (allotment, caps, per-sub-ontology render) |
| Checkpointing | Smoke 1+2 (all files written, loadable); §7c.3 (checkpoint rule, `sub_battery.json`) |
| Patch deltas / label normalisation / output length | §7c.2, §7c.4, §7c.5 |
| Determinism | Task 7 (five conditions pass, or the fallback is applied) |

**After this you are ready for Task 5 (pilot):** 4 seeds, B0D0 + B2D1,
R=15, full battery every round, frozen construction sample A, plus the
thinking-mode comparison (B2D1, one seed, R0 plus two rounds, on versus
off).  The pilot additionally reports feedback truncation frequency per
item per condition, the per-call entity-removal rate, and per-call latency
at full output size (v20).

**Before the pilot, also wire:**
- The real reasoner (not the stub) — consistency and unsatisfiable
  classes are in the feedback loop
- The real term extractor (not the whitespace fallback) — windowing
  quality depends on it
- OOPS! with a timeout and retry (it's a web service).  With all runs
  concurrent, many OOPS! requests can arrive at once; cap concurrent OOPS!
  calls (a semaphore in the wrapper) to stay within the service's limits
- The real salient-term inventory from Task 2, extracted from sample A

**Not needed until after the pilot:**
- CQ set (Task 1 authoring half — the scorer is done, §2.6)
- Community-structure pipeline (Task 6 — Paper 2)
- Population pipeline wiring (Task 9 — Paper 2; scaffolding done, see below)

**Task 9 wiring, when it comes (after the pilot):**

1. `python test_population.py` inside the package's parent directory must
   pass (fake LLM/NLI/reasoner; exercises extraction, conformance, sampling,
   verification, calibration, the RL checker, the timeout fallback, the
   on-disk layout).
2. Plug in the real pieces: an `LLMBackend` for extraction (the same vLLM
   client, text response, no OWL parsing), an `NLIModel` with
   `entailment_scores(pairs)` around the pinned NLI checkpoint, and a
   `DLReasonerHook.check(kg, ontology, timeout_s)` around the reasoner
   subprocess.
3. Calibrate on two or three pilot KGs (B0D0 and B2D1 at R0 and the
   terminal round): `make_injection_set` → `threshold_sweep` → pin
   `NLI_THRESHOLD`; `calibrate` for sensitivity/specificity per style,
   which goes into Paper 2 Table 1.  Style crossing must not show a
   B1/B2 gap larger than the precision half-width, or the verbalisation
   template needs revisiting before the campaign.
4. Time the DL reasoner on the largest pilot KG to set
   `VALIDATION_TIMEOUT_S`; if it cannot complete there, decide now to run
   the campaign on the RL instrument rather than discover it mid-campaign.
- Paper 3 mechanisms (Tasks 10–11)
