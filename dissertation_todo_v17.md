# Dissertation — Implementation and Pre-Campaign Task List

Companion to **dissertation_overview_and_paper_outlines_v17.md**. Covers all three papers. All effort figures are authorship and implementation effort, not the campaigns themselves, which are sized in Part I §12.

The battery is not human-free. It is human-*bounded*: the remaining effort is authorship and scholarship, performed once, and none of it scales with the number of experimental runs, rounds, or conditions.

---

## Completed

- **Codebook provenance review** against BFO 2020, ISO/IEC 21838-2 and Arp et al. — 6 codes × 6 fields, primary sources only. **Done (codebook v8).** *Retained in project archive; codebook is no longer a governing document for the dissertation but may be published separately.*
- **Historical→current E-code crosswalk** added to codebook front matter — 1 table. **Done (codebook v12 §0.01–0.02).** *Archived with codebook.*

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

## Task list

0. **Take the design to the committee.** Everything below commits infrastructure and a multi-month campaign to a factor structure that has not been approved. Approval is the first dependency, not a formality to be collected later.
1. **Author and freeze the CQ set** (~188 questions) with SPARQL translations, tagged by question type and genre relevance. First draft produced: 11 genres × 4 question types × 4 per cell = 176 single-genre CQs plus 12 cross-genre multi-hop CQs, each with a grounding-agnostic SPARQL query matching on `rdfs:label` patterns (no BFO/IOF IRIs). Remaining steps: export the CQ doc to markdown, run `cq_calibrate.py` against the real corpus with `--corpus-dir` and `--terms-dir` pointing to the salient-term inventories from task 2, review the calibration report (zero-hit CQs, per-genre hit rates, suggested synonym expansions), accept or reject each expansion, patch the SPARQL alternations with confirmed synonyms, do a domain-fit review pass (do the questions match the actual vocabulary and structure of the corpus?), prune any CQs that are trivially easy or unreachably hard, and freeze the final set as asset 4. Task 2 should run first or in parallel so that the salient-term inventories are available for the calibration step.
2. **Run the salient-term pipeline on the real corpus.** Load the corpus as `CorpusDocument` objects with genre labels, run `extract_terms_from_corpus()` against the Wikipedia IDF table, calibrate `SIM_THRESHOLD` from the similarity distribution, freeze the salient-term inventory (asset 2) and the salient-assertion inventory (asset 3). Record the threshold, term counts, and genre proportions in the manifest.
3. ~~**Implement co-occurrence-anomalous entailment scoring**~~ **(deferred / drop candidate)** — corpus co-occurrence statistics, reasoner-derived entailment extraction, anomaly ranking, and the threshold sensitivity sweep. Exploratory only; no hypothesis attached; not on the critical path; no other task depends on it. Can be built after the pilot if the committee requests it.
4. **Build the generation pipeline with round-state checkpointing and feedback logging**, so that the ontology state after each of the 9 rounds plus the R0 state is saved and evaluable, and so that payload tokens and flagged-item counts are recorded per round per condition. Each round receives fresh-only feedback (current ontology + reasoner, profile and conformance reports; no accumulated history; no round counter). Under D1, integration is re-run deterministically each round from the current sub-ontologies.
5. **Run the pre-campaign pilot.** Two seeds, two conditions (B0D0 and B2D1), R = 15, full battery at every round. Purposes, in order: settle the round count; measure integration loss and the defect-routing split; verify LogMap alignment stability across rounds (do alignments shift as sub-ontologies evolve?); expose the loop-coupling behaviour predicted in §6.7 before it is baked into 600 runs; measure feedback payload volume by condition for the H1e covariate; supply variance estimates for a real MDE; and shake out the pipeline end to end. A few days of compute that de-risks everything after it.
6. **Implement the community-structure pipeline for Paper 2** — Leiden with CPM over a resolution grid, node genre-labelling with the purity threshold, genre-AMI, and standard modularity as an ancillary comparison. Library calls; modest effort but must be in place before the Paper 2 campaign.
7. **Run the determinism audit** — three runs of one configuration under an identical seed, hashes compared.
8. **Verify redaction feasibility** on the corrective-action records before committing Paper 3.
9. **Build the population pipeline and NLI verifier**, with its calibration harness — schema-constrained extraction + verifier characterisation.
10. **Build the Paper 3 benchmark pipeline** — label mining, redaction, synthetic scenario injection, NLI answer matcher and its calibration.
11. **Implement the five retrieval mechanisms** as parameterised components for the Paper 3 system.
12. **Compute the minimum detectable effect** at *k* = 10 for each outcome scope, using pilot variance rather than assumed variance, including the within-subject round effects, and record it — together with the contingency for an MDE that exceeds plausible effects — in the pre-registration.
13. **Size the campaign** (Part I §12) from pilot throughput, and fix in advance the Paper 2 round subset and the Paper 3 Stage 1 factor cap that will apply if the full design proves infeasible.
14. **Verify all references** against the personal library, including the citations added in prior revisions (Traag et al. 2019; Traag, Van Dooren & Nesterov 2011; Duque-Ramos et al. 2011; Levy, Jacoby & Goldberg, ACL 2024; Liu et al., TACL 2024).
15. **Pre-register** design, hypotheses (H1a–H1f, with B×D×R noted as exploratory), instruments, the loop-coupled/held-out split, the analysis plan including the trajectory model, and the declared contingencies. Include the four checkpoint rounds (0, 3, 6, 9) for Paper 3 Stage 2 and the longitudinal mediation as ancillary.

