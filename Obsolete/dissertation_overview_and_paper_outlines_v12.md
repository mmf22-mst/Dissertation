# Dissertation Overview and Paper Outlines

**Revision 12 — validity pass: loop-coupled instruments identified and quarantined; feedback-channel confound with H1e addressed; a single common detector layer adopted for E-code scoring; the E5 B2 baseline-exclusion list promoted to a required asset; rate denominators and exposure offsets specified; D0 chunking and D1 iteration protocol specified; convergence hypotheses respecified as fitted rate parameters; community-structure instruments tightened (AMI, resolution profile, node genre-label rule); campaign sizing, a pilot, and a codebook crosswalk added. Point revision 11.1: OOPS! is retained in the feedback loop and classified as coupled rather than removed, with a pitfall-overlap audit added. point revision 11.2: corpus presentation order held constant across D, chunk boundaries genre-blind under D0, deterministic windowing adopted as the context-overflow policy at both D levels, position-gradient descriptives and a D0-shuffled ancillary arm added. Point revision 11.3: the prompt is decomposed into three separately pinned allotments so that corpus exposure and artefact visibility are identical across grounding levels. Point revision 11.4: D1 iteration moved onto the sub-ontologies with anchored re-integration each round, defect routing specified, integration-loss and merge-churn descriptives added. Revision 12: reconciled against codebook v12 — the E5 scope extension withdrawn, the common-detector-layer rule replaced by union scoring with a common-inventory contrast, R1–R9 adopted as the single rule scheme, the discrimination check imported, baseline exclusions widened to three codes**


*Body text presents the current design without backward references to prior revisions. Change logs are in the companion file **dissertation_change_logs_v12.md**.*

The evaluation architecture is fully automated and reference-free. No gold reference ontology, no hand-annotated triple sample, and no expert-adjudicated root cause benchmark. Instruments are either established tools with published validation (OOPS!, OWL reasoners, OntoQA-family structural metrics), formally decidable checks against BFO 2020 (Tier A and B codes), or corpus-grounded coverage measures. The human contribution is scholarship — the source-linked codebook derivation and the hand-authored competency question set — performed once and independent of the number of experimental runs.

---

## Part I — Dissertation Overview

### 1. Problem statement

Manufacturing organisations hold most of their process knowledge in unstructured documents: requirements, work instructions, process maps, FMEAs, manufacturing records, and quality reports. Turning that corpus into a machine-reasonable asset requires an ontology, a populated knowledge graph, and a retrieval mechanism capable of answering causal questions over both. Large language models have made the first two steps tractable at a cost that was previously prohibitive, but the field has no settled account of *how* an LLM should be directed to build such an ontology, and no evidence that the choice matters downstream.

Two candidate levers dominate the practitioner's decision:

- **What ontological scaffolding is supplied.** Hand the model nothing and it produces a flat, term-driven artefact. Hand it BFO and it inherits a realist upper structure. Hand it IOF Core and it inherits both BFO and a manufacturing-tuned mid-level vocabulary.
- **How the corpus is decomposed.** Process the whole corpus in one pass, or partition it by document genre, build a sub-ontology per genre, and integrate.

These are usually discussed as if they were the same choice, or as if one obviously subsumes the other. They are neither. This dissertation crosses them.

A third lever sits underneath both: **how many rounds of evidence-driven iteration the LLM performs**, and whether the payoff of additional rounds depends on the grounding and decomposition choices. The dissertation measures this by evaluating every intermediate ontology state, not only the final product.

### 2. Thesis statement

Upper-ontology grounding, corpus decomposition, and iteration depth are separable design choices in LLM-driven ontology construction; their effects persist through knowledge graph population and remain measurable in retrieval-augmented root cause analysis accuracy — and all three can be measured by automated, corpus-grounded instruments that require no reference ontology, no hand-annotated triples, and no expert-adjudicated benchmark.

*On portability.* Every instrument except the competency question set is domain-general or BFO-general by construction, which makes redeployment cheap in principle. This dissertation does not demonstrate transfer: it runs on one corpus in one domain. Portability is argued from the construction of the instruments and costed in §9, not evidenced, and the conclusion says so.

### 3. Why CCO is excluded

1. **Sibling, not rung.** IOF Core and CCO are both mid-level ontologies built directly on BFO, not ordered with respect to each other.
2. **No vetted mapping.** Any cross-condition comparison would rest on bridge axioms authored for this study.
3. **Confounded scope.** IOF Core is manufacturing-tuned; CCO is a general enterprise/defence vocabulary.

Noted in each paper as a deliberately excluded robustness arm. Under the automated battery it becomes cheap to add later, which is stated as future work.

### 4. The construct → populate → exploit pipeline

| Stage | Paper | Artefact produced | Question |
|---|---|---|---|
| Construct | 1 | 6 ontology conditions × *k* seeds × 10 round states | Do grounding, decomposition, and iteration change what the LLM builds? |
| Populate | 2 | Populated KGs, one per ontology-state | Do those differences survive population? |
| Exploit | 3 | RCA answers under hybrid GraphRAG retrieval | Do they change answer quality? |

The pipeline is deliberately *narrowing*: each stage risks washing out the upstream signal. Documenting where and whether the signal dies is itself a result, and the design pre-commits to reporting a null at any stage rather than reframing it.

### 5. Unified experimental design

Two crossed between-subject factors and one within-subject factor, held constant across all three papers.

**Factor B — Base ontology grounding (3 levels)**

| Level | Label | Supplied to the generator |
|---|---|---|
| B0 | Ungrounded | No upper or mid-level ontology; instructions on OWL 2 DL syntax only |
| B1 | BFO-grounded | BFO 2020 (ISO/IEC 21838-2) class and relation inventory, with definitions |
| B2 | IOF-grounded | IOF Core (which imports BFO), class and relation inventory, with definitions |

**Factor D — Corpus decomposition (2 levels)**

| Level | Label | Procedure |
|---|---|---|
| D0 | Monolithic | Sequential accumulation into a single ontology over genre-blind chunks of the concatenated corpus, presented in the same genre-blocked order D1 uses |
| D1 | Hierarchical | One sub-ontology per document genre, each built by the same sequential accumulation within its genre, then an integration pass; sub-ontologies persist and are the objects of iteration, with integration re-run each round |

**What the D contrast actually is.** The corpus exceeds any usable context window, so neither level is a literal single-shot generation; both accumulate over chunks. Presentation order is held constant between the two levels within a seed: documents reach the generator genre-blocked in both cases (all of genre 1, then all of genre 2, and so on). What differs is the *partition* — whether the accumulating artefact is one ontology or several that are integrated at the end.

**What the D contrast estimates, given that choice.** Holding order constant removes presentation order as a confound, which is why it is worth doing, but it narrows what D measures. Because D0's documents arrive genre-blocked, D0 already processes one genre at a time; it is genre-*ordered* without being genre-*partitioned*. The remaining manipulation is therefore the explicit partition into separate artefacts plus the integration pass, not genre-awareness in general. That is the practitioner's actual decision, so it is the right estimand — but it biases toward the null relative to a design that also scrambled D0's order, and a flat H1b should be read in that light rather than as evidence that genre-awareness does not matter. §8.5 bounds the difference empirically.

**Chunk boundaries are genre-blind under D0.** The corpus is concatenated in the genre-blocked order and chunked by token budget alone, so boundary chunks may straddle two genres. Aligning boundaries to genre would turn D0 into D1 with the partition removed and push the contrast further from the decision under study. The number of straddling chunks is recorded in the manifest and reported per seed.

**Context-overflow policy (both D levels).** The accumulated D0 ontology grows as it goes, so later chunks are eventually processed against an artefact that no longer fits alongside them; D1's per-genre construction rarely hits this, but its integration pass can. One policy applies to both, chosen because it neither discards structure silently (truncation) nor inserts a second generative step into construction (summarisation):

- **Deterministic windowing.** When the artefact exceeds the pinned window allotment (Paper 1 §5.2), the generator is shown a selected view rather than the whole ontology. Because the window allotment is fixed independently of the Factor B injection, windowing fires at the same artefact size in every grounding condition. The selection rule is fixed and seed-independent: the ancestor closure of every class whose label matches a term in the current chunk above the pinned similarity threshold; then those classes' siblings and direct children up to a fixed fan-out cap; then remaining budget filled in descending match-score order, ties broken by IRI sort. The injected scaffolding for Factor B is not part of the window and is always present in full.
- **Edit-merge semantics.** Because the model sees a subset, its output is applied as a patch against the window, not as a replacement artefact. A regenerated whole ontology from a windowed view would delete everything the model could not see. The patch is validated to touch only entities present in the window or newly introduced.
- **Visibility statistics.** The proportion of the artefact visible at each chunk, and the count of chunks processed under a degraded view, are recorded per run and reported by processing position and by genre. Under genre-blocked order this degradation concentrates on whichever genre is processed last, which is why S-GEN varies genre order across seeds (§6.5.1).

**Integration procedure for D1.** Sub-ontologies are merged by a two-stage procedure fixed in advance: deterministic label normalisation and IRI reconciliation, followed by an LLM-mediated merge pass under the same injection condition as the generation step. LogMap and AML are run over the same inputs as an audit trail, not as the merge mechanism (Paper 1 §8.1). Sub-ontology generation plus integration together constitute the R0 state for D1, so that R0 denotes "the first complete artefact, before any feedback" at both D levels.

**What iterates under D1, and why it is the sub-ontologies.** Under D1 the sub-ontologies persist as first-class artefacts and are the objects of feedback; integration is re-run each round to produce that round's evaluable state. The alternative — iterating the merged artefact and discarding the sub-ontologies after R0 — was specified in earlier revisions and is rejected because it cancels the manipulation. Once merged, a D1 artefact is the same size as a D0 artefact, sits under the same windowing rule, and is seen in the same proportion, so the narrower-scope advantage that H1f attributes to decomposition would exist for one round and be absent for the other nine. Iterating the sub-ontologies keeps decomposition operative across the whole trajectory, which is what the hypothesis is about.

**Anchored re-integration.** Each round's merge is applied as a patch to the previous round's integrated artefact, not rebuilt from the sub-ontologies alone. Rebuilding would make round-to-round differences a mixture of sub-ontology improvement and merge variance: greedy decoding makes the merge deterministic but not stable, and a small change upstream can flip a merge decision, reshuffle IRIs, and relocate or undo structure. Anchoring keeps IRIs stable, keeps trajectories comparable, and stops the merge from being a fresh roll each round. Merge churn and IRI stability are logged per round (§7.3).

**What this costs.** A D1 round is roughly *G* sub-ontology calls plus one integration call, against D0's one call — with six genres, about seven times the per-round compute. Round therefore stops being a matched unit of work across D, and H1f read against round index alone would partly say "D1 converges faster because D1 receives more model calls per round." This is the same shape of confound as the feedback-volume asymmetry across B, and gets the same treatment: per-round cost is logged, convergence is reported against cumulative tokens as well as round index, and the cost-adjusted comparison in Paper 1 §7.14 carries confirmatory weight for H1f rather than serving as a supplementary view. Feedback volume also diverges — *G* reports per round against one — and is logged as a covariate.

**Factor R — Iteration round (10 levels, within-subject)**

| Level | Label | State |
|---|---|---|
| R0 | No iteration | Raw generation output before any feedback |
| R1–R8 | Intermediate rounds | After 1–8 rounds of feedback |
| R9 | Final | After 9 rounds; the terminal ontology state |

The round count is set high enough that the plateau is observable for all conditions, including those that converge slowly, and that over-iteration degradation — if it occurs — is detectable. Where the plateau falls, and whether quality ever declines with further iteration, are themselves dependent variables. The round at which each condition plateaus is not known in advance and is one of the quantities the experiment measures.

R = 9 is currently a judgement, not a result: it replaced an earlier R = 5 that was also a guess. The pre-campaign pilot (Part VI item 1) runs the extreme conditions to R = 15 on two seeds precisely to settle it. If the pilot shows plateaus well before R9, the round count drops and the campaign shrinks; if trajectories are still moving at R9, it rises. The number is confirmed or revised before pre-registration, not defended after the fact.

