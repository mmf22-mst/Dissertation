# Dissertation Overview and Paper Outlines

**Revision 20.** *Body text presents the current design only. Revision history is in the companion file **dissertation_change_logs_v20.md**. A glossary of technical terms is in Appendix B.*

The evaluation architecture is fully automated and reference-free. No gold reference ontology, no hand-annotated triple sample, and no expert-adjudicated root cause benchmark. Paper 1's instruments are either established tools with published validation (OOPS!, OWL reasoners, OntoQA-family structural metrics) or corpus-grounded coverage measures; Papers 2 and 3 add two NLI-based instruments (the triple verifier and the answer matcher) that are characterised by injection before use. The human contribution is the hand-authored competency question set, performed once and independent of the number of experimental runs.

---

## Part I — Dissertation Overview

### 1. Problem statement

Electronics manufacturers record what goes wrong on the shop floor in non-conformance reports, and they record how work should be done in requirements, work instructions, FMEAs, risk registers, and issue trackers. When a defect recurs, root cause analysis depends on connecting these sources:

- the non-conformance itself;
- the process step it occurred in;
- the failure modes already anticipated for that step;
- the risks and issues already raised against it.

In practice those connections live in engineers' heads and in documents that nobody reads together.

A knowledge graph can make those connections explicit and queryable, and large language models have made it affordable to build one from the documents themselves. Building it takes three steps:

1. Define the vocabulary of things and relationships the graph will use (an *ontology*).
2. Extract facts from the documents into that vocabulary (*population*).
3. Answer questions over the result (*retrieval*).

The first step is where the engineer has the most design freedom and the least guidance.

Three design choices dominate that first step:

- **Whether to start from a standard vocabulary.** The model can be handled three ways:
  - given nothing, and left to invent its own categories;
  - given a general-purpose upper ontology that fixes the top-level categories (BFO, standardised as ISO/IEC 21838-2);
  - given a manufacturing vocabulary built on BFO (IOF Core, from the Industrial Ontologies Foundry).
- **Whether to split the documents by type.** The model can work through all document types as one stream building one ontology, or build a separate ontology per document type and merge them.
- **How long to iterate.** After the first draft, automated checks can report errors and gaps back to the model for correction, round after round.

Each choice costs effort or compute. There is no evidence about whether any of them changes the quality of root cause analysis at the end of the pipeline. This dissertation measures that.

### 2. Thesis statement

**Thesis.** In LLM-driven construction of manufacturing knowledge graphs, three choices are separable design decisions:

- the choice of standard vocabulary;
- the decision to split the corpus by document type;
- the depth of automated iteration.

Their effects on the ontology can be traced — or shown to vanish — through knowledge graph population to root cause analysis accuracy, together with what each choice costs.

**Dissertation-level hypotheses.**

- *H0:* Ontology construction strategy (grounding B, decomposition D, iteration round R) has no effect on root cause analysis accuracy over the resulting knowledge graph.
- *H1:* At least one of B, D and R, or an interaction among them, changes root cause analysis accuracy.

Whether any such effect is carried by differences in the populated knowledge graph is a separate, subordinate question (H3, §7): H1 can hold with the effect running through knowledge graph fidelity, around it, or both. H1 is decomposed into the paper-level hypothesis chain in §7. Each paper is designed so that a null result at its stage is interpretable and publishable.

*On method.* All measurements are automated and require no reference ontology, no hand-annotated triples, and no expert-adjudicated benchmark. The one human asset is a hand-authored competency question set, written once. This makes the study repeatable at scale. It is a secondary contribution, not the thesis.

*On portability.* Every instrument except the competency question set is domain-general by construction, which makes redeployment cheap in principle. This dissertation does not demonstrate transfer: it runs on one corpus in one domain. Portability is argued from the construction of the instruments and costed in §9, not evidenced, and the conclusion says so.

### 3. What each result would tell a manufacturing engineer

The experiment is built to inform three decisions an engineer makes before building a knowledge graph from shop-floor documents, plus one question about how the decisions combine. Each row reads a decision against the two outcomes the design can distinguish.

| Decision | If the effect is real | If it is null | What the engineer does with the answer |
|---|---|---|---|
| **Start from a standard vocabulary (B)** | Grounded ontologies populate cleaner graphs and answer more root-cause questions; the manufacturing vocabulary (IOF Core) adds to plain BFO, or does not | Supplying BFO or IOF Core in the prompt changes what the model builds but not what the graph can answer | Whether adopting IOF Core is worth the learning and conformance effort, and whether plain BFO is enough |
| **Split the corpus by document type (D)** | Per-genre construction covers the dense genres better, and the gain survives merging and population | Genre-blocked processing in one stream is as good; merging is a cost with no return | Whether to build one ontology or one per document type, and how much merge tooling to invest in |
| **Iterate under automated feedback (R)** | Quality rises to a plateau within a few rounds; over-iteration does or does not degrade it | Feedback fixes what the checker reports but changes nothing downstream | How many rounds to budget and when to stop |
| **Do the choices combine? (B × D, B × R, D × R)** | Grounding matters most when the corpus is one stream; grounding or decomposition shortens the climb | The choices contribute independently | Whether the investments are substitutes (pick one) or complements (do all), under a fixed budget |

**If everything is null.** A null at every stage is the cheapest outcome for practice: it means that, for a mid-size open model at temperature zero, the three choices can be made on cost and convenience alone. The design is built so that this reading is available rather than embarrassing. Each stage is pre-registered with its own null. The instruments that feed the iteration loop are reported as compliance, not quality, so a "the model fixed what it was told to fix" result cannot masquerade as an effect. The mediation analysis in Paper 3 says where a signal died if it did. Paper 1 stands on its own as the first crossed evaluation of these levers, and Paper 2 stands on its population-fidelity instruments, whatever Paper 3 finds.

### 4. The construct → populate → exploit pipeline

| Stage | Paper | Artefact produced | Question |
|---|---|---|---|
| Construct | 1 | 6 ontology conditions × 10 seeds × 10 round states | Do grounding, decomposition, and iteration change what the LLM builds? |
| Populate | 2 | Populated KGs at four checkpoint rounds (R0, R3, R6, R9) | Do those differences survive population? |
| Exploit | 3 | RCA answers under hybrid GraphRAG retrieval, at the same checkpoint rounds | Do they change answer quality? |

The pipeline is deliberately *narrowing*: each stage risks washing out the upstream signal. Documenting where and whether the signal dies is itself a result, and the design pre-commits to reporting a null at any stage rather than reframing it.

### 5. Unified experimental design

Two crossed between-subject factors and one within-subject factor, held constant across all three papers.

**Factor B — Base ontology grounding (3 levels)**

| Level | Label | Supplied to the generator |
|---|---|---|
| B0 | Ungrounded | No upper or mid-level ontology; instructions on OWL 2 DL syntax only |
| B1 | BFO-grounded | BFO 2020 classes and relations, with definitions (76 entries) |
| B2 | IOF-grounded | IOF Core classes and relations with definitions, including the BFO layer IOF Core imports (174 entries) |

The levels form a gradient: nothing; upper-level categories only; upper-level categories plus manufacturing vocabulary. IOF Core is the manufacturing choice because its classes (plan specification, manufacturing process, business process, and so on) target the domain directly and it is built on BFO. The Common Core Ontologies (CCO), the principal general-purpose alternative, are not a condition: their vocabulary is about ten times IOF Core's, and under the fixed prompt budget this design requires the comparison would mainly measure truncation (Appendix A.4); it is named as future work (Paper 3 §10.3). Exact source files, versions, and the small difference between the BFO build B1 uses and the one IOF Core imports are specified in Appendix A.

**Factor D — Corpus decomposition (2 levels)**

| Level | Label | Procedure |
|---|---|---|
| D0 | Monolithic | Sequential accumulation into a single ontology over genre-blind chunks of the concatenated corpus, presented in the same genre-blocked order D1 uses |
| D1 | Hierarchical | One sub-ontology per document genre (six genres, *G* = 6), each built by the same sequential accumulation within its genre, then an integration pass; sub-ontologies persist and are the objects of iteration, with integration re-run each round |

**What the D contrast actually is.** The corpus exceeds any usable context window, so neither level is a literal single-shot generation; both accumulate over chunks. Presentation order is held constant between the two levels within a seed: documents reach the generator genre-blocked in both cases (all of genre 1, then all of genre 2, and so on). What differs is the *partition* — whether the accumulating artefact is one ontology or several that are integrated at the end.

**What the D contrast estimates, given that choice.** Holding order constant removes presentation order as a confound, which is why it is worth doing, but it narrows what D measures. Because D0's documents arrive genre-blocked, D0 already processes one genre at a time; it is genre-*ordered* without being genre-*partitioned*. The remaining manipulation is therefore the explicit partition into separate artefacts plus the integration pass, not genre-awareness in general. That is the practitioner's actual decision, so it is the right estimand — but it biases toward the null relative to a design that also scrambled D0's order, and a flat H1b should be read in that light rather than as evidence that genre-awareness does not matter. The size of that bias is not measured in this design; an order-shuffled D0 arm is named as future work.

**Chunk boundaries are genre-blind under D0.** The corpus is concatenated in the genre-blocked order and chunked by token budget alone, so boundary chunks may straddle two genres. Aligning boundaries to genre would turn D0 into D1 with the partition removed and push the contrast further from the decision under study. The number of straddling chunks is recorded in the manifest and reported per seed.

**Context-overflow policy (both D levels).** The accumulated D0 ontology grows as it goes, so later chunks are eventually processed against an artefact that no longer fits alongside them; D1's per-genre sub-ontologies are smaller and hit it less often (integration is deterministic and involves no model call, so it never windows). One policy applies to both, chosen because it neither discards structure silently (truncation) nor inserts a second generative step into construction (summarisation):

- **Deterministic windowing.** When the artefact exceeds the pinned window allotment (Paper 1 §4.2), the generator is shown a selected view rather than the whole ontology. Because the window allotment is fixed independently of the Factor B injection, windowing fires at the same artefact size in every grounding condition. The selection rule is fixed and seed-independent: the ancestor closure of every class whose label matches a term in the current chunk above the pinned similarity threshold; then those classes' siblings and direct children up to a fixed fan-out cap; then remaining budget filled in descending match-score order, ties broken by IRI sort. The injected scaffolding for Factor B is not part of the window and is always present in full.
- **Edit-merge semantics.** In every call the model outputs a complete revised version of what it was shown — the whole ontology when it fits, the selected view when windowing fires. The model never emits a patch format. When windowing has fired, the pipeline differences the output against the view it supplied and applies the resulting patch (added and removed axioms and entities) to the full artefact; applying the output as a replacement would delete everything the model could not see. The patch is validated to touch only entities present in the window or newly introduced. Entities present in the view but absent from the output count as deletions, so unintended drops are possible; added and removed entity counts are logged per call and reported, and the pilot examines the removal rate.
- **Windowing in iteration rounds.** The same rule applies to feedback calls (R1–R9), with one substitution: the matching text that seeds the window is the feedback payload rather than a corpus chunk, so the view is built around the entities the feedback names. Under D1 the sub-ontologies are iterated individually and rarely exceed the allotment; the integrated artefact is not itself iterated.
- **Visibility statistics.** The proportion of the artefact visible at each chunk, and the count of chunks processed under a degraded view, are recorded per run and reported by processing position and by genre. Under genre-blocked order this degradation concentrates on whichever genre is processed last, which is why S-GEN varies genre order across seeds (Paper 1 §4.5.1).

**Integration procedure for D1.** Sub-ontologies are merged by a fully deterministic two-stage procedure fixed in advance: (1) label normalisation, IRI reconciliation, and raw union; (2) LogMap alignment-based reconciliation — LogMap identifies equivalent classes and properties across sub-ontologies that use different IRIs, and a deterministic rule (lexicographically first IRI) selects the canonical form, with owl:equivalentClass declarations added for transparency. AML is run over the same inputs as an audit comparison; agreement between the two matchers is reported (Paper 1 §6.15). No LLM call is involved in integration. Sub-ontology generation plus integration together constitute the R0 state for D1, so that R0 denotes "the first complete artefact, before any feedback" at both D levels.

**What iterates under D1, and why it is the sub-ontologies.** Under D1 the sub-ontologies persist as first-class artefacts and are the objects of feedback; integration is re-run each round to produce that round's evaluable state. The alternative — iterating the merged artefact and discarding the sub-ontologies after R0 — is rejected because it cancels the manipulation. Once merged, a D1 artefact is the same size as a D0 artefact, sits under the same windowing rule, and is seen in the same proportion, so the narrower-scope advantage that H1f attributes to decomposition would exist for one round and be absent for the other nine. Iterating the sub-ontologies keeps decomposition operative across the whole trajectory, which is what the hypothesis is about.

**Deterministic re-integration.** Because the merge procedure is fully deterministic, the same sub-ontology inputs always produce the same integrated artefact. There is no merge variance and no need for anchoring — integration is simply re-run each round from the current sub-ontologies. Round-to-round differences in the integrated artefact are caused entirely by sub-ontology changes (from iteration feedback), never by merge instability. IRI stability is still tracked because LogMap alignments may shift across rounds as sub-ontologies evolve; this is deterministic but not necessarily stable, and the stability rate is reported (Paper 1 §6.15).

