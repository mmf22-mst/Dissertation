# Dissertation Prospectus — v20

*How Ontology Construction Strategy Affects Downstream Manufacturing Root Cause Analysis*

*Source of truth for the two-page prospectus. Rendered to PDF from `dissertation_prospectus_v20.html`
(`wkhtmltopdf --page-size Letter --margin-top 15mm --margin-bottom 13mm --margin-left 18mm --margin-right 18mm`).
Edit the HTML for layout, this file for wording; keep the two in step. Aligned to
dissertation_overview_and_paper_outlines_v20.md.*

## Problem

Manufacturing process knowledge lives in unstructured documents — non-conformance reports, FMEAs, command media, work instructions, issue trackers, risk registers. Large language models now make it feasible to convert that knowledge into ontologies and knowledge graphs, but an engineer starting that work faces three design choices with no empirical guidance: what ontological scaffolding to supply the model (none, BFO, or IOF Core), how to decompose the corpus (one pass, or one per document type), and how much iteration to invest. These choices have never been evaluated together. This dissertation crosses them in a controlled experiment and traces their effects through construction, population, and use.

## What each result would tell a manufacturing engineer

| Decision | If the effect is real | If it is null | What the engineer does |
|---|---|---|---|
| **Start from a standard vocabulary** (B) | Grounded ontologies populate cleaner graphs and answer more root-cause questions; IOF Core adds to plain BFO, or does not | Supplying BFO or IOF Core changes what the model builds but not what the graph can answer | Whether adopting IOF Core is worth the learning and conformance effort, and whether plain BFO is enough |
| **Split the corpus by document type** (D) | Per-genre construction covers the dense genres better, and the gain survives merging and population | One genre-blocked stream is as good; merging is a cost with no return | Whether to build one ontology or one per document type, and how much merge tooling to invest in |
| **Iterate under automated feedback** (R) | Quality rises to a plateau within a few rounds; over-iteration does or does not degrade it | Feedback fixes what the checker reports but changes nothing downstream | How many rounds to budget, and when to stop |
| **Do the choices combine?** (B×D, B×R, D×R) | Grounding matters most when the corpus is one stream; grounding or decomposition shortens the climb | The choices contribute independently | Whether the investments are substitutes (pick one) or complements (do all) under a fixed budget |

**If everything is null.** That is the cheapest outcome for practice: the three choices can then be made on cost and convenience alone. The design is built so this reading is available rather than embarrassing. Each stage carries a pre-registered null; the instruments inside the feedback loop are reported as compliance rather than quality, so "the model fixed what it was told to fix" cannot masquerade as an effect; and the mediation analysis in Paper 3 says where a signal died if it did.

## Pipeline

Construct (Paper 1) → Populate (Paper 2) → Exploit (Paper 3).

- **Paper 1 — Construct.** BFO 2020 / IOF Core + construction sample A → Factors B (3) and D (2) → LLM construction, 60 runs → Factor R, 10 rounds → 600 ontology-states → ontology quality (automated, corpus-grounded, no reference ontology).
- **Paper 2 — Populate.** 240 checkpoint states + population sample B → schema-constrained extraction → 240 populated KGs → KG fidelity (entailment-verified, reference-free).
- **Paper 3 — Exploit.** Populated KGs + RCA benchmark (~200 items) → hybrid GraphRAG retrieval → RCA answers → RCA accuracy (known-answer, mediated through KG fidelity).

Each stage can wash out the upstream signal. Documenting where that happens is itself a result.

## Experimental design

A 3 × 2 crossed factorial with a 10-level within-subject repeated measure, blocked on *k* = 10 random seeds.

- **Factor B — grounding (3 levels).** B0 = ungrounded; B1 = BFO 2020 (76 labelled entries); B2 = IOF Core with the BFO layer it imports (174 entries). Each condition receives the package its source organisation ships, unmodified. Four prompt allotments — injection, ontology view, corpus chunk, feedback — are pinned identically across conditions, so the only thing that varies with B is the vocabulary itself.
- **Factor D — decomposition (2 levels).** D0 = one ontology over a genre-blocked stream; D1 = one sub-ontology per document genre, merged by a deterministic procedure with no model call. Six genres: process specifications, command media, FMEAs, non-conformance reports, issue-tracker items, risk-register entries.
- **Factor R — iteration (10 levels).** R0 (no feedback) through R9. Every round receives fresh automated feedback only — no accumulated history, no round counter — so any trajectory reflects the ontology's state, not the model tracking its own progress.
- **Scale.** 60 ontologies × 10 rounds = 600 ontology-states. Papers 2 and 3 consume four checkpoint rounds: 240 populated knowledge graphs, evaluated against an RCA benchmark of about 200 items.

