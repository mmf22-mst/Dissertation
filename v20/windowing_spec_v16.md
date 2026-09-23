# Windowing Selection Rule and Patch-Merge Semantics — Specification (v16)

Companion to dissertation_overview_and_paper_outlines_v20.md, Part I §5
(context-overflow policy, edit-merge semantics, windowing in iteration
rounds) and Paper 1 §4.2–4.4.

Originally task 4a of dissertation_todo_v15.md; maintained under task 4
of dissertation_todo_v20.md.

**v16 changes (aligned to overview v19.1/v20).** No change to the
selection rule or to the merge algorithm. (a) §4 now states explicitly
what the overview says: the model always outputs the complete revised
view and never a patch format; the patch is the pipeline's difference
between that output and the view it supplied. Entities present in the
view but absent from the output are deletions, so unintended drops are
possible; entity-level deltas are now logged for every call (§5.1) and
the pilot reports the removal rate. (b) §5.3 corrects a stale statement:
integration is deterministic and involves no model call, so it never
windows; in iteration rounds the window is seeded by the feedback payload.
(c) The prompt now has four pinned allotments — injection, window, chunk,
and (iteration calls) feedback — and the feedback payload is rendered
under its allotment before this specification's rule runs (§2.1 note).

---

## 1. Purpose

The accumulated ontology grows as the generator processes successive corpus
chunks. When it exceeds the pinned window allotment, the generator sees a
*selected view* rather than the whole ontology. This specification defines:

1. **When** windowing fires (§2).
2. **What** the generator sees (§3 — the selection rule).
3. **How** the generator's output is merged back (§4 — patch-merge semantics).
4. **What** is logged (§5 — visibility statistics).

All four components are deterministic and seed-independent. The only
stochastic element in the pipeline is the LLM call itself; everything
around it is reproducible from the ontology state and the chunk content.

---

## 2. When windowing fires

### 2.1 Budget structure

*v16 note.* The construction prompt carries injection + window + chunk;
the iteration prompt carries injection + window + feedback. All four
allotments are pinned (overview Paper 1 §4.2). The feedback payload is
rendered under the FEEDBACK allotment by `feedback_payload.py` with a
fixed item order and per-item truncation caps, so by the time the
windowing check runs the fourth part of the prompt has a known ceiling
at either D level.

The generation prompt has three pinned allotments (Paper 1 §4.2):

| Allotment  | Contents                                    | Varies with B? |
|------------|---------------------------------------------|----------------|
| Injection  | Factor B scaffolding (nothing / BFO / IOF)  | **Yes**         |
| Window     | View onto the accumulated ontology          | No             |
| Chunk      | Corpus text for this call                   | No             |

Window and chunk allotments are fixed once, at values that fit under B2's
injection (IOF Core, the largest; v19), and reused unchanged for B0 and B1.
All allotments are pinned in the generator's real tokens (todo task 0c). This guarantees that corpus
exposure, accumulation steps, and windowing frequency are identical across
grounding conditions.

### 2.2 Trigger condition

```
let serialised = render_ontology(current_ontology)
if token_count(serialised) <= WINDOW_ALLOTMENT:
    # Full view — no windowing
    prompt_ontology = serialised
    windowed = False
else:
    # Windowed view
    prompt_ontology = select_window(current_ontology, current_chunk)
    windowed = True
```

### 2.3 Parameters to pin before the pilot

| Parameter           | Description                                 | Pinned by   |
|---------------------|---------------------------------------------|-------------|
| `WINDOW_ALLOTMENT`  | Token budget for the ontology view          | B2 fit test |
| `CHUNK_ALLOTMENT`   | Token budget for the corpus chunk           | B2 fit test |
| `SIM_THRESHOLD`     | Embedding similarity threshold for matching | Calibration |
| `FAN_OUT_CAP`       | Max siblings + children added per matched class | Design choice |
| `EMBEDDING_MODEL`   | Model used for label ↔ term similarity      | Manifest    |

