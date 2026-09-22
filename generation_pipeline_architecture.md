That's the full pipeline — 15 modules, ~3,900 lines, all layers from the architecture sketch. Here's what you have and what to do next.

What's in the package (maps to the architecture sketch):

Layer	Modules	Status
0 — Foundations	ontology_model, corpus, checkpoint	Complete
1 — Chunking + injection	chunker, injection	Complete
2 — Windowing + patch-merge	windowing, patch_merge	Complete
3 — Prompt + LLM	prompt, llm	Complete (two backends: completions API and chat API)
4 — Integration + routing	integration, defect_routing	Complete (LogMap/AML as subprocess stubs — you'll need to wire to your Java installs)
5 — Battery + feedback	battery	Complete (instrument functions are pluggable — you wire in your existing structural_profile.py, salient_term_pipeline.py, etc.)
6 — Orchestrator	orchestrator, campaign	Complete

What you need to do to get it running:

Install deps on your machine: rdflib, numpy, sentence-transformers (or whatever embedding model you're using), requests (for the LLM API client).
Wire the battery instruments. The Battery class takes callables — plug in your existing structural_profile.py and salient_term_pipeline.py, write thin wrappers for the reasoner (HermiT or ELK via owlready2 or the OWL API) and the OOPS! client you already built.
Wire the LLM backend. Point OpenAICompatibleBackend or ChatBackend at your local vLLM/llama.cpp server.
Wire LogMap/AML. The _run_logmap stub shows the subprocess pattern — you'll need to adjust the command line to match your LogMap JAR's actual CLI.
Pin the allotments. Run the B2 fit test: load IOF Core, render the injection, measure tokens, and set WINDOW_ALLOTMENT and CHUNK_ALLOTMENT to fit comfortably alongside it.
Smoke test. One seed, B0D0, R=2. Then one seed, B2D1, R=2. Then three identical B0D0 runs for the determinism audit (Task 7).

The prompt templates in prompt.py are deliberately plain — you'll want to tune the system prompt wording, but the structure (three-allotment, no round counter, no history) is locked in by the spec. The files below have everything.

# Generation Pipeline — Architecture Sketch

Task 4 build plan.  Companion to `dissertation_overview_and_paper_outlines_v17.md` §4.2–4.4,
`windowing_spec_v15.md`, and `deterministic_integration_spec_v16.md`.

---

## 1. What the pipeline does in one sentence

For every (seed, condition) pair, sequentially accumulate an ontology from
corpus chunks, then run 9 rounds of feedback-driven iteration, checkpointing
and evaluating at every round state (R0–R9).

---

## 2. Top-level loop

```
for seed in seeds:                          # k = 10
    genre_order = resolve_genre_order(seed)  # S-GEN governs this
    for condition in [B0D0, B0D1, B1D0, B1D1, B2D0, B2D1]:
        run = init_run(seed, condition)

        # ── Phase 1: Construction (produces R0) ──────────────
        if condition.D == D0:
            ontology = construct_monolithic(run, genre_order)
        else:  # D1
            sub_ontologies = {}
            for genre in genre_order:
                sub_ontologies[genre] = construct_genre(run, genre)
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
                for genre in genre_order:
                    sub_ontologies[genre] = iterate_genre(
                        run, r, genre, sub_ontologies[genre], routed[genre]
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
| `corpus_loader` | **to build** | Loads documents with genre labels into `CorpusDocument` objects; same objects the salient-term pipeline uses. |
| `chunker_d0` | **to build** | Concatenates corpus in genre-blocked order, chunks by token budget (genre-blind, boundaries may straddle). Records straddling-chunk count. |
| `chunker_d1` | **to build** | Chunks within each genre separately. Same token budget as D0. |
| `genre_order_resolver` | **to build** | From S-GEN seed, produces the genre processing order (varied across seeds, identical between D0 and D1 within a seed). |

### 3.2  Prompt assembly

| Component | Status | Description |
|---|---|---|
| `injection_renderer` | **to build** | Deterministic extraction of class/relation labels + definitions from `bfo-core.owl` (B1) or resolved `Core.rdf` (B2); alphabetical sort, IRI tie-break; truncation at INJECTION_ALLOTMENT with truncation point logged. B0 produces an empty injection block. |
| `prompt_builder_construct` | **to build** | Assembles the three-allotment prompt: injection + window/full ontology + chunk. Calls windowing if needed. Uniform template across B; only injection content differs. |
| `prompt_builder_iterate` | **to build** | Assembles the iteration prompt: injection + window/full ontology + 6-item feedback payload. No round counter, no history. Same allotments as construction. |

### 3.3  Windowing & patch-merge

| Component | Status | Spec |
|---|---|---|
| `window_selector` | **to build** | `windowing_spec_v15.md` §3. Four-phase selection: term extraction → label matching → ancestor closure + siblings/children (FAN_OUT_CAP) → budget fill by score. Fires when serialised ontology > WINDOW_ALLOTMENT. |
| `patch_merger` | **to build** | `windowing_spec_v15.md` §4. Diff model output against window; validate (no invisible-entity references); apply patch to full ontology. Orphaned-reference handling for deletions. |
| `ontology_serialiser` | **to build** | Renders an ontology (or window subset) into the text format the prompt expects. Must be deterministic — same ontology → same string. Used for both prompt assembly and token counting. |

### 3.4  LLM caller

| Component | Status | Description |
|---|---|---|
| `llm_caller` | **to build** | Single entry point for all generation calls. Greedy decoding, batch size 1, deterministic flags. Logs: prompt hash, response hash, token counts (prompt / completion), wall time, condition metadata. Parses OWL from the model's response. |
| `owl_parser` | **to build** | Extracts well-formed OWL from the model's text response. Handles common failure modes (truncation, syntax errors). Logs parse success/failure and error details. |

### 3.5  Integration (D1 only)

| Component | Status | Spec |
|---|---|---|
| `deterministic_integrator` | **to build** | `deterministic_integration_spec_v16.md` §2. Two stages: (1) label normalisation + IRI reconciliation + union; (2) LogMap alignment + deterministic reconciliation. AML as audit. Produces `IntegrationResult` with provenance map. |
| `defect_router` | **to build** | `deterministic_integration_spec_v16.md` §4. Routes feedback items to sub-ontologies via the IRI provenance map. Single-source → one channel; multi-source → all involved channels. |

### 3.6  Evaluation battery

| Component | Status | Description |
|---|---|---|
| `reasoner_check` | **to build** | OWL 2 DL profile check, global consistency, unsatisfiable class list. Wraps a reasoner (HermiT or ELK). |
| `structural_profile` | **done (v16)** | `structural_profile.py` — seven OntoQA metrics via rdflib. |
| `oops_client` | **done (v16)** | `structural_profile.py` — OOPS! REST client with XML parsing. |
| `alignment_rate` | **done (v14)** | `alignment_rate.sparql` — single priority-cascade SPARQL query. |
| `salient_term_coverage` | **done (v16)** | `salient_term_pipeline.py` — coverage scoring and genre balance. |
| `cq_scorer` | **to build** (task 1) | SPARQL execution against the ontology; answerability = proportion returning non-empty. |
| `feedback_renderer` | partial (v16) | Assembles the 6-item feedback payload as text for the prompt. Needs integration with all battery components. |

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
      R01/
        ...                              # same structure
      ...
      R09/
        ...
      construction_log.jsonl             # per-chunk log from Phase 1 (§5.1)
      iteration_log.jsonl                # per-round log from Phase 2 (§5.2)
      run_summary.json                   # aggregated statistics
```

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
   render sorted label+definition blocks, truncate at INJECTION_ALLOTMENT.

### Layer 2 — Windowing + patch-merge (day 2–3)

7. **`window_selector`** — the four-phase selection algorithm.  Depends on
   the embedding model (pinned) and the term extractor (reuse from
   `salient_term_pipeline.py`).
8. **`patch_merger`** — diff, validate, apply.  Depends on `ontology_serialiser`
   for structural axiom comparison.

### Layer 3 — Prompt assembly + LLM calling (day 3)

9. **`prompt_builder_construct`** and **`prompt_builder_iterate`** — assemble
   the three-allotment prompt.  Templates in the appendix of the spec;
   only the injection block differs across B.
10. **`llm_caller`** — greedy decoding wrapper.  Logs everything listed in §5.
    Probably a thin wrapper around vLLM or the local inference server.

### Layer 4 — Integration + defect routing (day 3–4)

11. **`deterministic_integrator`** — implements `deterministic_integration_spec_v16.md`.
    Depends on LogMap (Java, called via subprocess or py4j) and AML.
12. **`defect_router`** — routes feedback using the IRI provenance map.

### Layer 5 — Battery integration + feedback renderer (day 4)

13. **`reasoner_check`** — wraps HermiT/ELK for consistency, satisfiability,
    OWL 2 DL profile.
14. **`feedback_renderer`** — assembles the 6-item payload from battery results.
    Pulls from: reasoner_check, oops_client, structural_profile,
    alignment_rate, salient_term_coverage.  CQ scorer is **not** included
    (held out).

### Layer 6 — Orchestrator (day 4–5)

15. **`run_orchestrator`** — the top-level loop from §2.  Wires everything
    together.  Handles D0 vs D1 branching, round looping, checkpoint writes,
    battery calls.
16. **`campaign_runner`** — iterates over seeds × conditions, manages
    parallelism (if any — probably sequential for determinism), writes the
    campaign manifest.

### Layer 7 — Validation (day 5–6)

17. **Smoke test:** one seed, one condition (B0D0), R = 2.  Verify:
    checkpoints written, battery scores populated, logs parseable,
    hashes recorded, round-to-round scores change.
18. **D1 smoke test:** one seed, B2D1, R = 2.  Verify: sub-ontologies
    checkpointed, integration log populated, defect routing produces
    non-trivial splits, IRI provenance map populated.
19. **Determinism audit (Task 7):** three identical runs, compare hashes.

---

## 8. Key parameters to pin before the pilot

All recorded in the campaign manifest.

| Parameter | Source | Notes |
|---|---|---|
| WINDOW_ALLOTMENT | B2 fit test | Token budget for ontology view |
| CHUNK_ALLOTMENT | B2 fit test | Token budget per corpus chunk |
| INJECTION_ALLOTMENT | B2 fit test | Token budget for B2 injection |
| SIM_THRESHOLD | Calibration (task 2 output) | Embedding similarity for windowing |
| FAN_OUT_CAP | Design choice | Max siblings+children per matched class |
| EMBEDDING_MODEL | Manifest | Same as salient-term pipeline |
| LOGMAP_CONFIDENCE | Default | Pinned, not tuned per run |
| R_MAX | Pilot | Currently 9; pilot confirms or revises |
| MODEL_ID + revision | Manifest | Generator weights |
| CONTEXT_WINDOW | Model spec | Total token limit |

---

## 9. What this does NOT include

These are separate tasks on the todo list and are not part of Task 4:

- **CQ scorer** (Task 1) — runs as part of the battery but is authored and
  frozen separately.
- **Consensus induction** — R9-only post-campaign analysis, not in the loop.
- **Population pipeline** (Task 9) — consumes checkpoints from this pipeline.
- **Paper 3 retrieval / benchmark** (Tasks 10–11) — consumes populated KGs.
- **The conformance-channel ablation** (§8.3) — a variant run, not core
  infrastructure.  Implemented by toggling a flag in `feedback_renderer`.
- **The D0-shuffled ancillary arm** (§8.5) — a variant of `genre_order_resolver`.