## Hypotheses

| | Hypothesis | Test |
|---|---|---|
| H1a | Grounding improves ontology quality | B main effect |
| H1b | Decomposition improves domain coverage | D main effect |
| H1c | Grounding matters more under monolithic construction (structural substitution) | B × D interaction |
| H1d | Iteration improves quality with diminishing returns | R main effect |
| H1e | Grounding and iteration are partially fungible (resource substitution) | B × R interaction |
| H1f | Decomposition accelerates convergence | D × R interaction |
| H2 | Ontology differences produce knowledge-graph fidelity differences | Paper 2 |
| H3 | Fidelity differences produce RCA accuracy differences, mediated through the pipeline | Paper 3 |

Each is pre-registered with its null. The three-way interaction is exploratory, not confirmatory.

## Evaluation

There is no reference ontology for this domain and building one would beg the question. The corpus is the ground truth for coverage; established tools supply quality measurement; the downstream papers supply the primary test.

- **Held-out primary outcome.** Competency-question answerability on the relational and multi-hop strata — 60 of about 108 hand-authored questions, each requiring a query that joins two label-matched classes through an object property. Never fed back. Existential and definitional questions are secondary, because a question answerable by a single class label is partly answerable through the coverage feedback and is not independent evidence.
- **Coupled instruments** (the practitioner loop, fed back each round): reasoner consistency, OWL 2 DL conformance, OOPS! pitfalls, OntoQA structural metrics, alignment rates, salient-term coverage, genre coverage balance. These are the tools a practising engineer would actually run, so feeding them back is the point rather than a flaw — but it means they measure compliance after round 0. They are confirmatory at R0 and reported as compliance evidence thereafter.
- **Downstream.** Paper 2 measures entailment-verified precision on a stratified sample of 2,000 triples per graph with confidence intervals, salience recall, schema conformance, utilisation, and community structure. Paper 3 measures root-cause answer accuracy on a benchmark built from held-out corrective-action records plus synthetic scenarios, with a retrieval-ablated control and a mediation analysis.

## Execution and feasibility

- **Generator and platform.** A single open-weights model (gemma-4-26B-A4B-it, bf16) on eight B200 GPUs, one replica per GPU, greedy decoding under batch-invariant kernels, with prompt and response hashing — so a run reproduces bit-for-bit and the concurrency needed to finish the campaign does not compromise that.
- **Corpus.** Two disjoint frozen samples drawn from the same collection: sample A for construction, sample B of equal size for population, sized from term-saturation curves and pre-registered with their hashes.
- **Pilot as a risk gate.** Four seeds, the two extreme conditions (B0D0 and B2D1), R = 15. It settles the round count, supplies the variance estimates the minimum-detectable-effect calculation needs, exposes the loop-coupling behaviour the design predicts, and shakes out the pipeline before anything is pre-registered.
- **Pre-committed fallbacks.** If the OWL reasoner cannot complete on graphs of this size, every graph is checked with a rule-based profile instead, uniformly, with the substitution recorded. If post-population inconsistency sits at the floor, the analysis falls back in a fixed order to near-violation counts, then to a declared null reported as a finding. Paper 3 retains two retrieval factors by default. All declared before results are seen.
- **Timeline.** Roughly three to four weeks of tooling, corpus preparation and pilot work stand between here and the campaign; the campaign itself runs in days to weeks per paper on the pinned platform.

## Contributions

1. An end-to-end empirical trace of whether upstream ontology design — and the iteration investment — survives to downstream root cause analysis performance, including the practitioner question of whether grounding substitutes for iteration.
2. The first crossed factorial evaluation of upper-ontology grounding against corpus decomposition for LLM-generated manufacturing ontologies, with iteration depth as a within-subject dimension and a testable interaction hypothesis.
3. An evaluation battery combining established structural metrics, corpus-grounded coverage measures, and an alignment-rate manipulation check with built-in contamination detection — applied without a reference ontology and at every round, and portable to other domains at modest cost.
4. Released artefacts: generators, battery scripts, the competency-question set, and the ontology-states themselves, subject to employer clearance.

A null result at any stage tells the manufacturing engineering community that the construction choice does not matter at the point of use — and that engineering effort is better spent elsewhere. That is a usable answer, and the design is built to deliver it credibly rather than to avoid it.