All parameters are recorded in the seed register and environment manifest.

---

## 3. Selection rule

### 3.1 Overview

The selection rule builds a *window* — a subset of the ontology's classes
and their connecting structure — that is most relevant to the current
corpus chunk. It is deterministic, seed-independent, and uses no
randomness.

### 3.2 Algorithm

```
function select_window(ontology, chunk) -> serialised_view:

    # ---------------------------------------------------------------
    # Phase 1: Seed set — classes whose labels match chunk terms
    # ---------------------------------------------------------------
    chunk_terms = extract_terms(chunk)          # tokenised noun phrases
    class_labels = {cls: label(cls) for cls in ontology.classes()}

    scored = []
    for cls, lbl in class_labels.items():
        sim = embedding_similarity(lbl, chunk_terms)   # max over terms
        if sim >= SIM_THRESHOLD:
            scored.append((cls, sim))

    # Sort descending by similarity, ties broken by IRI (lexicographic)
    scored.sort(key=lambda x: (-x[1], str(x[0])))

    seed_classes = {cls for cls, _ in scored}

    # ---------------------------------------------------------------
    # Phase 2: Ancestor closure — every ancestor up to owl:Thing
    # ---------------------------------------------------------------
    ancestors = set()
    for cls in seed_classes:
        ancestors |= ancestor_closure(ontology, cls)
        # ancestor_closure returns all named superclasses, transitively,
        # excluding owl:Thing itself

    # ---------------------------------------------------------------
    # Phase 3: Local neighbourhood — siblings and direct children
    # ---------------------------------------------------------------
    neighbourhood = set()
    for cls in seed_classes:
        parent_classes = direct_parents(ontology, cls)
        for parent in parent_classes:
            siblings = direct_children(ontology, parent)
            neighbourhood |= siblings
        children = direct_children(ontology, cls)
        neighbourhood |= children

    # Cap: if |neighbourhood \ (seed_classes ∪ ancestors)| > FAN_OUT_CAP
    # per seed class, keep only the FAN_OUT_CAP closest by IRI sort
    # (not by similarity — these are structural neighbours, not matches)
    neighbourhood = _apply_fan_out_cap(
        neighbourhood, seed_classes, ancestors, FAN_OUT_CAP, ontology
    )

    # ---------------------------------------------------------------
    # Phase 4: Budget fill — remaining space in descending match order
    # ---------------------------------------------------------------
    selected = seed_classes | ancestors | neighbourhood
    budget_used = token_count(render_classes(selected, ontology))

    if budget_used < WINDOW_ALLOTMENT:
        # Fill with remaining classes in descending similarity order
        remaining = [(cls, sim) for cls, sim in scored if cls not in selected]
        # Also add unscored classes (sim < threshold) at score 0.0,
        # sorted by IRI for determinism
        unscored = [
            (cls, 0.0) for cls in ontology.classes()
            if cls not in selected and cls not in {c for c, _ in scored}
        ]
        unscored.sort(key=lambda x: str(x[0]))
        candidates = remaining + unscored

        for cls, _ in candidates:
            trial = render_classes(selected | {cls}, ontology)
            if token_count(trial) <= WINDOW_ALLOTMENT:
                selected.add(cls)
            else:
                break  # budget exhausted

    # ---------------------------------------------------------------
    # Phase 5: Render the window
    # ---------------------------------------------------------------
    # Include: selected classes, all properties whose domain AND range
    # are both in the selected set (or are untyped/universal), and all
    # axioms that reference only entities in the selected set.
    # Exclude: the Factor B injection (always present separately).

    return render_window(selected, ontology)
```

### 3.3 Edge cases

**3.3.1 No matches above threshold.** If `seed_classes` is empty (the chunk
contains no terms matching any ontology class label), the entire budget is
filled in IRI-sort order. This can happen early in construction when the
ontology is small, or with a highly technical chunk whose vocabulary hasn't
been captured yet. The chunk still gets a generation call; it just sees
the ontology from the top rather than from a relevance-seeded view.

