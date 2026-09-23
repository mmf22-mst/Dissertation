# Generation Pipeline — Architecture Sketch

Task 4 build plan.  Companion to `dissertation_overview_and_paper_outlines_v20.md` (Paper 1 §4.2–4.5),
`windowing_spec_v16.md`, and `deterministic_integration_spec_v17.md`.

**v20 changes (aligned to overview v19.1/v20).**
- **Four pinned allotments.** Injection, window, chunk (construction) and **feedback** (iteration). The feedback payload is rendered by the new `feedback_payload.py` — fixed item order, always-present summary lines, per-item truncation caps in a deterministic order, omitted-entry counts, and a halving guard that must never fire once caps are pinned. Tokens, omitted counts and overflow steps are logged per call. Under D1 the payload is re-rendered per sub-ontology with the routed defects at position 0, under the same caps and allotment.
- **Output form stated.** The model always outputs the complete revised view; the pipeline differences it (`patch_merge.py`). Entity-level added/removed counts are logged for every call so the pilot can report the unintended-deletion rate. Output length grows to the window allotment — the throughput benchmark measures per-call latency at that size before *T*<sub>A</sub> is set.
- **Checkpoint rule.** `checkpoint_rounds_for(r_max)` = R0 plus three evenly spaced rounds to the terminal round; the D1 sub-ontology battery (`Battery.run_sub`, integration loss) runs only at those rounds and writes `sub_battery.json`.
- **CQ label normalisation.** `label_normalisation.py` pins the rule (CamelCase/underscore split, lower-case, punctuation stripped, whitespace collapsed, head noun singularised), builds a scoring copy carrying `scoring:normLabel`, rewrites CQ queries to match it, and reports the normalisation-only hit share. `cq_calibrate.py` flags pattern terms not in normalised form before the CQ set is frozen.
- **No few-shot exemplars** in either prompt; the manifest records `few_shot_exemplars: 0`. Coverage matches entity labels only (`coverage_match_level: entity_label_only`).

**v19 changes.**
- Factor B has three levels (B0, B1, B2 = IOF Core); CCO is no longer a condition. Six cells per seed.
- Six genres (DPBPS, Command Media, FMEA, NCR, Jira, Active Risk Management).
- The pipeline reads the frozen **construction sample A**, not the full collection. The census, square-root sampler and freeze live in `corpus.py`; sample sizing lives in `saturation.py`.
- Execution is **concurrent**: all runs at once under a campaign scheduler, and D1 genre sub-ontologies in parallel within a run. Determinism rests on vLLM batch-invariant mode, one GPU per replica, not on batch size 1. The expanded determinism audit (todo task 7) verifies it.
- Generator: gemma-4-26B-A4B-it, bf16, text-only, on 8×B200. Thinking mode is sent explicitly on every request and pinned per campaign.

---

## 1. What the pipeline does in one sentence

For every (seed, condition) pair — all pairs executing concurrently — sequentially
accumulate an ontology from the construction sample's chunks, then run 9 rounds of
feedback-driven iteration, checkpointing and evaluating at every round state (R0–R9).

---

## 2. Top-level loop

```
# All (seed, condition) runs are submitted to one thread pool (campaign.py);
# each run below is independent and executes concurrently with the others.
for seed in seeds:                          # k = 10
    genre_order = resolve_genre_order(seed)  # S-GEN governs this
    for condition in [B0D0, B0D1, B1D0, B1D1, B2D0, B2D1]:
        run = init_run(seed, condition)

        # ── Phase 1: Construction (produces R0) ──────────────
        if condition.D == D0:
            ontology = construct_monolithic(run, genre_order)
        else:  # D1
            # genres built in parallel; each genre's chunks stay sequential;
            # results reassembled in genre_order before integration
            sub_ontologies = parallel_map(construct_genre, genre_order)
            integrated = deterministic_integrate(sub_ontologies)
            ontology = integrated

        checkpoint(run, round=0, ontology, sub_ontologies_if_D1)
        evaluate_battery(run, round=0, ontology)          # ← R0 scores

        # ── Phase 2: Iteration (produces R1–R9) ─────────────
        for r in range(1, R_MAX + 1):                     # R_MAX from pilot
            feedback = build_feedback(ontology)            # 6-item payload

            if condition.D == D0:
                ontology = iterate_monolithic(run, r, ontology, feedback)
            else:  # D1
                routed = route_defects(feedback, iri_provenance_map)
                sub_ontologies = parallel_map(      # one call per genre, in parallel
                    lambda g: iterate_genre(run, r, g, sub_ontologies[g], routed[g]),
                    genre_order,
                )
                integrated = deterministic_integrate(sub_ontologies)
                ontology = integrated

            checkpoint(run, round=r, ontology, sub_ontologies_if_D1)
            evaluate_battery(run, round=r, ontology)
```

