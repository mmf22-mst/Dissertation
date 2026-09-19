# Dissertation — Implementation and Pre-Campaign Task List

Companion to **dissertation_overview_and_paper_outlines_v13.md**. Covers all three papers. All effort figures are authorship and implementation effort, not the campaigns themselves, which are sized in Part I §12.

The battery is not human-free. It is human-*bounded*: the remaining effort is authorship and scholarship, performed once, and none of it scales with the number of experimental runs, rounds, or conditions.

---

## Completed

- **Codebook provenance review** against BFO 2020, ISO/IEC 21838-2 and Arp et al. — 6 codes × 6 fields, primary sources only. **Done (codebook v8).** *Retained in project archive; codebook is no longer a governing document for the dissertation but may be published separately.*
- **Historical→current E-code crosswalk** added to codebook front matter — 1 table. **Done (codebook v12 §0.01–0.02).** *Archived with codebook.*

## Closed in v13

- **Freeze the lexical criterion for E4.** Closed: E-codes removed from the design.
- **Implement the six Tier A/B detectors.** Closed: E-codes removed from the design.
- **Build the three B2 baseline-exclusion lists.** Closed: E-codes removed from the design.
- **BFO build diff (codebook Table 0.2b).** Previously completed; no longer required by the design. Retained in codebook archive.
- **Codebook checklist items 9, 10, 18, 19, 20.** All closed: E-codes removed from the design; the codebook is archived.

---

## Task list

0. **Take the design to the committee.** Everything below commits infrastructure and a multi-month campaign to a factor structure that has not been approved. Approval is the first dependency, not a formality to be collected later.
1. **Author and freeze the CQ set** (50–100 questions) with SPARQL translations, tagged by question type and genre relevance.
2. **Implement the two alignment-rate queries** (BFO-only alignment rate and IOF alignment rate) with the priority-based partition rule defined in the overview §5.3. Two SPARQL queries against the asserted `rdfs:subClassOf` hierarchy, run on every ontology-state.
3. **Implement salient-term extraction and the coverage scoring pipeline**, and the salient-assertion extractor Paper 2 needs. Extractor + embedding matcher for terms; subject–predicate–object extractor for assertions.
4. **Implement structural profile computation** (OntoQA metrics; SPARQL or OWL API) and **set up the OOPS! pipeline** (web service or local scan). OOPS! is part of the feedback payload and is therefore loop-coupled by design.
4a. **Run the pitfall-overlap audit.** Walk the OOPS! catalogue (~41 pitfalls) against the OntoQA metrics; record the mapping; fix the suppressed-pitfall list for the fed-back report. Must be settled before the pilot, since it changes what the loop sees. Simpler than the v12 version: the audit no longer maps pitfalls against E-codes, only against OntoQA.
5. **Implement co-occurrence-anomalous entailment scoring** (exploratory) — corpus co-occurrence statistics, reasoner-derived entailment extraction, anomaly ranking, and the threshold sensitivity sweep. Piggybacks on item 3 for corpus statistics.
5a. **Implement the windowing selection rule and patch-merge semantics** for context overflow, with visibility logging per chunk. Deterministic selector + patch validator. Needed at both D levels and settled before the pilot, since it changes what the generator sees.
5b. **Implement anchored re-integration and defect routing for D1** — merge applied as a patch to the previous round's artefact, IRI provenance map maintained across rounds, feedback routed by provenance, churn and routing split logged. The heaviest new mechanism and a prerequisite for the pilot's D1 arm.
6. **Build the generation pipeline with round-state checkpointing and feedback logging**, so that the ontology state after each of the 9 rounds plus the R0 state is saved and evaluable, and so that payload tokens and flagged-item counts are recorded per round per condition. Each round receives fresh-only feedback (current ontology + reasoner, profile and conformance reports; no accumulated history; no round counter).
7. **Run the pre-campaign pilot.** Two seeds, two conditions (B0D0 and B2D1), R = 15, full battery at every round. Purposes, in order: settle the round count; **measure R0 merge churn under D1, against a pre-registered decision rule — low churn means the merge is largely mechanical and anchoring is a safeguard rather than a necessity, high churn means anchoring is mandatory and the integration feedback channel is doing substantive work, and either finding is reported; the churn threshold that separates "low" from "high" is set from the pilot data itself rather than assumed in advance, since no prior work provides a baseline for LLM-mediated ontology merge churn**; measure integration loss and the defect-routing split; expose the loop-coupling behaviour predicted in §6.7 before it is baked into 600 runs; measure feedback payload volume by condition for the H1e covariate; supply variance estimates for a real MDE; and shake out the pipeline end to end. A few days of compute that de-risks everything after it.
8. **Implement the community-structure pipeline for Paper 2** — Leiden with CPM over a resolution grid, node genre-labelling with the purity threshold, genre-AMI, and standard modularity as an ancillary comparison. Library calls; modest effort but must be in place before the Paper 2 campaign.
9. **Run the determinism audit** — three runs of one configuration under an identical seed, hashes compared.
10. **Verify redaction feasibility** on the corrective-action records before committing Paper 3.
11. **Build the population pipeline and NLI verifier**, with its calibration harness — schema-constrained extraction + verifier characterisation.
12. **Build the Paper 3 benchmark pipeline** — label mining, redaction, synthetic scenario injection, NLI answer matcher and its calibration.
13. **Implement the five retrieval mechanisms** as parameterised components for the Paper 3 system.
14. **Compute the minimum detectable effect** at *k* = 10 for each outcome scope, using pilot variance rather than assumed variance, including the within-subject round effects, and record it — together with the contingency for an MDE that exceeds plausible effects — in the pre-registration.
15. **Size the campaign** (Part I §12) from pilot throughput, and fix in advance the Paper 2 round subset and the Paper 3 Stage 1 factor cap that will apply if the full design proves infeasible.
16. **Verify all references** against the personal library, including the citations added in prior revisions (Traag et al. 2019; Traag, Van Dooren & Nesterov 2011; Duque-Ramos et al. 2011; Levy, Jacoby & Goldberg, ACL 2024; Liu et al., TACL 2024).
17. **Pre-register** design, hypotheses (H1a–H1f, with B×D×R noted as exploratory), instruments, the loop-coupled/held-out split, the analysis plan including the trajectory model, and the declared contingencies. Include the four checkpoint rounds (0, 3, 6, 9) for Paper 3 Stage 2 and the longitudinal mediation as ancillary.