**3.3.2 Seed set exceeds budget.** If the seed classes alone (before
ancestors) exceed `WINDOW_ALLOTMENT`, truncate the seed set at budget,
keeping the highest-similarity classes. Ancestors of the truncated set
are still added; the budget is soft (overrun is logged, not prevented)
because removing ancestors would break the hierarchy the model sees.
Siblings/children are skipped entirely in this case.

**3.3.3 Cycles.** `ancestor_closure` must handle cycles (OOPS! P06).
Implementation uses a visited set; a cycle is traversed once and then
stopped. The cyclic classes appear in the window; cycle-breaking is the
generator's job (and OOPS! will flag it in the feedback).

**3.3.4 Injected scaffolding.** BFO/IOF classes from the Factor B
injection are NOT part of the window budget and are NOT selected by the
windowing rule. They are always present in full in the injection allotment.
If a domain class's ancestor closure reaches a BFO/IOF class, that
ancestor is included in the window only if it is a *domain* class that
happens to share a BFO namespace (a contamination case); genuine BFO/IOF
classes are excluded from the window and accessed through the injection.

**3.3.5 Properties.** A property is included in the window if both its
declared domain and range (if any) are in the selected class set, or if
it has no declared domain/range. Properties with one end outside the
window are excluded — the model cannot reason about constraints it
can only half see. Annotation properties (labels, comments) are always
included for selected classes.

**3.3.6 Datatype properties.** Included if their domain is in the
selected class set.

### 3.4 Term extraction for matching

`extract_terms(chunk)` produces the set of noun phrases from the corpus
chunk that will be matched against ontology class labels. This uses the
same term extractor as the salient-term coverage instrument (task 2),
ensuring consistency between what the battery scores and what the window
selects. The extractor is pinned in the manifest.

### 3.5 Similarity function

`embedding_similarity(label, chunk_terms)` returns the maximum cosine
similarity between the embedding of `label` and the embeddings of all
terms in `chunk_terms`. The embedding model is pinned in the manifest
(same model as salient-term matching, governed by seed S-HAR for any
stochastic component — though typical embedding models are deterministic).

---

## 4. Patch-merge semantics

### 4.1 Problem

The generator sees a subset of the ontology. Its output is a complete
ontology *from the model's perspective* — but it is ignorant of
everything outside the window. Treating the output as a replacement
would delete every class, property, and axiom the model could not see.

### 4.2 Solution: patch extraction and application

The generator's output is differenced against the window it received,
producing a patch. The patch is then applied to the full ontology.

```
function patch_merge(full_ontology, window, model_output) -> updated_ontology:

    # ---------------------------------------------------------------
    # Step 1: Compute the patch
    # ---------------------------------------------------------------
    # The patch is the set of changes the model made, expressed as:
    #   - ADDED:    axioms/entities in model_output but not in window
    #   - REMOVED:  axioms/entities in window but not in model_output
    #   - (UNCHANGED: axioms in both — carried forward implicitly)

    added_axioms   = axioms(model_output) - axioms(window)
    removed_axioms = axioms(window) - axioms(model_output)

    added_entities   = entities(model_output) - entities(window)
    removed_entities = entities(window) - entities(model_output)

    # ---------------------------------------------------------------
    # Step 2: Validate the patch
    # ---------------------------------------------------------------
    # The patch must not reference entities that exist in the full
    # ontology but were not in the window — the model could not have
    # known about them, so any such reference is a hallucinated IRI
    # collision or a leakage from pretraining.

    invisible = entities(full_ontology) - entities(window) - added_entities
    violations = set()

    for axiom in added_axioms:
        referenced = entities_in(axiom)
        collision = referenced & invisible
        if collision:
            violations.add((axiom, collision))

    if violations:
        log_patch_violations(violations)
        # Policy: reject the violating axioms, keep the rest.
        # Rejected axioms are logged but not applied.
        added_axioms -= {a for a, _ in violations}

    # ---------------------------------------------------------------
    # Step 3: Apply the patch
    # ---------------------------------------------------------------
    updated = copy(full_ontology)

    for axiom in removed_axioms:
        updated.remove(axiom)

    for entity in removed_entities:
        # Remove the entity and all axioms that reference only it
        updated.remove_entity(entity)

    for axiom in added_axioms:
        updated.add(axiom)

    # New entities are implicitly added when their axioms are added.

    return updated
```

