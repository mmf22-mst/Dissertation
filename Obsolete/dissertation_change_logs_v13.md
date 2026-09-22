# Dissertation Overview and Paper Outlines — Change Logs

Archival change logs for the dissertation overview document. These were extracted from **dissertation_overview_and_paper_outlines_v13.md** to keep the design document focused on the current design. The two files are paired: this log is not valid against a different revision of the overview.

---

### Revision 13 change log

E-code simplification. The primary audience is the manufacturing engineering community, not the ontology engineering community; no committee members are ontology specialists; and the six E-codes operated only on B1 and B2 (40 of 60 ontologies) while ontology evaluation is not the dissertation's point — downstream RCA performance is. The open checklist items for the E-code apparatus (baseline-exclusion lists, E4 lexical criterion, full pitfall-overlap audit) represented 7–12 days of pre-campaign work.

1. **All six Tier A/B E-codes (E1–E6 in the current scheme) are removed from the design.** Along with them: the source-linked codebook as a governing document, the three B2 baseline-exclusion lists, the scoring-layer apparatus (union scoring, common-inventory contrast, Table 0.2b diff, indicators I4 and I5), rules R1–R9, descriptive indicators I1–I5, the codebook crosswalk, the three-family structure, and the sensitivity-ceiling analysis.
2. **Two SPARQL-based alignment-rate manipulation checks replace the E-codes** (new §5.3). BFO-only alignment rate and IOF alignment rate, with a priority-based partition rule: for each domain class, walk the asserted `rdfs:subClassOf` chain upward — IOF-aligned if the chain reaches an IOF Core class before a bare BFO class, BFO-only-aligned if it reaches BFO without passing through IOF, unaligned if neither. The three categories partition domain classes exhaustively. Expected pattern: B0 (≈ all unaligned), B1 (high BFO-only, ≈ 0 IOF), B2 (low BFO-only, high IOF). Both rates are coupled through the conformance channel; R0 is the clean check.
3. **The scope limit is stated explicitly.** Alignment rates measure vocabulary presence, not correctness. A high rate is compatible with category misuse. Any condition-linked misuse effect is invisible in Paper 1 and becomes visible only downstream in Papers 2 and 3.
4. **The pitfall-overlap audit is simplified** to OOPS!-to-OntoQA only. The v12 audit mapped OOPS! pitfalls against E-codes and OntoQA metrics; without E-codes, the mapping is against OntoQA only.
5. **RQ2.4's structural quality vector is now grounding-agnostic predictors only**, estimable on all 60 ontologies. The reduced-sample BFO-specific arm (40 ontologies) is removed.
6. **Paper 1 §3 (BFO-grounded modelling checks) is deleted.** The derivation, codebook, scoring layers, verified reference figures, and release reconciliation are all removed. Paper 1's evaluation battery (now §3, renumbered from §4) gains a manipulation-checks subsection (§3.6) referencing the Part I definition.
7. **Paper 2 §5.4 (calibration rationale) is reworded.** The old version cited Tier A/B validation; the new version says Paper 1 uses only established tools and corpus-grounded measures requiring no empirical calibration.
8. **H1a and H1c lose the "BFO-specific scope" arm.** Both are now tested on grounding-agnostic instruments across all three levels only. H1c's contrast simplifies to (B2 − B0 | D0) − (B2 − B0 | D1); the former (B2 − B1 | D0) − (B2 − B1 | D1) arm on the BFO-specific scope is removed.
9. **The held-out instrument set simplifies** to CQ answerability, salient-term coverage, genre coverage balance, and OntoQA structural profile. No E-codes.
10. **Integration-loss descriptives simplify** to grounding-agnostic instruments only. The per-code sub-ontology closure analysis (E2 inflated pre-merge, E3 partially affected, etc.) is removed.
11. **Paper 1 loop-coupled trajectories** drop E1 and E3 from the list, retaining consistency, unsatisfiable-class rate, OWL 2 DL conformance, OOPS! pitfall counts, and the two alignment rates.
12. **Shared research assets** drop the six detectors (old item 5), the three baseline-exclusion lists (old item 6), and the source-linked codebook (old item 7). The two alignment-rate queries are added (new item 5). The pinned-release set is simplified (no scoring-layer framing, no axiom-level diff requirement).
13. **Contributions** drop "Six BFO-grounded checks in two tiers" (old contribution 3) and edit the battery contribution to name the two-dimensional alignment-rate manipulation check. Released artefacts drop detectors and codebook.
14. **Cross-cutting risks** drop six E-code-specific rows and add two alignment-rate-specific rows.
15. **The portability claim** drops "BFO-general" detectors. All instruments are domain-general by construction.
16. **The codebook is retained in the project archive** for possible separate publication or reinstatement. Paper 3 §10.3 names BFO-specific modelling checks as a separate future instrument publication.
17. **The todo list** drops three tasks (E4 lexical criterion, six detectors, three baseline-exclusion lists), closes five codebook checklist items, simplifies the pitfall-overlap audit, and reduces the estimated pre-campaign tooling from four-to-five weeks to three-to-four weeks.
18. **No hypotheses, factors, research questions, or other instruments changed** beyond the scope reductions in items 8–11 above.

