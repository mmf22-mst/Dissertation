# Dissertation — Implementation and Pre-Campaign Task List

Companion to **dissertation_overview_and_paper_outlines_v20.md**. Supporting specifications: `windowing_spec_v16.md`, `deterministic_integration_spec_v17.md`, `generation_pipeline_architecture.md` (v20), `wiring_and_smoke_test_plan.md` (v20). Covers all three papers. All effort figures are authorship and implementation effort, not the campaigns themselves, which are sized in Part I §12.

The battery is not human-free. It is human-*bounded*: the remaining effort is authorship and scholarship, performed once, and none of it scales with the number of experimental runs, rounds, or conditions.

---

## Completed

- **Codebook provenance review** against BFO 2020, ISO/IEC 21838-2 and Arp et al. — 6 codes × 6 fields, primary sources only. **Done (codebook v8).** *Retained in project archive; codebook is no longer a governing document for the dissertation but may be published separately.*
- **Historical→current E-code crosswalk** added to codebook front matter — 1 table. **Done (codebook v12 §0.01–0.02).** *Archived with codebook.*

## Closed in v20

- **Review items from v19.1, all resolved in the overview.** CQ label matching: a fixed normalisation rule (CamelCase/underscore split, lower-case, punctuation strip, whitespace collapse, head-noun singularisation) is applied to a scoring copy before pattern matching, with the normalisation-only hit share reported per condition. Few-shot exemplars: the prompts contain none (confirmed against `prompt.py`); the stale mention was removed from what S-GEN governs. Coverage: entity-level (class/property label) only — definition mentions do not count, matching `salient_term_pipeline.py`. Population sample: *T*<sub>B</sub> = *T*<sub>A</sub> with the same allocation; the full-remainder option moved to future work; entailment-verified precision on a pinned stratified sample (*n* = 2,000 per KG) with Wilson intervals; reasoner check under a pinned timeout with a uniform OWL 2 RL fallback. Paper 3: two retained factors (4 configurations) is the default, a third only if pilot cost permits; benchmark target ~200 items (floor 150; ~120 mined, ~80 synthetic). D1 sub-ontology battery at the four checkpoints only (720 runs). Pilot on four seeds so the MDE variance has more than one degree of freedom. Part I restructured for the committee: §3 is now the practitioner decision table plus the "if everything is null" paragraph; the CCO argument moved to Factor B and Appendix A.4; "realist", "continuant", "punning" and "sequential ignorability" glossed or replaced; glossary extended. **Done (v20).**

## Closed in v19

- **MVP design review.** Factor B reduced to three levels (B0, B1, B2 = IOF Core); CCO dropped and named as future work. Six genres retained: DPBPS, Command Media, FMEAs, NCRs, Jira issues, Active Risk Management. Cut: consensus induction, LLM-merge ancillary, injection-format ablation, D0-shuffled arm, longitudinal mediation. Paper 2 community structure retained. **Done (v19).**
- **Co-occurrence-anomalous entailment scoring** (previously task 3). Dropped from the design. **Closed (v19).**
- **Generator and platform selection.** gemma-4-26B-A4B-it on 8×B200, one GPU per replica, bf16, text-only, vLLM batch-invariant mode (subject to the task 7 audit). Candidate models were screened against the employer's model restrictions; no permitted alternative offered a consistent improvement at similar speed. **Done (v19).**
- **Corpus design.** Two disjoint frozen samples: construction sample A (square-root genre allocation, floor, size from saturation curves) and population sample B (size set after the throughput benchmark, up to the full remainder). Corrective Action Reports excluded from both; synthetic scenarios in B only. **Specified (v19); executed in tasks 0c and 0d.**

## Closed in v18