**What this costs.** A D1 round is *G* sub-ontology calls against D0's one call — with six genres, six times the per-round compute. Integration adds no LLM calls (it is deterministic), but it adds compute for LogMap alignment. Round therefore stops being a matched unit of work across D, and H1f read against round index alone would partly say "D1 converges faster because D1 receives more model calls per round." This is the same shape of confound as the feedback-volume asymmetry across B, and gets the same treatment: per-round cost is logged, convergence is reported against cumulative tokens as well as round index, and the cost-adjusted comparison in Paper 1 §6.14 carries confirmatory weight for H1f rather than serving as a supplementary view. Feedback volume also diverges — *G* reports per round against one — and is logged as a covariate.

**Factor R — Iteration round (10 levels, within-subject)**

| Level | Label | State |
|---|---|---|
| R0 | No iteration | Raw generation output before any feedback |
| R1–R8 | Intermediate rounds | After 1–8 rounds of feedback |
| R9 | Final | After 9 rounds; the terminal ontology state |

The round count is set high enough that the plateau is observable for all conditions, including those that converge slowly, and that over-iteration degradation — if it occurs — is detectable. Where the plateau falls, and whether quality ever declines with further iteration, are themselves dependent variables. The round at which each condition plateaus is not known in advance and is one of the quantities the experiment measures.

R = 9 is currently a judgement, not a result. The pre-campaign pilot (todo task 5) runs the two extreme conditions (B0D0, B2D1) to R = 15 on four seeds precisely to settle it — four rather than two so that the variance estimate the minimum-detectable-effect calculation uses (Paper 1 §5.4) has more than one degree of freedom. If the pilot shows plateaus well before R9, the round count drops and the campaign shrinks; if trajectories are still moving at R9, it rises. The number is confirmed or revised before pre-registration, not defended after the fact. The checkpoint rounds Papers 2 and 3 use follow the terminal round by the rule under Scale below.

Round is a within-subject repeated measure: every ontology traverses all ten states in fixed order. R0 is included as a "no iteration" baseline. Instrument measurements at R0 may hit floor or ceiling values for some measures; these are noted rather than excluded, since they establish what iteration buys.

**Cells:** B0D0, B0D1, B1D0, B1D1, B2D0, B2D1 — each at rounds 0–9.

**Blocking:** generation seed, *k* = 10 (settled). Each seed runs through all six cells, giving matched sets and paired contrasts.

**Scale:**

- **Paper 1:** 60 terminal ontologies (6 cells × 10 seeds); 600 evaluated ontology-states (60 × 10 rounds).
- **Papers 2 and 3:** consume four checkpoint rounds — 240 ontology-states, 240 populated KGs, 24 ontology-states per seed. **Checkpoint rule:** the checkpoints are R0 plus three rounds evenly spaced to the terminal round; with R = 9 they are R0, R3, R6, R9. The count (four) is fixed; the positions follow the terminal round. If the pilot revises the round count, the checkpoints move with it, and every later reference to R3, R6 and R9 in this document reads as the corresponding rescaled rounds.
- **D1 sub-ontology battery runs:** under D1 the battery also runs over each of the six persisting sub-ontologies at the four checkpoint rounds, to support the integration-loss measure. That adds 30 runs × 4 checkpoints × 6 genres = 720 battery executions. Integration loss is descriptive, so the full ten-round trace is not needed; the round-to-round delta rate and IRI stability, which are cheap, are still computed at every round on the integrated artefact. This affects battery compute but not the number of ontology-states carried downstream.

### 6. The evaluation battery

#### 6.1 Design principle

No reference ontology. The corpus is the ground truth for coverage; established tools provide quality measurement; and the downstream papers provide the primary test of the hypothesis. The battery is evaluated at every round state (R0–R9) of every ontology, producing 600 evaluated ontology-states.

#### 6.2 Corpus-grounded coverage

**(a) Salient-term coverage — recall against the source, not against a human artefact.**

The corpus is the ground truth. Salient domain terms are extracted automatically from the construction sample (§8, asset 1) using a combination of statistical termhood scoring (C-value/NC-value, TF-IDF against a general-language background corpus) and embedding-based keyphrase extraction, producing a ranked salient-term inventory per genre. Coverage is the proportion of high-salience corpus terms represented in the ontology as a class or a property, matched on the entity's label by embedding similarity above a calibrated threshold. A term that appears only inside a definition text does not count: under the feedback loop a definition mention would be a costless way to satisfy a "missing term" report, and it gives the knowledge graph no vocabulary element to populate against.

This is more defensible than gold-reference recall, not less: it measures whether the ontology covers what the documents actually talk about, rather than whether it matches what one ontology engineer happened to build.

*Representativeness.* Coverage is also reported, descriptively, against a reference inventory extracted from a much larger portion of the collection (the saturation-curve extraction, §8 asset 1). The gap between the two figures shows how much of the collection's vocabulary the construction sample could have supplied.

**(b) Genre coverage balance.** Entropy over per-genre salient-term coverage.

It targets the predicted D0 failure mode of uneven coverage across genres. The construction sample keeps the collection's imbalance in compressed form (square-root allocation, §8 asset 1): the two record genres, NCRs and Jira issues, supply most of the text. Unevenness under D0 is therefore predicted from two sources:

- volume: the record genres dominate the accumulating artefact;
- processing position: genres processed late meet a larger artefact and more windowed views.

Genre differences in term density are a third, uncontrolled source, reported descriptively.

**(c) Competency question answerability.**

The set contains about 108 hand-authored competency questions:

- 6 genres × 4 question types (existential, definitional, relational, multi-hop) × 4 per cell = 96;
- plus 12 cross-genre multi-hop questions.

Each CQ is paired with a SPARQL query; answerability is the proportion returning a non-empty result. The set is frozen after the corpus is frozen and before any generation run. It is tagged by question type and genre, and per-stratum answerability is reported alongside the aggregate. This follows standard practice (Grüninger & Fox 1995; Ren et al. 2014; Wiśniewski et al. 2019).

*Label normalisation.* The CQ queries locate classes by label pattern. Ontologies built under different grounding levels use different labelling conventions — CamelCase against spaced words, singular against plural, hyphenated against not — so an unnormalised pattern would make part of any grounding effect a labelling artefact. Before scoring, every entity in the evaluated ontology receives a normalised scoring label computed by a fixed rule: split CamelCase and underscores, lower-case, strip punctuation, collapse whitespace, singularise the head noun. The CQ patterns match against the normalised label; the artefact itself is not modified, and the normalised label exists only in the scoring copy. The rule is pinned before the CQ set is frozen, and the share of pattern hits that arrive only through normalisation, rather than through the raw label, is reported per condition as a diagnostic of how far labelling conventions differ.

*Primary and secondary strata.* The salient-term coverage report fed back each round (§6.7) tells the model which corpus terms are missing. An existential or definitional CQ can therefore become answerable simply because the model added a class with the right label. That is salient-term coverage measured a second way, not independent evidence.

- **Primary: relational and multi-hop strata (60 CQs).** Each of these queries must join at least two label-matched classes through an object property path. Answering them requires structure that the coverage feedback does not supply.
- **Secondary: existential and definitional strata (48 CQs).**

The residual coupling — relational queries still depend on the labels being present — is declared rather than eliminated.

#### 6.3 Manipulation checks

A manipulation check confirms that each condition actually used the vocabulary it was given. A single SPARQL query walks each domain class's asserted superclass chain and classifies the class by the first standard-vocabulary ancestor it reaches:

- **IOF-aligned**;
- **BFO-only-aligned** (reaches BFO without passing through IOF);
- **unaligned**.

The query also recognises CCO ancestors (**CCO-aligned**). No condition is given CCO, so any CCO alignment is pretraining leakage. The rule cascade and its one special case are specified in Appendix A.

**Expected pattern and contamination signal.**

| | BFO-only aligned | IOF aligned | CCO aligned | Unaligned |
|---|---|---|---|---|
| B0 | ≈ 0 | ≈ 0 | ≈ 0 | ≈ all |
| B1 | high | ≈ 0 | ≈ 0 | remainder |
| B2 | low (bypass) | high | ≈ 0 | remainder |

**Contamination** is any nonzero count in a column the condition was not given vocabulary for:

- B0 with anything > 0 in the first three columns;
- B1 with IOF > 0 or CCO > 0;
- B2 with CCO > 0.

B2 with high BFO-only is bypass (the model attached to BFO despite IOF vocabulary being available), not contamination. Contamination counts are reported descriptively per condition. If any condition shows contamination above 5% of domain classes, the report discusses whether pretraining exposure threatens the manipulation.

**Coupling.** All alignment rates are reported by the conformance channel in the feedback payload, so the model is partly told to improve the quantities used to verify the manipulation. Alignment rates at R0 are the clean manipulation check; later rounds show how the manipulation is maintained under feedback.

**Scope limit.** Alignment rates measure vocabulary *presence*, not *correctness*. A high rate is compatible with misuse of the categories. For example, placing a process (something that happens) under an object category (something that persists) would still count as aligned. Any condition-linked misuse is invisible at this level and becomes visible only through downstream measures in Papers 2 and 3. BFO-specific modelling checks are outside the scope of this dissertation and are named as future work.

#### 6.4 Structural and logical quality

- **OWL 2 DL profile conformance:** binary pass/fail plus violation count.
- **Logical consistency and class satisfiability:** reasoner classification; global consistency, unsatisfiable class count, root unsatisfiable class count.
- **Structural profile:** inheritance richness, relationship richness, attribute richness, class count, maximum and mean depth, orphan rate (OntoQA; Tartir et al. 2005).
- **OOPS! pitfall counts:** pitfall counts by severity (critical, important, minor); Poveda-Villalón et al. 2014.

#### 6.5 The full instrument inventory

| Family | Instruments | Scope | Loop status |
|---|---|---|---|
| Manipulation check | BFO-only alignment rate; IOF alignment rate; CCO alignment rate (contamination only) | All levels | Coupled (conformance channel) |
| Corpus grounding | Salient-term coverage; genre coverage balance | All levels | **Coupled** (coverage channel) |
| Corpus grounding | CQ answerability — relational and multi-hop strata (primary); existential and definitional strata (secondary) | All levels | Held out (indirect coupling via labels, §6.2(c)) |
| Logical quality | Consistency; unsatisfiable classes; OWL 2 DL conformance | All levels | **Coupled** |
| Structural profile | OntoQA metrics | All levels | **Coupled** (via OOPS! channel) |
| Structural profile | OOPS! pitfall counts | All levels | **Coupled** |
| Cost | Cumulative tokens; wall-clock time; cost per round; feedback payload tokens and flagged-item counts | All levels | n/a |

All instruments run across all three grounding levels and are evaluated at every round state (R0–R9).

#### 6.6 Limitations of the battery

Four limits, stated plainly and carried into every limitations section:

1. **No correctness anchor.** The battery measures corpus fidelity, logical soundness, and structural profile. It cannot certify that an ontology is *right* in a way an expert would endorse. Claims are restated as specific named properties rather than "quality."
2. **The battery does not measure BFO-specific modelling correctness.** Alignment rates confirm that the generator used the vocabulary it was given, but they do not detect misuse of categories. Heuristic modelling errors — such as category conflation, role misassignment, or information/carrier confusion — that are consistent with OWL semantics are outside the battery's scope. If these errors vary systematically across conditions, that variation is invisible in Paper 1 and becomes visible only through downstream measures in Papers 2 and 3.
3. **The CQ set is hand-authored and domain-specific.** The ~108 questions do not transfer to other corpora without re-authoring, and they may be shallow or incomplete. Their label-based queries are also indirectly coupled to the coverage feedback, which is why only the relational and multi-hop strata are primary (§6.2(c)).
4. **Part of the battery is coupled to the iteration loop.** See §6.7. For the coupled instruments, improvement across rounds is partly definitional, and only the R0 contrast is a clean between-condition comparison.

#### 6.7 Loop-coupled and held-out instruments

Iteration needs a corrective signal, and any instrument used as that signal cannot also serve as an independent measure of whether iteration worked. The coupling is therefore declared and bounded.

**What is in the loop.** The feedback payload is six items: the reasoner report (global consistency and the list of unsatisfiable classes), the OWL 2 DL profile report, the OOPS! pitfall report, the conformance report, the salient-term coverage report (missing corpus terms by genre), and the genre coverage balance report (per-genre coverage entropy). These are the corrective signal; removing any of them would leave iteration with less to act on and would make H1d uninterpretable in the opposite direction. The payload occupies a pinned feedback allotment in the iteration prompt; how the six items are ordered and truncated within it is fixed in advance (Paper 1 §4.2).

**Why OOPS! stays in, given the cost.** Withholding a free, established, automated signal would make the artefacts worse than a competent practitioner would build, and those artefacts are the input to Papers 2 and 3. Since downstream usefulness is what the dissertation is ultimately measuring, depressing artefact quality to protect one secondary Paper 1 outcome is the wrong trade. Loop realism is an external-validity asset: the construction procedure being evaluated should be the one a practitioner would actually run. The accounting below absorbs the cost rather than the design paying it.

**Why salient-term coverage and genre coverage balance enter the loop.** The same standing-priority logic applies. Both instruments produce directly actionable feedback: the coverage report tells the LLM which corpus terms are missing, and the genre balance report tells it which genres are underrepresented. A practitioner who had these signals would use them. Withholding them would depress artefact quality for Papers 2 and 3 to protect secondary Paper 1 outcomes — the same trade rejected for OOPS! above.