Round is a within-subject repeated measure: every ontology traverses all ten states in fixed order. R0 is included as a "no iteration" baseline. Instrument measurements at R0 may hit floor or ceiling values for some measures; these are noted rather than excluded, since they establish what iteration buys.

**Cells:** B0D0, B0D1, B1D0, B1D1, B2D0, B2D1 — each at rounds 0–9.

**Blocking:** generation seed, *k* = 10 (settled). Each seed runs through all six cells, giving matched sets and paired contrasts.

**Scale:** 60 terminal ontologies (6 cells × 10 seeds); 600 evaluated ontology-states (60 × 10 rounds); 600 populated KGs. The 600 figure counts the evaluable whole-artefact states, which is what Papers 2 and 3 consume. Under D1 the battery additionally runs over each persisting sub-ontology at each round, to support the integration-loss measure: with *G* genres that is 30 runs × 10 rounds × *G* further battery executions, which affects battery compute but not the number of ontology-states carried downstream. RCA over a screened subset of retrieval configurations using four checkpoint rounds (R0, R3, R6, R9) × 6 conditions = 24 ontology-states per seed.

### 6. The evaluation battery

#### 5.1 Design principle

No reference ontology. The corpus is the ground truth for coverage; established tools and formally decidable checks provide quality measurement; and the downstream papers provide the primary test of the hypothesis. The battery is evaluated at every round state (R0–R9) of every ontology, producing 600 evaluated ontology-states.

#### 5.2 Corpus-grounded coverage

**(a) Salient-term coverage — recall against the source, not against a human artefact.**

The corpus is the ground truth. Salient domain terms are extracted automatically using a combination of statistical termhood scoring (C-value/NC-value, TF-IDF against a general-language background corpus) and embedding-based keyphrase extraction, producing a ranked salient-term inventory per genre. Coverage is the proportion of high-salience corpus terms represented in the ontology as a class, a property, or a definitional element, matched by embedding similarity above a calibrated threshold.

This is more defensible than gold-reference recall, not less: it measures whether the ontology covers what the documents actually talk about, rather than whether it matches what one ontology engineer happened to build.

**(b) Genre coverage balance.** Entropy over per-genre salient-term coverage; targets the predicted D0 failure mode of over-fitting to whichever genre dominates the token budget.

**(c) Competency question answerability.** A hand-authored set of 50–100 competency questions, covering the structurally important questions each document genre should answer (existential, relational, multi-hop, definitional). The final count is set when the CQ set is authored; the range is an estimate, not a commitment, and the binding constraint is adequate stratum coverage across the six genres and four question types rather than a target total. Each CQ is paired with a SPARQL query; answerability is the proportion returning a non-empty result. The CQ set is frozen before any generation run and tagged by question type and genre relevance, so per-stratum answerability is reported alongside the aggregate. This follows standard practice (Grüninger & Fox 1995; Ren et al. 2014; Wiśniewski et al. 2019).

**(d) Consensus induction — agreement as a descriptive measure, never as truth.** A consensus ontology is induced from the terminal (R9) ontologies by majority vote over normalised class and relation labels. Two properties are fixed to keep the measure interpretable:

- *Leave-one-out.* Each ontology is scored against a consensus induced from the other 59, so no artefact contributes to the standard it is measured against.
- *Per-condition alongside pooled.* Because the pool is balanced at ten per cell, a term must appear in at least 31 of 60 artefacts to survive a pooled majority vote, which means pooled consensus membership requires crossing condition boundaries and therefore favours whichever vocabulary convention is most cross-condition-common. Per-condition consensus (majority within each cell) is reported alongside the pooled figure, and the gap between them is itself descriptive of how much the conditions agree.

Cross-condition agreement and consensus recall are reported as *descriptive* structure measures. Consensus is not correctness: shared model bias produces shared errors. Consensus measures are therefore reported alongside, never in place of, corpus-grounded coverage.

#### 5.3 BFO-grounded modelling checks

Six codes, all formally decidable — Tier A (entailment-decidable) or Tier B (constraint-decidable).

| Code | Family | Tier | Eligible | Loop-coupled | What a detection means | Implementation | Denominator (R7) |
|---|---|---|---|---|---|---|---|
| E1 | BFO commitment | A | B1, B2 | **Yes** | Disjoint-category co-subsumption: a class inferred into both branches of a BFO disjoint pair | Reasoner classification against the scoring layer for the condition (§3.5); root unsatisfiable classes counted (R2); per-disjoint-pair breakdown (26 pairs, verified against `bfo-core.owl`) | Classes eligible to fall under a disjoint pair |
| E2 | BFO commitment | B | B1, B2 | No | SDC without bearer: a specifically dependent continuant with no `inheres_in` or `bearer_of` link | SHACL shape or SPARQL `ASK` over asserted + inferred graph | Classes resolving under `specifically dependent continuant` |
| E3 | BFO commitment | A | B1, B2 (B2 requires the baseline-exclusion list; see note) | **Yes** | Relation signature violation: domain, range, or universal-restriction violations on BFO 2020 relations | Reasoner classification; attributed by R3 | Axioms using a signature-bearing BFO relation |
| E4 | Realist practice | B | B1, B2 | No | Universal–particular conflation: individuals used where classes are expected, or vice versa | SHACL shape | Named classes plus named individuals |
| E5 | ISO conformance | B | B1, B2 (B2 requires the baseline-exclusion list) | No | Upper-level tampering and vocabulary fabrication: classes asserted as BFO peers, or novel BFO-namespace terms | SPARQL against the pinned BFO term inventory and, for B2, the IOF Core 202603 baseline-exclusion list. Direct attachment below `entity` is **not** part of this code; it is descriptive indicator I3 (codebook §1.5) | Asserted named classes |
| E6 | ISO conformance | B | B1, B2 (B2 requires the baseline-exclusion list) | No | Multiple asserted parents without defined-class status (ISO/IEC 21838-2, 4.6.2) | SPARQL over the asserted graph, exempting classes carrying an `owl:equivalentClass` definition — the permissive reading, including bare Boolean conjunctions, per codebook §0.00 item 11, with indicator I1 as the safeguard | Asserted named classes that are not defined classes |

**Crosswalk to the pre-renumbering labels.** The six retained codes carry their Revision 5 provenance under their original numbers. Anyone tracing a code to the codebook needs this map:

| Current | Codebook (E1–E10/E11 scheme) | Name |
|---|---|---|
| E1 | E1 | Disjoint-category co-subsumption |
| E2 | E3 | Specifically dependent continuant without bearer |
| E3 | E5 | Core relation signature violation |
| E4 | E7 | Universal–particular conflation |
| E5 | E9 | Upper-level tampering and vocabulary fabrication |
| E6 | E11 | Multiple asserted parents without defined-class status |

The dropped Tier C codes were E2, E4, E6, E8 and E10 in the old scheme. Note the collision hazard: old E4 (*directive content / process conflation*, dropped) is not current E4 (*universal–particular conflation*, retained). The codebook carries this table as its front matter.

**Scoring layers, and how the B1/B2 contrast stays clean.** B1 artefacts are scored against `bfo-core.owl`; B2 artefacts against the union of classic `bfo.owl` and IOF Core 202603, which is what a B2 artefact is entitled to use. Scoring B2 against `bfo-core.owl` alone would silently drop violations on relations B2 legitimately has available. The two builds have been diffed directly (codebook Table 0.2b): they differ by exactly 24 relations, all "at all times", "proper" or "some time proper" variants, so the difference is additive rather than contradictory and its extent is known. The comparison is kept honest not by equalising the scoring layer but by reporting the B1-versus-B2 contrast on the **common inventory** — the 36 shared classes and the Table 0.2 relations — with the full-inventory B2 rate alongside. Descriptive indicator I5 tracks B2-only upper-level term usage so the reader can see how much of B2's activity falls outside the common inventory. Classes unsatisfiable through IOF axioms alone, with no BFO axiom in any justification, are recorded as indicator I4 and kept out of E1 and E3 entirely.

**Sensitivity ceiling, stated numerically.** BFO 2020 asserts disjointness at 26 class pairs across 36 classes, and declares 40 object properties with 28 domain and 31 range axioms. E1 therefore fires only within the deductive closure of those 26 pairs: sibling conflations below that level (a class asserted under both `object` and `object aggregate`, for instance) produce no unsatisfiability and are invisible. E3 is bounded the same way by the relations that actually carry a signature. These are ceilings on sensitivity, not on precision.

**E3's B1/B2 asymmetry.** Both grounded levels are scored against the same BFO relation inventory, but B2 artefacts may also use IOF Core relations, which the common layer does not constrain. E3 rates are therefore comparable across B1 and B2 with respect to BFO relations only; IOF-relation misuse is out of scope and stated as such.

**Tier A** codes are detected by the reasoner; the reasoner is detector and oracle simultaneously. Sensitivity and specificity are not meaningful quantities — the detection *is* the classification result, and what is reported is the reasoner, its version, the axiomatization release, and the classification timeout.

**Tier B** codes are violations of closed constraints whose SHACL or SPARQL expression *is* the code's definition. Precision relative to the constraint is 1.0 by construction. What requires defence is the faithfulness of the formalisation to the BFO commitment it claims to capture, and that is handled by the source-linked codebook rather than by empirical calibration.

**Three families.** Only the BFO-commitment family (E1, E2, E3) is described as detecting BFO modelling error. E4 detects departures from realist modelling principles; E5 and E6 detect ISO conformance violations. Each family is reported separately.

**Scope.** The codes presuppose a BFO commitment to violate and are undefined for B0. The full B0/B1/B2 ordering is carried by the grounding-agnostic instruments and by Papers 2 and 3.

**Content validity.** Each code's derivation from the BFO literature is documented in the source-linked codebook (v12) with a primary-source citation, the formal expression of the violation, the tier assignment, and known limitations. Codes are confirmed against BFO 2020 (not BFO 2.0) and confirmed as axiom violations rather than stylistic preferences.

**Rules.** The codebook is the authority and its numbering is the single scheme; the overview's former CR1–CR4 are retired. In force:

- **R1 — condition-invariant eligibility.** A code's eligibility predicate must be evaluable identically on B1 and B2 using only the artefact's own terms and BFO-level typing. IOF-derived signals may inform detectors, never eligibility, and any code using an IOF detection aid reports B2 rates with and without it as a pre-registered sensitivity analysis. Eligibility that differs by condition is differential error by construction.
- **R2 — root counting** for Tier A codes (formerly CR1).
- **R3 — E1/E3 attribution** (formerly CR2): a root unsatisfiable class is attributed to E3 if any minimal justification contains a domain, range or universal-restriction axiom, otherwise to E1; each root is attributed to exactly one.
- **R5 — discrimination check.** Before any condition comparison uses a code, its positive rate per condition is reported. A code above 95% or below 5% of eligible sites in *every* condition is reported descriptively and excluded from inferential comparison. The codebook names E2 as the code most at risk, and E2 is a primary outcome, so this rule is pre-registered rather than invoked after the fact.
- **R6 — asserted vs inferred graph** stated per code (formerly CR3).
- **R7 — denominators** (formerly CR4): every code is a detection rate over the eligible-site denominator in the table above, never a bare count, with a matching `log(denominator)` offset in the count models.
- **R8 — loop status** and **R9 — sub-ontology closure**: recorded per code in codebook §1.1 and carried into §6.7 and the integration-loss measure respectively.

R4 governs the archived Tier C codes only and is not in force.

R6's asserted-graph reading for E6 is the conservative one: ISO/IEC 21838-2, 4.6.2 b1) speaks of the hierarchy of the resulting ontology, and multiple parents arising only through inference from restrictions arguably violate it too. The asserted-graph reading is chosen because it is the one an ontology author controls directly; the inferred-graph variant is computed and reported as a robustness check.

#### 5.4 Structural and logical quality