- **Prepare the CCO injection rendering** (task 0a). `GroundingLevel.B2b` added to the injection renderer (`injection.py`) with `CCO` namespace constant in `ontology_model.py`. Renderer parses `CommonCoreOntologiesMerged.ttl` (CCO v2.0, 2024-11-06) and extracts labels and definitions identically to B1 and B2a. Validated: renderer produces 1,687 labelled entries (48,001 word-count tokens); at B2a's allotment (5,138 tokens) B2b is truncated to 170 entries (10.1%); known CCO labels (Agent, Artifact, Facility, Act, Person, Organization) all present in rendered output. **Done (v18).** *In v19, B2b is dropped from the design; the renderer path is retained, unused. Before any reuse, fix the ordering defect: the alphabetical sort across BFO and CCO combined, followed by truncation, excludes every BFO entry and keeps only CCO entries early in the alphabet. BFO should be placed first, then CCO ordered by a relevance rule.*
- **Update the alignment-rate query for the four-category cascade** (task 0b). `cco:` namespace prefix match (`https://www.commoncoreontologies.org/`) added as priority rule 1 (before `iof-constr:`). Domain-class exclusion filter extended to exclude CCO-namespace classes. Output is now a four-way partition: CCO-aligned, IOF-aligned, BFO-only-aligned, Unaligned. Validated against a synthetic test ontology with six domain classes exercising all cascade paths: CCO-aligned (under `cco:` class), CCO-aligned (under `cco:` subclass of `BFO_0000144` — confirms `cco:` fires before the carve-out), IOF-aligned (under `iof-constr:` class), IOF-aligned (directly under `BFO_0000144` with no `cco:` intermediate — carve-out fires), BFO-only-aligned (under BFO class), Unaligned (no upper-level ancestor). All six classified correctly. **Done (v18).**

## Closed in v17

- **Reclassify salient-term coverage and genre coverage balance from held-out to coupled.** Both instruments produce directly actionable feedback (missing corpus terms, underrepresented genres) and enter the iteration loop alongside OOPS!, reasoner, conformance, and OntoQA. CQ answerability retained as the sole held-out instrument on two independent grounds: CQ feedback is not actionable for the LLM (requires reading SPARQL and reverse-engineering structural gaps), and the small CQ set (50–100) creates an overfitting risk if fed back. Confirmatory weight for H1d–H1f now rests on CQ answerability (Paper 1) plus KG fidelity and RCA accuracy (Papers 2–3, never fed back). **Done (v17).**
- **Clarify H3 mediation interpretation.** A residual direct path (ontology → RCA, bypassing KG fidelity) has a concrete mechanism: the ontology shapes GraphRAG retrieval traversal paths independently of triple-level fidelity. A nonzero direct effect is interpretable as an instrument gap in Paper 2's fidelity battery, not unexplained variance. Added to Paper 3 §8.3 and §9. **Done (v17).**

## Closed in v16

- **Implement structural profile computation and set up the OOPS! pipeline** (previously item 3). Implementation complete (`structural_profile.py`): seven OntoQA metrics via rdflib (validated against bfo-core.owl — 36 classes, 40 relations, max depth 5, mean depth 3.36), OOPS! REST client with XML response parsing, feedback report renderer, and flat scoring record for the battery log. OOPS! only implements 21 of 41 catalogued pitfalls. **Done (v16).**
- **Implement the windowing selection rule and patch-merge semantics** (previously item 4a). Specification complete (`windowing_spec_v15.md`): four-phase deterministic selection algorithm, patch-merge with collision validation, visibility logging with 18-field per-chunk record, five aggregated statistics for Paper 1, and eight-test validation plan. Five parameters to pin before pilot (WINDOW_ALLOTMENT, CHUNK_ALLOTMENT, SIM_THRESHOLD, FAN_OUT_CAP, EMBEDDING_MODEL). **Done (v16).**
- **Implement deterministic integration and defect routing for D1** (previously item 4b). Specification complete (`deterministic_integration_spec_v16.md`): two-stage deterministic procedure (union + LogMap alignment), IRI provenance map, defect routing to all involved sub-ontologies, per-round logging with delta rate and IRI stability. LLM merge replaced; anchored re-integration eliminated. Eight-test validation plan. **Done (v16).**
- **Implement salient-term extraction and the coverage scoring pipeline** (previously item 2). Implementation complete (`salient_term_pipeline.py`): C-value/NC-value + TF-IDF against Wikipedia IDF table, embedding-based matching via `embedding_utils.py`, genre coverage balance (normalised entropy), SPO assertion extractor for Paper 2. Smoke-tested with synthetic manufacturing data and the Wikipedia IDF table. **Done (v16).**

## Closed in v15

- **Run the pitfall-overlap audit** (previously item 3a). Closed: OntoQA structural profile reclassified from held out to loop-coupled (coupled through the OOPS! channel). The full OOPS! report is fed back with no suppression. No suppressed-pitfall list is needed because there is no held-out metric to protect. The audit analysis (pitfall_overlap_audit_v14.md) is retained in the project archive as the analysis that motivated this decision. **Closed (v15).**

