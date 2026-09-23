# Deterministic Integration and Defect Routing for D1 — Specification (v17)

Companion to dissertation_overview_and_paper_outlines_v20.md, Part I §5
(D1 integration), Paper 1 §4.4a (feedback routing), and Paper 1 §5.3
(integration descriptives).

Originally task 4b of dissertation_todo_v15.md; maintained under task 4
of dissertation_todo_v20.md.

**v17 changes (aligned to overview v20).** No change to the integration
procedure. (a) The sub-ontology battery that supports the integration-loss
measure (§5.4) runs at the four checkpoint rounds only (R0 plus three
evenly spaced to the terminal round; R0/R3/R6/R9 at R = 9), not at every
round — 720 runs instead of 1,800. The round-to-round delta rate and IRI
stability (§5.2–5.3) need no battery run and are still computed every
round. (b) Routed feedback is no longer prepended as free text by the
orchestrator: the payload is re-rendered per sub-ontology by
`feedback_payload.py` with the routed defects at position 0, under the
same pinned caps and FEEDBACK allotment as the global payload, so every
iteration call sits under the same ceiling. (c) Note that the label
normalisation in Stage 1 (§2.2, casing/whitespace/punctuation, applied to
the artefact during the merge) is distinct from the v20 CQ scoring
normalisation (`label_normalisation.py`, applied to a scoring copy at
evaluation time, with CamelCase splitting and head-noun singularisation);
the two rules are pinned separately.

**Design change from v15.** The LLM-mediated merge is replaced by a
fully deterministic integration procedure: union of sub-ontology axioms
plus LogMap alignment-based reconciliation. This eliminates anchored
re-integration, merge churn variance, the pilot churn decision rule,
and the integration feedback channel. The rationale is in §1.1.

---

## 1. Purpose

Under D1, the corpus is decomposed by genre, producing *G* sub-ontologies
(one per genre). These must be merged into an integrated artefact for
evaluation. This specification defines:

1. **How** the sub-ontologies are integrated (§2 — deterministic procedure).
2. **How** the IRI provenance map is built and maintained (§3).
3. **How** feedback is routed (§4 — defect routing).
4. **What** is logged (§5).

Everything is deterministic. Same sub-ontology inputs produce the same
integrated artefact every time.

### 1.1 Why deterministic, not LLM-mediated

The earlier design used an LLM merge pass that could resolve semantic
conflicts, harmonise structure, and create bridging concepts. But it
introduced merge variance — a small upstream change could flip a merge
decision, reshuffle IRIs, and relocate structure — which required
anchored re-integration to stabilise trajectories, a pilot decision
rule to characterise churn, and an integration feedback channel to
iterate the merge. These mechanisms were the heaviest new infrastructure
in the design and existed entirely to compensate for the instability
of the merge step.

H1f asks whether decomposition changes convergence rate. The
sub-ontologies are the objects of iteration — that is where the D1
treatment lives. The merge mechanism is infrastructure, not treatment.
A deterministic merge makes integration a fixed cost of decomposition
rather than a variable one, which is cleaner for H1f: trajectory
differences are purely about sub-ontology iteration, not merge variance.

The integrated artefact will be messier than an LLM-merged one — it
will contain redundancy, structural inconsistencies from cross-genre
overlap, and unresolved near-duplicates that a human or LLM merge
would have cleaned up. But that messiness is the *cost of decomposition*,
and measuring it honestly is better than cleaning it up and measuring
the cleanup. Integration loss (§5.4) captures exactly this cost.

The LLM merge remains a natural follow-on study: "does an LLM merge
pass recover the integration loss, and at what cost?" That question is
well-posed once the baseline (deterministic merge) is established.

---

## 2. Deterministic integration procedure

### 2.1 Overview

Integration takes *G* sub-ontologies and produces one merged artefact
in two stages, both deterministic:

```
Stage 1:  Label normalisation + IRI reconciliation + raw union
Stage 2:  LogMap alignment + deterministic reconciliation
```

No LLM call. No stochastic component. Same inputs → same output.

### 2.2 Stage 1 — Normalisation and union