### Revision 12 change log

Paired with **codebook v12**; the two documents move together and neither is valid against an earlier version of the other.

1. **The E5 "below *entity*" extension is withdrawn.** Codebook checklist item 14 had already settled this: ISO/IEC 21838-2's 4.6.2 clause is split, with "below *entity*" reported exactly as descriptive indicator **I3** and "lowest suitable level" left unoperationalised, because IOF itself places `ProcessCharacteristic` directly under `continuant` and a strict reading would penalise B2 for following IOF style. Folding I3 into E5 would have fused a conformance count with a different phenomenon, changed E5's denominator, and promoted into a primary outcome a quantity deliberately kept descriptive. E5 returns to its v11.2 scope.
2. **The single common detector layer is replaced.** Codebook Table 0.2b establishes by direct file diff that classic `bfo.owl` differs from `bfo-core.owl` by exactly 24 relations, all "at all times", "proper" or "some time proper" variants — additive, not contradictory. That bounds the confound the common-layer rule was introduced to remove. B2 artefacts are therefore scored against the union (classic `bfo.owl` + IOF Core), which catches real violations on those 24 relations, while indicator **I5** keeps the B1-versus-B2 contrast on the common inventory. The pre-campaign diff this revision previously commissioned is already done and is cited rather than repeated.
3. **R1–R9 replace CR1–CR4 as the single rule scheme.** The codebook is the authority. R2 is the former CR1, R3 the former CR2, R6 the former CR3, R7 the former CR4. Two rules the overview lacked are now in force: **R1** (condition-invariant eligibility — eligibility predicates evaluable identically on B1 and B2, IOF signals permitted in detectors but never in eligibility, and B2 rates reported with and without any IOF detection aid) and **R5** (discrimination check). R8 (loop status) and R9 (sub-ontology closure) are new in codebook v12.
4. **R5 applies to a primary outcome.** Any code whose positive rate exceeds 95% or falls below 5% of eligible sites in every condition is reported descriptively and excluded from inferential comparison. The codebook names current E2 as most at risk, and E2 is on the primary outcome list; the exclusion rule is pre-registered rather than decided after seeing the rates.
5. **Baseline-exclusion lists are required for three codes, not one:** current E3 (Table 0.2b scope), E5 (`BFO_0000144` term and its axioms) and E6 (asserted hierarchy). Without them IOF's own content produces systematic false positives before any generator acts.
6. **Integration loss is interpretable code by code, not in aggregate.** Under R9, a code whose eligibility is not closed within a sub-ontology cannot be read pre-merge. Current E2 is the clear case: a bearer may sit in another genre's sub-ontology, so pre-merge E2 is inflated and integration loss would read negative for reasons unrelated to merge quality. Salient-term coverage has the same problem and is scored against the relevant genre's inventory, not the whole corpus.
7. **Descriptive indicators are I1–I5**, renamed from D1–D5 to stop colliding with Factor D's levels.
8. **No hypotheses, factors, or instruments changed.**

### Revision 11.4 change log