## Closed in v14

- **Implement the alignment-rate query** (previously item 2). Design settled and query implemented (`alignment_rate.sparql`): a single SPARQL query implementing the priority cascade (`BFO_0000144` → IOF-aligned; `iof-constr:` → IOF-aligned; other `obo:BFO_` → BFO-only-aligned; else unaligned). Validated against IOF Core 202603 parse across eight critical topologies. **Done (v14).**

## Closed in v13

- **Freeze the lexical criterion for E4.** Closed: E-codes removed from the design.
- **Implement the six Tier A/B detectors.** Closed: E-codes removed from the design.
- **Build the three B2 baseline-exclusion lists.** Closed: E-codes removed from the design.
- **BFO build diff (codebook Table 0.2b).** Previously completed; no longer required by the design. Retained in codebook archive.
- **Codebook checklist items 9, 10, 18, 19, 20.** All closed: E-codes removed from the design; the codebook is archived.

---
---
## Task list

0. **Take the design to the committee.** Everything below commits infrastructure and a multi-month campaign to a factor structure that has not been approved. Approval is the first dependency, not a formality to be collected later.

0c. **Throughput benchmark, token census, and saturation curves.**
   - **Throughput.** Deploy gemma-4-26B-A4B-it on the 8×B200 platform with batch-invariant mode on, one GPU per replica. Measure per-call latency and aggregate throughput on real construction and extraction prompts, including the throughput cost of batch-invariant kernels. **Measure per-call latency with the output at the pinned window allotment**, not with a small artefact: the model regenerates the view it is shown (overview Part I §5), so output length is the term that sets the D0 stream length (overview Part I §12). Report the D0 run length this implies before *T*<sub>A</sub> is set; if impractical, apply the levers listed in §12 in order.
   - **Token census.** Count tokens per genre over the full collection with the model's tokenizer (CPU only).
   - **Allotment pinning.** Pin the injection, window, chunk and **feedback** allotments in real tokens, plus the per-item truncation caps for the feedback payload (overview Paper 1 §4.2).
   - **Saturation curves.** Run per-genre salient-term extraction on nested samples to produce the saturation curves and the split-half stability check for the floor.
   - **Sampling parameters.** Set *T*<sub>A</sub>, the floor, and the square-root shares; *T*<sub>B</sub> = *T*<sub>A</sub> with the same allocation (overview Part I §8, asset 1).

   Record all of these in the manifest. **Effort: 2–3 days, mostly CPU. Blocks 0d.**

0d. **Build and freeze the two corpus samples** (overview Part I §8, asset 1):
   1. Draw construction sample A with square-root allocation and the floor.
   2. Draw population sample B from the remainder, disjoint from A.
   3. Ensure the pre-registered minimum of NCRs linked to Corrective Action Reports is in B.
   4. Exclude Corrective Action Reports from both samples.
   5. Redact linked root-cause text in both samples.
   6. Insert the Source B synthetic scenario documents into B only.
   7. Run the leakage check on both samples, then freeze and hash.

   **Effort: 1–2 days after tasks 8 and 10a. Blocks tasks 1, 2, and 5.**

1. **Re-scope and freeze the CQ set** (~108 questions): 6 genres × 4 question types × 4 per cell, plus 12 cross-genre multi-hop CQs among the retained genres.
   1. Prune the draft's single-genre CQs for the five dropped genres.
   2. Replace any cross-genre CQ that touches a dropped genre.
   3. Rewrite every relational and multi-hop query that does not join at least two label-matched classes through an object property path.
   4. Tag strata so the primary aggregate (relational + multi-hop, 60 CQs) can be computed.
   5. Pin the label-normalisation rule (overview Part I §6.2(c)) and implement the scoring-copy normalised label; point the CQ regexes at it; add the normalisation-only hit share to the CQ scoring record. **Rule and helpers done (v20 support update)** — `label_normalisation.py` (`normalise_scoring_label`, `scoring_copy`, `rewrite_cq_query`, `normalisation_only_hit_share`); `cq_calibrate.py` flags non-normalised pattern terms. **Scorer done** — `cq_scorer.py`: asset parsing and validation, scoring on the scoring copy, injection-only rows discarded, per-stratum/per-genre/primary aggregates, normalisation-only share, battery plug-in and CLI; tested on real rdflib. Remaining in this task: author and freeze the CQ set (steps 1–4, 6), and add the injection-only rule to overview §6.2(c) at the next point revision.
   6. Calibrate with `cq_calibrate.py` against construction sample A and its salient-term inventory; review the calibration report (zero-hit CQs, per-genre hit rates, suggested synonym expansions); accept or reject each expansion; do a domain-fit review; prune trivially easy or unreachably hard CQs; freeze as asset 4.

   **Depends on tasks 0d and 2.** Effort: 2–3 days.