```
function stage1_union(sub_ontologies: list[Graph]) -> UnionResult:

    # ---------------------------------------------------------------
    # Step 1: Label normalisation
    # ---------------------------------------------------------------
    # Standardise rdfs:label casing, whitespace, punctuation.
    # Syntactic only — "Solder Paste" and "solder paste" unify;
    # "solder paste" and "solder cream" do NOT (that is Stage 2).

    for sub_onto in sub_ontologies:
        for entity in sub_onto.entities():
            if entity.label:
                entity.label = normalise_label(entity.label)

    # ---------------------------------------------------------------
    # Step 2: IRI reconciliation
    # ---------------------------------------------------------------
    # Entities sharing an IRI across sub-ontologies ARE the same entity.
    # Their axioms are collected into a union.

    iri_map = IRIProvenanceMap()
    shared_iris = set()

    all_entities = {}
    for g, sub_onto in enumerate(sub_ontologies):
        for entity in sub_onto.entities():
            if entity.iri in all_entities:
                shared_iris.add(entity.iri)
            all_entities.setdefault(entity.iri, []).append(g)
            iri_map.register(entity.iri, source=g)

    # ---------------------------------------------------------------
    # Step 3: Raw union
    # ---------------------------------------------------------------
    union_graph = Graph()
    for sub_onto in sub_ontologies:
        for axiom in sub_onto.axioms():
            union_graph.add(axiom)

    return UnionResult(
        union_graph=union_graph,
        iri_map=iri_map,
        shared_iris=shared_iris,
        labels_normalised=<count>,
    )
```

### 2.3 Stage 2 — LogMap alignment and deterministic reconciliation

LogMap identifies equivalent classes and properties across
sub-ontologies that use *different* IRIs for the same concept.
These are near-duplicates the raw union would preserve as separate
entities.

```
function stage2_align_and_reconcile(
    union_result: UnionResult,
    sub_ontologies: list[Graph],
) -> IntegrationResult:

    # ---------------------------------------------------------------
    # Step 1: Run LogMap pairwise
    # ---------------------------------------------------------------
    all_alignments = []
    for i, j in all_pairs(range(len(sub_ontologies))):
        alignments = logmap_align(sub_ontologies[i], sub_ontologies[j])
        all_alignments.extend(alignments)

    # Each alignment: (iri_a, iri_b, confidence, relation)
    # relation is typically '=' (equivalence)

    # ---------------------------------------------------------------
    # Step 2: Filter alignments by confidence threshold
    # ---------------------------------------------------------------
    # Use LogMap's default confidence threshold (typically 0.5).
    # Pinned in the manifest — not tuned per run.

    LOGMAP_CONFIDENCE_THRESHOLD = 0.5  # pinned
    accepted = [
        a for a in all_alignments
        if a.confidence >= LOGMAP_CONFIDENCE_THRESHOLD
           and a.relation == '='
    ]

    # ---------------------------------------------------------------
    # Step 3: Build equivalence clusters
    # ---------------------------------------------------------------
    # Group aligned IRIs into clusters. Each cluster represents one
    # concept with multiple IRIs across sub-ontologies.

    clusters = union_find(accepted)
    # clusters: list of sets of IRIs that LogMap considers equivalent

    # ---------------------------------------------------------------
    # Step 4: Deterministic IRI selection
    # ---------------------------------------------------------------
    # For each cluster, pick one canonical IRI by a fixed rule:
    # lexicographically first IRI. This is arbitrary but deterministic
    # and reproducible.

    integrated = copy(union_result.union_graph)
    iri_redirects = {}  # old_iri → canonical_iri

    for cluster in clusters:
        canonical = sorted(cluster)[0]  # lexicographic first
        for iri in cluster:
            if iri != canonical:
                iri_redirects[iri] = canonical

    # ---------------------------------------------------------------
    # Step 5: Apply redirects
    # ---------------------------------------------------------------
    # Replace non-canonical IRIs with canonical ones in all axioms.
    # Add owl:equivalentClass declarations for transparency.

    for old_iri, new_iri in iri_redirects.items():
        integrated.redirect_iri(old_iri, new_iri)
        integrated.add_axiom(EquivalentClass(old_iri, new_iri))

    # Remove orphaned entity declarations for redirected IRIs
    for old_iri in iri_redirects:
        integrated.remove_declaration(old_iri)

    # Update provenance map
    for old_iri, new_iri in iri_redirects.items():
        union_result.iri_map.merge(old_iri, into=new_iri)

    # ---------------------------------------------------------------
    # Step 6: Run AML as audit comparison
    # ---------------------------------------------------------------
    aml_alignments = []
    for i, j in all_pairs(range(len(sub_ontologies))):
        aml_alignments.extend(
            aml_align(sub_ontologies[i], sub_ontologies[j])
        )

    # Compare LogMap and AML agreement — reported in Paper 1 §8.1
    agreement = compute_alignment_agreement(accepted, aml_alignments)

    return IntegrationResult(
        integrated=integrated,
        iri_map=union_result.iri_map,
        alignments_found=len(accepted),
        iris_redirected=len(iri_redirects),
        clusters=len(clusters),
        logmap_aml_agreement=agreement,
    )
```