- **OWL 2 DL profile conformance:** binary pass/fail plus violation count.
- **Logical consistency and class satisfiability:** reasoner classification; global consistency, unsatisfiable class count, root unsatisfiable class count.
- **Structural profile:** inheritance richness, relationship richness, attribute richness, class count, maximum and mean depth, orphan rate (OntoQA; Tartir et al. 2005).
- **OOPS! pitfall counts:** pitfall counts by severity (critical, important, minor); Poveda-Villalón et al. 2014.
- **Co-occurrence-anomalous entailments (exploratory):** entailed subsumptions between classes whose corpus co-occurrence is at or near zero, flagged as candidate spurious inferences and ranked by anomaly score. This instrument is threshold-dependent and has no oracle, which is exactly the property that disqualified the Tier C codes. It is retained because it is cheap and potentially informative, but it is exploratory only: it is not a confirmatory outcome, no hypothesis is attached to it, and it is reported with its threshold and a sensitivity sweep over that threshold.

#### 5.5 The full instrument inventory

| Family | Instruments | Scope | Loop status |
|---|---|---|---|
| Manipulation check | BFO alignment rate | All levels | Coupled (conformance channel) |
| Corpus grounding | Salient-term coverage; genre coverage balance; CQ answerability | All levels | Held out |
| Logical quality | Consistency; unsatisfiable classes; OWL 2 DL conformance | All levels | **Coupled** |
| Logical quality (exploratory) | Co-occurrence-anomalous entailments | All levels | Held out |
| Structural profile | OntoQA metrics | All levels | Held out |
| Structural profile | OOPS! pitfall counts | All levels | **Coupled** |
| BFO-specific checks | E1 (with per-disjoint-pair breakdown), E3 | B1, B2 | **Coupled** |
| BFO-specific checks | E2, E4, E5, E6 | B1, B2 | Held out |
| Agreement | Pairwise cross-condition similarity; leave-one-out consensus recall (R9 only) | All levels | Held out |
| Cost | Cumulative tokens; wall-clock time; cost per round; feedback payload tokens and flagged-item counts | All levels | n/a |

All families except the BFO-specific checks run across all three grounding levels. The BFO-specific checks are scope-limited to B1 and B2, for the principled reason that they measure conformance to commitments an ungrounded artefact never made.

All instruments except consensus induction are evaluated at every round state (R0–R9). Consensus is computed once from R9 ontologies.

#### 5.6 Limitations of the battery

Six limits, stated plainly and carried into every limitations section:

1. **No correctness anchor.** The battery measures corpus fidelity, logical soundness, structural profile, and formally decidable BFO checks. It cannot certify that an ontology is *right* in a way an expert would endorse. Claims are restated as specific named properties rather than "quality."
2. **The battery detects only formally decidable patterns.** Heuristic modelling errors — such as category conflation, role misassignment, or information/carrier confusion — that are consistent with OWL semantics are outside the battery's scope. If these errors vary systematically across conditions, that variation is invisible in Paper 1 and becomes visible only through downstream measures in Papers 2 and 3.
3. **CQ set is hand-authored and domain-specific.** The 50–100 questions do not transfer to other corpora without re-authoring. They may be shallow or incomplete compared to a machine-generated set of several hundred.
4. **Consensus can launder shared bias.** Mitigated by reporting consensus only as descriptive and alongside corpus-grounded coverage.
5. **OOPS! pitfalls are general-purpose.** They may not capture domain-specific or BFO-specific issues beyond the six codes. They are also fed back, so their trajectory measures compliance rather than unprompted improvement (§6.7).
6. **Part of the battery is coupled to the iteration loop.** See §6.7. For the coupled instruments, improvement across rounds is partly definitional, and only the R0 contrast is a clean between-condition comparison.

#### 5.7 Loop-coupled and held-out instruments

Iteration needs a corrective signal, and any instrument used as that signal cannot also serve as an independent measure of whether iteration worked. Earlier revisions asserted that no outcome instrument entered the loop while feeding back reasoner output and OOPS! reports, both of which were scored as outcomes. That claim is withdrawn. The coupling is instead declared and bounded.

**What is in the loop.** The feedback payload is four items: the reasoner report (global consistency and the list of unsatisfiable classes), the OWL 2 DL profile report, the OOPS! pitfall report, and the conformance report. These are the corrective signal; removing any of them would leave iteration with less to act on and would make H1d uninterpretable in the opposite direction.

**Why OOPS! stays in, given the cost.** Withholding a free, established, automated signal would make the artefacts worse than a competent practitioner would build, and those artefacts are the input to Papers 2 and 3. Since downstream usefulness is what the dissertation is ultimately measuring, depressing artefact quality to protect one secondary Paper 1 outcome is the wrong trade. Loop realism is an external-validity asset: the construction procedure being evaluated should be the one a practitioner would actually run. The accounting below absorbs the cost rather than the design paying it.

**Consequences for inference.** The coupled measures are global consistency, unsatisfiable-class count (and therefore E1), E3, OWL 2 DL conformance, and OOPS! pitfall counts. For these:

- **R0 is clean.** At R0 no feedback has been applied, so R0 values are legitimate confirmatory outcomes for the between-condition hypotheses H1a, H1b and H1c.
- **R1–R9 are not.** Improvement on a coupled instrument across rounds is partly definitional: the model is handed the scorecard. Coupled trajectories are reported as *process* evidence that the loop is doing what it was designed to do, not as confirmatory support for H1d, H1e or H1f.
- **Floor effects are expected and are not findings.** Most artefacts should reach consistency within a few rounds, collapsing variance on the coupled measures. This is anticipated, pre-registered, and reported as a convergence fact rather than analysed as an effect.
- **Confirmatory round-related inference rests on the held-out set:** CQ answerability, salient-term coverage, genre coverage balance, OntoQA structural profile, and E2, E4, E5, E6. The three primary outcomes are all in this set, so the confirmatory core of H1d–H1f is unaffected by the coupling decision.
- **Coupled trajectories are reported as compliance, and that is worth reporting.** "Did the model fix what it was explicitly told to fix, and did compliance differ by condition?" is a real question with a practitioner-relevant answer. It is labelled compliance, not quality improvement, wherever it appears.

**Second-order coupling: the pitfall-overlap audit.** Coupling propagates if a fed-back signal mechanically moves a held-out measure. Several OOPS! pitfalls sit close to instruments in the held-out set — missing domain and range declarations against E3, undeclared equivalent classes against E6, missing disjointness against E1, and several structural pitfalls against OntoQA's inheritance, relationship and attribute richness. If the model is told to fix such a pitfall and thereby changes a held-out measure, that measure is coupled and nothing in the design would reveal it. Before the campaign, the OOPS! catalogue is walked once against the six codes and the OntoQA metrics; the mapping is recorded in the codebook; and any pitfall whose remediation would mechanically move a held-out measure is suppressed from the fed-back report. Suppression is per-pitfall, not per-instrument: the scan still computes every pitfall for scoring, and only the report shown to the model is filtered. The suppressed list is fixed before the pilot and reported in §7.1.

**The manipulation check is coupled too.** BFO alignment rate is reported by the conformance channel, so the model is partly being told to improve the quantity used to verify the manipulation. Alignment rate at R0 is the clean manipulation check; later rounds show how the manipulation is maintained under feedback.

### 7. Hypothesis chain

**H1 (Paper 1).**
- H1a — Grounding B affects ontology quality. Tested on two scopes: across all three levels on the grounding-agnostic instruments, and on B2 versus B1 for the Tier A/B detection rates, which are undefined for B0. The prediction is that grounded ontologies outperform ungrounded ones on the agnostic instruments, and that B2 shows lower detection rates than B1 on the held-out codes. Coupled measures (consistency, E1, E3, OWL 2 DL conformance, OOPS! pitfall counts) contribute at R0 only.
- H1b — Decomposition D affects domain coverage; D1 achieves higher CQ answerability and higher genre coverage balance than D0.
- H1c — B and D interact: grounding matters more under D0 than under D1. **Stated as a contrast:** the estimand is (B2 − B0 | D0) − (B2 − B0 | D1) on the agnostic instruments, and (B2 − B1 | D0) − (B2 − B1 | D1) on the BFO-specific scope, in both cases predicted to be positive in the direction of better quality. The omnibus B×D term is tested first; the contrast above is the pre-registered decomposition, and simple effects of B within each D level are descriptive support, not the test.
- **H1d — Iteration improves quality, with diminishing returns and possible degradation (round main effect).** Instruments improve from R0 toward a plateau, but over-iteration may degrade quality if the model begins introducing new errors while fixing old ones, or if feedback-driven edits destabilise previously correct structure. The round at which plateau occurs and whether post-plateau degradation is detectable are both measured.
- **H1e — Grounding changes convergence rate (B×R interaction).** B2 converges faster than B1, which converges faster than B0, because richer scaffolding constrains the generator and reduces the work iteration must do. This is the resource-substitution hypothesis: grounding and iteration are partially fungible. Grounding may also shift the plateau round or affect susceptibility to over-iteration degradation. The competing explanation — that grounded conditions simply receive more corrective signal per round — is addressed by covariate adjustment and by the conformance-channel ablation (Paper 1 §5.4, §8.3), and H1e is supported only if the effect survives both.
- **H1f — Decomposition changes convergence rate (D×R interaction).** D1 converges faster than D0, because genre-scoped sub-problems are individually simpler.
- **B×D×R is exploratory.** The three-way interaction is reported descriptively in a figure; no confirmatory hypothesis is attached.

**Scope restriction on H1d–H1f.** Confirmatory tests of the three round-related hypotheses are run on the held-out instruments only (§6.7). The coupled instruments are reported alongside as process evidence, clearly labelled, and are not counted toward support for any of the three.

**Primary outcome per hypothesis.** To keep the confirmatory set defensible under multiplicity, one primary outcome is designated per hypothesis: CQ answerability for H1a, H1c, H1d, H1e and H1f, and genre coverage balance for H1b. Salient-term coverage is co-primary throughout. Every other instrument is secondary and reported with effect sizes and intervals rather than family-corrected tests.

**H2 (Paper 2).** Differences attributable to B, D, and R produce measurable differences in population fidelity — entailment-verified precision, salience recall, post-population reasoner-inconsistency rate, and community structure (CPM resolution profile and genre-aligned AMI). The round effects carry through: a KG populated against an early-round ontology has lower fidelity than one populated against the terminal (R9) ontology from the same run.

**H3 (Paper 3).** Differences in KG fidelity produce measurable differences in RCA accuracy, and the effect of ontology condition on RCA accuracy is at least partially mediated by KG fidelity. Checkpoint-round contrasts test whether iteration level matters at the point of use.

### 8. Shared research assets

All frozen before any experimental run. All are generated or authored once and then run unsupervised.