2. **Run the salient-term pipeline on the frozen samples.** Freeze the salient-term inventory (asset 2) from construction sample A and the salient-assertion inventory (asset 3) from population sample B. Also freeze the larger reference inventory from the saturation-curve extraction, used for the representativeness figure (overview §6.2(a)). Calibrate `SIM_THRESHOLD` from the similarity distribution and record the threshold, term counts, and genre proportions in the manifest. Effort: 1–2 days.

4. **Wire the generation pipeline for concurrent execution**, covering B0, B1, B2 × D0, D1 = 6 cells per seed. Components are implementation-complete; the v19 work is:
   - **Grounding levels:** rename `GroundingLevel.B2a` to `B2` and remove B2b from the campaign loop.
   - **Genres:** reduce the `Genre` enum to the six retained genres.
   - **Corpus sampling:** add the two-sample sampler and token census to `corpus.py`, and create `saturation.py`.
   - **LLM client:** replace the synchronous batch-size-1 client in `llm.py` with a concurrent client against the vLLM server. Serving flags come from the model manifest. Pass the thinking-mode switch through the chat template, and strip any reasoning text before patch parsing.
   - **Scheduling:** add a campaign-level scheduler running all 60 runs concurrently. Under D1, build the six genre sub-ontologies in parallel at R0 (the orchestrator currently loops over genres sequentially) and issue each round's sub-ontology calls in parallel.
   - **Battery:** report CQ answerability per stratum plus the primary aggregate; run the D1 sub-ontology battery at the four checkpoint rounds only (delta rate and IRI stability still every round); confirm coverage matches on entity labels only. **Sub-ontology battery done (v20 support update)** — `Battery.run_sub` at `RunConfig.checkpoint_rounds` (`checkpoint_rounds_for(r_max)`), written to `sub_battery.json`; per-genre coverage via `coverage_by_genre_fn`. Coverage confirmed label-only in `salient_term_pipeline.py`.
   - **Manifest:** record that the prompts carry no few-shot exemplars. **Done** — `few_shot_exemplars: 0`, `checkpoint_rounds`, `label_normalisation_rule`, `coverage_match_level` in the campaign manifest.
   - **Feedback allotment (new in v19.1):** **Done (v20 support update)** — `feedback_payload.py` (fixed item order, always-present summary lines, per-item `FeedbackCaps`, deterministic truncation orders, omitted-entry counts, halving guard, truncation log); `battery.render_feedback` re-renders per D1 sub-ontology with routed defects at position 0; `prompt.build_iteration_prompt` checks the pinned allotment; `CampaignConfig.feedback_allotment` / `feedback_caps` recorded in the manifest. Remaining: pin the values (task 0c) and confirm `feedback_overflow_steps == 0` in the pilot (smoke plan §7c.1).
   - **Removal logging:** **Done (v20 support update)** — `patch_added_entities` / `patch_removed_entities` logged for every call, construction and iteration, windowed or not (orchestrator `_patch_fields`).

   Then complete the smoke tests in `wiring_and_smoke_test_plan.md`. Round-state checkpointing, fresh-only feedback, payload logging, and deterministic re-integration are unchanged. Effort: 4–7 days (the feedback allotment adds about a day).