### 4.3 What counts as an axiom

For differencing purposes, an "axiom" is a single OWL axiom as parsed by
the OWL API or rdflib — a subClassOf statement, an equivalentClass
statement, a property declaration with its domain/range, an annotation,
etc. Comparison is structural (by normalised axiom content), not textual
(not by serialisation string). This matters because the model may
reserialise unchanged content in a different order or with different
whitespace.

### 4.4 Entity identity

Entities are identified by IRI. The model may:

- **Reuse an IRI from the window** — this is an edit to an existing entity.
- **Introduce a new IRI** — this is a new entity (added by the patch).
- **Drop an IRI from the window** — this is a deletion (removed by the patch).
- **Produce a new IRI that collides with an invisible entity** — this is a
  violation (§4.2 Step 2) and is rejected.

### 4.5 Deletion semantics

When the model removes a class or property from its output:

- If the removed entity is referenced by axioms *outside the window*
  (in the invisible portion of the ontology), it becomes a dangling
  reference. Policy: the entity's declaration is retained (it is not
  deleted from the full ontology), but its axioms within the window
  are removed as the model requested. The dangling reference is logged
  as a **orphaned-reference event** and reported in the visibility
  statistics. Rationale: deleting an entity that other parts of the
  ontology depend on would propagate the model's local decision into
  structure it never saw, which is exactly what patch-merge exists to
  prevent.

- If the removed entity has no references outside the window, it is
  deleted cleanly.

### 4.6 Non-windowed calls

When windowing does not fire (the full ontology fits), the model's output
replaces the full ontology directly — no patch extraction is needed. The
model saw everything, so its output is authoritative. This is logged as
`windowed = False` and no patch statistics are recorded for this chunk.

---

## 5. Visibility statistics

### 5.1 Per-chunk log record

Every generation call (construction chunk or iteration round) produces
one log record:

```
{
    "run_id":           str,      # e.g. "B2D0_s03"
    "phase":            str,      # "construction" | "iteration"
    "round":            int,      # 0 for construction, 1–9 for iteration
    "chunk_index":      int,      # sequential within the run
    "genre":            str,      # genre of the current chunk (or "mixed" for straddlers)
    "processing_position": int,   # ordinal position in the genre-blocked sequence
    "windowed":         bool,     # whether windowing fired
    "ontology_tokens":  int,      # token count of the full ontology
    "window_tokens":    int,      # token count of the window (= ontology_tokens if not windowed)
    "visibility_ratio": float,    # window_tokens / ontology_tokens
    "classes_total":    int,      # classes in full ontology
    "classes_visible":  int,      # classes in window
    "class_visibility": float,    # classes_visible / classes_total
    "seed_classes":     int,      # classes selected in Phase 1
    "ancestor_classes": int,      # classes added in Phase 2
    "neighbour_classes":int,      # classes added in Phase 3
    "fill_classes":     int,      # classes added in Phase 4
    "fan_out_capped":   bool,     # whether the fan-out cap was hit
    "patch_added":      int,      # axioms added by the patch (0 if not windowed)
    "patch_removed":    int,      # axioms removed by the patch
    "patch_added_entities":   int,  # v16: entities introduced by the output
    "patch_removed_entities": int,  # v16: entities in the view but absent from the output
    "patch_violations": int,      # axioms rejected for referencing invisible entities
    "orphaned_refs":    int,      # entities retained due to external references
}
```

*v16.* The two entity-level fields are logged for every call, windowed or
not (when windowing has not fired, the pipeline computes the entity delta
between the previous artefact and the replacement). `patch_removed_entities`
is the pilot's unintended-deletion measure under full-view regeneration
(overview Part I §5); the aggregate is reported per condition alongside the
visibility statistics in §5.2.