**Why CQ answerability stays out.** Holding out CQs is well-motivated on two independent grounds. First, CQ feedback is not actionable for the LLM: acting on it would require reading SPARQL queries, inferring what structural patterns each expects, and reverse-engineering what the ontology is missing — a much harder inference chain than "add this missing term" or "fix this pitfall." Second, it preserves the cleanest independent measure of whether iteration works at the ontology level. Because the CQ set is small (about 108 questions), feeding it back would also risk overfitting: the LLM might add shallow structures that satisfy SPARQL patterns without genuinely modelling the domain. CQ answerability is not fully independent of the loop: §6.2(c) describes its indirect coupling through the coverage channel and why only the relational and multi-hop strata are primary.

**Consequences for inference.** The coupled measures are global consistency, unsatisfiable-class count, OWL 2 DL conformance, OOPS! pitfall counts, OntoQA structural profile, the alignment rates, salient-term coverage, and genre coverage balance. For these:

- **R0 is clean.** At R0 no feedback has been applied, so R0 values are legitimate confirmatory outcomes for the between-condition hypotheses H1a, H1b and H1c. The designated R0 confirmatory family is listed in §7; the remaining coupled measures are descriptive at R0.
- **R1–R9 are not.** Improvement on a coupled instrument across rounds is partly definitional: the model is handed the scorecard. Coupled trajectories are reported as *process* evidence that the loop is doing what it was designed to do, not as confirmatory support for H1d, H1e or H1f.
- **Floor effects are expected and are not findings.** Most artefacts should reach consistency within a few rounds, collapsing variance on the coupled measures. This is anticipated, pre-registered, and reported as a convergence fact rather than analysed as an effect.
- **Confirmatory round-related inference rests on CQ answerability on the relational and multi-hop strata (the held-out primary outcome) and on the downstream measures in Papers 2 and 3,** which are never fed back into the ontology loop. CQ answerability is the primary held-out outcome for H1d–H1f in Paper 1; KG fidelity (Paper 2) and RCA accuracy (Paper 3) provide independent confirmatory evidence at the downstream pipeline stages.
- **Coupled trajectories are reported as compliance, and that is worth reporting.** "Did the model fix what it was explicitly told to fix, and did compliance differ by condition?" is a real question with a practitioner-relevant answer. It is labelled compliance, not quality improvement, wherever it appears.

**No pitfall suppression.** The full OOPS! report is fed back. With OntoQA also coupled, there is no held-out structural metric to protect.

### 7. Hypothesis chain

**H1 (Paper 1).**
- H1a — Grounding B affects ontology quality. Tested across all three levels on the grounding-agnostic instruments. Prediction: B1 outperforms B0, and B2 outperforms B1. Pre-registered contrasts: B1 − B0 and B2 − B1. Coupled measures (consistency, OWL 2 DL conformance, OOPS! pitfall counts, OntoQA structural profile, alignment rates, salient-term coverage, genre coverage balance) contribute at R0 only.
- H1b — Decomposition D affects domain coverage: D1 achieves higher CQ answerability (primary) than D0, and higher genre coverage balance at R0 (secondary, tested in the R0 confirmatory family).
- H1c — B and D interact: grounding matters more under D0 than under D1, because decomposition supplies structure that grounding would otherwise have to provide.
  - **Stated as a contrast:** the primary estimand is (B2 − B0 | D0) − (B2 − B0 | D1) on the grounding-agnostic instruments, predicted to be positive in the direction of better quality.
  - The omnibus B×D term (3×2) is tested first; the contrast is the pre-registered decomposition.
  - Simple effects of B within each D level are descriptive support, not the test.
- **H1d — Iteration improves quality, with diminishing returns and possible degradation (round main effect).** Instruments improve from R0 toward a plateau, but over-iteration may degrade quality if the model begins introducing new errors while fixing old ones, or if feedback-driven edits destabilise previously correct structure. The round at which plateau occurs and whether post-plateau degradation is detectable are both measured.
- **H1e — Grounding changes convergence rate (B×R interaction).** B2 converges faster than B1, which converges faster than B0, because richer scaffolding constrains the generator and reduces the work iteration must do. This is the resource-substitution hypothesis: grounding and iteration are partially fungible. Grounding may also shift the plateau round or affect susceptibility to over-iteration degradation.
  - The competing explanation — that grounded conditions simply receive more corrective signal per round — is addressed two ways: by covariate adjustment and by the conformance-channel ablation (Paper 1 §4.4, §7.1). H1e is supported only if the effect survives both.
  - The ablation covers B2 only; the B1 contrasts rest on covariate adjustment alone.
- **H1f — Decomposition changes convergence rate (D×R interaction).** D1 converges faster than D0, because genre-scoped sub-problems are individually simpler.
- **B×D×R is exploratory.** The three-way interaction is reported descriptively in a figure; no confirmatory hypothesis is attached.

**Scope restriction on H1d–H1f.** Confirmatory tests of the three round-related hypotheses are run on CQ answerability on the relational and multi-hop strata (§6.2(c), §6.7) in Paper 1, and on KG fidelity and RCA accuracy in Papers 2 and 3. The coupled instruments are reported alongside as process evidence, clearly labelled, and are not counted toward support for any of the three.

**Primary outcome per hypothesis.** CQ answerability on the relational and multi-hop strata is the sole primary outcome for H1a–H1f. It is held out of the feedback loop, and it requires structure that the coverage feedback does not supply. There is no co-primary.

Secondary outcomes are reported with effect sizes and intervals, in two groups:

- **R0 confirmatory family** (coupled instruments; tested for H1a–H1c at R0 only; Holm-corrected as one family): salient-term coverage, genre coverage balance, global consistency, unsatisfiable-class rate, OWL 2 DL conformance. From R1 onward these are compliance evidence (§6.7).
- **Descriptive secondaries:** existential and definitional CQ strata at all rounds; OOPS! pitfall counts, OntoQA structural profile and alignment rates at R0; and every other instrument — reported with effect sizes and intervals, not tested.

**H2 (Paper 2).** Differences attributable to B, D, and R produce measurable differences in population fidelity — entailment-verified precision, salience recall, post-population reasoner-inconsistency rate, and community structure (CPM resolution profile and genre-aligned AMI). The round effects carry through: a KG populated against an R0 ontology has lower fidelity than one populated against the R9 ontology from the same run, tested at the checkpoint rounds R0, R3, R6, R9.

**H3 (Paper 3).** Differences in KG fidelity produce measurable differences in RCA accuracy, and the effect of ontology condition on RCA accuracy is at least partially mediated by KG fidelity. Checkpoint-round contrasts test whether iteration level matters at the point of use.

### 8. Shared research assets

All frozen before any experimental run. All are generated or authored once and then run unsupervised.

1. **The corpus: two disjoint frozen samples.** Electronics manufacturing documentation in six genres:
   - requirements (DPBPS);
   - work instructions (Command Media);
   - FMEAs;
   - non-conformance reports (NCRs);
   - Jira issues;
   - Active Risk Management records.

   The source collection holds on the order of a million NCRs, a million Jira issues, tens of thousands of pages of requirements and work instructions, about 10,000 dense risk records, and about 1,000 dense FMEAs. Two disjoint samples are drawn from it:

   - **Construction sample (A)**, used by Paper 1. Ontologies are built only from A. Assets 2 and 4 are derived from A.
   - **Population sample (B)**, used by Papers 2 and 3. Every KG is populated from B, so each ontology is tested on documents it was not built from — the deployment situation, in which a schema is built once and new records keep arriving. Asset 3 and the Paper 3 retrieval corpus are derived from B.

   **Construction sample (A): size.** Total size *T*<sub>A</sub> is set from per-genre saturation curves. For each genre, salient terms are extracted from nested random samples of increasing size, and new-term discovery is plotted against tokens sampled. *T*<sub>A</sub> is chosen where the curves flatten, subject to a compute ceiling from the throughput benchmark. The curves are reported in Paper 1's methods.

   **Construction sample (A): allocation.** *T*<sub>A</sub> is divided across genres in proportion to the square root of each genre's measured token total in the collection. This is a standard compromise in stratified sampling between proportional allocation (which would give NCRs and Jira about 94% of the text) and equal allocation (which would remove the volume imbalance H1b depends on). Illustratively, it gives the two record genres about 74% and each dense genre 6–7%.

   **Construction sample (A): floor.** A pre-registered floor guarantees each genre enough text for a stable term inventory. Stability means the top-ranked terms extracted from two random halves of the genre's sample largely agree. If a genre's full collection is smaller than its share, the whole genre is included and the shortfall is recorded.

   **Population sample (B).** Size *T*<sub>B</sub> = *T*<sub>A</sub>, drawn from the remainder with the same square-root allocation and floor, so the two samples are matched in size and genre proportions. Population from a larger sample, up to the full remainder of the collection, is named as future work (Paper 3 §10.3) rather than run: triple verification and reasoner checking do not scale to it, and the deployment-scale question is separable from the construction-strategy question this dissertation asks. *T*<sub>B</sub> and its allocation are pre-registered.

   **Rules for both samples:**

   - *Whole documents.* Documents are sampled whole, never truncated, by simple random sampling without replacement within genre. Each sample has its own corpus-sampling seed, recorded with the asset; these are fixed asset parameters, not replication seeds.
   - *Disjointness.* No document appears in both samples, and B is drawn from what remains after A.
   - *Linked NCRs.* Population sample B includes a pre-registered minimum number of NCRs linked to a Corrective Action Report, because those links anchor the Paper 3 benchmark (asset 9).
   - *Corrective Action Reports are excluded from both samples.* They are the source of the Paper 3 root-cause labels and are held out entirely. Root-cause statements that also appear in linked documents in either sample (NCR dispositions, Jira comments, risk records) are redacted.
   - *Synthetic scenarios go into B only.* The Paper 3 synthetic causal-chain scenarios (Source B) are written as documents in the corpus genres and inserted into the population sample. The ontologies never see them, as with real defects that arise after a schema is built. A scenario can fail because the ontology lacks a needed concept; that failure is measurement, not noise.

   **Freeze order.**
   1. Measure token totals for each genre over the full collection.
   2. Run the saturation curves; set *T*<sub>A</sub> and the floor.
   3. Draw A.
   4. Draw B from the remainder.
   5. Redact both samples.
   6. Insert the synthetic scenarios into B.
   7. Run the leakage check on both samples.
   8. Freeze and hash.

   De-identification is documented. For each sample, document counts, token counts and genre proportions are recorded in the manifest and reported in every paper. The release position is stated explicitly: whether the corpus can be published, and if not, which public surrogate corpus a replication should use.
2. **The salient-term inventory.** Auto-extracted per genre from the construction sample (A), with the extractor and its parameters pinned.
3. **The salient-assertion inventory** (Paper 2). Auto-extracted subject–predicate–object candidates from the population sample (B) against which salience recall is computed, with the extractor and its parameters pinned. Distinct from the term inventory and frozen on the same schedule.
4. **The CQ set.** About 108 hand-authored competency questions with SPARQL translations, tagged by question type and genre relevance, and calibrated against the construction sample. The relational and multi-hop strata are designated primary. Frozen after the corpus and before generation.
5. **The alignment-rate query.** A single SPARQL query implementing the alignment cascade specified in Appendix A. Versioned and pinned.
6. **The pinned-release set.** The B1 and B2 injection sources and the CCO release used as the reference for the query's contamination rule. File names, versions, and hashes are listed in Appendix A and recorded in the seed register.
7. **The model manifest.** Pinned for the duration of all campaigns:
   - **Generator:** `google/gemma-4-26B-A4B-it` at a recorded revision hash; bf16 weights; loaded text-only; thinking mode off (unless the pilot comparison, todo task 5, favours on, in which case it is on everywhere).
   - **Serving runtime:** vLLM at a pinned version, with batch-invariant mode enabled (`VLLM_BATCH_INVARIANT=1`). Each replica runs on one GPU, with no tensor parallelism. Prefix caching is enabled only if the determinism audit passes with it (Paper 1 §4.5.4).
   - **Hardware:** 8×NVIDIA B200 (4TB host memory). All eight GPUs serve generation during Paper 1. In Papers 2–3, seven serve generation and one serves the NLI verifier, the embedding model, and the answer matcher.
   - **Other models:** revision and runtime recorded for the NLI verifier (Paper 2), the NLI answer matcher (Paper 3), and the embedding model used in salient-term matching.
8. **The entailment-based triple verifier** (Paper 2).
9. **The held-out root-cause label set** (Paper 3). Mined automatically from Corrective Action Reports, which are excluded from both samples. Each label is anchored to a linked NCR in the population sample (B). Matching root-cause text in linked documents is redacted in both samples before freeze (asset 1).
10. **The seed register and environment manifest.** A single frozen document covering all three papers, recording every seed, what it governs, and the execution environment. Four seed roles: **S-GEN** (ontology generation, Paper 1), **S-POP** (KG population, Paper 2, nested within S-GEN), **S-RET** (retrieval DoE randomisation and synthetic scenario generation, Paper 3; scenario generation executes before corpus freeze), **S-HAR** (any stochastic component of the battery instruments — embedding-based term extraction). The two corpus-sampling seeds (construction sample A, population sample B) and the saturation-curve sampling seed are fixed asset parameters recorded in the register, not replication seeds.

### 9. Portability

The battery is designed to be rerun on a different corpus, domain, or base ontology. What a new deployment must supply:

| Must be supplied by hand | Automatic |
|---|---|
| The corpus | Salient-term extraction |
| A genre map (which documents are of which genre) | Structural metrics, OOPS!, OWL 2 DL conformance |
| The source files each grounding condition uses, with their import chains resolved | Alignment-rate query (generic SPARQL; the special-case rule in Appendix A may need updating for a different mid-level) |
| The CQ set and its SPARQL translations | CQ scoring |
| An execution environment and its manifest | Seed register generation and output hashing |
| — | Population verification |
| — | RCA label mining, if corrective-action records exist |

The CQ set is the only asset that does not transfer without re-authoring. All other instruments are domain-general by construction. A new deployment re-runs the battery at compute cost and modest human cost (~3–5 days for a new CQ set).

This is an argument from construction, not a demonstration. No second corpus is run in this dissertation, so portability is a designed property and a costing, not a finding. The conclusion states it that way, and a second-domain replication is named as future work.

### 10. Contributions

1. **An end-to-end empirical trace of whether upstream ontology design — and the iteration investment — survives to downstream root cause analysis performance**, including the practitioner question of whether grounding substitutes for iteration.
2. **The first crossed factorial evaluation of upper-ontology grounding against corpus decomposition for LLM-generated manufacturing ontologies**, with iteration depth as a within-subject dimension and a testable interaction hypothesis.
3. An evaluation battery combining established structural metrics (OntoQA, OOPS!), corpus-grounded coverage measures, and an alignment-rate manipulation check with built-in contamination detection. It is applied without a reference ontology and at every iteration round.
4. Released artefacts: generators, battery scripts (including the alignment-rate query), the CQ set, and all 60 × 10 ontology-states (the ontology-states subject to employer clearance, §11).

A process-awareness formalism encoding part-specific routing order and defect-propagation asymmetry is a natural extension of the pipeline and is identified as a candidate follow-on paper rather than pursued within this dissertation.

### 11. Cross-cutting risks

| Risk | Mitigation |
|---|---|
| Effects wash out by Paper 3 | Pre-register the null; mediation localises attenuation; Papers 1 and 2 retain standalone value |
| BFO-specific modelling correctness is not measured directly | Alignment rates confirm the manipulation; downstream effects carry the signal; stated as a scope limit |
| Alignment rates measure vocabulary presence, not correctness | Acknowledged; any condition-linked misuse effect is detectable in Papers 2–3 via post-population inconsistency, fidelity measures, and RCA accuracy |
| Heuristic modelling patterns outside the battery's scope | Any effect is detectable downstream in Papers 2–3 via post-population reasoner inconsistency, fidelity measures, and RCA accuracy |
| Instruments coupled to the feedback loop | Coupling declared in §6.7; coupled measures confirmatory at R0 only; CQ primary restricted to relational and multi-hop strata to limit indirect coupling through labels (§6.2(c)); round-related confirmatory inference rests on those strata and on Papers 2–3 |
| Feedback volume increases with grounding level, mimicking H1e | Payload tokens and flagged-item counts logged per round and carried as a covariate; conformance-channel ablation on B2 (Paper 1 §7.1), with B0 as the naturally ablated baseline |
| BFO and IOF are present in the generator's pretraining data, so B0 is not a true no-upper-ontology condition | B0 is defined as "no scaffolding supplied in context", not "no scaffolding known"; the alignment-rate query's contamination signal quantifies spontaneous BFO/IOF usage in B0 (and IOF leakage in B1) at R0 and is reported as a finding in its own right; > 5% triggers explicit discussion |
| D1 rounds cost more than D0 rounds, inflating H1f | Per-round cost logged; convergence reported against cumulative tokens as well as round index; Paper 1 §6.14 carries confirmatory weight, and H1f requires both readings to agree |
| Merge variance masquerading as trajectory movement under D1 | Eliminated: deterministic integration (union + LogMap); same sub-ontology inputs always produce the same integrated artefact; IRI stability logged per round |
| Cross-genre defects invisible to a per-sub-ontology feedback loop | Feedback computed on the integrated artefact and routed to all involved sub-ontologies (Paper 1 §4.4a) |
| Presentation order confounded with D | Order held constant across D within a seed; genre order varied across seeds; the narrowed estimand is declared (Part I §5); an order-shuffled D0 arm is future work |
| Late-processed genres disadvantaged by context overflow under D0 | Deterministic windowing with patch-based merge rather than truncation; visibility statistics reported by position and genre; genre order varied across seeds |
| R = 9 chosen without convergence data | Pre-campaign pilot at R = 15 on the extreme conditions, four seeds; round count confirmed or revised before the main campaign; checkpoint rounds follow the rule in §5 |
| CQs shallow or incomplete | Stratify by question type; report per stratum; downstream measures in Papers 2–3 provide independent confirmation |
| Underpowering | *k* = 10 settled; MDE computed per outcome scope from the four-seed pilot's variance; B×D×R is exploratory, not confirmatory |
| Context-budget confound between B levels | Window, chunk and feedback allotments pinned independently of the injection; the injection rendering format is fixed in advance and declared; the residual total-length difference is the treatment itself and is declared, not padded |
| Feedback payload grows with ontology size and grounding level, and could exceed the context | Pinned feedback allotment with a pre-registered item order and per-item truncation caps (Paper 1 §4.2); truncation events logged and reported per condition |
| Per-call output grows with the artefact, lengthening the sequential D0 stream | Output length measured at the pinned window allotment in the throughput benchmark before *T*<sub>A</sub> is set (§12); the levers are pre-specified there |
| Release of artefacts built from employer data requires IP clearance | Clearance requested at design approval, not at submission; fallback release is generators, battery scripts, the alignment-rate query and the CQ set, with ontology-states released conditionally |
| Environment drift over a multi-month campaign | Self-hosted weights and fixed GPU allocation; full environment manifest; output hashes |
| Autocorrelated round observations | Model AR(1) or similar within-subject correlation structure; 10 within-subject observations per run are correlated, not independent |
| Round-0 ontologies may hit instrument floors | Include R0 as baseline with floor values noted; instrument behaviour at floor is informative about what iteration buys |
| Over-iteration degradation may be condition-dependent | Monitored as an explicit DV; post-plateau trajectory shape reported by condition |
| Paper 3 DoE complexity with round threaded through | Use four checkpoint rounds (R0, R3, R6, R9) rather than all ten; B×D×R interaction in Paper 3 is exploratory |
| Root-cause text leaks into the corpus the ontologies and KGs are built from | Corrective Action Reports excluded from both samples; linked root-cause text redacted and leakage-checked before freeze |
| Construction sample misses concepts the collection contains | Sample size set from per-genre saturation curves; coverage also reported against a larger reference inventory (§6.2(a)) |
| Schema has seen the text it is populated from, inflating fidelity | Eliminated: population uses a disjoint sample (§8, asset 1) |
| Paper 2 compute (population passes, triple verification, reasoner checking) | Paper 2 runs on the four checkpoint rounds (240 KGs) by design; population sample fixed at *T*<sub>A</sub>; triple verification on a pinned per-KG sample (Paper 2 §5.1); reasoner check under a pinned timeout with a uniform fallback (Paper 2 §4.4) |
| CQ answerability partly reflects labelling conventions rather than structure | Fixed label-normalisation rule applied in the scoring copy before matching (§6.2(c)); normalisation-only hit share reported per condition |
| Batch-invariant execution fails the determinism audit | Fallback pre-registered: batch size 1 for Paper 1 construction; batched execution with a measured replicate-noise estimate for population and RCA |

### 12. Campaign sizing

These are the run counts the design implies, with indicative times for the pinned platform: gemma-4-26B-A4B-it on 8×B200, batch-invariant batching, one GPU per replica. The times come from a roofline estimate. The throughput benchmark replaces them before the pre-registration is finalised.

| Stage | Unit | Count | Driver | Indicative time |
|---|---|---|---|---|
| Paper 1 construction (R0) | Generation calls | 60 runs, all concurrent. A D0 run is one sequential stream of *T*<sub>A</sub> ÷ chunk allotment calls. A D1 run is six genre streams in parallel, each shorter. That gives 210 concurrent streams | *T*<sub>A</sub>; chunk allotment; per-call latency (~20 s while the artefact is small; see the note below) | ~1.5 days for *T*<sub>A</sub> ≈ 50M tokens; the D0 runs are the critical path |
| Paper 1 feedback rounds | Generation calls | 60 runs × 9 rounds; one call per round under D0, six parallel calls under D1 | Ontology size | Small next to R0 |
| Paper 1 battery | Instrument runs | 600 whole-artefact states plus 720 D1 sub-ontology evaluations at the checkpoint rounds; reasoner classification and the OOPS! scan dominate | Ontology size; reasoner timeout | CPU-bound; runs alongside generation |
| Paper 2 population | Extraction passes over population sample B | 240 (checkpoint rounds R0, R3, R6, R9) | *T*<sub>B</sub> = *T*<sub>A</sub> | ~0.6–1.2 days for *T*<sub>B</sub> ≈ 50M tokens |
| Paper 2 verification | NLI verifications | 240 × *n* = 2,000 sampled triples per KG = 480,000 | Pinned sample size *n* | Hours on one GPU |
| Paper 2 community structure | Leiden runs | 240 × resolution-profile points | Profile granularity; KG size | CPU-bound; uses host memory |
| Paper 3 Stage 1 | RCA runs | Screening design size × benchmark size × 2 screening conditions (B0D0, B2D1) | Fractional factorial resolution | Set after the pilot |
| Paper 3 Stage 2 | RCA runs | 4 retrieval configurations (two retained two-level factors; a third only if pilot cost permits) × 6 conditions × 4 checkpoint rounds × 10 seeds × ~200 benchmark items ≈ 192,000, plus ~48,000 for the retrieval-ablated control | Retained-factor cap; benchmark size | Confirmed after the pilot |

The estimate assumes a ~30K-token construction prompt, 8K-token chunks, 60% of peak memory bandwidth and 40% of peak compute. **Output length is the unsettled term.** The model regenerates the view it was shown (Part I §5), so output per call grows with the artefact up to the window allotment rather than staying at a small patch; the ~20 s per-call figure holds only while the artefact is small. Because D0 construction is a single sequential stream, per-call latency at full window size sets the run length, and the throughput benchmark (todo task 0c) must measure it at the pinned window allotment before *T*<sub>A</sub> is set. If the measured figure makes D0 runs impractically long, the levers are, in order: a smaller window allotment, a smaller *T*<sub>A</sub>, and — as a design change rather than a sizing choice — a delta output format. Batch-invariant kernels cost some throughput, which the benchmark measures.

Three levers control the cost:

- **Construction sample size *T*<sub>A</sub>.** It is set by the saturation curves, and compute acts only as a ceiling. Paper 1 construction is limited by per-stream latency, not total throughput, so a larger *T*<sub>A</sub> lengthens every run.
- **Population sample size *T*<sub>B</sub>.** Fixed at *T*<sub>A</sub> (§8, asset 1). Population is throughput-bound and parallel; at this size the binding costs are triple verification, which is sampled (Paper 2 §5.1), and reasoner checking, which runs under a pinned timeout with a uniform fallback (Paper 2 §4.4).
- **Paper 3 Stage 2 retained-factor cap.** Two retained factors give 4 configurations × 240 ontology-states × ~200 items. A third factor doubles Stage 2 and is added only if the pilot's measured cost per RCA run leaves headroom. The cap is fixed in the pre-registration, not after seeing Stage 1 results.

---

## Part II — Paper 1

**Working title:** *Grounding, Decomposition, or Iteration? A Crossed Factorial Study of LLM-Generated Manufacturing Ontologies*

**Target venue:** *Journal of Intelligent Manufacturing*, or *Journal of Manufacturing Systems*
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
2.3 Standards-based foundations: BFO as ISO/IEC 21838-2; IOF Core as a BFO-conformant manufacturing mid-level. CCO is noted as the principal general-purpose alternative, with the reason it is not a condition here (Part I §5; Appendix A.4). Release and build details are in the methods appendix (Appendix A).
2.4 Modularisation and integration.
2.5 **Ontology evaluation.** Gold-standard, task-based, application-based, and data-driven paradigms; OntoQA as a reference-free structural framework (Tartir et al. 2005); OQuaRE as a quality-model framework (Duque-Ramos et al. 2011); OOPS! as automated pitfall detection (Poveda-Villalón et al. 2014); WiseOWL (Dalal et al. 2026) as a recent automated structural/semantic evaluation combining documentation coverage, BERT-based definition quality, connectivity, and hierarchical balance. The persistent reliance on hand-built references and what it costs.
2.6 **Iterative refinement of LLM outputs.** Self-correction and tool-augmented iteration in LLM generation; convergence behaviour under feedback.
2.7 Gap statement: the uncrossed factors, the uncharacterised iteration trajectories, and the reliance on reference ontologies.

### 3. Evaluation battery

3.1 **Design principle.** No reference ontology. Battery evaluated at every round state (R0–R9).
3.2 **Salient-term coverage** and genre coverage balance (both loop-coupled; confirmatory at R0, compliance evidence thereafter).
3.3 **Competency question answerability.** About 108 hand-authored CQs with automated SPARQL scoring, stratified by question type. The relational and multi-hop strata are primary; existential and definitional strata are secondary (Part I §6.2(c)).
3.4 **Structural profile and pitfall detection.** OntoQA metrics and OOPS! pitfall counts by severity (both loop-coupled; confirmatory at R0, compliance evidence thereafter). Full OOPS! report fed back with no pitfall suppression.
3.5 **Logical quality.** OWL 2 DL conformance; consistency and satisfiability.
3.6 **Manipulation checks.** BFO-only and IOF alignment rates, with CCO alignment as a contamination signal (Part I §6.3; Appendix A). Contamination reported for B0, B1, and B2.