---

## Indicative sequencing

| | Task | Effort | Blocks |
|---|---|---|---|
| 0 | Committee approval of the design | — | Everything |
| 1 | CQ set: calibrate against corpus, domain-fit review, freeze | 2–3 days (draft done; calibration + review remain) | CQ scoring; depends on task 2 for salient-term inventories |
| 2 | Run salient-term pipeline on real corpus; calibrate threshold; freeze assets 2–3 | 1–2 days | Corpus-grounded coverage; Paper 2 salience recall |
| 3 | ~~Co-occurrence-anomalous entailment scoring~~ | deferred | — |
| 4 | Generation pipeline with round-state checkpointing, windowing/patch-merge, deterministic integration, defect routing, and feedback logging | 4–6 days | Pilot, then Paper 1 campaign |
| 5 | Pilot: 2 seeds × 2 conditions × R = 15 | 2–4 days plus compute | Round count; MDE; campaign sizing |
| 6 | Community-structure pipeline (Leiden/CPM profile, genre-AMI, modularity) | 1–2 days | Paper 2 campaign |
| 7 | Determinism audit | 1 day | Paper 1 campaign |
| 8 | Redaction feasibility check for Paper 3 | 1–2 days | Paper 3 design |
| 9 | Population pipeline + NLI verifier with calibration | 3–5 days | Paper 2 campaign |
| 10 | Paper 3 benchmark pipeline + answer matcher with calibration | 3–5 days | Paper 3 campaign |
| 11 | Five retrieval mechanisms | 3–5 days | Paper 3 campaign |
| 12 | MDE from pilot variance, campaign sizing, pre-registration | 3–4 days | Paper 1 campaign |
| 13 | Campaign sizing | 1 day | Paper 1 campaign |
| 14 | Verify all references | 1 day | Submission |
| 15 | Pre-register | 1–2 days | Paper 1 campaign |

Roughly **two to three weeks of tooling and pilot work** (reduced from three to four by closing tasks 2–4b in v16), not counting committee time and not counting the campaigns themselves, which are sized in Part I §12 and are where the real elapsed time sits. Items 1 and 2 are partially parallelisable: the CQ draft is done and the domain-fit review can begin immediately, but the SPARQL calibration step in task 1 uses the salient-term inventories produced by task 2 — so task 2 should run first or concurrently, with calibration as the join point. Items 6 and 9–11 can run in parallel with the Paper 1 campaign. The critical path is item 4 → item 5 → item 12: the generation pipeline gates the pilot, the pilot gates the round count and the MDE, and both gate the pre-registration that the main campaign should not start without.
