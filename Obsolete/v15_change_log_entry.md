# v15 Change Log Entry

Append to dissertation_change_logs_v14.md.

---

### Revision 15 change log

**Standing priority applied again.** The same logic that kept OOPS! in the feedback loop (revision 11.1) now applies to the pitfall-overlap audit: suppressing pitfalls to protect a secondary held-out metric (OntoQA) would withhold useful structural feedback from the generator, producing worse ontologies — and those ontologies are the input to Papers 2 and 3. OntoQA was already a secondary outcome. The cost of reclassifying it is narrow; the benefit is a better construction procedure and a simpler design.

1. **OntoQA structural profile reclassified from held out to loop-coupled.** The full OOPS! report — all pitfalls, no suppression — is fed back to the generator. OntoQA is now coupled through the OOPS! channel: many pitfall remediations mechanically change structural metrics (class count, inheritance richness, relationship richness, attribute richness, depth, orphan rate). OntoQA values at R0 remain confirmatory; R1–R9 values are reported as process evidence alongside the other coupled trajectories.

2. **The pitfall-overlap audit is removed.** With OntoQA coupled, there is no held-out metric to protect, so the per-pitfall suppression mechanism is unnecessary. The audit document (pitfall_overlap_audit_v14.md) is retained in the project archive as the analysis that motivated this decision.

3. **The held-out instrument set simplifies** to three families: CQ answerability, salient-term coverage, and genre coverage balance. These are the primary outcomes for all confirmatory hypotheses and are untouched by any feedback channel.

4. **The coupled instrument set expands** to: global consistency, unsatisfiable-class count, OWL 2 DL conformance, OOPS! pitfall counts, OntoQA structural profile, and the two alignment rates. All confirmatory at R0; reported as process/compliance evidence for R1–R9.

5. **No hypotheses, factors, primary outcomes, or statistical plan changed.** The primary outcome per hypothesis is unchanged: CQ answerability for H1a, H1c, H1d, H1e, H1f; genre coverage balance for H1b; salient-term coverage co-primary throughout. The trajectory model still fits on held-out instruments; OntoQA trajectories are now reported alongside the coupled set.

**Sections requiring edits in dissertation_overview_and_paper_outlines_v14.md → v15:**

| Section | Edit |
|---|---|
| §5.5 instrument inventory table | OntoQA row: loop status changes from "Held out" to "**Coupled**" |
| §5.7 "Second-order coupling: the pitfall-overlap audit" paragraph | Delete entirely. Replace with one sentence: "The full OOPS! report is fed back with no suppression; OntoQA is coupled through the OOPS! channel and is treated accordingly (§5.7, items 1–4 above)." |
| §5.7 "Confirmatory round-related inference rests on the held-out set" | Remove "and OntoQA structural profile" — list becomes "CQ answerability, salient-term coverage, and genre coverage balance" |
| §5.7 "Scope restriction on H1d–H1f" (under §7) | Same: held-out instruments = CQ answerability, salient-term coverage, genre coverage balance |
| Paper 1 §5.3 loop-coupled trajectories list | Add "OntoQA structural profile" to the parenthetical: "(consistency, unsatisfiable-class rate, OWL 2 DL conformance, OOPS! pitfall counts, OntoQA structural profile, alignment rates across R1–R9)" |
| Paper 1 §5.3 secondary outcomes | OntoQA structural profile remains listed as a secondary outcome; add note that it is loop-coupled and confirmatory at R0 only |
| §5.5 trajectory model | "For each run and each held-out instrument" unchanged — OntoQA trajectories are now fitted and reported alongside the coupled set, not as part of this sentence's scope |
| Paper 1 §7.1 | Remove reference to the suppressed-pitfall list |
| Todo list (task 3a) | Closed: pitfall-overlap audit removed from the design |
| Todo list (task 3 effort) | Effort for task 3 drops slightly: OOPS! pipeline still needed, but the audit sub-task is gone |

**Specification document:** dissertation_overview_and_paper_outlines_v15.md will supersede v14 with these changes.