### 2.4 Why LogMap as primary, AML as audit

Both are well-established, benchmarked at OAEI, and freely available.
LogMap is chosen as the primary mechanism because it runs without a
GUI, has a stable Java API, and handles large ontologies efficiently.
AML is run as an audit comparison — if LogMap and AML disagree
substantially, that is reported as a finding about matcher sensitivity,
not resolved by picking a winner.

The LogMap confidence threshold is pinned in the manifest and not
tuned per run. This is a deliberate choice: per-run tuning would
introduce a researcher degree of freedom. The default threshold is
a defensible, citable baseline.

### 2.5 What the deterministic merge does NOT do

Unlike the LLM merge, this procedure does not:

- Resolve semantic conflicts between axiom sets (e.g., contradictory
  domain declarations for the same property). Both axioms survive in
  the union. The reasoner will flag the inconsistency.
- Create bridging concepts that connect sub-ontologies at a
  higher level of abstraction.
- Harmonise modelling patterns (e.g., one sub-ontology uses
  processes-as-classes, another uses processes-as-properties).
- Remove redundant intermediate classes across sub-ontologies.

All of these show up as measurable quality differences in the
evaluation battery — OOPS! flags the redundancy, the reasoner flags
inconsistencies, CQ answerability suffers if cross-genre queries
can't traverse the unharmonised structure. This is the cost of
decomposition, measured honestly.

### 2.6 Re-integration across rounds

Because the merge is deterministic, the same sub-ontology inputs
always produce the same integrated artefact. There is no merge
variance and no need for anchoring. Each round simply re-runs
the full procedure:

```
R0:  sub_ontologies_R0 → stage1 → stage2 → integrated_R0
R1:  sub_ontologies_R1 → stage1 → stage2 → integrated_R1
...
R9:  sub_ontologies_R9 → stage1 → stage2 → integrated_R9
```

Round-to-round differences in the integrated artefact are caused
entirely by sub-ontology changes (from iteration feedback), never
by merge instability. This is the property that eliminates the need
for anchoring.

Sub-ontology generation plus integration together constitute the R0
state for D1, so that R0 denotes "the first complete artefact, before
any feedback" at both D levels.

---

## 3. IRI provenance map

### 3.1 Structure

The provenance map tracks, for every entity IRI in the integrated
artefact, which sub-ontology or sub-ontologies contributed it.

```
@dataclass
class IRIProvenance:
    iri: str
    sources: set[int]          # sub-ontology indices (0..G-1)
    redirected_from: list[str] # original IRIs merged into this one
    first_seen_round: int
```

### 3.2 Construction

Built fresh each round from the integration result (no cross-round
maintenance needed, since the merge is deterministic — the map for
round R depends only on the sub-ontologies at round R).