**Figure 1.** Battery architecture — corpus in, instrument battery out.
**Table 1.** Instrument inventory: family, instruments, scope.

### 4. Experimental design

4.1 Factors and levels; the 3×2×10 cell table (B×D×R); what each cell represents as a practitioner decision.
4.2 **Injection protocol for Factor B, and the four-allotment prompt.** The prompt has four variable parts, and only one of them is the manipulation. A construction call carries the first three; an iteration call replaces the chunk with the feedback payload:

| Allotment | Contents | Varies with B? |
|---|---|---|
| **Injection** | The Factor B scaffolding: nothing for B0; `bfo-core.owl` inventory for B1; resolved `Core.rdf` inventory (BFO + IOF) for B2 | **Yes — this is the manipulation** |
| **Window** | The view onto the accumulated ontology (Part I §5) | No — pinned |
| **Chunk** | The corpus text processed in this call (construction calls) | No — pinned |
| **Feedback** | The six-item feedback payload (iteration calls, §4.4) | No — pinned; content varies, the ceiling does not |

The window, chunk and feedback allotments are fixed once, at values that fit comfortably under B2's injection (the largest), and reused unchanged for B0 and B1.

**Feedback allotment and truncation rule.** The payload is rendered in a fixed order — (1) reasoner report, (2) OWL 2 DL profile report, (3) OOPS! pitfall report, (4) conformance report, (5) salient-term coverage report, (6) genre coverage balance report — and the summary line of every item is always present. Only the list-valued parts (unsatisfiable classes, profile violations, pitfalls, missing terms) can grow. Each list is truncated to a per-item cap in a deterministic order — pitfalls by severity then IRI, missing terms by salience rank then genre, the rest by IRI — and each truncated list ends with a count of omitted entries. The caps are pinned with the allotments before the pilot and pre-registered. Truncation events and omitted counts are logged per item, per round, per condition, so the pilot and the campaign report how often each condition's feedback was cut. Because the ceiling is identical everywhere, no condition is told more than the allotment allows; what still differs within it is content, which is the treatment (see the feedback-volume confound, §4.4). Under D1 the rule applies to each sub-ontology's routed payload (§4.4a), so every iteration call, at either D level, sits under the same ceiling.

A single shared budget that the four parts competed for would have two defects:

- It would leave chunk size, chunk count, and windowing frequency free to drift with injection length, so incidental properties of the pipeline would vary with the treatment.
- Worse, the richest condition's injection would compete directly with its window. The most heavily grounded condition would hit degraded views earliest and most often — a mechanism capable of suppressing quality and masking the grounding effect the design exists to measure.

Fixed allotments remove both. Five things are identical across grounding levels by construction: corpus exposure per call, the number of accumulation steps, how much of the artefact the model can see, how often windowing fires, and the ceiling on feedback per round.

**No exemplars.** The prompts contain no few-shot exemplars. Apart from the corpus chunk (construction) or the feedback payload (iteration), the only vocabulary the generator receives is the Factor B injection, so B0 receives none, and no example ontology can leak BFO- or IOF-style modelling into any condition.

**Injection sources.** Each grounded condition receives the package its source organisation ships, unmodified ("the treatment is the package"). B2 therefore includes the BFO build that IOF Core imports, which differs slightly from the build B1 uses. Source files, versions, and the build difference are in Appendix A.

**Injection rendering.** B1 and B2 injections are produced by a deterministic renderer. It extracts class and relation labels with their definitions and orders them alphabetically on label, with ties broken by IRI. The injection allotment is sized to hold B2's full inventory, so neither grounded condition is truncated. Rendered sizes are B1: 76 labelled entries (2,673 words) and B2: 174 entries (5,138 words). Token counts on the pinned model's tokenizer are recorded when the allotment is pinned.

The rendering format (structured summary rather than raw OWL) is fixed in advance and not ablated. It is declared as a design choice in §9.

**Total prompt length is not equalised, and B0 is not padded.** With the other three allotments fixed, the residual difference in total prompt length across B is exactly the treatment: B2's prompt is longer because it contains more vocabulary. Padding B0 with filler would not control for anything — it would add a third manipulation and dilute attention without contributing content. What remains is attention dilution over a longer prompt, which cannot be designed away and is recorded in §9 as a stated limit rather than a mitigated one. The concern is empirically grounded: Levy, Jacoby & Goldberg (ACL 2024) show that LLM reasoning degrades with input length alone — even when the added content is relevant — and Liu et al. (TACL 2024) document positional attention bias that concentrates on prompt boundaries. Both effects operate at the scale of the B0/B2 length difference, and padding would worsen both rather than control for either.

**Cost.** Every condition runs at the chunk count B2's allotment implies, so the campaign is sized by the worst case rather than the average (§12). This is accepted deliberately: the alternative buys compute at the price of confounding the manipulation with pipeline mechanics.

The conformance-channel ablation (§7.1) tests the feedback-side counterpart of the injection.
4.3 **Generation procedure for Factor D.** Sequential accumulation over chunks at both levels. Presentation order is genre-blocked and identical across D within a seed; D0 chunks the concatenated stream by token budget, genre-blind, so boundary chunks may straddle genres; D1 chunks within genre and closes R0 with an integration pass, after which the sub-ontologies persist and integration is re-run (deterministically) at every round. Integration is deterministic label normalisation, IRI reconciliation, and LogMap alignment-based reconciliation (AML as audit comparison, §6.15); no LLM call is involved. Context overflow at either level is handled by the deterministic windowing rule and patch-based edit merge specified in Part I §5, with visibility statistics logged per chunk. Prompt templates in appendix, differing only in manipulated content. Chunk count, chunk size, straddling-chunk count, integration statistics, and windowed-chunk counts are reported per condition, since they are the operational content of the D manipulation.
4.4 **Fixed iteration protocol.** Nine rounds of feedback. The round count is set high enough that the convergence plateau is observable for all conditions and that over-iteration degradation — if it occurs — is detectable. Where the plateau falls and whether quality ever declines with further iteration are themselves dependent variables and are not assumed in advance. The ontology state is saved after each round, including the raw R0 state before any feedback.

**Feedback design.** Every round receives exactly the same prompt structure: the current ontology (or its windowed view, Part I §5) and fresh feedback on it. The model outputs the complete revised ontology or view; the pipeline computes the patch (Part I §5). The payload is six items — the reasoner report (global consistency and unsatisfiable classes), the OWL 2 DL profile report, the full OOPS! pitfall report, the conformance report, the salient-term coverage report (missing corpus terms by genre), and the genre coverage balance report (per-genre coverage entropy). OOPS! is fed back deliberately and without pitfall suppression, and the coverage instruments are fed back because they produce directly actionable feedback (missing terms, underrepresented genres): the loop is meant to be the one a practitioner would run, and the resulting coupling — including its propagation to OntoQA through structural pitfall remediations — is accounted for rather than avoided (Part I §6.7). No accumulated history from prior rounds is carried forward. The model does not know which round it is on, how many rounds remain, or what it changed in prior rounds. This ensures that each round's edit decisions are conditioned only on the ontology-as-it-stands and its current feedback, not on a growing narrative or a round-position signal. Any trajectory pattern in the data is therefore attributable to the ontology's state, not to the model adjusting its strategy based on round position. The pinned feedback allotment (§4.2) also removes context-budget variation across rounds and conditions: every iteration call has the same length ceiling regardless of round or grounding level. Payload content varies within that ceiling and is logged — tokens, flagged-item counts, truncation events — which is what the feedback-volume covariate below uses.

No human judgement enters the loop, and the sole held-out instrument is never fed back: CQ answerability. Holding out CQs is motivated on two independent grounds: (1) CQ feedback is not actionable — acting on it requires reading SPARQL queries and reverse-engineering missing structural patterns, a much harder inference chain than "add this missing term"; and (2) the small CQ set (about 108 questions) creates an overfitting risk if fed back. What *is* fed back is coupled to its corresponding outcomes by construction, and Part I §6.7 states what follows for inference.

**The feedback-volume confound.** For B0 the conformance report is trivially empty (no BFO or IOF terms to check). For B1 it reports BFO alignment. For B2 it reports BFO and IOF alignment. Prompt structure and payload format are identical across grounding levels, but *information content* increases with grounding richness. That matters because H1e predicts exactly the same ordering of convergence rates that differential feedback volume would produce on its own. Three measures address it:

- **Measurement.** Feedback payload tokens, flagged-item counts and truncation events are logged per item, per round, per condition and reported as descriptives, so the size of the asymmetry is visible rather than assumed away.
- **Adjustment.** Payload volume enters the H1e model as a covariate. The resource-substitution claim is evaluated on the grounding effect that survives adjustment.
- **Ablation.** §7.1 runs B2D0 with the conformance section suppressed, leaving the other five payload items. B0's conformance report is empty by construction, so B0D0 on the same seeds is already the ablated baseline. If B2's rate advantage over B0 persists without the conformance channel, the resource-substitution reading is supported. If it disappears, the effect was feedback volume.

Unadjusted H1e results are reported alongside adjusted ones in all cases.

4.4a **Feedback routing under D1.** Feedback is computed on the *integrated* artefact, then routed to the sub-ontology or sub-ontologies that can act on it. Computing it per sub-ontology in isolation would be clean and parallel but blind to everything the integration creates — cross-genre disjointness violations, duplicate classes landing under conflicting parents, relation signature clashes between genres — which are precisely the defects decomposition causes. A loop that fixes the easy errors and preserves the interesting ones is worse than useless for H1f.

The routing rule, fixed in advance:

- A defect whose participating entities all originate in one sub-ontology is routed to that sub-ontology's feedback section.
- A defect spanning entities from two or more sub-ontologies is routed to *all* involved sub-ontologies. Each sub-ontology sees the defect and can address its own side of the conflict.
- Provenance for routing comes from the IRI provenance map built during integration; entities with ambiguous provenance (e.g. redirected IRIs claimed by multiple sub-ontologies) route to all claiming sub-ontologies.

There is no integration feedback channel — the merge is deterministic and has no LLM call to receive feedback. Cross-genre defects that persist across rounds are measured as integration loss (§5.3), which is an honest measure of what decomposition costs. The split between single-source and multi-source defects, per round and per condition, is reported: it directly measures where decomposition's costs land.

D0 has no routing: all feedback attaches to the single artefact.

4.5 **Seeds, blocking, and the seed register.**
- 4.5.1 *What the seed governs.* S-GEN fixes document presentation order within genre, chunk boundaries, and **genre processing order, which varies across seeds and is held identical between D0 and D1 within a seed**. Paired contrasts are preserved, and which genre is processed last — the one most exposed to windowed views under D0 — is averaged over rather than fixed by an arbitrary choice.
- 4.5.2 *Decoding regime.* Greedy decoding; seed variance estimates sensitivity to corpus presentation order — a meaningful quantity reported in §6.3.
- 4.5.3 *Execution determinism with batching.* Generation runs on vLLM with batch-invariant mode enabled. Under that mode, a request's output does not depend on batch size or on the other requests in the batch. Each replica uses one GPU (no tensor parallelism), with fixed kernel settings and greedy decoding. Replicas are identical, so the number of replicas can change between stages without changing outputs. Prefix caching is enabled only if the audit (§4.5.4) shows identical outputs with it on and off. All 60 runs execute concurrently, and D1 genre sub-ontologies are built in parallel.
- 4.5.4 *Determinism audit.* Before the campaign, outputs are hashed and compared under five conditions:

  1. three repeat runs of one configuration under an identical seed;
  2. the same prompts at batch size 1 and at campaign batch sizes;
  3. the same prompts on different replicas;
  4. the same prompts under concurrent load, with continuous batching;
  5. prefix caching on versus off.

  The audit covers construction, feedback, and extraction prompts. Matching hashes confirm bitwise reproducibility. The fallback is pre-registered:

  - If conditions 1–4 fail, Paper 1 construction reverts to batch size 1. Population and RCA remain batched, with divergence measured on a replicate subset and reported.
  - If only condition 5 fails, prefix caching stays disabled.
- 4.5.5 *Seed count and allocation.* *k* = 10, settled. S-POP nested within S-GEN; S-RET and S-HAR independent.

**Table 1b.** Seed register and environment manifest fields.

4.6 **Environment manifest and drift check.** Manifest captured automatically per run. One full seed set re-run at end of campaign against recorded hashes.
4.7 Pre-registration.

**Figure 2.** Design schematic.

### 5. Measures and analysis

5.1 **Manipulation checks.** BFO-only and IOF alignment rates, with CCO alignment as contamination, by condition and round. The expected ordering for total alignment is B2 > B1 > B0, with the BFO-only / IOF partition distinguishing B1 from B2.
5.2 **Primary and confirmatory secondary outcomes** (pre-registered). Outcomes are named individually. No composite is formed, because an unspecified composite is a researcher-degrees-of-freedom hole in a pre-registered design.

