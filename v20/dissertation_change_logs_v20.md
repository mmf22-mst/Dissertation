# Dissertation Change Logs — Revision 20

*This file holds the v20 entry. Append it after the v19.1 entry in the change-log archive (entries for v9–v19.1); the overview body carries no revision history.*

---

## Revision 20 — Committee-facing Part I, corpus and compute caps, instrument fixes

**Governing documents:** dissertation_overview_and_paper_outlines_v20.md and dissertation_todo_v20.md supersede v19.1. Factor structure (3×2×10), scale (60 ontologies, 600 states, 240 checkpoint KGs), hypotheses and primary outcome are unchanged. All v16–v19 specification documents remain valid; two implementation notes below.

### Context

v20 implements the eight items recorded in the v19.1 todo under "Open from the v19.1 review". They fall into three groups: fixes to instruments that would otherwise have carried a validity problem into the campaign (label matching, coverage counting, exemplars); caps on Paper 2–3 compute that make the MVP runnable on the pinned platform (population sample, triple verification, reasoner checking, Paper 3 configurations and benchmark size, sub-ontology battery, pilot seeds); and a restructuring of Part I for a committee with no ontology specialists.

### Design changes

**CQ label normalisation (Part I §6.2(c); Paper 1 §9).** Before scoring, every entity in the evaluated ontology receives a normalised scoring label — CamelCase and underscores split, lower-cased, punctuation stripped, whitespace collapsed, head noun singularised — and the CQ patterns match against it. The artefact is not modified. The rule is pinned before the CQ set is frozen, and the share of hits that arrive only through normalisation is reported per condition. *Reason:* B0 and B2 ontologies use different labelling conventions, so an unnormalised pattern would make part of any grounding effect on the primary outcome a labelling artefact. The calibration's synonym expansions are unchanged.

**Coverage counts entity labels only (Part I §6.2(a)).** "Definitional element" is removed from the coverage definition. A term inside a definition text does not count. *Reason:* under coupling a definition mention is a costless way to satisfy a "missing term" report and gives the KG nothing to populate against. This matches what `salient_term_pipeline.py` already does (label matching only); the overview had been broader than the code.

**No few-shot exemplars (Paper 1 §4.2, §4.5.1).** The prompts contain none — confirmed against `prompt.py` — so the stale "few-shot exemplar selection" is removed from what S-GEN governs, and §4.2 states that the Factor B injection is the only vocabulary the generator receives beyond the corpus and the feedback.

**Population sample fixed at *T*<sub>A</sub> (Part I §8, §12).** *T*<sub>B</sub> = *T*<sub>A</sub>, same square-root allocation and floor. The "up to the full remainder" option moves to future work (already listed in Paper 3 §10.3). *Reason:* triple verification and reasoner checking do not scale to it, and deployment scale is a separable question.

**Sampled triple verification (Paper 2 §5.1, §9; Part I §12).** Entailment-verified precision is estimated on a stratified random sample of *n* = 2,000 triples per KG (proportional by source genre; every triple if fewer), with a Wilson interval. Half-width ≈ ±2 points at 80% precision. 480,000 verifications in total instead of a count that scaled with yield. Sampling seed under S-HAR.

**Reasoner-scalability contingency (Paper 2 §4.4, §9).** The validation pass runs under a pinned per-KG timeout. If the OWL 2 DL reasoner times out on any KG, every KG in the campaign is checked instead with an OWL 2 RL rule-based consistency check (sound, incomplete: disjointness, domain/range, functional-property and type clashes). Uniform substitution keeps the instrument identical across cells; the instrument used and the DL completion rate are reported.

**Paper 3 sizing (Paper 3 §3.4, §5.2; Part I §12).** Two retained retrieval factors (four configurations) is the Stage 2 default; a third is added only if the pilot's cost per RCA run leaves headroom, decided before Stage 1. Benchmark target ~200 items with a floor of 150: ~120 mined (Source A) and ~80 synthetic (Source B), stratified by hop distance and genre pair; composition pre-registered before the Paper 1 campaign. Indicative Stage 2 load ≈ 192,000 RCA runs plus ≈ 48,000 for the retrieval-ablated control.

**D1 sub-ontology battery at checkpoints (Part I §5, §12; Paper 1 §5.3, §6.15).** 720 sub-ontology battery runs (30 × 4 × 6) instead of 1,800. Integration loss is descriptive and is reported at the checkpoint rounds; the delta rate and IRI stability, which need no battery run, are still computed every round.

**Pilot on four seeds (Part I §5, §11; Paper 1 §5.4).** Four seeds × two conditions × R = 15, so the variance the MDE calculation uses has more than one degree of freedom.

**Part I restructured for the committee.**
- **§3 is now "What each result would tell a manufacturing engineer":** a four-row decision table (B, D, R, and the interactions) reading each choice against a real effect, a null, and what the engineer does with either — followed by one paragraph on why a null at every stage is the cheapest practical outcome and how the design keeps that reading available.
- **The CCO argument** moves to a paragraph under Factor B in §5, with the full case (renderer counts, allotment, why raising the allotment was rejected) in new Appendix A.4. Paper 1 §2.3 now points there.
- **Jargon:** "realist foundations" → "standards-based foundations"; "realist structure" → "BFO- or IOF-style structure"; the continuant example in §6.3 glossed in plain words; "punning" and "sequential ignorability" glossed inline. Glossary gains Mediation, Punning, OWL 2 RL and Wilson interval.
- Section numbering of Part I is unchanged, so no cross-references moved.

### Implementation notes

- `cq_calibrate.py` / battery CQ scoring: add the scoring-copy normalised label and point the regexes at it (task 1, step 5).
- Orchestrator: run the sub-ontology battery only at checkpoint rounds (task 4).
- Population pipeline: stratified triple sampler; validation pass with timeout and OWL 2 RL fallback (task 9).

### Todo changes

- "Open from the v19.1 review" section closed into "Closed in v20".
- Task 0c: *T*<sub>B</sub> = *T*<sub>A</sub>. Task 1: new step 5 (normalisation rule). Task 4: checkpoint-only sub-ontology battery; entity-label coverage confirmation; manifest records no exemplars. Task 5: four seeds. Task 9: sampler, timeout, fallback; effort 4–6 days (was 3–5). Task 10a: fix the mined-item count against the target and floor. Task 12: four-seed variance. Task 13: two-factor default. Task 15: normalisation rule, *n*, timeout and fallback, benchmark target and floor, two-factor default added to the pre-registration list.