```
function build_provenance_map(
    sub_ontologies: list[Graph],
    iri_redirects: dict[str, str],
) -> dict[str, IRIProvenance]:

    iri_map = {}

    for g, sub_onto in enumerate(sub_ontologies):
        for entity in sub_onto.entities():
            # Resolve redirects
            canonical = iri_redirects.get(entity.iri, entity.iri)

            if canonical in iri_map:
                iri_map[canonical].sources.add(g)
                if entity.iri != canonical:
                    iri_map[canonical].redirected_from.append(entity.iri)
            else:
                iri_map[canonical] = IRIProvenance(
                    iri=canonical,
                    sources={g},
                    redirected_from=(
                        [entity.iri] if entity.iri != canonical else []
                    ),
                    first_seen_round=current_round,
                )

    return iri_map
```

---

## 4. Defect routing

### 4.1 Design rationale

Feedback is computed on the *integrated* artefact. Per-sub-ontology
feedback would be blind to cross-genre defects — disjointness
violations, duplicate classes under conflicting parents, relation
signature clashes — which are precisely the defects decomposition
causes. Computing feedback on the integrated artefact and routing
it back to the responsible sub-ontology gives each sub-ontology the
information it needs to fix its own contribution to cross-genre
problems.

### 4.2 Routing rule

```
function route_defect(
    defect: Defect,
    iri_map: dict[str, IRIProvenance],
) -> list[str]:
    """Determine which sub-ontology feedback section(s) receive this defect.

    Returns
    -------
    List of channels:
      "sub:<g>"  — routed to sub-ontology g
    A defect may route to multiple sub-ontologies if it spans them.
    """
    participating_iris = defect.involved_entities()
    sources = set()

    for iri in participating_iris:
        prov = iri_map.get(iri)
        if prov is None:
            continue
        sources.update(prov.sources)

    if not sources:
        # No provenance found — should not happen; log and skip
        log_routing_failure(defect)
        return []

    if len(sources) == 1:
        # All entities from one sub-ontology
        return [f"sub:{sources.pop()}"]

    # Entities from multiple sub-ontologies — route to ALL involved.
    # Each sub-ontology sees the defect in its feedback and can
    # address its own contribution.
    return [f"sub:{g}" for g in sorted(sources)]
```

### 4.3 Key difference from the LLM-merge design

Under the LLM-merge design, cross-genre defects routed to an
"integration" feedback channel consumed by the merge step. Under
the deterministic merge, there is no integration channel — the merge
has no LLM call to receive feedback. Instead, cross-genre defects
route to *all involved sub-ontologies*. Each sub-ontology sees the
defect and can address its own side of the conflict.

This is the right behaviour: if sub-ontology A declares "SolderJoint
rdfs:subClassOf Component" and sub-ontology B declares "SolderJoint
rdfs:subClassOf Defect", the reasoner flags an inconsistency on the
integrated artefact. Both A and B receive this defect in their
feedback. Whichever sub-ontology changes its declaration resolves
the conflict. If neither does, the conflict persists — and that
persistence is measured as integration loss.

### 4.4 Feedback sections

Each sub-ontology has its own feedback section in its iteration prompt.
A sub-ontology's feedback contains defects routed to it — both
single-source defects (its own internal problems) and multi-source
defects (cross-genre conflicts it is involved in).

```
D1 round structure:
    # Integrate current sub-ontologies
    integrated = deterministic_integrate(sub_ontologies)
    iri_map = build_provenance_map(sub_ontologies, iri_redirects)

    # Compute feedback on the integrated artefact
    feedback = compute_all_feedback(integrated)

    # Route defects to sub-ontologies
    for defect in feedback.defects:
        channels = route_defect(defect, iri_map)
        for channel in channels:
            assign_to_channel(defect, channel)

    # Iterate each sub-ontology with its routed feedback
    for g in range(G):
        prompt = sub_ontology[g] + injection + feedback_for_sub[g]
        sub_ontology[g]' = llm_call(prompt)

    # Re-integrate with updated sub-ontologies (next round)

D0 round structure (for comparison):
    prompt = ontology + injection + all_feedback
    ontology' = llm_call(prompt)
```

### 4.5 Edge cases

**4.5.1 No defects.** All feedback sections are empty. Sub-ontologies
still receive their (empty) feedback and produce their next-round
output. This is a legitimate outcome — the sub-ontologies may have
converged.