- *Primary — all three grounding levels, all rounds:* CQ answerability, relational and multi-hop strata. The sole primary for H1a–H1f; there is no co-primary.
- *R0 confirmatory family — all three grounding levels, R0 only:* salient-term coverage; genre coverage balance (the instrument built for H1b's predicted D0 failure mode); global consistency; unsatisfiable-class rate; OWL 2 DL conformance. Tested for H1a–H1c at R0, Holm-corrected as one family.
- *Descriptive secondary — all rounds:* CQ answerability, existential and definitional strata.

The R0-only restriction on the confirmatory family follows from loop coupling (Part I §6.7), not from any doubt about the instruments themselves.

5.3 **Secondary and process outcomes:** OntoQA structural profile; cumulative token cost and wall-clock time; feedback payload volume. **D1 integration descriptives:** integration loss — the battery delta between the union of the sub-ontologies and the integrated artefact, computed at the four checkpoint rounds on the grounding-agnostic instruments, which quantifies how much quality the deterministic merge loses and whether that varies with grounding. Salient-term coverage on a sub-ontology is scored against that genre's inventory, not the whole-corpus inventory. Round-to-round delta rate (the proportion of axioms that change in the integrated artefact between consecutive rounds, caused entirely by sub-ontology iteration, not merge variance); IRI stability across rounds (including LogMap alignment stability as sub-ontologies evolve); and the defect-routing split between single-source and multi-source defects. **Position-gradient descriptives:** per-genre salient-term coverage by processing position, which tests the recency/primacy mechanism behind H1b more directly than the entropy-based genre coverage balance does; straddling-chunk counts; and windowed-chunk counts by position and genre, with the proportion of the artefact visible. **Loop-coupled trajectories** (consistency, unsatisfiable-class rate, OWL 2 DL conformance, OOPS! pitfall counts, OntoQA structural profile, alignment rates across R1–R9) are reported as process evidence that the loop functions, labelled as such in every table, and excluded from confirmatory tests of H1d, H1e and H1f.

5.4 **Statistical plan.** Mixed-effects models: B, D, and R fixed; seed random. R is a within-subject repeated measure with an AR(1) correlation structure. Binomial GLMM or beta regression for proportions; linear mixed-effects models for continuous scores.

**Trajectory model (primary specification for H1d–H1f).** The round-related hypotheses are about *rates of convergence*, and an interaction term on a polynomial trajectory does not estimate a rate. For each run and each held-out instrument, a three-parameter asymptotic regression is fitted:

> *y*(R) = *a* − (*a* − *f*) · exp(−*c* · R)

with *f* the R0 floor, *a* the asymptote, and *c* the rate constant. H1d is then a test that *a* exceeds *f*; H1e is a test of the *c* parameter across B; H1f is a test of *c* across D. Plateau round is derived from the fitted *c* with an interval rather than read off a heuristic threshold. Over-iteration degradation is tested by a quadratic extension and by a pre-registered test for a negative slope over R6–R9. Where the asymptotic model fails to converge for a run, that run is reported as non-convergent and handled by a pre-specified rule rather than dropped silently.

**Secondary specification.** The B×R and D×R interaction terms in the mixed-effects model are retained and reported alongside the fitted-parameter results. Agreement between the two specifications is reported as robustness; disagreement is reported and discussed rather than resolved by selection.

Pre-registered contrasts:
- *B main effect:* B1–B0, B2–B1 (all instruments, all levels).
- *D main effect:* D1–D0.
- *R main effect:* R9–R0 (total change); modelled as a continuous or polynomial trajectory, with the plateau round and any post-plateau degradation characterised.
- *B×D interaction:* H1c — the omnibus B×D term (3×2), then the pre-registered contrast (B2 − B0 | D0) − (B2 − B0 | D1). Simple effects of B within each D level are descriptive support, not the test.
- *B×R interaction:* H1e — does grounding change convergence rate? Rate constants for all three B levels.
- *D×R interaction:* H1f — does decomposition change convergence rate?
- *B×D×R:* exploratory, reported in a figure, no confirmatory test.

Holm correction within families. On the primary outcome, the B-contrast family contains two tests (B1–B0, B2–B1); D, B×D, and each round-related hypothesis form their own families. The R0 confirmatory family (§5.2) is corrected separately, once per hypothesis it serves. Descriptive secondaries are reported with effect sizes and intervals, labelled as such, and are not tested.

**Power, honestly.** H1c is the central hypothesis and is the least-powered test in the design: interactions need roughly four times the sample of main effects, and *k* = 10 is settled. The minimum detectable effect is therefore computed per outcome *before* pre-registration, not alongside it, from the variance observed in the four-seed pilot, and the pre-registration states in advance what happens if the MDE exceeds any plausible effect size — namely that H1c is reported as an estimation result with intervals and an explicit statement of what the design could and could not have detected, rather than as a null hypothesis test whose non-significance would be uninformative.

5.5 **Convergence and over-iteration characterisation.** Reported from the fitted trajectory parameters rather than from observed maxima, because "round at which the instrument reaches 90% of its peak" is biased when the peak is itself a maximum over a short noisy series and is undefined in direction for instruments where lower is better. Per condition: the fitted rate constant *c* and asymptote *a* with intervals; the derived round at which 90% of (*a* − *f*) is attained, direction-normalised so that improvement is always positive; evidence for post-plateau decline from the quadratic extension and the R6–R9 slope test; and cost-to-convergence in tokens. Reported as a practitioner-facing summary.

### 6. Results

*Pre-specified shell, conditional language.*

6.1 **Instrument confirmation.** OOPS! version; model manifest for the generator and the embedding model.
6.2 Determinism audit result and drift check.
6.3 Seed variance — sensitivity of each outcome to corpus presentation order.
6.4 Manipulation checks — BFO-only and IOF alignment rates, and CCO contamination, by condition and round.
6.5 Descriptives by cell and round. Trajectory plots (outcome by round, panelled by B, coloured by D).
6.6 H1a — grounding main effect.
6.7 H1b — decomposition main effect.
6.8 H1c — B×D interaction.
6.9 **H1d — iteration main effect.** CQ answerability, primary strata. Fitted floor, asymptote and rate constant; total change R0→R9; diminishing returns; over-iteration degradation if present. Loop-coupled trajectories reported in a separate, clearly labelled panel as process evidence.
6.10 **H1e — B×R interaction.** Does grounding change convergence rate? Fitted rate constants by grounding level, unadjusted and adjusted for feedback payload volume, with the conformance-channel ablation (§7.1) read alongside. Trajectory plots overlaid by grounding level.
6.11 **H1f — D×R interaction.** Does decomposition change convergence rate?
6.12 **B×D×R — exploratory.** Three-way pattern described and shown in a figure. No confirmatory test.
6.13 **Convergence and over-iteration characterisation.** Round-to-90%, round-to-peak, post-peak trajectory, and cost-to-convergence by condition. The practitioner question: given a fixed token budget, spend on grounding, decomposition, or more iteration? And: when should you stop?
6.14 **Cost-adjusted comparison.** Convergence against cumulative tokens as well as round index, for all conditions. Carries confirmatory weight for H1f, because a D1 round is not a matched unit of work against a D0 round (Part I §5): the round-index reading and the cost reading are reported together, and H1f is supported only where both point the same way.
6.15 **D1 integration analysis.** Integration loss at the checkpoint rounds by grounding level; LogMap alignment stability and IRI stability; the defect-routing split (single-source vs. multi-source) and what it implies about where decomposition's costs land.

**Table 2.** Cell means and SDs, all outcomes, at R9.
**Table 2b.** Trajectory summary: round-to-90%, round-to-peak, and cost-to-convergence by condition.
**Table 3.** Model coefficients, effect sizes, CIs — B, D, R main effects and two-way interactions.
**Figure 3.** Trajectory plots: primary outcomes by round, panelled by B, lines by D.
**Figure 4.** B×D interaction plot at R9.
**Figure 5.** B×R interaction: convergence rate by grounding level.
**Figure 6.** B×D×R exploratory pattern (three-way figure).

### 7. Ancillary studies

7.1 **Conformance-channel ablation.** B2D0 is run with the conformance section suppressed from the feedback payload, leaving the reasoner, OWL 2 DL profile, OOPS!, and coverage reports, on three pre-registered seeds. B0's conformance report is empty by construction, so B0D0 on the same seeds is the ablated comparison at no extra cost.

- If B2's convergence-rate advantage over B0 survives the ablation, the resource-substitution reading of H1e is supported.
- If it disappears, the effect was feedback volume.

B1 is not ablated; its H1e contrasts rest on covariate adjustment.

7.2 **B0 spontaneous alignment.** BFO-only, IOF, and CCO alignment rates for B0 artefacts at R0, reported as a finding rather than a floor. They quantify how much BFO- or IOF-style structure the generator supplies unprompted, and therefore how much of a contrast B0 really provides. IOF and CCO alignment in B0 and B1 ontologies, and CCO alignment in B2 ontologies, is informative about pretraining leakage.

### 8. Discussion

8.1 What the interaction means under a fixed budget.
8.2 Whether grounding substitutes for iteration — the H1e finding.
8.3 Whether decomposition substitutes for iteration — the H1f finding.
8.4 The resource-allocation question: grounding, decomposition, or iteration? And when to stop iterating.
8.5 What B0 reveals about LLM defaults, read from the agnostic instruments.
8.6 What the battery can and cannot certify — its limits, including the absence of BFO-specific correctness checks.
8.7 Forward-link to Papers 2 and 3.

### 9. Threats to validity

- **Construct.** No correctness anchor; hand-authored CQs may be shallow or incomplete; structural metrics are necessary conditions, not sufficient; OOPS! pitfalls are general-purpose and may miss domain-specific issues; alignment rates measure vocabulary presence, not correctness — a high alignment rate is compatible with category misuse; heuristic modelling patterns consistent with OWL semantics (e.g. category conflation, role misassignment) are outside the battery's scope — any effect is detectable only downstream. CQ answerability is indirectly coupled to the coverage feedback through label matching; this is mitigated by designating the relational and multi-hop strata primary. Label normalisation removes convention differences (case, spacing, number) but not synonymy; the calibration's synonym expansions address that only for terms in the salient-term inventory.
- **Internal.** Total prompt length differs across B because the injection differs, which is the treatment; the window, chunk and feedback allotments are pinned so that nothing else varies with it (§4.2). Feedback truncation is uniform in mechanism but may fire at different rates by condition; the rates are reported. The irreducible residual is attention dilution over a longer prompt — a mechanism with empirical support (Levy et al., ACL 2024; Liu et al., TACL 2024) — which no padding scheme improves and which is declared rather than mitigated. Also: prompt-template equivalence across D; **the narrowed D estimand** that follows from holding presentation order constant, which biases H1b toward the null and is declared rather than bounded (an order-shuffled arm is future work); **position-dependent context degradation under D0**, mitigated by windowing rather than eliminated; **unequal per-round work across D**, addressed by cost-adjusted reporting rather than by design, since equalising calls per round would require crippling D1; **loop coupling**, which is bounded rather than eliminated (Part I §6.7) and which restricts coupled measures to R0 for confirmatory purposes; **feedback-volume asymmetry across B**, addressed by measurement, covariate adjustment and the §7.1 ablation but not removed by design; fresh-only feedback eliminates context-budget variation across rounds but means the model has no memory of prior correction attempts. Autocorrelation across rounds modelled but not eliminated. The injection rendering format is fixed and not ablated.
- **External.** Single corpus, single domain, single generator family. **The decoding regime narrows the inference further than "single generator" suggests:** with fixed weights, greedy decoding and bitwise-deterministic execution, the only stochastic input is S-GEN, which governs corpus presentation order. The seed random effect therefore estimates sensitivity to presentation order, not run-to-run generator variability, and intervals will be correspondingly narrow for a reason unrelated to how the generator behaves in deployment. Conclusions generalise to this model at temperature zero across presentation orders. **BFO, IOF Core, and CCO are almost certainly in the generator's pretraining data,** so B0 is "no scaffolding supplied", not "no scaffolding known"; §7.2 quantifies the spontaneous alignment this produces. **Portability is argued, not tested:** no second corpus is run. Ontologies are built from a sample of six genres with square-root allocation, which compresses the collection's genre imbalance; the sample size is justified by saturation curves, and coverage against a larger reference inventory is reported. Results hold for one mid-size open generator (gemma-4-26B-A4B-it, about 4B active parameters) at temperature zero; a larger model may already supply more of the structure grounding provides, narrowing or widening the grounding effect.
- **Instrument.** The battery does not measure BFO-specific modelling correctness. Alignment rates confirm that the manipulation produced the intended vocabulary usage, but they do not detect misuse of categories. Any condition-linked misuse effect is invisible in Paper 1 and becomes visible only through downstream measures in Papers 2 and 3.
- **Statistical.** Power for B×D×R is limited; three-way interaction is exploratory only. Within-subject correlation structure assumed AR(1); misspecification would affect standard errors on round-related contrasts. Ten within-subject observations per run improve power for round-related effects but increase the risk of overfitting the trajectory shape.

### 10. Conclusion

---

## Part III — Paper 2

**Working title:** *Knowledge Graph Population from LLM-Generated Manufacturing Ontologies: Effects of Ontology Design and Iteration Depth*

**Target venue:** *Journal of Intelligent Manufacturing*, or *Computers in Industry*
**Target length:** 10,000–12,000 words

### 1. Introduction

1.1 Ontologies without instances answer no questions.
1.2 Population is the pipeline's second narrowing point: the question is whether the grounding, decomposition, and iteration effects observed in Paper 1 survive into a populated graph, or wash out.
1.3 The inherited variable — six ontology conditions × four checkpoint rounds, with the factorial structure intact.
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
- **RQ2.4** Does the source-ontology structural quality profile (as measured by the Paper 1 battery) predict post-population reasoner inconsistency in the resulting KG? *(The predictor is the vector of Paper 1 grounding-agnostic outcome measures. Estimable on all 240 checkpoint ontology-states (60 ontologies × 4 rounds), with run and seed as random effects.)* **Floor contingency, pre-registered:** schema-constrained generative extraction may prevent inconsistency largely by construction, leaving this outcome at or near zero across all cells with no variance to predict. If observed inconsistency is below a pre-specified threshold, the analysis falls back in a fixed order to (i) near-violation counts — assertions satisfying the antecedent of a violated constraint but escaping it through missing type information, (ii) punning (the same name used as both a class and an individual) and type-assertion anomaly rates, and (iii) a declared null, reported as a substantive finding that schema constraint suffices to prevent formal inconsistency regardless of upstream construction strategy.
- **RQ2.5** What proportion of each ontology is actually used during population, and does grounding change it?
- **RQ2.6** Does iteration round affect population fidelity? Does a KG populated against an early-round ontology differ from one populated against the terminal R9 ontology? Does over-iteration degrade fidelity?
- **RQ2.7** Do B×R and D×R interactions from Paper 1 carry through to population outcomes? The resource-substitution question extended downstream.

### 4. Method

4.1 **Inputs.** The 240 checkpoint ontology-states (60 runs × R0, R3, R6, R9) and the population sample (B), which is disjoint from the construction sample the ontologies were built from (Part I §8, asset 1).
4.2 **Population procedure.** Schema-constrained generative extraction; identical prompt template across conditions; only the schema varies.
4.3 Entity resolution, applied uniformly.
4.4 **Validation pass.** Reasoner-based consistency check of the populated KG against its own generating ontology, under a pinned wall-clock timeout per KG. **Scalability contingency, pre-registered.** An OWL 2 DL reasoner may not complete on a KG of this size. If classification times out on any KG, the check falls back — for every KG in the campaign, so that the instrument is the same across cells — to an OWL 2 RL rule-based consistency check over the full graph. The fallback is sound but incomplete: it detects the violation types populated graphs actually produce (disjointness, domain and range, functional-property and type clashes) and misses inconsistencies that need full DL reasoning. The instrument actually used is recorded, and the proportion of KGs on which the DL reasoner completed within the timeout is reported.
4.5 **Seeds.** S-POP nested within S-GEN; decoding is greedy; the deterministic execution regime applies.
4.6 **Defensive handling of early-round ontologies.** Round-0 schemas may be sparse, malformed, or missing class hierarchies. The population pipeline fails gracefully: an empty or near-empty schema produces an empty or near-empty KG, not an error. These cases are included rather than excluded, since they establish what iteration buys for population. Community-structure instruments (Leiden/CPM, genre-AMI) may produce degenerate outputs on near-empty KGs — a single community, an undefined partition, or a resolution profile with no stable plateau — for the same reason; these floor values are noted alongside the fidelity floor values rather than excluded, and the proportion of KGs with no identifiable plateau is reported per cell.

### 5. Reference-free fidelity measurement

5.1 **Entailment-verified precision.** A stratified random sample of extracted triples from each KG is verbalised and checked against its source passage by NLI: *n* = 2,000 per KG, stratified by source genre with proportional allocation, or every triple if the KG holds fewer. Precision is estimated with a Wilson interval; at *n* = 2,000 the half-width is about two percentage points at 80% precision, which is finer than any effect the design is powered to detect. Verifying every triple was rejected because its cost scales with yield, which B and D change by construction, and adds nothing to the estimate at this resolution. *n* is pinned in the pre-registration, and the sampling seed is recorded under S-HAR. Per-triple precision with no annotation.
5.2 **Salience recall.** Recall against the automatically extracted salient-assertion inventory (Part I §8, asset 3), which is a distinct asset from Paper 1's salient-*term* inventory and is frozen on the same schedule. The salient-assertion inventory is extracted from the population sample (B).
5.3 **Verifier validation.** The NLI verifier is characterised by injection of correct and mutated triples. Sensitivity and specificity reported with Wilson intervals. Style crossing (triples expressed against B1-style and B2-style schemas) measures whether verifier behaviour differs by schema richness.

*Why calibration here and not in Paper 1.* Paper 1 uses only established tools (OOPS!, OntoQA, OWL reasoner) and corpus-grounded coverage measures, none of which requires empirical calibration. The NLI verifier is a heuristic instrument with no oracle, so it needs calibration. The same argument licenses the answer-matcher characterisation in Paper 3 §3.6.
5.4 **Schema-conformance outcomes:** post-population reasoner inconsistency rate.
5.5 **Utilisation outcomes:** ontology utilisation rate; population yield per 1,000 corpus tokens; orphan-instance rate.
5.6 **Community structure outcomes.** Leiden community detection (Traag, Waltman & van Eck 2019), applied uniformly to every populated KG, optimising the Constant Potts Model (Traag, Van Dooren & Nesterov 2011) rather than standard modularity as the primary objective function — a same-library, single-parameter choice that avoids the resolution limit modularity is known to have in denser or larger graphs, which matters here because B and D already change graph size and density (§5.5). Three specification decisions are fixed in advance rather than left to the implementation:

- **Resolution profile, not a single score.** A CPM objective value is not a normalised quality score and is not comparable across graphs of different size and density, which is precisely the situation here. Each KG is therefore partitioned across a pre-registered grid of resolution values γ, and the reported outcomes are profile-derived: the number of communities as a function of γ, the width of the stable plateau in that profile, and the partition at the plateau's centre. A single γ is additionally fixed in advance for the headline comparison, and its choice is reported with the profile that justifies it.
- **AMI, not NMI.** Normalised mutual information is not adjusted for chance and rises with the number of communities, and community counts will differ across conditions by construction, since B and D change graph size. Adjusted mutual information is used for the genre-alignment outcome; NMI is reported alongside for comparability with prior work.
- **Node-level genre labels.** Genre alignment needs a hard partition on the ground-truth side, but entities are typically mentioned across several genres. The rule is fixed: each node is labelled by the genre of the majority of the passages it was extracted from, ties broken by first mention; nodes whose majority share falls below a pre-registered purity threshold are assigned to an "ambiguous" label and excluded from the AMI computation, with the excluded proportion reported per cell as a measure of how well-defined the genre partition is in the first place.

Community outcomes are reported alongside graph size, density and yield so that structural differences are not confounded with yield differences. Standard modularity is also computed on every KG (§7.2) as an ancillary robustness comparison against CPM, not as a second confirmatory outcome.

5.7 *Rationale for homogeneous projection over heterogeneous methods, if needed.*
5.8 **Statistical plan.** Mixed-effects models: B, D, R fixed; seed random (with S-POP nested within S-GEN). Round is a four-level within-subject factor (R0, R3, R6, R9) with an AR(1) correlation structure. Round-related questions are tested as R9 − R0 and adjacent-checkpoint contrasts, not with the Paper 1 asymptotic trajectory model, which four points cannot support. RQ2.1–2.3, RQ2.5–2.7 run on all three grounding levels. RQ2.4 tested as a pre-registered regression of post-population reasoner-inconsistency rate on the Paper 1 structural quality vector (grounding-agnostic predictors, estimable on all 240 checkpoint ontology-states). The plateau-centre partition's community count and genre-AMI enter the same B/D/R mixed-effects model as additional confirmatory outcomes under RQ2.1–2.3, with yield included as a covariate to guard against size/density confounds. Modularity is not entered into this model; it is analysed separately in §7.2.

**Table 1.** Fidelity instrument inventory and validation status.

### 6. Results

*Pre-specified shell.*

6.1 Verifier operating characteristics.
6.2 Descriptives by cell and round.
6.3 RQ2.1–2.3: main effects and interaction on precision and salience recall at R9.
6.3a **RQ2.1–2.3 extended: community structure.** Main effects and interaction on the plateau-partition community count and genre-AMI at R9, with yield as covariate and the resolution profile shown per condition; whether D1 produces a detectably more genre-aligned partition than D0. Ambiguous-node proportions reported per cell.
6.4 **RQ2.4: the structural-quality → inconsistency path.** Which Paper 1 measures predict post-population reasoner inconsistency? Estimated on all 240 checkpoint ontology-states.
6.5 RQ2.5: utilisation.
6.6 **RQ2.6: iteration round effect on fidelity.** Do early-round ontologies produce worse KGs?
6.7 **RQ2.7: B×R and D×R on population outcomes.** Does grounding substitute for iteration at the population stage?
6.8 Qualitative failure analysis by condition.

**Table 2.** Fidelity outcomes by cell at R9.
**Table 2b.** Fidelity trajectory: outcomes by checkpoint round, summarised by condition.
**Table 3.** Inconsistency and utilisation rates by cell and round.
**Figure 2.** Interaction plot for entailment-verified precision at R9.
**Figure 3.** Fidelity by checkpoint round, panelled by B, lines by D.
**Figure 4.** Scatter of Paper 1 structural quality vector against post-population reasoner-inconsistency rate.
**Figure 5.** Resolution profiles by cell and genre-AMI at R9, with yield-adjusted estimates alongside raw values.

### 7. Ancillary analysis

7.1 **Schema-free population baseline.** Open extraction with no schema constraint.
7.2 **CPM versus modularity: instrument comparison.** Standard modularity, computed on the same partitions, correlated against the plateau-partition CPM solution and against graph size/density/yield by cell. Divergence between the two that tracks density is treated as corroborating evidence for the resolution-limit concern in §9; agreement throughout is reported as robustness of the community-structure result to objective-function choice. Not a confirmatory test; no RQ is answered differently depending on its outcome.

### 8. Discussion

8.1 Whether the ontology-first / extraction-first bridge holds empirically.
8.2 Which schema properties help extraction — and whether they are the properties Paper 1's metrics reward.
8.2a Whether decomposition's per-genre construction is legible in the populated graph's community structure, and what that implies about D1 versus D0 as an integration strategy rather than just a construction-time convenience. Read alongside §7.2: if CPM and modularity agree, the result is reported as robust to instrument choice; if they diverge specifically in denser/higher-yield cells, that divergence is itself evidence that the resolution-limit concern is operating where predicted, and is discussed as an instrument-sensitivity finding rather than an inconsistency to explain away.
8.3 **The iteration trade-off at the population stage.** Whether additional iteration rounds improve fidelity enough to justify the cost, and whether grounding compresses that curve.
8.4 **If the RQ2.4 floor contingency fires.** If schema-constrained extraction prevents formal inconsistency largely by construction, that is itself a finding: upstream construction strategy does not matter for formal consistency because the extraction template absorbs it. Discussed as a substantive result rather than a fallback, since it answers the practitioner question of whether careful ontology engineering pays off at the population stage or whether the extraction harness renders it moot.
8.5 Generalisation to unseen documents: how well ontologies built from one sample structure documents they never saw, and whether that differs by grounding, decomposition, and round.
8.6 Forward-link to Paper 3.
8.7 **Future work: process-awareness as its own research line.** Part-specific routing order and defect-propagation asymmetry are real properties of manufacturing KGs, but representing and validating them is a separate contribution from measuring whether construction strategy affects population fidelity. A follow-on paper could layer a process-awareness formalism on top of this design and ask whether construction-strategy effects further attenuate — or amplify — once process-specific constraints are checked.

### 9. Threats to validity

- NLI verifier precision ceiling. Style-dependent verifier behaviour measured directly; uniform error attenuates, condition-linked error biases.
- Salience recall inherits extractor biases.
- Single extraction model; schema-constrained extraction may favour some schema shapes.
- Population and construction samples are disjoint but drawn from the same collection and period, so generalisation is within-collection, not to a new site or product line.
- Early-round ontologies may produce degenerate KGs; these are informative but contribute floor values.
- Entailment-verified precision is estimated on a pinned sample of triples per KG, not the whole graph; intervals are reported, and genre strata with few triples carry wide intervals.
- If the reasoner-scalability fallback fires (§4.4), the inconsistency instrument is OWL 2 RL rather than OWL 2 DL for every KG; inconsistencies that need full DL reasoning are then undetected, uniformly across cells.
- Community-detection outcomes are sensitive to graph size and density, which themselves vary with B and D; yield is a covariate, CPM with a resolution profile replaces a single modularity score for this reason, but residual confounding cannot be fully ruled out.
- Genre-AMI presumes genre labels are available and meaningfully distinct at the passage level; where genre boundaries are fuzzy, the node-labelling rule pushes nodes into the ambiguous class and the metric is computed on a shrinking, possibly non-random subset. The excluded proportion is reported so the reader can judge this directly.
- Single community-detection algorithm (Leiden), applied to the graph's homogeneous projection; results characterise this algorithm's view of the graph, not community structure in general, and predicate-type structure is not used by the instrument (see §5.7's rationale for not adopting a heterogeneous/multi-relational method).

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

3.1 **Source A — mined held-out labels.** Corrective Action Reports, which are excluded from both corpus samples, supply root-cause statements. Each is paired with its linked NCR in the population sample to form a question–answer item. Root-cause text appearing in linked documents is redacted before freeze (Part I §8, asset 1). Retrieval runs over the KG populated from the population sample and over that sample's text.
3.2 **Redaction verification.** Automated leakage checking of the frozen corpus against the label set, run before the Paper 1 campaign.
3.3 **Source B — synthetic scenario injection.** Causal chains are constructed first, with exact control over hop distance and causal type. They are then written as documents in the corpus genres and inserted into the population sample before freeze. The KGs contain them; the ontologies never saw them. A scenario can fail because the ontology lacks a concept the chain needs, and that failure is part of what is measured.
3.4 **Stratification and benchmark statistics.** Target size about 200 items with a pre-registered floor of 150: roughly 120 mined items (Source A) and 80 synthetic (Source B), stratified by hop distance (1, 2, 3 or more) and by the genre pair the causal chain crosses. The mined count depends on how many Corrective-Action-linked NCRs survive redaction and is fixed after that step (todo task 10a); the synthetic count is fixed by the scenario grid. The composition is pre-registered before the Paper 1 campaign.
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
- **Stage 1 (screening).** Resolution IV fractional factorial over retrieval parameters, run on **two ontology conditions at R9 — B0D0 and B2D1, the extremes of the design** — with the active-factor set taken as the union. Screening on a single condition would assume that factor activity is invariant to graph structure, which is exactly what RQ3.3 puts in question; a factor inactive on a sparse ungrounded graph could be active on a rich grounded one and would never reach Stage 2. Two factors are retained for Stage 2 by default (Part I §12), giving four configurations. If Stage 1 finds more than two active factors, the two with the largest effects are retained and the others are fixed at their best level. A third factor is added only if the pilot's measured cost per RCA run leaves headroom, and that decision is recorded in the pre-registration before Stage 1 runs.
- **Stage 2 (confirmation).** Active retrieval factors, fully crossed with the six B×D conditions and **four checkpoint rounds (R0, R3, R6, R9)** = 24 ontology-states per seed. Seed as block.

*Design rationale for four checkpoints.* Ten rounds × six conditions × multiple retrieval configurations would produce a combinatorial explosion. R0 (no iteration), R3 (early), R6 (mid), and R9 (terminal) are evenly spaced and capture the practically relevant questions — whether early stopping costs RCA accuracy and whether over-iteration degrades it — without fitting a full convergence curve at the RCA level. The full curve is available in Paper 1; Paper 2 uses the same four checkpoints. Four points can fit a curve with an inflection, which is expected if there is rapid early improvement followed by plateau or decline.

5.3 Generation configuration; weights and runtime pinned per manifest; identical prompt across configurations. Seed S-RET governs DoE run-order randomisation and synthetic scenario generation.
5.4 **Retrieval-ablated control.** Answers generated with no retrieved content; establishes how much of RCA accuracy is generation-model prior.

**Figure 2.** System architecture with parameterised mechanisms.
**Table 2.** DoE structure, both stages.

### 6. Evaluation

6.1 **Accuracy:** root-cause identification accuracy at top-1 and top-3; mean reciprocal rank.
6.2 **Evidence quality, reference-free:** label-entity coverage; path plausibility (synthetic items); groundedness; hallucination rate.
6.3 **Efficiency:** retrieval latency; tokens retrieved; tokens generated.
6.4 **Statistical plan.** Mixed-effects models with retrieval factors, B, D, R, and interactions fixed; seed and scenario random. RQ3.4 via mediation with Paper 2 fidelity outcomes as mediator and bootstrapped indirect effects. RQ3.5 and RQ3.6 tested on the four checkpoint rounds.

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
7.9 Performance by stratum, with attention to multi-hop and cross-genre items.
7.10 Mined versus synthetic item agreement.
7.11 Efficiency trade-offs.
7.12 Failure analysis.

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
8.3 Where the signal attenuates, read from the mediation results. A residual direct path (ontology → RCA, bypassing KG fidelity), if observed, points to retrieval-structural effects of the ontology — class hierarchy navigability, relation vocabulary coverage for traversal — that the Paper 2 fidelity battery does not measure. This identifies a concrete next instrument for future work.
8.4 **The end-to-end resource-allocation question.** Given a fixed budget, spend on grounding, decomposition, iteration, or retrieval tuning? Synthesising the B×R findings across all three papers.
8.5 The automated benchmark as a transferable instrument.

### 9. Threats to validity

- Mined labels record what the investigation concluded, which may not be the true root cause.
- Redaction leakage; residual leakage inflates accuracy uniformly.
- Synthetic items may be easier or structurally unlike real ones; §7.10 tests this.
- Fractional factorial aliasing in Stage 1.
- Single generation model. NLI matcher precision ceiling.
- Retrieval-ablated control establishes a floor, but generation-model prior may still inflate accuracy when retrieval adds only marginal information.
- Mediation (RQ3.4) has a randomised treatment-to-mediator path but an observational mediator-to-outcome path: any unmeasured common cause of KG fidelity and RCA accuracy biases the indirect effect. Sequential ignorability — no unmeasured common cause of KG fidelity and RCA accuracy — is assumed and stated, and a sensitivity analysis over the assumed correlation of the two error terms is reported rather than the point estimate alone. Power for indirect effects at this sample size is limited and is reported as such.
- Mediation (RQ3.4) may show a residual direct path from ontology condition to RCA accuracy. The ontology shapes retrieval traversal paths independently of the KG fidelity measures Paper 2 captures; a nonzero direct effect is therefore interpretable as an instrument gap rather than unexplained variance, and is reported as such.
- Four checkpoint rounds (R0, R3, R6, R9) cannot characterise the full RCA convergence curve; the full curve is available in Paper 1. B×D×R in Paper 3 is exploratory.
- Synthetic scenarios are absent from the construction sample, so Source B items test ontology generalisation as well as retrieval; Source A items carry the same property for real defects.

### 10. Conclusion

10.1 Findings.
10.2 The end-to-end picture across all three papers — grounding, decomposition, and iteration.
10.3 Future work:
- a comparison of mid-level ontologies (IOF Core vs CCO) under a budget that truncates neither;
- an order-shuffled D0 arm;
- an LLM-mediated merge for D1;
- trajectory-level (longitudinal) mediation;
- population from the full collection for all conditions (deployment-scale KGs);
- multi-model replication;
- battery transfer to a second domain;
- BFO-specific modelling checks as a separate instrument publication.

---

## Appendix A — Grounding sources and the alignment-rate query

### A.1 Injection sources

| Condition | Source | Content |
|---|---|---|
| B1 | `bfo-core.owl` (BFO 2020, as the BFO project distributes it) | 36 classes, 40 relations |
| B2 | IOF Core `Core.rdf`, release 202603, with its import chain resolved | Classic `bfo.owl` (36 classes, 64 relations) + IOF construct-namespace vocabulary (91 classes including `BFO_0000144`, 83 object properties) |
| — | `CommonCoreOntologiesMerged.ttl` (CCO v2.0, 2024-11-06) | Not injected. Pinned as the reference for the query's CCO contamination rule |

File hashes are recorded in the seed register. ISO/IEC 21838-1 and -2:2021 are reference documents, not injection sources.

### A.2 The BFO build difference between B1 and B2

Two OWL builds of BFO 2020 exist:

- `bfo-core.owl`, the canonical build, used for B1;
- classic `bfo.owl`, which IOF Core imports.

A pre-campaign file-level diff confirms that their class-level content is identical. The difference is confined to 24 temporal relation variants ("at all times", "proper", and "some time proper" forms) that only the classic build contains.

IOF Core was designed against the classic build, and its own axioms depend on those relations: 12 of them appear in 29 axiom references across core IOF class definitions (including `PlanSpecification`, `Agreement`, `BusinessProcess`, `Organization`, and several IOF property declarations). Substituting `bfo-core.owl` into B2 would create a degraded IOF Core that no practitioner would encounter. The difference is therefore part of the treatment, not a confound. The diff is reported in Paper 1's methods appendix.

### A.3 Alignment-rate cascade

For each domain class C, the query walks the asserted `rdfs:subClassOf` chain upward. It applies the following rules, in priority order, at the first ancestor whose IRI matches:

1. **Any `cco:` IRI** (`https://www.commoncoreontologies.org/`) → **CCO-aligned** (contamination in every condition).
2. **Any `iof-constr:` IRI** → **IOF-aligned.**
3. **`obo:BFO_0000144`** (process profile) → **IOF-aligned.** This class has a BFO-namespace IRI but is supplied to the generator only through IOF Core, so a class reaching it has used IOF vocabulary. It is also curated in CCO, but any CCO route passes through a `cco:` intermediate first and is caught by rule 1.
4. **Any other `obo:BFO_` IRI** → **BFO-only-aligned.**
5. **No match** → **Unaligned.**

The categories partition domain classes exhaustively. The query requires no condition-specific class inventories. It was validated against IOF Core 202603 across eight critical topologies and against a synthetic ontology exercising all cascade paths.

### A.4 Why CCO is not a condition

The Common Core Ontologies (CCO) are the principal general-purpose alternative to IOF Core: an enterprise vocabulary, also built on BFO. Comparing the two would ask whether manufacturing-specific vocabulary helps more than general-purpose vocabulary. However, CCO's vocabulary is roughly ten times larger than IOF Core's — on the pinned renderer, 1,687 labelled entries against 174. Under the fixed injection allotment this design requires (Paper 1 §4.2), sized to hold IOF Core in full, CCO would be truncated to about a tenth of its entries, and the comparison would mainly measure how much of each vocabulary survived truncation. Raising the allotment to hold CCO in full was rejected because a ~48,000-word injection would dilute attention across every condition and would create a condition more favourable than any practitioner would run. A comparison of mid-level ontologies under a budget that truncates neither is therefore named as future work (Paper 3 §10.3). CCO is retained only as the reference for the alignment-rate query's contamination rule (A.3, rule 1).

## Appendix B — Glossary

| Term | Meaning in this dissertation |
|---|---|
| Ontology | A formal vocabulary of the kinds of things in a domain and the relationships between them, written so software can reason over it |
| Upper ontology | A domain-neutral ontology fixing the most general categories (object, process, quality, role, …) |
| BFO | Basic Formal Ontology, an upper ontology standardised as ISO/IEC 21838-2 |
| Mid-level ontology | An ontology between the upper level and a specific application, supplying reusable vocabulary for a broad domain |
| IOF Core | The Industrial Ontologies Foundry's mid-level ontology for manufacturing, built on BFO |
| CCO | Common Core Ontologies, a general-purpose mid-level ontology built on BFO; used here only to detect pretraining leakage |
| OWL 2 DL | The W3C ontology language used for all generated ontologies; "DL" is the decidable profile that reasoners can check completely |
| Reasoner | Software that checks an ontology for logical consistency and finds classes that can have no members (*unsatisfiable classes*) |
| SPARQL | The query language for ontologies and knowledge graphs |
| Competency question (CQ) | A question the ontology should be able to answer, paired with a SPARQL query that tests whether it can |
| Knowledge graph (KG) | Facts extracted from documents and stored using the ontology's vocabulary |
| Population | Extracting facts from the corpus into the KG under the ontology's schema |
| OOPS! | OntOlogy Pitfall Scanner, a published tool that detects common ontology-modelling mistakes |
| OntoQA | A published set of structural metrics for ontologies (depth, richness of relations and attributes, orphan classes) |
| Salient term | A term the corpus uses distinctively often, found automatically; coverage is the share represented in the ontology |
| Alignment rate | The share of an ontology's classes placed under the supplied standard vocabulary; the manipulation check |
| Contamination | Use of a standard vocabulary the condition was not given, indicating knowledge from the model's pretraining |
| Round (R0–R9) | One cycle of automated feedback and correction; R0 is the first complete draft |
| Loop-coupled / held-out | Whether an instrument's output is fed back to the model (coupled) or kept out of the loop so it can measure the loop's effect (held out) |
| Windowing | Showing the model a fixed-size selected view of an ontology too large for its context |
| Integration loss | Quality lost when D1's per-genre sub-ontologies are merged |
| LogMap / AML | Published ontology-matching tools used in D1 integration (LogMap) and as an audit (AML) |
| NLI | Natural language inference: a model that judges whether one text entails another; used to verify extracted facts and match answers |
| GraphRAG | Retrieval-augmented generation that retrieves from a knowledge graph as well as from text |
| RCA | Root cause analysis |
| Leiden / CPM | A community-detection algorithm and the objective it optimises (Constant Potts Model) |
| AMI | Adjusted mutual information, a chance-corrected measure of agreement between two partitions |
| MDE | Minimum detectable effect: the smallest effect the design can reliably detect |
| Greedy decoding | Always choosing the model's most likely next token; with fixed hardware settings, this makes runs exactly reproducible |
| Mediation | A statistical test of whether an effect of one thing on another runs through an intermediate step; here, whether the ontology's effect on RCA accuracy runs through KG fidelity |
| Punning | Using the same name for both a class and an individual; legal in OWL 2 but usually a modelling accident in a populated graph |
| OWL 2 RL | A rule-based profile of OWL that scales to large graphs; it catches the common violation types but not everything a full reasoner would |
| Wilson interval | A confidence interval for a proportion that behaves well near 0% and 100% |

---

## Parts V–VI — Implementation tasks

Moved to the companion file **dissertation_todo_v20.md**, which integrates the human-effort inventory and the sequenced next-actions list into a single task list with effort estimates and dependency tracking.