5. **Run the pre-campaign pilot.** Four seeds, two conditions (B0D0 and B2D1), R = 15, full battery at every round. Purposes, in order:
   - settle the round count;
   - measure integration loss and the defect-routing split;
   - verify LogMap alignment stability across rounds;
   - expose the loop-coupling behaviour predicted in overview §6.7;
   - measure feedback payload volume by condition for the H1e covariate;
   - supply variance estimates for a real MDE;
   - verify the alignment-rate cascade and contamination signal on real generated ontologies;
   - report the patch parse-failure rate per condition;
   - report feedback truncation frequency per item per condition, and the per-call entity-removal rate (unintended deletions under full-view regeneration);
   - run a thinking-mode comparison (B2D1, one seed, R0 plus two rounds, on versus off; compare parse failures, relational-CQ answerability, and per-call latency) and pin the setting;
   - confirm the campaign-level concurrency scheduler;
   - shake out the pipeline end to end.

   **Depends on tasks 0d, 4, and 7.**

6. **Implement the community-structure pipeline for Paper 2** — Leiden with CPM over a resolution grid, node genre-labelling with the purity threshold, genre-AMI, and standard modularity as an ancillary comparison. Library calls; modest effort but must be in place before the Paper 2 campaign.

7. **Run the determinism audit** under the five conditions in overview Paper 1 §4.5.4:
   1. repeat runs;
   2. batch size 1 versus campaign batch sizes;
   3. across replicas;
   4. under concurrent load;
   5. prefix caching on versus off.

   Cover construction, feedback, and extraction prompts. Apply the pre-registered fallback if a condition fails. **Effort: 1 day. Run before the pilot so the pilot uses the final regime.**

8. **Verify redaction feasibility** on Corrective Action Reports and their linked NCR, Jira, and risk records. **Blocks task 0d.** Effort: 1–2 days.

9. **Build the population pipeline and NLI verifier**, with its calibration harness — schema-constrained extraction + verifier characterisation. Includes the stratified triple sampler (*n* = 2,000 per KG, proportional by source genre, seed under S-HAR) with Wilson intervals, and the validation pass with its pinned per-KG timeout and OWL 2 RL fallback (overview Paper 2 §4.4, §5.1).

   **Scaffolding done (v20 support update), tested on real rdflib with fake LLM/NLI/reasoner:** `kg_model.py` (KG + per-triple provenance, deterministic entity resolution, schema view, on-disk layout), `population_extract.py` (schema-constrained extraction prompt, JSON-lines parsing, conformance tallies, degenerate-schema handling), `triple_sampler.py` (proportional stratified sampling with largest-remainder allocation, Wilson intervals), `nli_verifier.py` (verbalisation in plain/B1/B2 styles, `NLIModel` protocol, sampled precision, calibration-by-injection with same-class subject/object swaps and compatible predicate swaps, style crossing, threshold sweep), `validation_pass.py` (DL hook under a thread-guarded timeout, campaign-wide uniform OWL 2 RL fallback, near-violation counts, punning and type-anomaly rates), `population_run.py` (S-POP/S-HAR derivation, per-state driver, utilisation outcomes, manifest). **Remaining:** wire the real NLI model (pin id and revision), the DL reasoner hook (HermiT/Openllet via subprocess), the vLLM backend for extraction, and pin the extraction chunk allotment, NLI threshold (from the calibration sweep) and validation timeout; run the calibration on pilot KGs before the campaign.

10a. **Paper 3 benchmark assets needed before corpus freeze:** Corrective Action Report label mining, the linked-text redaction procedure, and Source B synthetic scenario generation written as genre documents for the population sample. Fix the mined-item count once redaction is done and confirm the benchmark composition against the ~200-item target and 150 floor (overview Paper 3 §3.4). **Blocks task 0d.** Effort: 3–4 days.

10b. **Paper 3 answer matcher and its calibration.** Blocks the Paper 3 campaign. Effort: 1–2 days.

11. **Implement the five retrieval mechanisms** as parameterised components for the Paper 3 system.

12. **Compute the minimum detectable effect** at *k* = 10 for each outcome scope, **including the B-contrast family (B1–B0, B2–B1)**, using the four-seed pilot's variance rather than assumed variance, including the within-subject round effects, and record it — together with the contingency for an MDE that exceeds plausible effects — in the pre-registration.

13. **Size the campaign** (overview Part I §12) from the throughput benchmark and pilot. The design fixes three parameters:
    - Paper 1 is 60 runs × 10 rounds, with the construction sample size from task 0c.
    - Paper 2 runs on 240 checkpoint states, over population sample B at *T*<sub>B</sub> = *T*<sub>A</sub>.
    - The Paper 3 Stage 2 cap is two retained factors; a third only if pilot cost per RCA run leaves headroom. Record which in the pre-registration.