---

## Indicative sequencing

| | Task | Effort | Blocks |
|---|---|---|---|
| 0 | Committee approval of the design | — | Everything |
| 1 | CQ set and SPARQL translations | 3–5 days | CQ scoring |
| 2 | Two alignment-rate queries | <1 day | Manipulation check |
| 3 | Salient-term and salient-assertion extraction, coverage scoring | 4–5 days | Corpus-grounded coverage; Paper 2 salience recall |
| 4 | Structural metrics and OOPS! pipeline, plus the pitfall-overlap audit | 1–2 days | Structural profile; feedback payload contents |
| 5 | Co-occurrence-anomalous entailment scoring (exploratory) | 1–2 days | Exploratory logical quality (depends on 3) |
| 6 | Generation pipeline with round-state checkpointing, windowing/patch-merge, anchored re-integration, defect routing, and feedback logging | 5–8 days | Pilot, then Paper 1 campaign |
| 7 | Pilot: 2 seeds × 2 conditions × R = 15 | 2–4 days plus compute | Round count; MDE; campaign sizing |
| 8 | Community-structure pipeline (Leiden/CPM profile, genre-AMI, modularity) | 1–2 days | Paper 2 campaign |
| 9 | Determinism audit | 1 day | Paper 1 campaign |
| 10 | Redaction feasibility check for Paper 3 | 1–2 days | Paper 3 design |
| 11 | Population pipeline + NLI verifier with calibration | 3–5 days | Paper 2 campaign |
| 12 | Paper 3 benchmark pipeline + answer matcher with calibration | 3–5 days | Paper 3 campaign |
| 13 | Five retrieval mechanisms | 3–5 days | Paper 3 campaign |
| 14 | MDE from pilot variance, campaign sizing, pre-registration | 3–4 days | Paper 1 campaign |

Roughly **three to four weeks of tooling and pilot work**, not counting committee time and not counting the campaigns themselves, which are sized in Part I §12 and are where the real elapsed time sits. The reduction from v12's four-to-five-week estimate reflects the removal of E-code tasks (detector implementation, baseline-exclusion lists, E4 lexical criterion, and the full pitfall-overlap audit). Items 1–5 are parallelisable (item 5 depends on 3). Items 8 and 11–13 can run in parallel with the Paper 1 campaign. The critical path is item 6 → item 7 → item 14: the generation pipeline gates the pilot, the pilot gates the round count and the MDE, and both gate the pre-registration that the main campaign should not start without.