**4.5.2 Defect involves only redirected IRIs.** An entity that was
redirected (merged with another by LogMap) keeps the provenance of
both original sources. The defect routes to all originating
sub-ontologies.

**4.5.3 Defect involves an entity with no provenance.** Should not
occur if the provenance map is correctly built. Logged as a routing
failure and excluded from the routing split statistics.

---

## 5. Logging

### 5.1 Per-round integration log record

```
{
    "run_id":                    str,
    "round":                     int,     # 0–9
    "n_sub_ontologies":          int,     # G

    # Stage 1 — normalisation and union
    "labels_normalised":         int,
    "shared_iris":               int,     # IRIs appearing in 2+ sub-ontologies
    "total_axioms_union":        int,     # axiom count in the raw union

    # Stage 2 — LogMap alignment
    "alignments_found":          int,     # equivalence alignments above threshold
    "iris_redirected":           int,     # IRIs merged into a canonical form
    "equivalence_clusters":      int,     # distinct concept clusters found
    "logmap_aml_agreement":      float,   # proportion of alignments both agree on

    # Integrated artefact
    "classes_integrated":        int,
    "properties_integrated":     int,
    "axioms_integrated":         int,

    # Round-to-round change (not "churn" — fully deterministic)
    "axioms_added_vs_prev":      int,     # axioms in R_n not in R_{n-1}
    "axioms_removed_vs_prev":    int,     # axioms in R_{n-1} not in R_n
    "delta_rate":                float,   # (added + removed) / total

    # IRI stability
    "iris_added_vs_prev":        int,
    "iris_removed_vs_prev":      int,
    "iris_stable":               int,
    "iri_stability_rate":        float,

    # Defect routing
    "defects_total":             int,
    "defects_single_source":     int,     # routed to exactly one sub-ontology
    "defects_multi_source":      int,     # routed to 2+ sub-ontologies
    "defects_per_sub":           dict,    # {sub_index: count}
    "multi_source_pct":          float,   # multi / total

    # Integration loss (computed by the battery)
    "integration_loss":          dict,    # {instrument: delta_value}
}
```

### 5.2 Delta vs. churn

Under the deterministic merge, round-to-round changes in the
integrated artefact are caused entirely by sub-ontology changes.
The log records these as "delta" rather than "churn" to signal that
they reflect sub-ontology improvement, not merge instability. The
delta rate is still informative — it shows how much the integrated
artefact changes per round and whether it converges — but its
interpretation is simpler than churn under an LLM merge.

### 5.3 IRI stability

IRI stability is still tracked because LogMap alignments may shift
across rounds: if a sub-ontology renames or restructures a concept
at round R, LogMap may find a different alignment at R than at R-1.
This is deterministic (same inputs → same alignment) but not
necessarily stable across rounds. The stability rate measures how
much the alignment decisions change as the sub-ontologies evolve.

### 5.4 Integration loss