**60 runs × 10 round-states = 600 checkpoints.**
Under D1 each checkpoint also stores the G sub-ontologies and the integration log.

---

## 3. Component inventory

Each box below is a module.  Existing specs / implementations are noted;
"**to build**" marks what Task 4 must produce.

### 3.1  Corpus & chunking

| Component | Status | Description |
|---|---|---|
| `corpus_loader` | **to build** | Loads documents with genre labels into `CorpusDocument` objects; same objects the salient-term pipeline uses. Points at the frozen construction sample A. |
| `corpus_sampler` | **built (v19)** | `corpus.py`: token census over the full collection (no text held), square-root allocation with floor, disjoint samples A and B, CAR-linked NCR reservation for B, `write_sample` with per-file SHA-256 manifest. |
| `saturation` | **built (v19)** | `saturation.py`: per-genre saturation and split-half stability curves; recommends T_A and the floor; writes the larger reference inventory. |
| `chunker_d0` | **to build** | Concatenates corpus in genre-blocked order, chunks by token budget (genre-blind, boundaries may straddle). Records straddling-chunk count. |
| `chunker_d1` | **to build** | Chunks within each genre separately. Same token budget as D0. |
| `genre_order_resolver` | **to build** | From S-GEN seed, produces the genre processing order (varied across seeds, identical between D0 and D1 within a seed). |

### 3.2  Prompt assembly