1. **D1 iterates the sub-ontologies, with a fresh integration each round.** The previous protocol iterated the integrated artefact, which cancelled the decomposition manipulation after R0: once merged, a D1 artefact is the same size as a D0 artefact and runs under the same windowing rule, so the smaller-scope advantage H1f is built on existed for one round out of ten. Under the revised protocol it is live across the whole trajectory.
2. **Integration is anchored, not rebuilt.** Each round's merge is applied as a patch to the previous round's integrated artefact rather than reconstructed from the sub-ontologies alone. Unanchored re-integration would let merge variance masquerade as trajectory movement, which would damage H1f specifically.
3. **Feedback is computed on the integrated artefact and routed** (Paper 1 §5.4a). Single-sub-ontology defects route to that sub-ontology; cross-sub-ontology and merge-created defects route to the integration step, which therefore has its own feedback section and prompt. Computing feedback per sub-ontology in isolation would be blind to exactly the defects decomposition causes.
4. **Round is no longer a matched unit of work across D**, and the document now says so. A D1 round costs roughly *G* sub-ontology calls plus one integration call against D0's one. Convergence is therefore reported against cumulative tokens as well as against round index, and the cost-adjusted comparison (§7.14) becomes load-bearing for H1f rather than supplementary. Per-round feedback volume diverges across D too and is logged alongside the B-side asymmetry.
5. **New descriptives:** integration loss (the battery delta between the union of sub-ontologies and the merged artefact), merge churn per round, IRI stability across rounds, and the defect-routing split between sub-ontology and integration.
6. **A pilot decision rule is pre-registered** for R0 merge churn: low churn means the merge is largely mechanical and anchoring is belt-and-braces; high churn means anchoring is mandatory and the integration feedback channel is doing real work. The threshold that separates "low" from "high" is set from the pilot data itself, since no prior work provides a baseline.
7. **Paper 2 is unaffected:** population still runs from integrated artefacts at every round state.

### Revision 11.3 change log

1. **The generation prompt is decomposed into three separately pinned allotments** (§5.2): the Factor B injection, the window onto the accumulated artefact, and the corpus chunk. Only the first varies with B.
2. **Chunk and window allotments are fixed at values that fit under B2**, the largest injection, and reused unchanged for B1 and B0. Corpus exposure per call, number of accumulation steps, artefact visibility, and windowing frequency are therefore identical across grounding levels by construction rather than approximately equal by accident.
3. **This removes an asymmetry the shared-budget formulation created.** Under a single shared budget, B2's injection would eat into the window, so B2 would hit degraded views earlier and more often than B0 — a mechanism that could suppress B2 quality and mask the very grounding effect the design tests.
4. **Total prompt length is still not equalised, and padding is still declined.** With allotments fixed, the residual length difference across B is exactly the treatment: B2's prompt is longer because it contains IOF Core. The only live concern is attention dilution over a longer prompt, which filler would worsen rather than mitigate. Recorded as a stated limit, not a mitigated one.
5. **Consequences accepted:** every condition runs at B2's chunk count, so the Paper 1 campaign is sized by the worst case (§12); the two allotments join the similarity threshold and fan-out cap as manifest-pinned parameters set before the pilot.
6. **No hypotheses, factors, or instruments changed.**

### Revision 11.2 change log

1. **Corpus presentation order is held constant across D within a seed.** D0 receives documents in the same genre-blocked order D1 processes them in. This removes presentation order as a confound of the D contrast, at the price of narrowing the estimand: see the new *What the D contrast estimates* paragraph in §4.
2. **Chunk boundaries under D0 are genre-blind.** The corpus is chunked by token budget over the concatenated stream, so boundary chunks may straddle genres. Aligning boundaries to genre would make D0 into D1 with the partition removed, which is further from the decision being studied. Straddling-chunk counts are reported.
3. **Context overflow is handled by deterministic windowing at both D levels** (§4, new *Context-overflow policy*). The accumulated artefact eventually exceeds the prompt budget under D0 and during D1's integration pass; the selection rule, the edit-merge semantics it requires, and the visibility statistics to report are all specified.
4. **Position-gradient descriptives added.** Per-genre coverage by processing position, and the count of chunks processed under a degraded (windowed) view by position and genre. Under genre-blocked order, degradation lands disproportionately on the last genre in the sequence, so this is reported rather than assumed away.
5. **S-GEN now varies genre processing order across seeds** while holding it identical between D0 and D1 within a seed, so that which genre goes last is averaged over rather than fixed.
6. **A D0-shuffled ancillary arm is added** (Paper 1 §8.5) to bound how much of any D effect is ordering rather than partition.
7. **No hypotheses, factors, or instruments changed.** Chunk size and count remain manifest-recorded quantities, pending the genre and context-window figures.

