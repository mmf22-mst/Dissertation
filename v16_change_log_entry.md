# v16 Change Log Entry

Append to dissertation_change_logs_v15.md (which becomes dissertation_change_logs_v16.md).

---

### Revision 16 change log

**LLM-mediated merge replaced by deterministic integration.** The same minimum-viable-product logic that simplified the evaluation battery in earlier revisions now simplifies the D1 integration procedure. The LLM merge was the most capable option — it could resolve semantic conflicts, harmonise patterns, and create bridging concepts — but it introduced merge variance that required anchored re-integration, a pilot churn decision rule, and an integration feedback channel to compensate. These mechanisms were the heaviest new infrastructure in the design and existed entirely to stabilise an unstable merge step.

H1f asks whether decomposition changes convergence rate. The sub-ontologies are the objects of iteration — that is where the D1 treatment lives. The merge is infrastructure, not treatment. A deterministic merge makes integration a fixed cost of decomposition rather than a variable one, which is cleaner for H1f: trajectory differences are purely about sub-ontology iteration, not merge variance.

1. **Integration procedure redesigned.** Two-stage deterministic procedure: (1) label normalisation, IRI reconciliation, and raw union; (2) LogMap alignment-based reconciliation with a deterministic canonical-IRI rule (lexicographic first). AML runs as an audit comparison; LogMap/AML agreement is reported. No LLM call is involved in integration.

2. **Anchored re-integration eliminated.** Not needed — same sub-ontology inputs always produce the same integrated artefact. Integration is simply re-run each round from the current sub-ontologies.

3. **Integration feedback channel eliminated.** No merge LLM call to receive feedback. Cross-genre defects route to *all involved sub-ontologies* rather than to an integration channel. Each sub-ontology sees the defect and can address its own side of the conflict. Defects that persist are measured as integration loss.

4. **Merge churn replaced by deterministic delta.** Round-to-round changes in the integrated artefact are caused entirely by sub-ontology changes, not merge instability. Logged as "delta rate" rather than "churn" to signal the different interpretation.

5. **Pilot churn decision rule removed.** No merge variance to characterise. Pilot still measures integration loss, defect-routing split, and (new) LogMap alignment stability across rounds.

6. **Per-round D1 compute drops from G+1 to G LLM calls.** Integration adds LogMap compute but no LLM calls.

7. **LogMap promoted from audit trail to merge mechanism.** AML retained as audit comparison. Both pinned by version in the manifest.

8. **LLM-mediated merge repositioned as ancillary study §8.1.** "Does an LLM merge recover the integration loss, and at what cost?" — well-posed once the deterministic baseline is established.

9. **No hypotheses, primary outcomes, or statistical plan changed.** Integration loss, IRI stability, and the defect-routing split remain D1 integration descriptives. The routing split now reports single-source vs. multi-source rather than sub-ontology vs. integration.

**Sections edited in dissertation_overview_and_paper_outlines_v16.md:**

| Section | Edit |
|---|---|
| Revision header | v16 with change summary |
| §5 "Integration procedure for D1" | Rewritten: deterministic two-stage, LogMap as mechanism, AML as audit |
| §5 "Anchored re-integration" | Replaced with "Deterministic re-integration" — no anchoring needed |
| §5 "What this costs" | G calls, not G+1; integration adds no LLM calls |
| §10 threat table, merge variance row | Eliminated: deterministic integration |
| §10 threat table, cross-genre defects row | Feedback routed to all involved sub-ontologies |
| §12 campaign sizing, D1 surcharge row | 6× not 7×; no integration LLM call |
| Paper 1 §4.3 generation procedure | Deterministic integration, no LLM call, LogMap/AML |
| Paper 1 §4.4a feedback routing | Rewritten: route to all involved sub-ontologies, no integration channel |
| Paper 1 §5.3 D1 integration descriptives | Delta rate replaces merge churn; single-source/multi-source replaces sub-ontology/integration |
| Paper 1 §7.15 D1 integration analysis | LogMap alignment stability; routing split redefined |
| Paper 1 §8.1 | LLM merge repositioned as follow-on study |
| Todo list task 4b | Rewritten for deterministic integration |
| Todo list task 5 | Deterministic integration, no anchoring |
| Todo list task 6 pilot | Churn decision rule removed; LogMap stability check added |
| Todo list sequencing table row 5 | Effort reduced from 5–8 to 4–6 days |

**Specification document:** dissertation_overview_and_paper_outlines_v16.md supersedes v15.