1. **The corpus.** Electronics manufacturing documentation across six genres, with de-identification documented. Document counts, token counts and genre proportions are recorded in the manifest and reported in every paper, since they determine chunking behaviour and therefore what the D contrast means. The release position is stated explicitly: whether the corpus can be published, and if not, which public surrogate corpus a replication should use.
2. **The salient-term inventory.** Auto-extracted per genre, with the extractor and its parameters pinned.
3. **The salient-assertion inventory** (Paper 2). Auto-extracted subject–predicate–object candidates against which salience recall is computed, with the extractor and its parameters pinned. Distinct from the term inventory and frozen on the same schedule.
4. **The CQ set.** 50–100 hand-authored competency questions with SPARQL translations, tagged by question type and genre relevance. Frozen before generation.
5. **The six Tier A/B detectors.** Reasoner queries, SHACL shapes, and SPARQL detectors, versioned, with tier, family, eligibility, denominator, loop status and sub-ontology closure recorded per code, implementing R1 through R9.
6. **The B2 baseline-exclusion lists.** Three are required, not one, and none is optional: **E3** over Table 0.2b's relation scope, **E5** over the `BFO_0000144` term and the axioms IOF asserts on it, and **E6** over IOF's asserted hierarchy. Without them, IOF's own content produces systematic false positives in every B2 artefact before any generator acts, inflating three codes for B2 and potentially inverting the H1a prediction for a purely artefactual reason. Derived once from the pinned release and hashed.
7. **The source-linked codebook (v12, paired with this document).** Six fields per code: the BFO commitment presupposed, a primary-source citation, the formal expression of the violation, the tier assignment, the detector implementation reference, and known limitations. Includes the historical→current crosswalk (codebook §0.01–0.02), the reference tables (26 disjoint pairs; Table 0.2 relation signatures; Table 0.2b's 24 B2-only relations), the three-system identifier map (OWL, CLIF, Prover9 labels), the IOF Core 202603 baselines, rules R1–R9, descriptive indicators I1–I5, the OOPS! pitfall-overlap mapping, and the archived Tier C entries retained for provenance.
8. **The pinned-release set.** `bfo-core.owl` (B1 scoring layer); classic `bfo.owl` as cached in the IOF release (B2 injection material and, with IOF Core, part of the B2 scoring layer); IOF Core `Core.rdf` release 202603; ISO/IEC 21838-1 and -2:2021. File hashes recorded in the seed register, together with the pre-campaign axiom-level diff between the two BFO builds.
9. **The model manifest.** Generator weights and revision, serving runtime and version, quantisation if any, context window, and the same for the NLI verifier (Paper 2), the NLI answer matcher (Paper 3), and the embedding model used in salient-term matching. Pinned for the duration of the campaign.
10. **The entailment-based triple verifier** (Paper 2).
11. **The held-out root-cause label set** (Paper 3), mined automatically from corrective-action statements and redacted from the retrieval corpus.
12. **The seed register and environment manifest.** A single frozen document covering all three papers, recording every seed, what it governs, and the execution environment. Four seed roles: **S-GEN** (ontology generation, Paper 1), **S-POP** (KG population, Paper 2, nested within S-GEN), **S-RET** (retrieval DoE randomisation and synthetic scenario generation, Paper 3), **S-HAR** (any stochastic component of the battery instruments — embedding-based term extraction, consensus induction).

### 9. Portability

The battery is designed to be rerun on a different corpus, domain, or base ontology. What a new deployment must supply:

| Must be supplied by hand | Automatic |
|---|---|
| The corpus | Salient-term extraction |
| A genre map (which documents are of which genre) | Structural metrics, OOPS!, OWL 2 DL conformance |
| The base ontologies for Factor B | Tier A/B detectors (reasoner + SHACL/SPARQL) |
| The CQ set and its SPARQL translations | CQ scoring |
| An execution environment and its manifest | Seed register generation and output hashing |
| — | Consensus induction |
| — | Population verification |
| — | RCA label mining, if corrective-action records exist |

The CQ set is the only asset that does not transfer without re-authoring. All other instruments are either domain-general (OOPS!, OntoQA, OWL reasoner) or BFO-general (the six Tier A/B detectors). A new deployment re-runs the battery at compute cost and modest human cost (~3–5 days for a new CQ set).

This is an argument from construction, not a demonstration. No second corpus is run in this dissertation, so portability is a designed property and a costing, not a finding. The conclusion states it that way, and a second-domain replication is named as future work.

### 10. Contributions

1. **The first crossed factorial evaluation of upper-ontology grounding against corpus decomposition for LLM-generated manufacturing ontologies**, with iteration depth as a within-subject dimension and a testable interaction hypothesis.
2. An evaluation battery combining established structural metrics (OntoQA, OOPS!), formally decidable BFO-specific checks (Tier A/B), and corpus-grounded coverage measures, applied without a reference ontology and at every iteration round.
3. Six BFO-grounded checks in two tiers, derived from BFO 2020 with source-linked provenance, in three families (BFO commitment, realist practice, ISO conformance).
4. **An end-to-end empirical trace of whether upstream ontology design — and the iteration investment — survives to downstream task performance**, including the practitioner-relevant question of whether grounding substitutes for iteration.
5. Released artefacts: generators, battery scripts, detectors, CQ set, codebook, and all 60 × 10 ontology-states.

A process-awareness formalism encoding part-specific routing order and defect-propagation asymmetry is a natural extension of the pipeline and is identified as a candidate follow-on paper rather than pursued within this dissertation.

### 11. Cross-cutting risks

| Risk | Mitigation |
|---|---|
| Effects wash out by Paper 3 | Pre-register the null; mediation localises attenuation; Papers 1 and 2 retain standalone value |
| Codes are stylistic conventions rather than BFO violations | Provenance review completed (codebook v8); three-family structure; only BFO-commitment family described as BFO modelling error |
| BFO-specific instruments undefined for B0 | Scope limit stated; the three-level ordering carried by grounding-agnostic instruments and Papers 2–3 |
| Heuristic modelling patterns outside the battery's scope | Any effect is detectable downstream in Papers 2–3 via post-population reasoner inconsistency, fidelity measures, and RCA accuracy |
| Instruments coupled to the feedback loop | Coupling declared in §6.7; coupled measures confirmatory at R0 only; round-related confirmatory inference rests on held-out instruments |
| Feedback volume increases with grounding level, mimicking H1e | Payload tokens and flagged-item counts logged per round and carried as a covariate; conformance-channel ablation run as a pre-registered ancillary arm |
| B1 and B2 scored by different axiomatizations | Difference bounded and known (codebook Table 0.2b: 24 additive relation variants); B2 scored against the union so real violations are not dropped; the B1-versus-B2 contrast reported on the common inventory, with indicator I5 tracking B2-only usage and I4 quarantining IOF-only unsatisfiability |
| E3, E5 and E6 systematically inflated for B2 by IOF Core's own content | Three baseline-exclusion lists built from the pinned release before the campaign and treated as required assets |
| A code saturating or flatlining across all conditions | R5 discrimination check, pre-registered: above 95% or below 5% of eligible sites in every condition means descriptive reporting only, no inferential comparison |
| Eligibility predicates that behave differently on B1 and B2 | R1: eligibility evaluable identically across conditions; IOF signals confined to detectors; B2 rates reported with and without any IOF aid |
| Detection counts confounded with artefact size | R7 denominators; `log(denominator)` offsets in all count models |
| BFO and IOF are present in the generator's pretraining data, so B0 is not a true no-upper-ontology condition | B0 is defined as "no scaffolding supplied in context", not "no scaffolding known"; BFO alignment rate at R0 quantifies spontaneous alignment and is reported as a finding in its own right |
| D1 rounds cost more than D0 rounds, inflating H1f | Per-round cost logged; convergence reported against cumulative tokens as well as round index; §7.14 carries confirmatory weight, and H1f requires both readings to agree |
| Merge variance masquerading as trajectory movement under D1 | Anchored re-integration (patch against the previous round's artefact); merge churn and IRI stability logged per round; pilot decision rule on R0 churn |
| Cross-genre defects invisible to a per-sub-ontology feedback loop | Feedback computed on the integrated artefact and routed; integration carries its own feedback channel (§6.4a) |
| Presentation order confounded with D | Order held constant across D within a seed; genre order varied across seeds; D0-shuffled ancillary arm bounds the order component (Paper 1 §8.5) |
| Late-processed genres disadvantaged by context overflow under D0 | Deterministic windowing with patch-based merge rather than truncation; visibility statistics reported by position and genre; genre order varied across seeds |
| R = 9 chosen without convergence data | Pre-campaign pilot at R = 15 on the extreme conditions; round count confirmed or revised before the main campaign |
| CQs shallow or incomplete | Stratify by question type; report per-stratum; the CQ set is a secondary measure, not the primary DV |
| Underpowering | *k* = 10 settled; MDE computed per outcome scope; B×D×R is exploratory, not confirmatory |
| Context-budget confound between B levels | Window and chunk allotments pinned independently of the injection, so corpus exposure, accumulation steps and windowing frequency are identical across B; injection rendering ablated (§8.2); residual total-length difference is the treatment itself and is declared, not padded |
| Environment drift over a multi-month campaign | Self-hosted weights and fixed GPU allocation; full environment manifest; output hashes |
| Autocorrelated round observations | Model AR(1) or similar within-subject correlation structure; 10 within-subject observations per run are correlated, not independent |
| Round-0 ontologies may hit instrument floors | Include R0 as baseline with floor values noted; instrument behaviour at floor is informative about what iteration buys |
| Over-iteration degradation may be condition-dependent | Monitored as an explicit DV; post-plateau trajectory shape reported by condition |
| Paper 3 DoE complexity with round threaded through | Use four checkpoint rounds (R0, R3, R6, R9) rather than all ten; B×D×R interaction in Paper 3 is exploratory |

### 12. Campaign sizing

The design is large, and its cost has not previously been written down. These are the run counts the design implies; the compute and wall-clock columns are filled from the pilot before the pre-registration is finalised.

| Stage | Unit | Count | Driver |
|---|---|---|---|
| Paper 1 generation | Generation calls | 60 runs × (R0 construction + 9 feedback rounds), multiplied under D1 by the number of genre sub-ontologies at R0 and by chunk count at both D levels | Corpus token count ÷ the pinned chunk allotment — which is set to fit under B2, so every condition runs at the worst-case chunk count |
| Paper 1 generation, D1 surcharge | Additional calls | Per round, *G* sub-ontology calls plus one integration call rather than one call; with six genres, roughly 7× D0's per-round cost | Genre count |
| Paper 1 battery | Instrument runs | 600 whole-artefact states × the instrument inventory, plus 30 D1 runs × 10 rounds × *G* sub-ontology evaluations for integration loss; reasoner classification and OOPS! scan dominate | Ontology size; reasoner timeout; genre count |
| Paper 2 population | Full-corpus extraction passes | 600, one per ontology-state | Corpus token count |
| Paper 2 verification | NLI verifications | 600 × extracted triples per KG | Yield |
| Paper 2 community structure | Leiden runs | 600 × resolution-profile points | Profile granularity |
| Paper 3 Stage 1 | RCA runs | Screening design size × benchmark size × 2 screening conditions | Fractional factorial resolution |
| Paper 3 Stage 2 | RCA runs | Active retrieval configurations × 6 conditions × 4 checkpoint rounds × 10 seeds × benchmark size | Number of active factors surviving screening |

Two of these are the ones that can break the project. Paper 2 is 600 full-corpus extraction passes plus per-triple NLI verification, on hardware deliberately configured for determinism rather than throughput (batch size 1, prefix caching disabled). Paper 3 Stage 2 multiplies out fast: four active two-level factors would give 16 configurations × 240 ontology-states × the benchmark, before any replication. Two mitigations are pre-committed rather than improvised later: Paper 2 may be restricted to a pre-registered subset of rounds (R0, R3, R6, R9, matching Paper 3's checkpoints) if the full 600 proves infeasible, with the reduction declared in the pre-registration rather than after seeing results; and Paper 3 Stage 2 caps the number of retained retrieval factors at the screening stage, with the cap stated in advance.

---

## Part II — Paper 1

**Working title:** *Grounding, Decomposition, or Iteration? A Crossed Factorial Study of LLM-Generated Manufacturing Ontologies*

**Target venue:** *Applied Ontology*, or *Journal of Intelligent Manufacturing*
**Target length:** 9,000–11,000 words

### 1. Introduction

1.1 The manufacturing knowledge capture problem.
1.2 LLMs as ontology construction instruments.
1.3 The three levers: grounding, decomposition, and iteration — and the literature's conflation of the first two.
1.4 Contribution statement: the first crossed evaluation of these levers, with iteration trajectories measured at every round.
1.5 Roadmap.

### 2. Background and related work

2.1 Ontology learning from text.
2.2 LLMs for ontology engineering: LLMs4OL (Babaei Giglou et al., ISWC 2023); OLLM (Lo et al., NeurIPS 2024); Text2KGBench (Mihindukulasooriya et al., ISWC 2023); OntoChat (Zhang et al., ESWC 2024); Xiao et al. (*J. Intell. Manuf.* 36(5), 2025).
2.3 Realist foundations: BFO as ISO/IEC 21838-2; IOF Core as a BFO-conformant manufacturing mid-level; CCO as sibling, with the absence of a vetted mapping stated.
2.4 Modularisation and integration.
2.5 **Ontology evaluation.** Gold-standard, task-based, application-based, and data-driven paradigms; OntoQA as a reference-free structural framework (Tartir et al. 2005); OQuaRE as a quality-model framework (Duque-Ramos et al. 2011); OOPS! as automated pitfall detection (Poveda-Villalón et al. 2014); WiseOWL (Dalal et al. 2026) as a recent automated structural/semantic evaluation combining documentation coverage, BERT-based definition quality, connectivity, and hierarchical balance. The persistent reliance on hand-built references and what it costs.
2.6 **Iterative refinement of LLM outputs.** Self-correction and tool-augmented iteration in LLM generation; convergence behaviour under feedback.
2.7 Gap statement: the uncrossed factors, the uncharacterised iteration trajectories, and the reliance on reference ontologies.

### 3. BFO-grounded modelling checks

3.1 Derivation, grounded in BFO's category distinctions. Sources: BFO 2020 in its OWL formalisation; ISO/IEC 21838-2:2021; Arp, Smith and Spear (2015).
3.2 Six formally decidable codes in three families:
- *BFO commitment:* E1 (disjoint-category co-subsumption), E2 (SDC without bearer), E3 (relation signature violation).
- *Realist practice:* E4 (universal–particular conflation).
- *ISO conformance:* E5 (upper-level tampering), E6 (multiple asserted parents).

Each with definition, positive example, near-miss negative, and downstream consequence. The three families are reported separately; only the BFO-commitment family is described as detecting BFO modelling error.

3.3 **Scope of applicability.** The codes presuppose a BFO commitment and are undefined for B0.

3.4 Codebook, in the six-field source-linked format. A code without a primary-source citation is not in the codebook.

3.5 **Release reconciliation and scoring layers.** Four BFO-related artefacts are pinned. B1 artefacts are scored against `bfo-core.owl` (BFO 2020); B2 artefacts against the union of the classic BFO 2020 build imported by IOF Core release 202603 and IOF Core itself. The two BFO builds have been diffed directly (codebook Table 0.2b): they differ by exactly 24 relations, all temporalised or proper-parthood variants, so the difference is additive and bounded. Scoring B2 against `bfo-core.owl` alone would drop genuine violations on relations B2 is entitled to use; scoring the contrast on the union would compare inventories rather than artefacts. The resolution is to score on the union and report the B1-versus-B2 contrast on the common inventory, with indicator I5 quantifying B2-only usage. ISO/IEC 21838-2 is cited for domain-ontology conformance requirements. Detectors are confirmed against BFO 2020 rather than BFO 2.0.

**Verified reference figures.** `bfo-core.owl` asserts disjointness at 26 class pairs (five `owl:disjointWith` axioms plus 21 pairs from five `AllDisjointClasses` axioms) across 36 declared classes, and declares 40 object properties carrying 28 domain and 31 range axioms. These figures bound E1 and E3 sensitivity and are reported as such.

### 4. Evaluation battery

4.1 **Design principle.** No reference ontology. Battery evaluated at every round state (R0–R9).
4.2 **Salient-term coverage** and genre coverage balance.
4.3 **Competency question answerability.** 50–100 hand-authored CQs with automated SPARQL scoring; stratified by question type.
4.4 **Structural profile and pitfall detection.** OntoQA metrics (held out); OOPS! pitfall counts by severity (loop-coupled; confirmatory at R0, compliance evidence thereafter).
4.5 **Logical quality.** OWL 2 DL conformance; consistency and satisfiability; co-occurrence-anomalous entailments.
4.6 **BFO-specific checks.** E1 and E3 (Tier A, reasoner); E2, E4, E5, E6 (Tier B, SHACL/SPARQL). Scored per §3.5, with the three B2 baseline-exclusion lists applied to E3, E5 and E6. BFO alignment rate as manipulation check. Rules R1–R9 per codebook §1.2, reported in full: eligibility, root counting, E1/E3 attribution, discrimination check, graph choice, denominators, loop status, sub-ontology closure.

4.6a **Loop status.** E1 and E3 are loop-coupled through the reasoner report and are confirmatory at R0 only; E2, E4, E5 and E6 are held out and carry the round-related inference on the BFO-specific scope. See Part I §6.7.
4.7 **Consensus induction** (R9 only), with the explicit non-truth caveat.

**Figure 1.** Battery architecture — corpus in, instrument battery out, with the scope boundary between grounding-agnostic and BFO-specific instruments marked.
**Table 1.** Instrument inventory: family, instruments, scope.

### 5. Experimental design

5.1 Factors and levels; the 3×2×10 cell table (B×D×R); what each cell represents as a practitioner decision.
5.2 **Injection protocol for Factor B, and the three-allotment prompt.** The generation prompt has three variable parts, and only one of them is the manipulation:

| Allotment | Contents | Varies with B? |
|---|---|---|
| **Injection** | The Factor B scaffolding: nothing for B0, the BFO class and relation inventory for B1, the IOF Core inventory for B2 | **Yes — this is the manipulation** |
| **Window** | The view onto the accumulated ontology (Part I §5) | No — pinned |
| **Chunk** | The corpus text processed in this call | No — pinned |

The window and chunk allotments are fixed once, at values that fit comfortably under B2's injection, and reused unchanged for B1 and B0. Earlier revisions specified a single shared budget that the three parts competed for, which had two defects. It left chunk size, chunk count, and windowing frequency free to drift with injection length, so incidental properties of the pipeline would have varied with the treatment. Worse, it made B2's injection compete directly with B2's window: the richest condition would have hit degraded views earliest and most often, a mechanism capable of suppressing B2 quality and masking the grounding effect the design exists to measure. Fixing the allotments removes both. Corpus exposure per call, the number of accumulation steps, how much of the artefact the model can see, and how often windowing fires are identical across grounding levels by construction.

**Injection rendering.** B1 and B2 injections are produced by a deterministic renderer (class and relation labels with their definitions, truncated at the pinned injection allotment by a fixed ordering rule, with the truncation point recorded). B2 is therefore a *summarised* IOF Core condition and is described as such throughout, not as full IOF Core.

**Total prompt length is not equalised, and B0 is not padded.** With the other two allotments fixed, the residual difference in total prompt length across B is exactly the treatment: B2's prompt is longer because it contains IOF Core. Padding B0 with filler would not control for anything — it would add a third manipulation and dilute attention without contributing content. What remains is attention dilution over a longer prompt, which cannot be designed away and is recorded in §10 as a stated limit rather than a mitigated one. The concern is empirically grounded: Levy, Jacoby & Goldberg (ACL 2024) show that LLM reasoning degrades with input length alone — even when the added content is relevant — and Liu et al. (TACL 2024) document positional attention bias that concentrates on prompt boundaries. Both effects operate at the scale of the B0/B2 length difference, and padding would worsen both rather than control for either.

**Cost.** Every condition runs at the chunk count B2's allotment implies, so the campaign is sized by the worst case rather than the average (§12). This is accepted deliberately: the alternative buys compute at the price of confounding the manipulation with pipeline mechanics.

The injection-format ablation (§8.2) tests the rendering choice; the conformance-channel ablation (§8.3) tests the feedback-side counterpart.
5.3 **Generation procedure for Factor D.** Sequential accumulation over chunks at both levels. Presentation order is genre-blocked and identical across D within a seed; D0 chunks the concatenated stream by token budget, genre-blind, so boundary chunks may straddle genres; D1 chunks within genre and closes R0 with an integration pass, after which the sub-ontologies persist and integration is re-run, anchored, at every round. Integration is deterministic label normalisation and IRI reconciliation followed by one LLM-mediated merge pass under the same injection condition (LogMap and AML as audit trail, §8.1). Context overflow at either level is handled by the deterministic windowing rule and patch-based edit merge specified in Part I §5, with visibility statistics logged per chunk. Prompt templates in appendix, differing only in manipulated content. Chunk count, chunk size, straddling-chunk count, integration statistics, and windowed-chunk counts are reported per condition, since they are the operational content of the D manipulation.
5.4 **Fixed iteration protocol.** Nine rounds of feedback. The round count is set high enough that the convergence plateau is observable for all conditions and that over-iteration degradation — if it occurs — is detectable. Where the plateau falls and whether quality ever declines with further iteration are themselves dependent variables and are not assumed in advance. The ontology state is saved after each round, including the raw R0 state before any feedback.

**Feedback design.** Every round receives exactly the same prompt structure: the current ontology and fresh feedback on it. The payload is four items — the reasoner report (global consistency and unsatisfiable classes), the OWL 2 DL profile report, the OOPS! pitfall report filtered by the suppression list, and the conformance report. OOPS! is fed back deliberately: the loop is meant to be the one a practitioner would run, and the resulting coupling is accounted for rather than avoided (Part I §6.7). No accumulated history from prior rounds is carried forward. The model does not know which round it is on, how many rounds remain, or what it changed in prior rounds. This ensures that each round's edit decisions are conditioned only on the ontology-as-it-stands and its current feedback, not on a growing narrative or a round-position signal. Any trajectory pattern in the data is therefore attributable to the ontology's state, not to the model adjusting its strategy based on round position. The constant feedback payload also eliminates context-budget variation across rounds — every round has the same generation budget regardless of how many rounds have preceded it.

No human judgement enters the loop, and the held-out instruments are never fed back: CQ answerability, salient-term coverage, genre coverage balance, OntoQA metrics, and the E2, E4, E5, E6 detectors. Nor are OOPS! pitfalls whose remediation would mechanically move one of those measures; the suppression list from the pitfall-overlap audit is applied to the fed-back report. What *is* fed back is coupled to its corresponding outcomes by construction, and Part I §6.7 states what follows for inference.

**The feedback-volume confound.** For B0 the conformance report is trivially empty (no BFO or IOF terms to check); for B1 it reports BFO alignment only; for B2 it reports both. Prompt structure and payload format are identical across grounding levels, but *information content* is monotonically increasing in B. That matters because H1e predicts exactly the same ordering of convergence rates that differential feedback volume would produce on its own. Three measures address it:

- **Measurement.** Feedback payload tokens and flagged-item counts are logged per round per condition and reported as descriptives, so the size of the asymmetry is visible rather than assumed away.
- **Adjustment.** Payload volume enters the H1e model as a covariate. The resource-substitution claim is evaluated on the grounding effect that survives adjustment.
- **Ablation.** §8.3 runs B1 and B2 with the conformance section suppressed, leaving reasoner and profile reports only. If the B×R pattern persists without the conformance channel, the resource-substitution reading is supported; if it disappears, the effect was feedback volume.

Unadjusted H1e results are reported alongside adjusted ones in all cases.

5.4a **Feedback routing under D1.** Feedback is computed on the *integrated* artefact, then routed to the artefact that can act on it. Computing it per sub-ontology in isolation would be clean and parallel but blind to everything the merge creates — cross-genre disjointness violations, duplicate classes landing under conflicting parents, relation signature clashes between genres — which are precisely the defects decomposition causes. A loop that fixes the easy errors and preserves the interesting ones is worse than useless for H1f.

The routing rule, fixed in advance:

- A defect whose participating entities all originate in one sub-ontology is routed to that sub-ontology's feedback section.
- A defect spanning entities from two or more sub-ontologies, or involving an entity the merge created, is routed to the integration step, which carries its own feedback section and its own prompt.
- Provenance for routing comes from the IRI reconciliation map produced during integration; entities with ambiguous provenance route to integration by default, and the ambiguous proportion is reported.

Integration is therefore an iterated step with a feedback channel, not a fixed post-process. The split between sub-ontology-routed and integration-routed defects, per round and per condition, is reported (§6.3): it is a direct measure of what decomposition costs, and it is the quantity that tells a practitioner whether the integration step is where their effort should go.

D0 has no routing: all feedback attaches to the single artefact.

5.5 **Seeds, blocking, and the seed register.**
- 5.5.1 *What the seed governs.* S-GEN fixes document presentation order within genre, chunk boundaries, few-shot exemplar selection, and **genre processing order, which now varies across seeds and is held identical between D0 and D1 within a seed**. Paired contrasts are preserved, and which genre is processed last — the one most exposed to windowed views under D0 — is averaged over rather than fixed by an arbitrary choice.
- 5.5.2 *Decoding regime.* Greedy decoding; seed variance estimates sensitivity to corpus presentation order — a meaningful quantity reported in §7.3.
- 5.5.3 *Execution determinism on self-hosted hardware.* Fixed GPU allocation, deterministic kernel flags, batch size 1, prefix caching disabled. Cost is throughput, accepted for a campaign of 60 runs.
- 5.5.4 *Determinism audit.* Three runs of one configuration under identical seed, outputs hashed. Matching hashes confirm bitwise reproducibility. Non-matching hashes trigger the documented fallback: divergence rate measured and reported.
- 5.5.5 *Seed count and allocation.* *k* = 10, settled. S-POP nested within S-GEN; S-RET and S-HAR independent.

**Table 1b.** Seed register and environment manifest fields.

5.6 **Environment manifest and drift check.** Manifest captured automatically per run. One full seed set re-run at end of campaign against recorded hashes.
5.7 Pre-registration.

**Figure 2.** Design schematic.

### 6. Measures and analysis

6.1 **Manipulation checks.** BFO alignment rate by condition and round; expected ordering B2 > B1 > B0.
6.2 **Primary outcomes** (pre-registered). The undefined "logical soundness composite" of earlier revisions is dissolved: composites require a formula, and an unspecified one is a researcher-degrees-of-freedom hole in a pre-registered design. Outcomes are named individually.

- *All three grounding levels, all rounds:* CQ answerability (designated primary); salient-term coverage (co-primary); genre coverage balance (primary for H1b).
- *B1 and B2, all rounds:* E2, E4, E5 and E6 detection rates, reported by family, each over its R7 denominator.
- *R0 only, all three grounding levels:* global consistency; unsatisfiable-class rate; OWL 2 DL conformance.
- *R0 only, B1 and B2:* E1 detection rate with per-pair breakdown; E3 detection rate.

The R0-only restriction on the last two groups follows from loop coupling (Part I §6.7), not from any doubt about the instruments themselves.

6.3 **Secondary and process outcomes:** OntoQA structural profile; cumulative token cost and wall-clock time; feedback payload volume. **D1 integration descriptives:** integration loss — the battery delta between the union of the sub-ontologies and the merged artefact, computed at every round, which quantifies how much quality the merge destroys and whether that varies with grounding. **Read code by code, never in aggregate (R9):** an instrument whose eligibility is not closed within a sub-ontology cannot be scored pre-merge. E2 is the clear case, since a bearer may sit in another genre's sub-ontology, so its pre-merge rate is inflated and its integration loss would read negative for reasons unrelated to merge quality; E3 is partially affected, because cross-genre signature clashes can only surface after the merge. E1, E4, E5 and E6 are closed within sub-ontologies and their integration loss is interpretable (codebook §1.1 records the status per code). Salient-term coverage on a sub-ontology is scored against that genre's inventory, not the whole-corpus inventory. Instruments failing closure are reported as descriptive pre-merge values with the caveat attached; merge churn per round (the proportion of axioms the LLM merge pass changes beyond deterministic normalisation and reconciliation); IRI stability across rounds; and the defect-routing split between sub-ontology and integration. **Position-gradient descriptives:** per-genre salient-term coverage by processing position, which tests the recency/primacy mechanism behind H1b more directly than the entropy-based genre coverage balance does; straddling-chunk counts; and windowed-chunk counts by position and genre, with the proportion of the artefact visible. **Loop-coupled trajectories** (consistency, unsatisfiable-class rate, OWL 2 DL conformance, E1, E3, OOPS! pitfall counts across R1–R9) are reported as process evidence that the loop functions, labelled as such in every table, and excluded from confirmatory tests of H1d, H1e and H1f. **Exploratory:** co-occurrence-anomalous entailments, with a threshold sensitivity sweep.

6.4 **Descriptive only:** cross-condition agreement; leave-one-out consensus recall, pooled and per-condition (R9 only).

6.5 **Statistical plan.** Mixed-effects models: B, D, and R fixed; seed random. R is a within-subject repeated measure with an AR(1) correlation structure. Negative-binomial GLMM for counts, **with a `log(eligible-site denominator)` offset in every count model**, so that detection rates rather than raw counts are modelled and artefact size is not silently absorbed into the condition effect; binomial GLMM or beta regression for proportions.

**Trajectory model (primary specification for H1d–H1f).** The round-related hypotheses are about *rates of convergence*, and an interaction term on a polynomial trajectory does not estimate a rate. For each run and each held-out instrument, a three-parameter asymptotic regression is fitted:

> *y*(R) = *a* − (*a* − *f*) · exp(−*c* · R)

with *f* the R0 floor, *a* the asymptote, and *c* the rate constant. H1d is then a test that *a* exceeds *f*; H1e is a test of the *c* parameter across B; H1f is a test of *c* across D. Plateau round is derived from the fitted *c* with an interval rather than read off a heuristic threshold. Over-iteration degradation is tested by a quadratic extension and by a pre-registered test for a negative slope over R6–R9. Where the asymptotic model fails to converge for a run, that run is reported as non-convergent and handled by a pre-specified rule rather than dropped silently.

**Secondary specification.** The B×R and D×R interaction terms in the mixed-effects model are retained and reported alongside the fitted-parameter results. Agreement between the two specifications is reported as robustness; disagreement is reported and discussed rather than resolved by selection.

Pre-registered contrasts:
- *B main effect:* B1–B0, B2–B1 (agnostic instruments, all levels); B2–B1 (BFO-specific, two grounded levels).
- *D main effect:* D1–D0.
- *R main effect:* R9–R0 (total change); modelled as a continuous or polynomial trajectory, with the plateau round and any post-plateau degradation characterised.
- *B×D interaction:* H1c — the omnibus B×D term, then the pre-registered contrast (B2 − B0 | D0) − (B2 − B0 | D1) on the agnostic scope and (B2 − B1 | D0) − (B2 − B1 | D1) on the BFO-specific scope. Simple effects of B within each D level are descriptive support, not the test.
- *B×R interaction:* H1e — does grounding change convergence rate?
- *D×R interaction:* H1f — does decomposition change convergence rate?
- *B×D×R:* exploratory, reported in a figure, no confirmatory test.

Holm correction within families, applied to the designated primary outcomes; secondary outcomes are reported with effect sizes and intervals and are labelled as such. The grounding-agnostic and BFO-specific scopes are separate families, as are the R0-only coupled measures.

**Power, honestly.** H1c is the central hypothesis and is the least-powered test in the design: interactions need roughly four times the sample of main effects, and *k* = 10 is settled. The minimum detectable effect is therefore computed per outcome *before* pre-registration, not alongside it, and the pre-registration states in advance what happens if the MDE exceeds any plausible effect size — namely that H1c is reported as an estimation result with intervals and an explicit statement of what the design could and could not have detected, rather than as a null hypothesis test whose non-significance would be uninformative.

6.6 **Convergence and over-iteration characterisation.** Reported from the fitted trajectory parameters rather than from observed maxima, because "round at which the instrument reaches 90% of its peak" is biased when the peak is itself a maximum over a short noisy series and is undefined in direction for instruments where lower is better. Per condition: the fitted rate constant *c* and asymptote *a* with intervals; the derived round at which 90% of (*a* − *f*) is attained, direction-normalised so that improvement is always positive; evidence for post-plateau decline from the quadratic extension and the R6–R9 slope test; and cost-to-convergence in tokens. Reported as a practitioner-facing summary.

### 7. Results

*Pre-specified shell, conditional language.*

7.1 **Instrument confirmation.** Reasoner version and classification timeout for Tier A codes; SHACL/SPARQL correctness check results for Tier B codes; OOPS! version and the suppressed-pitfall list from the overlap audit; the `bfo-core.owl` / classic `bfo.owl` diff as recorded in codebook Table 0.2b; the three B2 baseline-exclusion lists and their sizes; R5 positive rates per code per condition, with any code excluded from inferential comparison named here; model manifest for the generator and the embedding model.
7.2 Determinism audit result and drift check.
7.3 Seed variance — sensitivity of each outcome to corpus presentation order.
7.4 Manipulation checks.
7.5 Descriptives by cell and round. Trajectory plots (outcome by round, panelled by B, coloured by D).
7.6 H1a — grounding main effect.
7.7 H1b — decomposition main effect.
7.8 H1c — B×D interaction.
7.9 **H1d — iteration main effect.** Held-out instruments only. Fitted floor, asymptote and rate constant; total change R0→R9; diminishing returns; over-iteration degradation if present. Loop-coupled trajectories reported in a separate, clearly labelled panel as process evidence.
7.10 **H1e — B×R interaction.** Does grounding change convergence rate? Fitted rate constants by grounding level, unadjusted and adjusted for feedback payload volume, with the conformance-channel ablation (§8.3) read alongside. Trajectory plots overlaid by grounding level.
7.11 **H1f — D×R interaction.** Does decomposition change convergence rate?
7.12 **B×D×R — exploratory.** Three-way pattern described and shown in a figure. No confirmatory test.
7.13 **Convergence and over-iteration characterisation.** Round-to-90%, round-to-peak, post-peak trajectory, and cost-to-convergence by condition. The practitioner question: given a fixed token budget, spend on grounding, decomposition, or more iteration? And: when should you stop?
7.14 **Cost-adjusted comparison.** Convergence against cumulative tokens as well as round index, for all conditions. Carries confirmatory weight for H1f, because a D1 round is not a matched unit of work against a D0 round (Part I §5): the round-index reading and the cost reading are reported together, and H1f is supported only where both point the same way.
7.15 **D1 integration analysis.** Integration loss by round and grounding level; merge churn and IRI stability; the defect-routing split and what it implies about where decomposition's costs land.

**Table 2.** Cell means and SDs, all outcomes, at R9.
**Table 2b.** Trajectory summary: round-to-90%, round-to-peak, and cost-to-convergence by condition.
**Table 3.** Model coefficients, effect sizes, CIs — B, D, R main effects and two-way interactions.
**Figure 3.** Trajectory plots: primary outcomes by round, panelled by B, lines by D.
**Figure 4.** B×D interaction plot at R9.
**Figure 5.** B×R interaction: convergence rate by grounding level.
**Figure 6.** B×D×R exploratory pattern (three-way figure).

### 8. Ancillary studies

8.1 **LLM-mediated merge.** Merging B2D0 and B2D1 within seed, with LogMap and AML audit trail.
8.2 **Injection-format ablation.** Structured summaries versus raw OWL for B1 and B2.
8.3 **Conformance-channel ablation.** B1 and B2 run with the conformance section suppressed from the feedback payload, leaving the reasoner and OWL 2 DL profile reports only. Separates the resource-substitution reading of H1e from the alternative that grounded conditions simply receive more corrective signal per round. Run on a pre-registered subset of seeds; the subset size is set from pilot throughput and cost data and fixed before the main campaign.
8.4 **B0 spontaneous alignment.** BFO alignment rate for B0 artefacts at R0, reported as a finding rather than a floor: it quantifies how much realist structure the generator supplies unprompted, and therefore how much of a contrast B0 really provides.
8.5 **D0-shuffled arm.** D0 rerun on three pre-registered seeds with genres interleaved rather than blocked, holding everything else fixed. Three seeds is an engineering-intuition choice: enough to distinguish a consistent ordering effect from noise, few enough to stay ancillary. Bounds how much of any observed D effect is attributable to partition rather than to the genre-blocked presentation order both main-design levels share. Reported as an ancillary bound on the estimand described in Part I §5, not as a fourth cell.

### 9. Discussion

9.1 What the interaction means under a fixed budget.
9.2 Whether grounding substitutes for iteration — the H1e finding.
9.3 Whether decomposition substitutes for iteration — the H1f finding.
9.4 The resource-allocation question: grounding, decomposition, or iteration? And when to stop iterating.
9.5 What B0 reveals about LLM defaults, read from the agnostic instruments.
9.6 What the battery can and cannot certify — its limits.
9.7 Forward-link to Papers 2 and 3.

### 10. Threats to validity

- **Construct.** No correctness anchor; hand-authored CQs may be shallow or incomplete; structural metrics are necessary conditions, not sufficient; OOPS! pitfalls are general-purpose and may miss domain-specific issues; heuristic modelling patterns consistent with OWL semantics (e.g. category conflation, role misassignment) are outside the battery's scope — any effect is detectable only downstream.
- **Internal.** Total prompt length differs across B because the injection differs, which is the treatment; the window and chunk allotments are pinned so that nothing else varies with it (§5.2). The irreducible residual is attention dilution over a longer prompt — a mechanism with empirical support (Levy et al., ACL 2024; Liu et al., TACL 2024) — which no padding scheme improves and which is declared rather than mitigated. Also: prompt-template equivalence across D; **the narrowed D estimand** that follows from holding presentation order constant, which biases H1b toward the null and is bounded by §8.5; **position-dependent context degradation under D0**, mitigated by windowing rather than eliminated; **unequal per-round work across D**, addressed by cost-adjusted reporting rather than by design, since equalising calls per round would require crippling D1; **loop coupling**, which is bounded rather than eliminated (Part I §6.7) and which restricts four measures to R0 for confirmatory purposes; **feedback-volume asymmetry across B**, addressed by measurement, covariate adjustment and the §8.3 ablation but not removed by design; fresh-only feedback eliminates context-budget variation across rounds but means the model has no memory of prior correction attempts. Autocorrelation across rounds modelled but not eliminated.
- **External.** Single corpus, single domain, single generator family. CCO excluded. **The decoding regime narrows the inference further than "single generator" suggests:** with fixed weights, greedy decoding and bitwise-deterministic execution, the only stochastic input is S-GEN, which governs corpus presentation order. The seed random effect therefore estimates sensitivity to presentation order, not run-to-run generator variability, and intervals will be correspondingly narrow for a reason unrelated to how the generator behaves in deployment. Conclusions generalise to this model at temperature zero across presentation orders. **BFO and IOF Core are almost certainly in the generator's pretraining data,** so B0 is "no scaffolding supplied", not "no scaffolding known"; §8.4 quantifies the spontaneous alignment this produces. **Portability is argued, not tested:** no second corpus is run.
- **Instrument.** Tier A codes are exact with respect to the BFO 2020 axiomatization. Tier B codes are exact with respect to their SHACL/SPARQL formalisation; the residual question is whether the formalisation faithfully captures the BFO commitment, addressed by the source-linked codebook. Patterns not expressible as OWL entailments or SHACL constraints are invisible. The BFO-specific checks are scoped to B1/B2; the three-level ordering rests on the agnostic instruments and on Papers 2 and 3.
- **Statistical.** Power for B×D×R is limited; three-way interaction is exploratory only. Within-subject correlation structure assumed AR(1); misspecification would affect standard errors on round-related contrasts. Ten within-subject observations per run improve power for round-related effects but increase the risk of overfitting the trajectory shape.

### 11. Conclusion

---

## Part III — Paper 2

**Working title:** *Knowledge Graph Population from LLM-Generated Manufacturing Ontologies: Effects of Ontology Design and Iteration Depth*

**Target venue:** *Journal of Intelligent Manufacturing*, or *Computers in Industry*
**Target length:** 10,000–12,000 words

### 1. Introduction

1.1 Ontologies without instances answer no questions.
1.2 Population is the pipeline's second narrowing point: the question is whether the grounding, decomposition, and iteration effects observed in Paper 1 survive into a populated graph, or wash out.
1.3 The inherited variable — six ontology conditions × iteration round, with the factorial structure intact.
1.4 The evaluation problem restated: population scored without hand-annotated triples.
1.5 Contributions.

### 2. Background

2.1 KG population approaches: pipeline extraction versus schema-constrained generative extraction.
2.2 The ontology-first / extraction-first divide as motivation for testing schema effects on extraction.
2.3 Reference-free extraction evaluation.
2.4 Gap: population quality is almost never reported as a function of the schema, and almost never scored without hand annotation.

### 3. Research questions

- **RQ2.1** Does grounding B affect population fidelity, including the community structure of the populated graph?
- **RQ2.2** Does decomposition D affect population fidelity, including the community structure of the populated graph — in particular, whether D1's per-genre construction leaves a detectable genre-aligned community signature?
- **RQ2.3** Do B and D interact?
- **RQ2.4** Does the source-ontology structural quality profile (as measured by the Paper 1 battery) predict post-population reasoner inconsistency in the resulting KG? *(The predictor is the vector of Paper 1 outcome measures. Estimable on all 60 ontologies for grounding-agnostic predictors, and on 40 for BFO-specific predictors.)* **Floor contingency, pre-registered:** schema-constrained generative extraction may prevent inconsistency largely by construction, leaving this outcome at or near zero across all cells with no variance to predict. If observed inconsistency is below a pre-specified threshold, the analysis falls back in a fixed order to (i) near-violation counts — assertions satisfying the antecedent of a violated constraint but escaping it through missing type information, (ii) punning and type-assertion anomaly rates, and (iii) a declared null, reported as a substantive finding that schema constraint suffices to prevent formal inconsistency regardless of upstream construction strategy.
- **RQ2.5** What proportion of each ontology is actually used during population, and does grounding change it?
- **RQ2.6** Does iteration round affect population fidelity? Does a KG populated against an early-round ontology differ from one populated against the terminal R9 ontology? Does over-iteration degrade fidelity?
- **RQ2.7** Do B×R and D×R interactions from Paper 1 carry through to population outcomes? The resource-substitution question extended downstream.

### 4. Method

4.1 **Inputs.** The 600 ontology-states (60 runs × 10 rounds) plus the same source corpus.
4.2 **Population procedure.** Schema-constrained generative extraction; identical prompt template across conditions; only the schema varies.
4.3 Entity resolution, applied uniformly.
4.4 **Validation pass.** Reasoner-based consistency check of the populated KG against its own generating ontology.
4.5 **Seeds.** S-POP nested within S-GEN; decoding is greedy; the deterministic execution regime applies.
4.6 **Defensive handling of early-round ontologies.** Round-0 and round-1 schemas may be sparse, malformed, or missing class hierarchies. The population pipeline fails gracefully: an empty or near-empty schema produces an empty or near-empty KG, not an error. These cases are included rather than excluded, since they establish what iteration buys for population. Community-structure instruments (Leiden/CPM, genre-AMI) may produce degenerate outputs on near-empty KGs — a single community, an undefined partition, or a resolution profile with no stable plateau — for the same reason; these floor values are noted alongside the fidelity floor values rather than excluded, and the proportion of KGs with no identifiable plateau is reported per cell.

### 5. Reference-free fidelity measurement

5.1 **Entailment-verified precision.** Every extracted triple is verbalised and checked against its source passage by NLI. Per-triple precision with no annotation.
5.2 **Salience recall.** Recall against the automatically extracted salient-assertion inventory (Part I §8, asset 3), which is a distinct asset from Paper 1's salient-*term* inventory and is frozen on the same schedule.
5.3 **Consensus recall.** Descriptive only.
5.4 **Verifier validation.** The NLI verifier is characterised by injection of correct and mutated triples. Sensitivity and specificity reported with Wilson intervals. Style crossing (triples expressed against B1-style and B2-style schemas) measures whether verifier behaviour differs by schema richness.

*Why calibration here and not in Paper 1.* Paper 1's simplification removed the V1–V5 apparatus because no heuristic instrument remained to calibrate: Tier A codes are validated by the reasoner and Tier B codes by their own formalisation. The NLI verifier is a heuristic instrument with no oracle, so it needs exactly the calibration Paper 1 no longer requires. The standard is unchanged; the instruments differ. The same argument licenses the answer-matcher characterisation in Paper 3 §3.6.
5.5 **Schema-conformance outcomes:** post-population reasoner inconsistency rate.
5.6 **Utilisation outcomes:** ontology utilisation rate; population yield per 1,000 corpus tokens; orphan-instance rate.
5.7 **Community structure outcomes.** Leiden community detection (Traag, Waltman & van Eck 2019), applied uniformly to every populated KG, optimising the Constant Potts Model (Traag, Van Dooren & Nesterov 2011) rather than standard modularity as the primary objective function — a same-library, single-parameter choice that avoids the resolution limit modularity is known to have in denser or larger graphs, which matters here because B and D already change graph size and density (§5.6). Three specification decisions are fixed in advance rather than left to the implementation:

- **Resolution profile, not a single score.** A CPM objective value is not a normalised quality score and is not comparable across graphs of different size and density, which is precisely the situation here. Each KG is therefore partitioned across a pre-registered grid of resolution values γ, and the reported outcomes are profile-derived: the number of communities as a function of γ, the width of the stable plateau in that profile, and the partition at the plateau's centre. A single γ is additionally fixed in advance for the headline comparison, and its choice is reported with the profile that justifies it.
- **AMI, not NMI.** Normalised mutual information is not adjusted for chance and rises with the number of communities, and community counts will differ across conditions by construction, since B and D change graph size. Adjusted mutual information is used for the genre-alignment outcome; NMI is reported alongside for comparability with prior work.
- **Node-level genre labels.** Genre alignment needs a hard partition on the ground-truth side, but entities are typically mentioned across several genres. The rule is fixed: each node is labelled by the genre of the majority of the passages it was extracted from, ties broken by first mention; nodes whose majority share falls below a pre-registered purity threshold are assigned to an "ambiguous" label and excluded from the AMI computation, with the excluded proportion reported per cell as a measure of how well-defined the genre partition is in the first place.

Community outcomes are reported alongside graph size, density and yield so that structural differences are not confounded with yield differences. Standard modularity is also computed on every KG (§7.3) as an ancillary robustness comparison against CPM, not as a second confirmatory outcome.
5.8 **Why not a heterogeneous/multi-relational community-detection method.** The populated KGs are multi-relational (multiple typed predicates), which is exactly the setting heterogeneous-graph community detection targets. That literature is real but immature relative to Leiden/Louvain/Infomap: there is no single consolidated, published-and-validated standard comparable to what OOPS!, OntoQA, or the OWL reasoner already are for this dissertation's other instruments. Adopting one would trade a boring, defensible, single-parameter instrument for a less-validated method whose own behaviour would need characterising — the same kind of bespoke apparatus this dissertation has been actively removing (V1–V5, Tier C, the process-awareness formalism). Leiden run on the graph's homogeneous projection (nodes and edges, predicate type discarded) is treated as the appropriate off-the-shelf instrument; predicate-type structure is left as future work rather than folded into this battery.
5.9 **Statistical plan.** Mixed-effects models: B, D, R fixed; seed random (with S-POP nested within S-GEN). Round is a within-subject factor with AR(1) correlation structure. RQ2.1–2.3, RQ2.5–2.7 run on all three grounding levels; BFO-specific predictors in RQ2.4 fitted on B1/B2. RQ2.4 tested as a pre-registered regression of post-population reasoner-inconsistency rate on the Paper 1 structural quality vector. The plateau-centre partition's community count and genre-AMI enter the same B/D/R mixed-effects model as additional confirmatory outcomes under RQ2.1–2.3, with yield included as a covariate to guard against size/density confounds. Modularity is not entered into this model; it is analysed separately in §7.3.

**Table 1.** Fidelity instrument inventory and validation status.

### 6. Results

*Pre-specified shell.*

6.1 Verifier operating characteristics.
6.2 Descriptives by cell and round.
6.3 RQ2.1–2.3: main effects and interaction on precision and salience recall at R9.
6.3a **RQ2.1–2.3 extended: community structure.** Main effects and interaction on the plateau-partition community count and genre-AMI at R9, with yield as covariate and the resolution profile shown per condition; whether D1 produces a detectably more genre-aligned partition than D0. Ambiguous-node proportions reported per cell.
6.4 **RQ2.4: the structural-quality → inconsistency path.** Which Paper 1 measures predict post-population reasoner inconsistency? Estimated on the full set for grounding-agnostic predictors; on B1/B2 for BFO-specific.
6.5 RQ2.5: utilisation.
6.6 **RQ2.6: iteration round effect on fidelity.** Do early-round ontologies produce worse KGs?
6.7 **RQ2.7: B×R and D×R on population outcomes.** Does grounding substitute for iteration at the population stage?
6.8 Qualitative failure analysis by condition.

**Table 2.** Fidelity outcomes by cell at R9.
**Table 2b.** Fidelity trajectory: outcomes by round, summarised by condition.
**Table 3.** Inconsistency and utilisation rates by cell and round.
**Figure 2.** Interaction plot for entailment-verified precision at R9.
**Figure 3.** Fidelity trajectories by round, panelled by B, lines by D.
**Figure 4.** Scatter of Paper 1 structural quality composite against post-population reasoner-inconsistency rate.
**Figure 5.** Resolution profiles by cell and genre-AMI at R9, with yield-adjusted estimates alongside raw values.

### 7. Ancillary analysis

7.1 **Schema-free population baseline.** Open extraction with no schema constraint.
7.2 **Consensus-schema ceiling.** Population against the consensus ontology induced in Paper 1.
7.3 **CPM versus modularity: instrument comparison.** Standard modularity, computed on the same partitions, correlated against the plateau-partition CPM solution and against graph size/density/yield by cell. Divergence between the two that tracks density is treated as corroborating evidence for the resolution-limit concern in §9; agreement throughout is reported as robustness of the community-structure result to objective-function choice. Not a confirmatory test; no RQ is answered differently depending on its outcome.

### 8. Discussion

8.1 Whether the ontology-first / extraction-first bridge holds empirically.
8.2 Which schema properties help extraction — and whether they are the properties Paper 1's metrics reward.
8.2a Whether decomposition's per-genre construction is legible in the populated graph's community structure, and what that implies about D1 versus D0 as an integration strategy rather than just a construction-time convenience. Read alongside §7.3: if CPM and modularity agree, the result is reported as robust to instrument choice; if they diverge specifically in denser/higher-yield cells, that divergence is itself evidence that the resolution-limit concern is operating where predicted, and is discussed as an instrument-sensitivity finding rather than an inconsistency to explain away.
8.3 **The iteration trade-off at the population stage.** Whether additional iteration rounds improve fidelity enough to justify the cost, and whether grounding compresses that curve.
8.4 **If the RQ2.4 floor contingency fires.** If schema-constrained extraction prevents formal inconsistency largely by construction, that is itself a finding: upstream construction strategy does not matter for formal consistency because the extraction template absorbs it. Discussed as a substantive result rather than a fallback, since it answers the practitioner question of whether careful ontology engineering pays off at the population stage or whether the extraction harness renders it moot.
8.5 The same-corpus decision and what a held-out corpus would show.
8.6 Forward-link to Paper 3.
8.7 **Future work: process-awareness as its own research line.** Part-specific routing order and defect-propagation asymmetry are real properties of manufacturing KGs, but representing and validating them is a separate contribution from measuring whether construction strategy affects population fidelity. A follow-on paper could layer a process-awareness formalism on top of this design and ask whether construction-strategy effects further attenuate — or amplify — once process-specific constraints are checked.

### 9. Threats to validity

- NLI verifier precision ceiling. Style-dependent verifier behaviour measured directly; uniform error attenuates, condition-linked error biases.
- Salience recall inherits extractor biases.
- Single extraction model; schema-constrained extraction may favour some schema shapes.
- Same-corpus construction and population inflates absolute fidelity; relative comparisons remain valid.
- Early-round ontologies may produce degenerate KGs; these are informative but contribute floor values.
- Community-detection outcomes are sensitive to graph size and density, which themselves vary with B and D; yield is a covariate, CPM with a resolution profile replaces a single modularity score for this reason, but residual confounding cannot be fully ruled out.
- Genre-AMI presumes genre labels are available and meaningfully distinct at the passage level; where genre boundaries are fuzzy, the node-labelling rule pushes nodes into the ambiguous class and the metric is computed on a shrinking, possibly non-random subset. The excluded proportion is reported so the reader can judge this directly.
- Population is run on the same corpus the ontologies were built from, so the schema has seen the text; this inflates absolute fidelity and is why only relative comparisons are interpreted.
- Single community-detection algorithm (Leiden), applied to the graph's homogeneous projection; results characterise this algorithm's view of the graph, not community structure in general, and predicate-type structure is not used by the instrument (see §5.8's rationale for not adopting a heterogeneous/multi-relational method).

### 10. Conclusion

---

## Part IV — Paper 3

**Working title:** *Hybrid GraphRAG Root Cause Analysis over LLM-Populated Manufacturing Knowledge Graphs: Effects of Upstream Ontology Design and Iteration Depth*

**Target venue:** *Advanced Engineering Informatics*, or *Expert Systems with Applications*
**Target length:** 10,000–12,000 words

### 1. Introduction

1.1 RCA in electronics manufacturing; why defect causation questions are multi-hop and cross-genre.
1.2 Why plain vector RAG fails: causation lives in graph structure, not passage similarity.
1.3 The two-factor experiment plus iteration, carried through — does upstream design still register at the point of use?
1.4 The benchmark problem.
1.5 Contributions.

### 2. Background

2.1 GraphRAG and hybrid retrieval architectures.
2.2 The five retrieval mechanisms.
2.3 RCA in manufacturing.
2.4 Prior GraphRAG applications in industrial settings.
2.5 Automated benchmark construction.
2.6 Gap: GraphRAG evaluations hold the graph fixed and vary retrieval. This paper varies both, on an automatically constructed benchmark, with iteration depth as a third dimension.

### 3. Automated RCA benchmark construction

3.1 **Source A — mined held-out labels.** Corrective-action records with root cause extracted as a question–answer pair; root-cause statement redacted from the retrieval corpus.
3.2 **Redaction verification.** Automated leakage checking.
3.3 **Source B — synthetic scenario injection.** Causal chains constructed first; exact control over hop distance and causal type.
3.4 **Stratification and benchmark statistics.**
3.5 **Benchmark validation.** Recoverability established by construction (Source B) and bounded (Source A).
3.6 **Automated answer matching.** NLI-based entailment matching. Matcher characterised by injection of correct and mutated answers. Style crossing (ontology-vocabulary vs corpus-vocabulary phrasing) measures whether matcher behaviour varies with schema richness.

**Figure 1.** Benchmark construction pipeline.
**Table 1.** Benchmark composition by source and stratum.

### 4. Research questions

- **RQ3.1** Which retrieval mechanism parameters most affect RCA accuracy? *(Screening.)*
- **RQ3.2** Does upstream ontology condition affect RCA accuracy at optimised retrieval settings?
- **RQ3.3** Do retrieval parameters and ontology condition interact — does a better-structured graph change which retrieval strategy wins?
- **RQ3.4** Is the effect of ontology condition on RCA accuracy mediated by KG fidelity?
- **RQ3.5** Does iteration round affect RCA accuracy at the point of use? Tested at checkpoint rounds R0, R3, R6, R9.
- **RQ3.6** Does the B×R interaction carry through to RCA accuracy? Does grounding substitute for iteration at the RCA stage?

### 5. Method

5.1 System architecture; the five mechanisms as parameterised components.
5.2 **Design of experiments.** Two-stage:
- **Stage 1 (screening).** Resolution IV fractional factorial over retrieval parameters, run on **two ontology conditions at R9 — B0D0 and B2D1, the extremes of the design** — with the active-factor set taken as the union. Screening on a single condition would assume that factor activity is invariant to graph structure, which is exactly what RQ3.3 puts in question; a factor inactive on a sparse ungrounded graph could be active on a rich grounded one and would never reach Stage 2. The number of retained factors is capped in advance (Part I §12) so that Stage 2 stays tractable; the cap itself is set after the pilot, once per-run cost is known and the Stage 2 combinatorial can be costed concretely.
- **Stage 2 (confirmation).** Active retrieval factors, fully crossed with six B×D conditions and **four checkpoint rounds (R0, R3, R6, R9)** = 24 ontology-states per seed. Seed as block.

*Design rationale for four checkpoints.* Ten rounds × six conditions × multiple retrieval configurations would produce a combinatorial explosion. R0 (no iteration), R3 (early), R6 (mid), and R9 (terminal) are evenly spaced and capture the practically relevant questions — whether early stopping costs RCA accuracy and whether over-iteration degrades it — without fitting a full convergence curve at the RCA level. The full curve is available in Papers 1 and 2. Four points can fit a curve with an inflection, which is expected if there is rapid early improvement followed by plateau or decline.

5.3 Generation configuration; weights and runtime pinned per manifest; identical prompt across configurations. Seed S-RET governs DoE run-order randomisation and synthetic scenario generation.
5.4 **Retrieval-ablated control.** Answers generated with no retrieved content; establishes how much of RCA accuracy is generation-model prior.

**Figure 2.** System architecture with parameterised mechanisms.
**Table 2.** DoE structure, both stages.

### 6. Evaluation

6.1 **Accuracy:** root-cause identification accuracy at top-1 and top-3; mean reciprocal rank.
6.2 **Evidence quality, reference-free:** label-entity coverage; path plausibility (synthetic items); groundedness; hallucination rate.
6.3 **Efficiency:** retrieval latency; tokens retrieved; tokens generated.
6.4 **Statistical plan.** Mixed-effects models with retrieval factors, B, D, R, and interactions fixed; seed and scenario random. RQ3.4 via mediation with Paper 2 fidelity outcomes as mediator and bootstrapped indirect effects. RQ3.5 and RQ3.6 tested on the four checkpoint rounds.

**Longitudinal mediation (ancillary).** The trajectory-level mediation — does the *improvement trajectory* in structural quality predict the *improvement trajectory* in KG fidelity, which in turn predicts the *improvement trajectory* in RCA accuracy — is a growth-curve mediation model (multilevel SEM). Treated as an ancillary analysis with simpler treatment if time is constrained.

### 7. Results

*Pre-specified shell.*

7.1 Benchmark leakage bounds and matcher operating characteristics.
7.2 Retrieval-ablated control — the generation-prior floor.
7.3 Stage 1 screening: active retrieval factors and effect sizes.
7.4 Stage 2: ontology condition effects at optimised retrieval settings, at R9.
7.5 The retrieval × ontology interaction.
7.6 **RQ3.5: iteration-round effect on RCA accuracy.** R0 vs R3 vs R6 vs R9.
7.7 **RQ3.6: B×R interaction on RCA accuracy.** Does grounding substitute for iteration at the RCA stage?
7.8 Mediation: direct and indirect paths at R9.
7.9 **Longitudinal mediation (ancillary).** Trajectory-level mediation across rounds.
7.10 Performance by stratum, with attention to multi-hop and cross-genre items.
7.11 Mined versus synthetic item agreement.
7.12 Efficiency trade-offs.
7.13 Failure analysis.

**Table 3.** Screening effects.
**Table 4.** Accuracy by ontology condition and retrieval configuration at R9.
**Table 4b.** Accuracy by ontology condition at checkpoint rounds R0, R3, R6, R9.
**Figure 3.** Interaction plot: accuracy by retrieval configuration, lines by ontology condition.
**Figure 4.** Mediation path diagram with coefficients.
**Figure 5.** Accuracy by hop-distance stratum and condition.
**Figure 6.** Accuracy by checkpoint round, panelled by B, lines by D.

### 8. Discussion

8.1 Whether upstream ontology design survives to the point of use — and the honest reading if it does not.
8.2 Whether retrieval tuning is portable across graph structures.
8.3 Where the signal attenuates, read from the mediation results.
8.4 **The end-to-end resource-allocation question.** Given a fixed budget, spend on grounding, decomposition, iteration, or retrieval tuning? Synthesising the B×R findings across all three papers.
8.5 The automated benchmark as a transferable instrument.

### 9. Threats to validity

- Mined labels record what the investigation concluded, which may not be the true root cause.
- Redaction leakage; residual leakage inflates accuracy uniformly.
- Synthetic items may be easier or structurally unlike real ones; §7.11 tests this.
- Fractional factorial aliasing in Stage 1.
- Single generation model. NLI matcher precision ceiling.
- Retrieval-ablated control establishes a floor, but generation-model prior may still inflate accuracy when retrieval adds only marginal information.
- Mediation (RQ3.4) has a randomised treatment-to-mediator path but an observational mediator-to-outcome path: any unmeasured common cause of KG fidelity and RCA accuracy biases the indirect effect. Sequential ignorability is assumed and stated, and a sensitivity analysis over the assumed correlation of the two error terms is reported rather than the point estimate alone. Power for indirect effects at this sample size is limited and is reported as such.
- Four checkpoint rounds (R0, R3, R6, R9) cannot characterise the full RCA convergence curve; the full curve is available in Papers 1 and 2. B×D×R in Paper 3 is exploratory.

### 10. Conclusion

10.1 Findings.
10.2 The end-to-end picture across all three papers — grounding, decomposition, and iteration.
10.3 Future work: the excluded CCO arm; held-out population corpora; multi-model replication; battery transfer to a second domain.

---

## Parts V–VI — Implementation tasks

Moved to the companion file **dissertation_todo_v12.md**, which integrates the human-effort inventory and the sequenced next-actions list into a single task list with effort estimates and dependency tracking.