### Revision 11.1 change log

1. **OOPS! stays in the feedback payload.** Revision 11 removed it to protect it as a held-out outcome. That was an over-correction. A practitioner building an ontology this way would use every free automated signal available, and withholding one means Papers 2 and 3 inherit artefacts deliberately worse than best practice — which lowers the ceiling on the downstream results the dissertation exists to measure. Loop realism is an external-validity asset, and the cost of coupling is narrow: OOPS! was already a secondary outcome, and the primary held-out set (CQ answerability, salient-term coverage, genre coverage balance) is untouched.
2. **OOPS! is reclassified as loop-coupled** in §5.5, §5.7, §6.3 and Paper 1 §5.4. Confirmatory at R0; reported for R1–R9 as compliance evidence — did the model fix what it was told to fix — rather than as evidence of quality improvement under H1d–H1f.
3. **A pitfall-overlap audit is added** (§5.7, Parts V and VI). Several OOPS! pitfalls sit close to held-out instruments: missing domain and range declarations against E3, undeclared equivalent classes against E6, missing disjointness against E1, and several structural pitfalls against the OntoQA profile. Where a fed-back pitfall would mechanically change a held-out measure, that measure is silently coupled. The catalogue is walked once against the six codes and the OntoQA metrics, the mapping is recorded in the codebook, and any pitfall found to overlap is suppressed from the fed-back report rather than the whole instrument being reclassified.
4. **No hypotheses, factors, or other instruments changed.**

### Revision 11 change log

1. **Loop-coupled instruments are identified and quarantined (new §5.7).** Two battery instruments were inside the iteration feedback loop while also serving as outcomes: reasoner consistency/satisfiability and OOPS! pitfall counts. *(Superseded in 11.1: OOPS! is retained in the loop and classified as coupled. The rest of this entry stands.)* The reasoner report and the OWL 2 DL profile report remain in the loop because they are the corrective signal iteration is built on. Consequently the reasoner-derived measures — global consistency, unsatisfiable-class count, E1, E3 — and OWL 2 DL conformance are **confirmatory at R0 only** and are reported as loop-coupled process measures for R1–R9. The claim that no outcome instrument enters the loop is withdrawn; the honest version is that the coupling is declared, bounded, and analysed.
2. **The feedback-channel confound with H1e is addressed (Paper 1 §5.4, §8.3).** Conformance-report content increases monotonically with grounding level, so faster convergence under B2 was predicted by the manipulation and by feedback volume alike. Feedback payload tokens and flagged-item counts are now logged per round per condition and carried as a covariate, and a conformance-channel ablation is added as a pre-registered ancillary arm.
3. **A single common detector layer is adopted (§3.5).** All artefacts, in every condition, are scored against `bfo-core.owl` (BFO 2020). The classic build imported by IOF Core 202603 is used as B2 injection material only, never as a scoring layer. An axiom-level diff between the two builds is run pre-campaign and reported.
4. **The E5 B2 baseline-exclusion list is promoted from an implied asset to a required one** (§5.3, §8, Parts V and VI). Without it, IOF Core's own vocabulary produces a systematic E5 false positive in every B2 artefact, independent of generator behaviour.
5. **Rate denominators and exposure offsets are specified.** A fourth counting rule, CR4, fixes the denominator for every code; count models carry a `log(size)` offset. Outcome terminology is standardised on *detection rate*.
6. **Per-code B1/B2 eligibility is made explicit** as a column in the §5.3 table rather than a flat "B1, B2" scope.
7. **D0 and D1 are specified.** D0 is sequential accumulation over order-determined chunks, not a literal single pass; the D contrast is therefore order-determined versus genre-determined partitioning, and is stated as such. Under D1, sub-ontology generation and integration together constitute R0; all nine feedback rounds are applied to the integrated artefact, so R means the same thing at both D levels.
8. **H1d–H1f are respecified as fitted-parameter hypotheses** (§6.5, §6.6). A three-parameter asymptotic regression is fitted per run; the rate constant and asymptote are the estimands compared across conditions. The polynomial B×R and D×R interaction terms are retained as a secondary specification.
9. **H1c's contrast is given explicitly** rather than described as "simple effects of B within each D level."
10. **Co-occurrence-anomalous entailments are demoted to exploratory** and the undefined "logical soundness composite" is dissolved into its named components.
11. **Community-structure instruments are tightened:** AMI replaces NMI, a resolution profile replaces a single CPM score, and the node-level genre-label rule is specified.
12. **Consensus induction is made leave-one-out** and per-condition consensus is reported alongside the pooled consensus.
13. **Campaign sizing (new Part I §12), a pre-campaign pilot (Part VI item 1), and a committee milestone (Part VI item 0) are added.** The former "two to three weeks" figure covered tooling only and is relabelled as such.
14. **Housekeeping:** an old→new E-code crosswalk is added (§5.3); the stale downstream "SHACL violations" mitigation in §11 is corrected; shared assets are renumbered; the thesis statement's portability claim is aligned with what the design tests; E5's scope is extended to cover direct attachment below `entity` (ISO/IEC 21838-2, 4.6.2); the E1/E3 sensitivity ceiling is stated numerically; missing citations added.