| Component | Status | Description |
|---|---|---|
| `injection_renderer` | **to build** | Deterministic extraction of class/relation labels + definitions from `bfo-core.owl` (B1) or resolved `Core.rdf` (B2); alphabetical sort, IRI tie-break. The allotment is sized to hold B2's full inventory; the renderer raises if either grounded condition would be truncated (v19). B0 produces an empty injection block. |
| `prompt_builder_construct` | **done** (`prompt.py`) | Assembles the construction prompt: injection + window/full ontology + chunk. Calls windowing if needed. Uniform template across B; only injection content differs. No few-shot exemplars. |
| `prompt_builder_iterate` | **done** (`prompt.py`) | Assembles the iteration prompt: injection + window/full ontology + 6-item feedback payload in the FEEDBACK allotment. No round counter, no history. Raises `FeedbackAllotmentExceeded` if the rendered payload is over the pinned allotment (a configuration error — rendering under the allotment is `feedback_payload.py`'s job). |
| `feedback_payload` | **done (v20)** (`feedback_payload.py`) | Renders the payload under the pinned allotment: fixed item order (routed defects → reasoner → profile → OOPS! → conformance → coverage → balance), summary lines always present, per-item caps (`FeedbackCaps`, pinned in task 0c), deterministic truncation orders, "... and N more (omitted)" tails, halving guard, and a truncation log record for the round log. |

### 3.3  Windowing & patch-merge

| Component | Status | Spec |
|---|---|---|
| `window_selector` | **to build** | `windowing_spec_v16.md` §3. Four-phase selection: term extraction → label matching → ancestor closure + siblings/children (FAN_OUT_CAP) → budget fill by score. Fires when serialised ontology > WINDOW_ALLOTMENT. |
| `patch_merger` | **done** (`patch_merge.py`) | `windowing_spec_v16.md` §4. Diff the model's complete revised view against the window; validate (no invisible-entity references); apply patch to full ontology. Orphaned-reference handling for deletions. Entity-level deltas logged for every call (v20). |
| `ontology_serialiser` | **to build** | Renders an ontology (or window subset) into the text format the prompt expects. Must be deterministic — same ontology → same string. Used for both prompt assembly and token counting. |

### 3.4  LLM caller

| Component | Status | Description |
|---|---|---|
| `llm_caller` | **to build** | Single entry point for all generation calls. Thread-safe; greedy decoding; round-robin over identical single-GPU vLLM replicas running batch-invariant mode; explicit `chat_template_kwargs.enable_thinking`; strips any reasoning block before parsing; bounded retries on connection errors and 5xx. Logs: prompt hash, response hash, token counts (prompt / completion), wall time, condition metadata. Parses OWL from the model's response. |
| `owl_parser` | **to build** | Extracts well-formed OWL from the model's text response. Handles common failure modes (truncation, syntax errors). Logs parse success/failure and error details. |

### 3.5  Integration (D1 only)

| Component | Status | Spec |
|---|---|---|
| `deterministic_integrator` | **to build** | `deterministic_integration_spec_v17.md` §2. Two stages: (1) label normalisation + IRI reconciliation + union; (2) LogMap alignment + deterministic reconciliation. AML as audit. Produces `IntegrationResult` with provenance map. |
| `defect_router` | **to build** | `deterministic_integration_spec_v17.md` §4. Routes feedback items to sub-ontologies via the IRI provenance map. Single-source → one channel; multi-source → all involved channels. |

### 3.6  Evaluation battery

| Component | Status | Description |
|---|---|---|
| `reasoner_check` | **to build** | OWL 2 DL profile check, global consistency, unsatisfiable class list. Wraps a reasoner (HermiT or ELK). |
| `structural_profile` | **done (v16)** | `structural_profile.py` — seven OntoQA metrics via rdflib. |
| `oops_client` | **done (v16)** | `structural_profile.py` — OOPS! REST client with XML parsing. |
| `alignment_rate` | **done (v14)** | `alignment_rate.sparql` — single priority-cascade SPARQL query. |
| `salient_term_coverage` | **done (v16)** | `salient_term_pipeline.py` — coverage scoring and genre balance. |
| `label_normalisation` | **done (v20)** (`label_normalisation.py`) | Pinned CQ label-normalisation rule; `scoring_copy()` adds `scoring:normLabel` to a copy of the graph; `rewrite_cq_query()` points a CQ at it; `normalisation_only_hit_share()` is the per-condition diagnostic. |
| `cq_scorer` | **done (v20)** (`cq_scorer.py`) | Parses the frozen CQ set (same block regex as `cq_calibrate.py`; SHA-256 recorded), validates it before freeze (parse errors, non-normalised pattern terms, duplicate ids), and scores an ontology state on the scoring copy with every CQ rewritten by `rewrite_cq_query`. A CQ is answered when at least one result row projects a constructed entity; rows whose projected entities are all injected (BFO/IOF/CCO namespaces or the condition's injection IRIs) are discarded, so the injection alone can never answer a CQ. Reports overall, per stratum, per genre, the primary aggregate (relational + multi-hop), the normalisation-only share, injection-only CQs, and errors. Plug in as `Battery(cq_fn=CQScorer(cq_set, injection_iris))`; CLI for `--validate`, `--ontology`, `--run-dir`. The CQ set itself (task 1, authoring half) is still to freeze. |
| `feedback_renderer` | **done (v20)** | Superseded by `feedback_payload.py` (above); `battery.render_feedback` is a thin wrapper. `Battery.render_feedback(reports, routed_defects, genre_key)` is the D1 per-sub-ontology entry point. |
| `sub_battery` | **done (v20)** (`Battery.run_sub`) | Grounding-agnostic instruments on one sub-ontology, coverage against that genre's inventory; called at checkpoint rounds only. |

### 3.7  Checkpointing & logging

| Component | Status | Description |
|---|---|---|
| `checkpoint_store` | **to build** | Saves the evaluable ontology state at each round. See §4 below. |
| `run_log` | **to build** | Flat append-only log per run. See §5 below. |
| `campaign_manifest` | **to build** | Top-level manifest recording parameters, seeds, hashes. |

---

## 4. Checkpoint structure

Every round-state is a self-contained snapshot that Papers 2 and 3 can consume
without re-running Paper 1.

```
campaign/
  manifest.json                          # parameters, seeds, environment
  runs/
    seed_03_B2D1/
      config.json                        # condition, seed, allotments, model
      R00/
        ontology.owl                     # the evaluable artefact (integrated for D1)
        battery.json                     # all instrument scores for this round
        feedback_payload.txt             # what the model will see next round
        prompt_hash.txt                  # SHA-256 of the construction/iteration prompt
        response_hash.txt                # SHA-256 of the raw model response
        sub_ontologies/                  # D1 only
          genre_0_ncr.owl
          genre_1_fmea.owl
          ...
        integration_log.json             # D1 only: alignments, redirects, delta, AML audit
        iri_provenance.json              # D1 only
        sub_battery.json                 # D1 only, checkpoint rounds only (v20): per-genre sub-ontology scores
      R01/
        ...                              # same structure
      ...
      R09/
        ...
      construction_log.jsonl             # per-chunk log from Phase 1 (§5.1)
      iteration_log.jsonl                # per-round log from Phase 2 (§5.2)
      run_summary.json                   # aggregated statistics
```

**Checkpoint rounds.** `checkpoint_rounds_for(R_MAX)` (`checkpoint.py`) = R0 plus three rounds evenly spaced to the terminal round: (0, 3, 6, 9) at R = 9, (0, 5, 10, 15) in the R = 15 pilot. Papers 2 and 3 consume only these; the sub-ontology battery runs only at these.

**Size estimate.** Each `.owl` file is likely 100 KB–1 MB depending on how large
the ontology grows.  600 checkpoints × ~1 MB ≈ 600 MB for the main artefacts;
D1 sub-ontologies multiply that by G for 30 runs.  Total campaign storage on
the order of a few GB — fits comfortably on local disk.

---

## 5. Logging

### 5.1  Construction log (per-chunk, Phase 1)

One JSONL record per chunk processed during initial construction:

```json
{
  "seed": 3, "condition": "B2D1", "phase": "construct",
  "genre": "ncr",  "chunk_index": 42,
  "chunk_tokens": 2048, "straddles_genre": false,
  "windowed": true,
  "window_classes_shown": 87, "window_classes_total": 214,
  "visibility_ratio": 0.407,
  "matched_terms": 12, "ancestor_classes": 34, "fan_out_classes": 41,
  "budget_fill_classes": 12,
  "patch_added_axioms": 23, "patch_removed_axioms": 5,
  "patch_violations": 0, "orphaned_references": 0,
  "prompt_tokens": 14280, "completion_tokens": 3100,
  "prompt_hash": "a1b2c3...", "response_hash": "d4e5f6...",
  "wall_seconds": 18.4, "parse_success": true
}
```

### 5.2  Iteration log (per-round, Phase 2)

One JSONL record per round per D-level unit (one record for D0, G records for D1):

```json
{
  "seed": 3, "condition": "B2D1", "phase": "iterate", "round": 4,
  "target": "sub:genre_2_fmea",
  "windowed": false,
  "feedback_payload_tokens": 1820,
  "feedback_flagged_items": {"reasoner": 0, "oops": 3, "conformance": 1,
                              "coverage_missing_terms": 7, "coverage_entropy": 0.82},
  "defects_routed_here": 4, "defects_multi_source": 1,
  "prompt_tokens": 11500, "completion_tokens": 2800,
  "prompt_hash": "...", "response_hash": "...",
  "wall_seconds": 15.1, "parse_success": true
}
```

Plus one integration-level record per D1 round:

```json
{
  "seed": 3, "condition": "B2D1", "phase": "integrate", "round": 4,
  "alignments_found": 12, "iris_redirected": 8, "clusters": 5,
  "logmap_aml_agreement": 0.92,
  "delta_axioms_added": 14, "delta_axioms_removed": 3,
  "iri_stability_rate": 0.97,
  "wall_seconds": 4.2
}
```

### 5.3  Battery log (per round-state)

`battery.json` in each checkpoint — flat record of every instrument score:

```json
{
  "seed": 3, "condition": "B2D1", "round": 4,
  "cq_answerability": 0.64,
  "salient_term_coverage": 0.71,
  "genre_coverage_balance": 0.88,
  "consistency": true, "unsatisfiable_classes": 0,
  "owl2dl_conformant": true,
  "oops_pitfall_counts": {"critical": 0, "important": 2, "minor": 5},
  "ontoqa": {"RR": 0.42, "AR": 0.31, "IR": 0.08, "CR": 0.67, ...},
  "bfo_alignment_rate": 0.34, "iof_alignment_rate": 0.52, "unaligned_rate": 0.14,
  "class_count": 214, "property_count": 87
}
```

---

## 6. Data flow diagram (text form)

```
                        ┌─────────────┐
                        │  S-GEN seed │
                        └──────┬──────┘
                               │
                   ┌───────────▼───────────┐
                   │  genre_order_resolver  │
                   └───────────┬───────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │              corpus_loader                  │
         │  (documents with genre labels)              │
         └──────────┬───────────────────┬──────────────┘
                    │                   │
              ┌─────▼─────┐       ┌─────▼─────┐
              │ chunker_d0│       │ chunker_d1│
              │(monolithic)│      │(per-genre) │
              └─────┬─────┘       └─────┬─────┘
                    │                   │
                    ▼                   ▼
   ┌─────────── PHASE 1: CONSTRUCTION ────────────────┐
   │                                                   │
   │  for each chunk:                                  │
   │    injection_renderer(B)                          │
   │      ↓                                            │
   │    window_selector(ontology, chunk)  ← if needed  │
   │      ↓                                            │
   │    prompt_builder_construct                        │
   │      ↓                                            │
   │    llm_caller  →  owl_parser                      │
   │      ↓                                            │
   │    patch_merger(full_ontology, window, output)     │
   │      ↓                                            │
   │    updated ontology                               │
   │                                                   │
   │  D1 only, after all genres:                       │
   │    deterministic_integrator(sub_ontologies)        │
   │      ↓                                            │
   │    integrated ontology = R0 state                  │
   │                                                   │
   └─────────────────────┬─────────────────────────────┘
                         │
                   checkpoint(R0)
                   evaluate_battery(R0)
                         │
   ┌─────────── PHASE 2: ITERATION ───────────────────┐
   │                                                   │
   │  for round 1..R_MAX:                              │
   │                                                   │
   │    ┌────────────────────────────┐                 │
   │    │   evaluate_battery*        │ ← battery was   │
   │    │   (already done at end     │   run after the │
   │    │    of prior round)         │   prior round   │
   │    └────────────┬───────────────┘                 │
   │                 │                                  │
   │    feedback_renderer(battery_results)              │
   │                 │                                  │
   │    ┌────── D0 path ──────┐  ┌──── D1 path ──────┐│
   │    │                      │  │                    ││
   │    │ prompt_builder_iter  │  │ defect_router      ││
   │    │     ↓                │  │     ↓              ││
   │    │ window_selector      │  │ for each genre:    ││
   │    │     ↓                │  │   prompt_builder   ││
   │    │ llm_caller           │  │     ↓              ││
   │    │     ↓                │  │   window_selector  ││
   │    │ owl_parser           │  │     ↓              ││
   │    │     ↓                │  │   llm_caller       ││
   │    │ patch_merger         │  │     ↓              ││
   │    │     ↓                │  │   owl_parser       ││
   │    │ updated ontology     │  │     ↓              ││
   │    │                      │  │   patch_merger     ││
   │    └──────────────────────┘  │     ↓              ││
   │                              │ sub_ontology       ││
   │                              │                    ││
   │                              │ deterministic_     ││
   │                              │   integrator       ││
   │                              │     ↓              ││
   │                              │ integrated onto.   ││
   │                              └────────────────────┘│
   │                                                   │
   │    checkpoint(round)                               │
   │    evaluate_battery(round)                         │
   │                                                   │
   └───────────────────────────────────────────────────┘
```

---

## 7. Build plan — suggested order

The modules below are grouped by dependency.  Rough effort in parentheses.

### Layer 0 — Foundations (day 1)

These have no dependencies on each other and everything else depends on them.

1. **`ontology_serialiser`** — deterministic render of an rdflib `Graph` into the
   text format the prompt expects.  Needed by windowing (to measure size),
   prompt building, and checkpointing.
2. **`owl_parser`** — extract OWL from model text, load into rdflib.  Needed by
   every call that consumes model output.
3. **`corpus_loader` + `genre_order_resolver`** — load documents, resolve order
   from seed.  Needed by both chunkers.
4. **`checkpoint_store`** — write and read a round-state directory.  Simple I/O;
   define the schema now so everything writes to it.

### Layer 1 — Chunking + injection (day 1–2)

5. **`chunker_d0`** and **`chunker_d1`** — genre-blocked concatenation and
   per-genre chunking.  Both use the same token budget.
6. **`injection_renderer`** — parse `bfo-core.owl` / resolved `Core.rdf`,
   render sorted label+definition blocks; raise if the allotment would
   truncate either grounded condition.

### Layer 2 — Windowing + patch-merge (day 2–3)

7. **`window_selector`** — the four-phase selection algorithm.  Depends on
   the embedding model (pinned) and the term extractor (reuse from
   `salient_term_pipeline.py`).
8. **`patch_merger`** — diff, validate, apply.  Depends on `ontology_serialiser`
   for structural axiom comparison.

### Layer 3 — Prompt assembly + LLM calling (day 3)

9. **`prompt_builder_construct`** and **`prompt_builder_iterate`** — assemble
   the prompt under the four pinned allotments (the fourth, feedback, is
   rendered upstream by `feedback_payload.py`).  Templates in the appendix
   of the spec; only the injection block differs across B; no exemplars.
10. **`llm_caller`** — greedy decoding wrapper over the vLLM chat endpoint,
    thread-safe, replica round-robin, thinking mode explicit.  Logs
    everything listed in §5.

### Layer 4 — Integration + defect routing (day 3–4)

11. **`deterministic_integrator`** — implements `deterministic_integration_spec_v17.md`.
    Depends on LogMap (Java, called via subprocess or py4j) and AML.
12. **`defect_router`** — routes feedback using the IRI provenance map.

### Layer 5 — Battery integration + feedback renderer (day 4)

13. **`reasoner_check`** — wraps HermiT/ELK for consistency, satisfiability,
    OWL 2 DL profile.
14. **`feedback_payload`** (done, v20) — renders the 6-item payload from battery results under the pinned caps and allotment.
    Pulls from: reasoner_check, oops_client, structural_profile,
    alignment_rate, salient_term_coverage.  CQ scorer is **not** included
    (held out).

### Layer 6 — Orchestrator (day 4–5)

15. **`run_orchestrator`** — the top-level loop from §2.  Wires everything
    together.  Handles D0 vs D1 branching, round looping, checkpoint writes,
    battery calls.
16. **`campaign_runner`** — submits all seeds × conditions to a thread pool
    (`max_concurrent_runs`, default all), records failures without stopping
    other runs, sorts summaries by run_id, and writes the campaign manifest
    including the serving configuration and thinking mode.  Concurrency is
    safe because outputs are batch-invariant; the determinism audit checks it.

### Layer 7 — Validation (day 5–6)

17. **Smoke test:** one seed, one condition (B0D0), R = 2.  Verify:
    checkpoints written, battery scores populated, logs parseable,
    hashes recorded, round-to-round scores change.
18. **D1 smoke test:** one seed, B2D1, R = 2.  Verify: sub-ontologies
    checkpointed, integration log populated, defect routing produces
    non-trivial splits, IRI provenance map populated.
19. **Determinism audit (Task 7):** hashes compared under five conditions —
    repeat runs, batch size 1 versus campaign batch sizes, across replicas,
    under concurrent load, and prefix caching on versus off.

---

## 8. Key parameters to pin before the pilot

All recorded in the campaign manifest.

| Parameter | Source | Notes |
|---|---|---|
| WINDOW_ALLOTMENT | B2 fit test (task 0c, real tokens) | Token budget for ontology view |
| CHUNK_ALLOTMENT | B2 fit test (task 0c, real tokens) | Token budget per corpus chunk |
| INJECTION_ALLOTMENT | B2 fit test (task 0c, real tokens) | Holds B2's full inventory; neither grounded condition is truncated |
| FEEDBACK_ALLOTMENT | Task 0c, real tokens (v20) | Token ceiling for the iteration payload at either D level; identical across B and rounds |
| FEEDBACK_CAPS | Task 0c (v20) | Per-item list caps (`FeedbackCaps`): unsatisfiable classes, profile violations, pitfalls, affected elements per pitfall, missing terms per genre, routed defects. Pinned so the halving guard never fires (pilot check: `feedback_overflow_steps == 0`) |
| CHECKPOINT_ROUNDS | Derived from R_MAX (v20) | `checkpoint_rounds_for(R_MAX)`; recorded, not chosen |
| LABEL_NORMALISATION_RULE | `label_normalisation.py` (v20) | Rule version string; pinned before the CQ set is frozen |
| SIM_THRESHOLD | Calibration (task 2 output) | Embedding similarity for windowing |
| FAN_OUT_CAP | Design choice | Max siblings+children per matched class |
| EMBEDDING_MODEL | Manifest | Same as salient-term pipeline |
| LOGMAP_CONFIDENCE | Default | Pinned, not tuned per run |
| R_MAX | Pilot | Currently 9; pilot confirms or revises |
| MODEL_ID + revision | Manifest | gemma-4-26B-A4B-it at a recorded revision; bf16; text-only |
| CONTEXT_WINDOW | Model spec | Total token limit |
| THINKING_MODE | Pilot (task 5) | Off by default; identical across all conditions |
| SERVING | Manifest | vLLM version, `VLLM_BATCH_INVARIANT=1`, 8 replicas × 1 GPU (B200), prefix caching per audit |
| MAX_CONCURRENT_RUNS / MAX_GENRE_WORKERS | Throughput benchmark | Throughput only; outputs unaffected |
| T_A, floor, T_B = T_A, sampling seeds | Task 0c / 0d | Corpus sample parameters (asset 1); *T*<sub>B</sub> equals *T*<sub>A</sub> with the same allocation (v20) |

---

## 9. What this does NOT include

These are separate tasks on the todo list and are not part of Task 4:

- **CQ scorer** (Task 1) — runs as part of the battery but is authored and
  frozen separately.
- **Population pipeline** (Task 9) — consumes checkpoints from this pipeline.
  Scaffolded in v20: `kg_model.py`, `population_extract.py`, `triple_sampler.py`,
  `nli_verifier.py`, `validation_pass.py`, `population_run.py`. It reads
  `R<nn>/ontology.owl` from the checkpoint rounds and writes its own tree under
  `<population_dir>/<run_id>/R<nn>/` (kg.nt, provenance.jsonl, population_stats,
  sample, verification, utilisation, validation). The extraction backend is the
  same `LLMBackend` as this pipeline; the NLI model and DL reasoner are injected
  hooks. Pin before the Paper 2 campaign: `EXTRACTION_CHUNK_ALLOTMENT`, `SAMPLE_N`
  (2,000), `NLI_MODEL_ID` + revision, `NLI_THRESHOLD` (from the calibration
  sweep), `VALIDATION_TIMEOUT_S`, `HAR_MASTER_SEED`.
- **Paper 3 retrieval / benchmark** (Tasks 10–11) — consumes populated KGs.
- **The conformance-channel ablation** (Paper 1 §7.1: B2D0, three seeds) — a
  variant run, not core infrastructure.  Implemented by toggling a flag in
  `feedback_payload.py` that drops item 4 (conformance report) from the
  rendered payload while keeping the ceiling.