### 5.2 Aggregated statistics (reported in Paper 1)

From the per-chunk log, the following are computed and reported:

- **Windowed-chunk count** by condition, by genre, and by processing
  position. Tests whether late-processed genres are disadvantaged.

- **Mean visibility ratio** by condition and by processing position.
  The fraction of the ontology the model can see, averaged over chunks
  that are windowed.

- **Visibility gradient** — the regression of visibility ratio on
  processing position, by condition. A negative slope means later chunks
  see less of the ontology. Reported alongside the position-gradient
  descriptives in Paper 1 §5.3.

- **Patch violation rate** — the proportion of windowed chunks with at
  least one patch violation. A high rate would indicate the model is
  frequently hallucinating references to entities it cannot see, which
  is a threat to patch-merge validity.

- **Orphaned-reference rate** — the proportion of windowed chunks with
  at least one orphaned reference. Measures how often the model's local
  deletions conflict with the invisible structure.

### 5.3 Iteration rounds

During iteration (R1–R9), the feedback call operates on the *full*
ontology at both D levels. Under D0 this means the accumulated artefact;
under D1 it means each sub-ontology individually (smaller, and less
likely to trigger windowing). The integrated artefact is not itself
iterated, and integration is deterministic with no model call, so it
never windows (deterministic_integration_spec v17).

If windowing fires during an iteration round, the same selection rule,
patch-merge semantics, and logging apply, with one substitution: the
text that seeds Phase 1 (term matching) is the rendered feedback payload
rather than a corpus chunk, so the view is built around the entities
the feedback names. The `phase` field distinguishes construction from
iteration in the log, and iteration records also carry the feedback
truncation fields (`feedback_tokens`, `feedback_omitted`,
`feedback_overflow_steps`; see `feedback_payload.py`).

---

## 6. Integration with the generation pipeline (task 5)

This specification feeds directly into the generation pipeline (task 5).
The pipeline calls:

1. `should_window(ontology, WINDOW_ALLOTMENT)` → bool
2. `select_window(ontology, chunk)` → serialised view
3. `patch_merge(full_ontology, window, model_output)` → updated ontology
4. `log_visibility(...)` → appended to the per-chunk log

The pipeline owns the prompt assembly, the LLM call, the round-state
checkpointing, and the feedback logging. This specification owns the
content-selection and merge logic that sits on either side of the LLM call.

---

## 7. Test plan

Before the pilot, validate with:

1. **Round-trip test.** Load an ontology, window it, pass the window
   through unchanged, patch-merge. The result must be identical to the
   original. (Tests that no-op patches are truly no-ops.)

2. **Addition test.** Window, add a new class to the output, patch-merge.
   The new class must appear in the full ontology; all invisible classes
   must be unchanged.

3. **Deletion test — no external refs.** Window, remove a visible class
   with no references outside the window, patch-merge. The class must be
   gone. All invisible classes unchanged.

4. **Deletion test — with external refs.** Window, remove a visible class
   that IS referenced by an invisible axiom, patch-merge. The class
   declaration must survive; its window-scoped axioms must be removed;
   an orphaned-reference event must be logged.

5. **Collision test.** Window, add an axiom referencing an invisible
   entity's IRI, patch-merge. The axiom must be rejected; a patch
   violation must be logged.

6. **Budget overflow test.** Construct an ontology large enough to trigger
   windowing. Verify that the window fits within `WINDOW_ALLOTMENT` (soft
   overrun from ancestors is logged, not prevented). Verify that the
   visibility ratio is correctly computed.

7. **Determinism test.** Run the selection rule twice on the same inputs.
   Outputs must be identical (tests that IRI-sort tiebreaking and
   fan-out capping are deterministic).

8. **Cycle test.** Load an ontology with a subClassOf cycle. Verify that
   ancestor_closure terminates and the cyclic classes appear in the window.