*Revisions 5 through 7 use the pre-renumbering E-code labels (E1, E3, E5, E7, E9, E11). The crosswalk in the codebook §0.01 maps them to the current E1–E6.*

### Revision 10 change log

1. **H2 updated.** Removed stale "SHACL violation rate" and "process-constraint satisfaction" (artefacts of the pre-v9 process-awareness formalism). Replaced with "post-population reasoner-inconsistency rate" and "community structure (CPM score and genre-aligned NMI)" to match the current Paper 2 design.
2. **Paper 3 working title updated.** "Process-Aware" replaced with "LLM-Populated" to reflect the removal of the process-awareness formalism in Revision 9.
3. **E-code table (§5.3) reordered** from tier-first (E1, E3, E2, E4, E5, E6) to sequential-by-family (E1, E2, E3, E4, E5, E6), matching the family grouping used in §5.3's prose.
4. **Contribution 4 (process-awareness formalism as future work) removed from the numbered contributions list** and restated as a future-work sentence below the list. Remaining contributions renumbered 1–5.
5. **Feedback-design paragraph (Paper 1 §5.4) expanded** to clarify what the IOF conformance report contains for B0 (trivially empty) and B1 (BFO alignment only), confirming that prompt structure is identical across all three grounding levels.
6. **Paper 2 §4.6 (defensive early-round handling) expanded** to note that community-structure instruments may produce degenerate outputs on near-empty KGs, treated as floor values alongside fidelity floors.
7. **"Seven of eight families" (§5.5) replaced** with "All families except the BFO-specific checks" to avoid a fragile count.
8. **Part V and Part VI updated** to include two missing implementation tasks: co-occurrence-anomalous entailment scoring (Paper 1) and the community-structure pipeline (Paper 2). Sequencing table renumbered accordingly.
9. **No hypotheses, research questions, or design decisions changed.**

### Revision 9 change log

1. **The process-awareness formalism is removed from Paper 2** and deferred as a candidate follow-on research line: representing and validating part-specific routing order and defect-propagation asymmetry is a separate contribution from measuring whether construction strategy affects population fidelity. Its SHACL encoding, the two process-constraint violation-rate metrics it fed, and its dedicated background/method sections are removed.
2. **RQ2.4 is recast**, not dropped: instead of measuring process-constraint violations, it uses reasoner-flagged inconsistency of the populated KG against its own generating ontology — an instrument the population pipeline already runs, requiring no authored construct.
3. **A knowledge-graph community-structure thread is added**, folded into the existing fidelity battery under RQ2.1–2.3 rather than run as a new RQ or a separate sweep of clustering techniques. Leiden community detection, applied uniformly to every populated KG, optimising the Constant Potts Model (CPM) as the primary objective function — chosen over standard modularity because CPM does not have modularity's resolution limit, which matters here since B and D already change graph size and density. Genre-aligned NMI is added alongside CPM to test whether D1's per-genre construction leaves a genre-aligned community signature. Yield is carried as a covariate throughout.
4. **Standard modularity is retained as an ancillary, non-confirmatory comparison against CPM** (new §7.3 in Paper 2), correlated against graph density and yield: divergence that tracks density corroborates the resolution-limit concern; agreement is reported as robustness to objective-function choice.
5. **Heterogeneous/multi-relational community-detection methods are considered and declined**, with the rationale recorded in the method section: that literature is real but immature relative to Leiden/Louvain/Infomap, with no consolidated, published-and-validated standard comparable to this dissertation's other instruments — adopting one would reintroduce the kind of bespoke, under-validated apparatus the evaluation battery has been actively simplified away from (V1–V5, Tier C, and now the process-awareness formalism).
6. **Contributions list (Part I §10) updated**: the process-awareness formalism is removed as a numbered contribution and named as future work instead; community-structure measurement is folded into the existing evaluation-battery contribution rather than listed separately, since it is an instrument, not a new methodological claim.
7. **Places changed:** Part I preamble, §3 (pipeline table), §10 (Contributions); Part III §§1–9 in full.