14. **Verify all references** against the personal library, including the citations added in prior revisions (Traag et al. 2019; Traag, Van Dooren & Nesterov 2011; Duque-Ramos et al. 2011; Levy, Jacoby & Goldberg, ACL 2024; Liu et al., TACL 2024).

15. **Pre-register** design, hypotheses (H1a–H1f, with B×D×R noted as exploratory), instruments, the loop-coupled/held-out split, the analysis plan including the trajectory model, and the declared contingencies. Include the four checkpoint rounds (R0, R3, R6, R9) for Papers 2 and 3, and add:
    - the CQ primary strata (relational + multi-hop) as the sole primary, and the R0 confirmatory family (salient-term coverage, genre coverage balance, consistency, unsatisfiable-class rate, OWL 2 DL conformance) as one Holm family;
    - the feedback allotment, item order and per-item caps;
    - the checkpoint rule (R0 plus three evenly spaced rounds to the terminal round);
    - the corpus design: *T*<sub>A</sub> with its saturation justification, square-root allocation and floor, *T*<sub>B</sub> = *T*<sub>A</sub>, and disjointness;
    - the label-normalisation rule;
    - the triple-verification sample size *n*, the reasoner timeout and fallback;
    - the benchmark target and floor;
    - the linked-NCR minimum;
    - the Paper 3 retained-factor cap (two by default);
    - the model manifest, including the thinking-mode setting;
    - the determinism regime and its fallback.

---

## Indicative sequencing

| | Task | Effort | Blocks |
|---|---|---|---|
| 0 | Committee approval of the design | — | Everything |
| 0c | Throughput benchmark, token census, saturation curves, sampling parameters | 2–3 days | 0d |
| 8 | Redaction feasibility check | 1–2 days | 0d |
| 10a | Paper 3 benchmark assets needed before freeze (label mining, redaction procedure, synthetic scenarios) | 3–4 days | 0d |
| 0d | Build and freeze the two corpus samples | 1–2 days | 1, 2, 5 |
| 2 | Salient-term and salient-assertion inventories from the frozen samples | 1–2 days | 1; coverage scoring; Paper 2 salience recall |
| 1 | CQ set: re-scope, calibrate against sample A, review, freeze | 2–3 days | CQ scoring |
| 4 | Pipeline wiring for concurrent execution, six cells per seed, feedback allotment, plus smoke tests | 4–7 days | 5, then Paper 1 campaign |
| 7 | Determinism audit (five conditions) | 1 day | 5, then Paper 1 campaign |
| 5 | Pilot: 4 seeds × 2 conditions (B0D0, B2D1) × R = 15, plus thinking-mode comparison | 3–5 days plus compute | Round count; MDE; campaign sizing |
| 6 | Community-structure pipeline (Leiden/CPM profile, genre-AMI, modularity) | 1–2 days | Paper 2 campaign |
| 9 | Population pipeline, sampled NLI verifier with calibration, validation pass with fallback — scaffolding done; wiring and pinning remain | 2–3 days | Paper 2 campaign |
| 10b | Paper 3 answer matcher with calibration | 1–2 days | Paper 3 campaign |
| 11 | Five retrieval mechanisms | 3–5 days | Paper 3 campaign |
| 12 | MDE from pilot variance | 1–2 days | 15 |
| 13 | Campaign sizing | 1 day | 15 |
| 14 | Verify all references | 1 day | Submission |
| 15 | Pre-register | 1–2 days | Paper 1 campaign |

Roughly **three to four weeks of tooling, corpus, and pilot work**, not counting committee time or the campaigns. On the 8×B200 platform, the campaigns themselves are indicatively days to a few weeks (overview Part I §12). The corpus freeze adds about a week of work that previously sat after the Paper 1 campaign, where it would have been too late.

The critical path runs:

1. tasks 0c, 8 and 10a (in parallel);
2. task 0d, the corpus freeze;
3. tasks 2 and 1 (inventories and CQ freeze), in parallel with task 4 (pipeline wiring) and task 7 (determinism audit);
4. task 5, the pilot;
5. tasks 12 and 13;
6. task 15.

Task 0c can start as soon as the B200 platform is available. Tasks 6, 9, 10b and 11 can run in parallel with the Paper 1 campaign.