The battery delta between the union of sub-ontologies and the
integrated artefact, computed at the four checkpoint rounds on the
grounding-agnostic instruments (v17; the orchestrator runs
`Battery.run_sub` for each sub-ontology only when the round is in
`RunConfig.checkpoint_rounds`, and writes `sub_battery.json` beside the
round's `battery.json`). Sub-ontology coverage is scored against that
genre's inventory. This is the headline measure of what decomposition
costs; it is descriptive, so the full ten-round trace is not needed.

Under the deterministic merge, integration loss has two components:

- **Redundancy cost.** Near-duplicate concepts that LogMap didn't
  align inflate class count and lower CQ answerability (queries that
  should traverse the full hierarchy may miss a branch).

- **Conflict cost.** Contradictory axioms from different sub-ontologies
  that survive into the integrated artefact, flagged by the reasoner
  as inconsistencies.

Both are honest measures of decomposition's cost. A practitioner
reading Paper 1 learns: "if you decompose by genre, here is how much
quality the merge loses, and here is what kind of defects it
introduces."

---

## 6. Integration with the generation pipeline (task 5)

The generation pipeline calls these components for each D1 round:

```
for round in 0..9:
    # Integrate current sub-ontologies
    union_result = stage1_union(sub_ontologies)
    integration_result = stage2_align_and_reconcile(
        union_result, sub_ontologies
    )
    integrated = integration_result.integrated
    iri_map = build_provenance_map(
        sub_ontologies, integration_result.iri_redirects
    )

    # Compute feedback on the integrated artefact
    feedback = compute_all_feedback(integrated)

    # Route defects
    for defect in feedback.defects:
        channels = route_defect(defect, iri_map)
        for channel in channels:
            assign_to_channel(defect, channel)

    # Log
    log_integration_record(round, integration_result, feedback, iri_map)

    # Checkpoint
    save_round_state(round, sub_ontologies, integrated, iri_map)

    # Iterate sub-ontologies (feedback applied in the next generation call)
    for g in range(G):
        sub_ontologies[g] = iterate_sub_ontology(
            sub_ontologies[g], injection, feedback_for_sub[g]
        )
```

Per-round LLM calls: G (sub-ontology iterations only). No merge call.

---

## 7. Parameters to pin

| Parameter | Description | Pinned by |
|---|---|---|
| `LOGMAP_CONFIDENCE_THRESHOLD` | Minimum confidence for accepted alignments | LogMap default (0.5) |
| `CANONICAL_IRI_RULE` | How to pick the surviving IRI in a cluster | Lexicographic first |
| `LABEL_NORMALISATION` | Casing, whitespace, punctuation rules | Fixed specification |
| `LOGMAP_VERSION` | LogMap release | Manifest |
| `AML_VERSION` | AML release | Manifest |

---

## 8. What this eliminates from the design

| Mechanism | Status |
|---|---|
| LLM-mediated merge pass | Removed |
| Anchored re-integration | Not needed (deterministic merge) |
| Merge churn logging | Replaced by deterministic delta |
| Pilot churn decision rule | Not needed |
| Integration feedback channel | Not needed (no merge call to iterate) |
| Per-round merge token cost | Zero |
| Merge prompt design | Not needed |

---

## 9. What this changes in the pilot (todo task 5)

The pilot still runs (2 seeds × 2 conditions — B0D0 and B2D1 — × R = 15), but its
purposes simplify:

- ~~Measure R0 merge churn under D1~~ → Not needed (deterministic)
- ~~Pre-registered churn decision rule~~ → Not needed
- **Measure integration loss** — still needed; now the primary
  integration diagnostic
- **Measure the defect-routing split** — still needed
- **Settle the round count** — still needed
- **Expose loop-coupling behaviour** — still needed
- **Supply variance estimates for the MDE** — still needed
- **Shake out the pipeline** — still needed
- **NEW: Verify LogMap alignment stability across rounds** — do
  alignments shift as sub-ontologies evolve?

---

## 10. Test plan

1. **Determinism test.** Run integration twice on the same
   sub-ontologies. Output must be bitwise identical.

2. **Shared-IRI test.** Two sub-ontologies with the same IRI for
   one concept. Verify the entity appears once in the integrated
   artefact with axioms from both sub-ontologies.

3. **LogMap alignment test.** Two sub-ontologies with different IRIs
   for the same concept (similar labels). Verify LogMap finds the
   alignment and the deterministic reconciliation redirects one IRI.

4. **Provenance accuracy.** After integration, verify every IRI in
   the integrated artefact has correct provenance (which sub-ontologies
   contributed it, and which IRIs were redirected).

5. **Routing — single source.** Inject a defect involving entities from
   one sub-ontology. Verify it routes only to that sub-ontology.

6. **Routing — multi-source.** Inject a defect spanning two
   sub-ontologies. Verify it routes to both.

7. **Round stability.** Run integration at R0 and R1 where one
   sub-ontology has a small change. Verify the delta reflects only
   that change. Verify IRI stability rate is high.

8. **Contradictory axioms.** Two sub-ontologies declare contradictory
   axioms for the same entity. Verify both survive in the union,
   the reasoner flags the inconsistency, and the defect routes to
   both sub-ontologies.