### Revision 8 change log (summary)

Presentation-only pass: the body text was rewritten to present the current design directly, without comparative "changed from prior revision" language inline; no content, hypotheses, or design decisions changed. Superseded by Revision 9's substantive changes but noted for the archival record.

### Revision 7 change log

1. **The evaluation battery is simplified.** The E1–E11 detector suite is reduced to six formally decidable codes: Tier A (E1, E5) and Tier B (E3, E7, E9, E11). The five Tier C codes (E2, E4, E6, E8, E10) are removed because they required heuristic or judge-based detection and the full V2–V5 validation apparatus. The grounding-agnostic instruments — salient-term coverage, CQ answerability, structural profile, OOPS! pitfall counts, OWL 2 DL conformance, logical consistency — are retained and are now the primary battery rather than a convergent check for a detector suite.
2. **V1–V5 are removed in their entirety.** Tier A codes are validated by the reasoner (detector and oracle are the same); Tier B codes are validated by their SHACL/SPARQL formalisation. No heuristic codes remain, so no empirical calibration is needed.
3. **The CQ generator is replaced by a hand-authored CQ set** (50–100 questions with automated SPARQL scoring). The genre-templated generator is deferred as future work.
4. **E4's focal-code role is relocated to Paper 2**, where its consequence — process-backbone corruption — is measured directly as SHACL constraint violations on the populated KG. RQ2.4 is reframed from "E4 incidence predicts violations" to "Paper 1 structural quality predicts violations."
5. **Iteration round (R) is promoted from an ancillary study to a primary within-subject analysis dimension.** The evaluation battery is run at each of the ten ontology states per run (rounds 0–9), giving 600 evaluated ontology-states. Round threads through all three papers: Paper 1 analyses convergence trajectories and over-iteration degradation; Paper 2 populates KGs from all 600 states; Paper 3 Stage 2 uses four checkpoint rounds (0, 3, 6, 9) crossed with the six B×D conditions and the active retrieval factors.
6. **Paper 1 gains iteration-trajectory hypotheses.** H1d: quality improves with iteration (round main effect). H1e: grounding changes the convergence rate (B×R interaction). H1f: decomposition changes the convergence rate (D×R interaction). B×D×R is exploratory.
7. **Paper 2 is expanded** to include round as a within-subject factor. The statistical model gains B×R, D×R, and round main-effect terms.
8. **Paper 3 Stage 2 uses four checkpoint rounds** (0, 3, 6, 9) rather than all ten, keeping the DoE tractable. The longitudinal mediation analysis (RQ3.4 extended) is treated as an ancillary analysis.
9. **Appendix A (criterion validation framework) is removed.** No Tier C codes remain to trigger it.
10. **Places changed:** Part I §4, §6, §6.3, §6.3a, §6.4, §6.5, §6.6 (removed), §6.7, §7, §9, §10, §11, §12; Part II §§1–11; Part III §§4–7; Part IV §§4–7; Parts V and VI; Appendix A removed.

### Revision 6 change log (summary)

The V2 clean seeds were pinned from the IOF release 202603; the style renderer was automated; specificity became apparent specificity. These changes are superseded by the removal of V2 in Revision 7 but are noted for the archival record.

### Revision 5 change log (summary)

The taxonomy was finalised at eleven codes in three families; V1 triage was completed; the first-order test-theory package was built; six counting rules and five descriptive indicators were specified. The codebook, provenance review, and test-theory package remain in the project archive. The six codes retained in the current design carry their Revision 5 provenance.
