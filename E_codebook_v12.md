# Source-Linked Codebook — v12

*Six retained codes (E1–E6 in the current scheme), five archived. Historical entries use the E1–E11 scheme throughout; §0.02 maps between them.*

**Status:** Draft for provenance review. Full file, superseding v8. v12 reconciles the codebook with dissertation overview v12: the code set is reduced to six, the Tier C material and the V2 apparatus are archived rather than deleted, and the rules gain denominators, loop status and sub-ontology closure. Earlier change logs (§0.00, §0.0) are retained for provenance. Nothing below is a diff.

**Governs:** Paper 1 §3–§4 of dissertation overview v12, which is the paired document; the two move together. The codes apply to B1 and B2 artefacts only, per the scope limit in overview §5.3.

---

## 0.000 — Changes from v8 (reconciliation with overview v12)

1. **The code set is six.** E1, E3, E5, E7, E9 and E11 of the historical scheme are retained and renumbered E1–E6. E2, E4, E6, E8 and E10 are archived: they required heuristic or judge-based detection and the V2–V5 validation apparatus, both removed from the design. Their entries stay in §2 under their historical numbers, marked **ARCHIVED**, because their derivation is sound and a later paper may revive them.
2. **The V2 apparatus is archived with them.** R4 (mutant stratification), §0.4 (the Prover9 test-theory package) and checklist items 7, 8 and 15 specify machinery the design no longer contains. They are marked superseded, not deleted. No heuristic code remains, so no empirical calibration is needed: Tier A codes are validated by the reasoner, Tier B codes by their own formalisation.
3. **R7 is added: denominators.** Every code reports a detection *rate* over a stated eligible-site denominator, never a bare count, because artefact size varies systematically with condition. The per-code denominators already stated in §2 are now the normative list, and count models in the overview carry a matching `log(denominator)` offset.
4. **Loop status is recorded per code (§1.1).** The reasoner report is part of the iteration feedback payload, so E1 and E3 (current scheme) are loop-coupled: the model is told about unsatisfiable classes and fixes them. They are confirmatory at R0 and reported as process evidence thereafter. E2, E4, E5 and E6 are held out.
5. **Sub-ontology closure is recorded per code (§1.1).** Overview v12 evaluates D1's persisting sub-ontologies to compute integration loss. A code whose eligibility is not closed within a sub-ontology cannot be read that way: E2 is the clear case, since a bearer may sit in another genre's sub-ontology, so pre-merge E2 is inflated and integration loss would read negative for a reason that has nothing to do with merge quality.
6. **Descriptive indicators renamed I1–I5.** The former D1–D5 collided with Factor D's levels D0 and D1 throughout the overview.
7. **Checklist item 17 is closed as overtaken.** It asked for the overview to expand to E1–E11; the design moved the other way.
8. **A new §4 holds the OOPS! pitfall-overlap mapping**, which overview v12 designates the codebook as the home for.
9. **Unchanged and reaffirmed:** R1 (condition-invariant eligibility), R2, R3, R5 (discrimination check), R6, the B2 baseline requirement for current E3/E5/E6, Table 0.2b's role in B2 scoping, and indicator I3 as the operationalisation of "below *entity*" — the overview's v11.3 attempt to fold that into E5 is withdrawn in v12.

---

## 0.01 — The six retained codes

| Current | Historical | Name | Tier | Family |
|---|---|---|---|---|
| E1 | E1 | Disjoint-category co-subsumption | A | BFO commitment |
| E2 | E3 | Specifically dependent continuant without bearer | B | BFO commitment |
| E3 | E5 | Core relation signature violation | A | BFO commitment |
| E4 | E7 | Universal–particular conflation | B | Realist practice |
| E5 | E9 | Upper-level tampering and vocabulary fabrication | B | ISO conformance |
| E6 | E11 | Multiple asserted parents without defined-class status | B | ISO conformance |

**Archived:** historical E2 (role-bearing type as primitive material subtype), E4 (directive content / process conflation), E6 (quality / realizable misassignment), E8 (information content / material carrier conflation), E10 (nominal grounding). All Tier C.

## 0.02 — Reading the historical numbering

Everything in §§0.0–0.5, §1 and §2 uses the historical E1–E11 scheme, and the rules R1–R6 were written against it. Two collisions matter when tracing a code between documents:

- Historical **E4** (*directive content / process conflation*, archived) is **not** current E4 (*universal–particular conflation*, retained).
- Historical **E5** (*core relation signature violation*, retained as current E3) is **not** current E5 (*upper-level tampering*, historical E9).

R3, which attributes a root unsatisfiable class between "E1" and "E5", uses the historical labels: it is the current E1/E3 attribution rule.

---

## 0.00 — Changes from v7 (decisions on checklist items 11–15)

1. **Item 11 — bare conjunctions count as defined classes (E11).** E11 adopts the permissive reading: any `owl:equivalentClass` axiom satisfies the (b2) proxy, including a bare Boolean conjunction.
   - *Rationale:* ISO/IEC 21838-2:2021's own defined-class example in §4.8.2.4 (*attribute* ≡ quality or realizable entity) is a bare Boolean, so the strict reading would contradict the standard's illustration.
   - *Safeguard:* a new descriptive indicator I1 reports, per condition, how many E11-eligible classes are defined only by a bare conjunction. A sharp condition difference would show the permissive reading masking multiple inheritance.
2. **Item 12 — E2 stays a principle.**
   - §3.5 is cited as supporting evidence only. No clause makes primitive assertion of a role-based term non-conformant: `Operator ⊑ object` satisfies §4.6.2(b1).
   - Calling it non-conformant presupposes that *Operator* is not a universal, which is the realist principle itself. An ISO grading would therefore be circular, and E2's limitations now say so.
3. **Item 13 — no relabelling-disclosure code.**
   - There is no normative disclosure requirement for domain ontologies, and a disclosure check would need a new validated instrument for a low-prevalence phenomenon.
   - Instead, descriptive indicator I2 counts protected-IRI labels that differ from the release, a free by-product of the E9 diff. If I2 is non-trivial, it is examined as a Paper 2 covariate, because extraction prompts read labels.
4. **Item 14 — split the §4.6.2 level requirement.**
   - "In any case at a level below *entity*" is reported exactly, as descriptive indicator I3: domain classes asserted directly under `BFO_0000001`.
   - "Lowest suitable level" is not operationalised separately. It requires the category judgement E6, E8 and E10 already approximate, and IOF's own `ProcessCharacteristic ⊑ continuant` shows that a strict version would penalise B2 artefacts for following IOF style.
5. **Item 15 — V2 mutants stratified 50/50, prevalence-weighted pooling (R4 revised).**
   - Each Tier C code's 200 mutants split into 100 lexical-match and 100 non-lexical-match, giving a worst-case 95% CI of about ±10 points per stratum.
   - Sensitivity is reported per stratum. Pooled sensitivity is weighted by the proportion of non-lexical class names observed in the generated B1/B2 artefacts; the weighting rule is pre-registered now and the proportion filled in once artefacts exist.
   - This replaces v7's proposed one-third floor. The budget is unchanged at 1,000 mutants + 1,000 clean runs.
6. **New §1.5 — Descriptive indicators I1–I5.** These gather the non-code quantities the codebook reports: I1–I3 above, plus v7's "IOF-only unsatisfiable" classes (I4) and B2-only upper-level term usage (I5). None enters inferential condition comparisons.

---

## 0.0 — Changes from v6 (v7 log, retained)

**Measurement fixes (change what gets counted)**

1. **Condition-invariant eligibility (new §1.2, rule R1).** Eligibility predicates for every code are now identical in B1 and B2. IOF-specific structural signals are used only as detection aids, with a pre-registered sensitivity analysis. v4–v6 let B2 artefacts become eligible for E4 and E8 through routes B1 artefacts lacked. That is condition-linked differential error, which can reverse a condition comparison rather than merely attenuate it.
2. **E4's IOF detection aid corrected.** IOF's `PlanSpecification` (IOF synonyms: "work instruction", "process specification", "process design") has no `prescribes` restriction in OWL, so reasoners never infer it under `DirectiveInformationContentEntity`. The aid is now the union of `DirectiveInformationContentEntity`, `PlanSpecification` and `ActionSpecification`. IOF's `PlannedProcess` is added as an E4b near-miss negative.
3. **Root-unsatisfiable counting and a workable E1/E5 attribution rule (rules R2, R3).** Counting all unsatisfiable classes rewarded hierarchy depth. The v6 attribution rule could never assign E5, because every domain/range clash also needs a disjointness axiom. E1's vacuous "probe form" is removed.
4. **E11 computed on the asserted hierarchy over all named parents.** The classified hierarchy would give false positives from IOF Core's 41 defined classes. Restricting to BFO/IOF parents missed domain-level multiple inheritance. The (b2) test is stated as a syntactic operationalisation of the standard's modal "able to be defined".
5. **E7 rebuilt.** v6's "individual as restriction filler" condition would flag ordinary `owl:hasValue`. The punning condition did not detect the code's own definition. v3's claim that punning violates BFO axiom `qkp-1` by entailment is withdrawn, because under OWL 2 punning the class and individual readings denote distinct entities. E7 returns to the realist-practice family.
6. **Lexicon/injection separation (rule R4).** Tier C mutants must be sampled from a frame independent of the detector lexicon, including non-lexical names. Otherwise V2 measures a detector finding its own vocabulary.
7. **E3 discrimination check (rule R5)** added, against a floor/ceiling effect.
8. **E9 definition-change check restored.** ISO §4.8.2.5 concerns *relabelling*. v6 also dropped `skos:definition` changes, which relabelling does not cover. Label changes stay excluded.

**Citation and provenance fixes**

9. **Table 0.4 rebuilt with a "present in `bfo-core.owl`?" column.** v6 conflated "carries no OWL identifier" with "exists only in CLIF/Prover9". Disjointness and domain/range axioms *are* in the OWL file; they just carry no `nnn-BFO` annotation.
10. **Axiom counts corrected.** The CLIF files contain 367 axiom entries (354 unique codes); the Prover9 files contain 380 labels (366 unique). The 13 unmatched Prover9 labels include axioms codes rely on (§0.3). One of them, the definition of independent continuant, exists in the Prover9 files but not in the CLIF files of the same generation date.
11. **ISO citation scope corrected.** The CL axiomatization cited is the 2025-12 maintained release, which post-dates ISO/IEC 21838-2:2021 and includes revised axioms. §4.4 is now cited only for the requirement of a CL layer, not as the source of 2025 axiom codes. §4.8.2 ("conformant profiles") concerns versions of BFO itself; domain-ontology conformance is §4.6. v6's use of §4.8.2.3 for B1 was wrong and is removed. §4.8.2.4 and §4.8.2.5 are now cited as interpretive analogies, flagged as such.
12. **Arp, Smith & Spear chapter numbering marked provisional.** It was inferred from an ebook contents view that may be flattened.
13. **Benson et al. full reference added and year corrected to 2025** (STIDS 2025), per the paper itself; the project filename says 2024.

**Consistency fixes**

14. **E6 grading corrected.** Single misplacements are elucidation-based. Only the restriction forms are axiom-detectable, and those are E5.
15. **E2's possible ISO grounding recorded** as an open grading question (§3, item 12), not silently asserted either way.
16. **Table 1.1 overlaps added:** E5 & E6, E1 & E9.
17. **E9(b) B2 baseline** now excludes IOF's own axioms on `BFO_0000144`, not only the term.
18. **Families reported at sub-pattern level, no double-counting:** six BFO-commitment codes, three realist-practice codes, two ISO-conformance codes.
19. **V2 budget finding restored** (lost in the v4 fold).
20. **§4.6.2's "lowest suitable level, below entity" requirement noted** as an uncaptured scope item (§3, item 14).

---

## 0.1 — Pinned references

| Reference | Pin | Role in codebook | Status |
|---|---|---|---|
| BFO 2020 OWL | `bfo-core.owl`, versionIRI `http://purl.obolibrary.org/obo/bfo/2020/bfo-core.owl` | Detector layer (B1) | In project; verified |
| BFO 2020 OWL, classic build | `bfo.owl`, versionIRI `.../bfo/2020/bfo.owl`, as cached in IOF release 202603 | Detector layer (B2, via IOF import) | Read in-session; verified |
| BFO 2020 Common Logic (CLIF) | 13 modules + temporal profile, generated 2025/12/05 | First-order commitments | Read in-session; **post-dates ISO publication** |
| BFO 2020 Prover9 | 13 modules + temporal profile + consistency model, generated 2025/12/05 | First-order commitments; test theories | Read in-session; **diverges from CLIF in at least one axiom (§0.3)** |
| IOF Core | `core/Core.rdf`, versionIRI `https://spec.industrialontologies.org/ontology/202603/core/Core/` | B2 baseline | Read in-session; verified |
| ISO/IEC 21838-1:2021 | Clauses 3–5, Annexes | Conformance framework | In project; verified |
| ISO/IEC 21838-2:2021 | Clauses 3–4.10 | Conformance framework | In project; verified |
| Arp, R., Smith, B., & Spear, A. D. (2015). *Building Ontologies with Basic Formal Ontology*. MIT Press. | Chapter/page ranges (provisional numbering) | Realist principles | Chapter ranges only |
| Benson, C.-B., Sculley, A., Liebers, A., & Beverley, J. (2025). My Ontologist: Evaluating BFO-Based AI for Definition Support. *STIDS 2025: Semantic Technology for Intelligence, Defense, and Security.* | — | Empirical motivation | In project; verified |

**Release reconciliation (for Paper 1's methods section).** Four BFO-related artefacts are pinned:
- **`bfo-core.owl`** — detector layer for B1.
- **Classic `bfo.owl`** — imported by IOF, so the detector layer for B2. It has the same 36 classes as `bfo-core.owl` plus 24 additional relations.
- **CLIF (2025-12)** — the maintained first-order axiomatization, revised after the 2021 ISO publication. For example, `participates-in-domain-range` moved from `ild-1` to `ild-2`: the formula was rewritten, though the domain is logically equivalent.
- **Prover9 (2025-12)** — generated alongside the CLIF, but not identical to it.

No conflict material to any code's definition was found. The first-order citations are nonetheless to the *maintained* axiomatization, not to the ISO-normative 2021 text. If ISO-exact first-order citations are required, the 2021 CLIF release must be obtained (§3, item 9).

**Arp, Smith & Spear contents (provisional).** The ebook contents view lists these sections in order, with starting pages: What Is an Ontology? (1); Kinds of Ontologies and the Role of Taxonomies (27); Domain Ontology Design (43); Terms, Definitions and Classification (59); Continuants (85); Occurrents (121); Basic Formal Ontology at Work (151); Languages, Editors, Reasoners, Browsers, Tools (173); Web Links (187). Chapter numbers 1–7 below are assigned from that order. The view may be flattened, so the print edition may contain chapters or sub-parts it does not show; for example, there is no separate relations chapter between Occurrents and BFO at Work. "Languages, Editors…" and "Web Links" are probably appendices. All Arp citations below are marked *(prov.)* until checked against the print contents.

**ISO/IEC 21838 clause map (verified from both PDFs).**
- **21838-1 §5 (Conformity)** requires a TLO to provide ontology documentation (§5.2: natural-language, OWL 2 and CL axiomatizations) and supplementary documentation (§5.3). It concerns the TLO, not domain ontologies.
- **21838-2 §3.2** defines *universal*; **§3.5** defines *defined class* ("collection … whose members are defined by specifying a restriction on one or more universals … that is not the extension of any universal"). Its examples include *lathe operator (meaning: person with an employment role realized through operating a lathe)*. **§3.6** defines *instance*.
- **21838-2 §4.3** specifies the OWL 2 formalization of BFO-2020; **§4.4** the CL axiomatization.
- **21838-2 §4.6** is the operative clause for *domain-ontology* conformance. **§4.6.2** (direct extension) requires:
  - (a) the merge with BFO is consistent;
  - each term either (b1) connects to BFO by a unique is_a chain, or (b2) is able to be defined from terms satisfying (b1);
  - "no term in the resulting ontology shall have more than one parent";
  - BFO categories are used "at the lowest level in the BFO hierarchy suitable … and in any case at a level below 'entity'".
  
  **§4.6.3** covers indirect extension, **§4.6.4** re-engineering, and **§4.6.5** validation (consistency plus interpretability of BFO, via reasoners for OWL).
- **21838-2 §4.8.2** defines *conformant profiles*: versions of BFO itself (profiles, subsets, slims, views, modules) whose derivable assertions are provable from BFO-2020-CL (§4.8.2.1). The named types are alternative axiomatization (§4.8.2.2), signature restriction (§4.8.2.3), incorporation of defined classes (§4.8.2.4) and relabelling with IRIs preserved (§4.8.2.5). **These clauses govern modified versions of BFO, not domain ontologies.** Where this codebook uses §4.8.2.4 or §4.8.2.5 for domain artefacts (E9, E11), it does so by analogy, and says so.

**Citation convention.** BFO content is cited in three identifier systems:
- the OWL `identifier` annotation `[nnn-BFO]`, on 76 terms;
- the CLIF short code `xyz-n`;
- the Prover9 `label("…")`.

§0.3 maps them. IOF content is cited by IRI under `iof:` = `https://spec.industrialontologies.org/ontology/construct/`. `obo:` = `http://purl.obolibrary.org/obo/`.

---

## 0.2 — BFO 2020 reference tables

### Table 0.1 — Asserted disjointness in `bfo-core.owl` (complete; 26 pairs)

Most pairs are asserted via `owl:AllDisjointClasses` groups rather than pairwise `owl:disjointWith`. Class IRIs are `obo:BFO_0000nnn`; the suffix is in brackets.

| # | Pair | # | Pair |
|---|---|---|---|
| 1 | continuant [002] ⊥ occurrent [003] | 14 | 1-D spatial region [026] ⊥ 0-D spatial region [018] |
| 2 | continuant fiat boundary [140] ⊥ site [029] | 15 | 1-D temporal region [038] ⊥ 0-D temporal region [148] |
| 3 | continuant fiat boundary [140] ⊥ spatial region [006] | 16 | process [015] ⊥ process boundary [035] |
| 4 | disposition [016] ⊥ role [023] | 17 | process [015] ⊥ spatiotemporal region [011] |
| 5 | fiat line [142] ⊥ fiat point [147] | 18 | process [015] ⊥ temporal region [008] |
| 6 | fiat line [142] ⊥ fiat surface [146] | 19 | process boundary [035] ⊥ spatiotemporal region [011] |
| 7 | fiat point [147] ⊥ fiat surface [146] | 20 | process boundary [035] ⊥ temporal region [008] |
| 8 | GDC [031] ⊥ independent continuant [004] | 21 | quality [019] ⊥ realizable entity [017] |
| 9 | GDC [031] ⊥ SDC [020] | 22 | site [029] ⊥ spatial region [006] |
| 10 | immaterial entity [141] ⊥ material entity [040] | 23 | spatiotemporal region [011] ⊥ temporal region [008] |
| 11 | independent continuant [004] ⊥ SDC [020] | 24 | 3-D spatial region [028] ⊥ 2-D spatial region [009] |
| 12 | 1-D spatial region [026] ⊥ 3-D spatial region [028] | 25 | 3-D spatial region [028] ⊥ 0-D spatial region [018] |
| 13 | 1-D spatial region [026] ⊥ 2-D spatial region [009] | 26 | 2-D spatial region [009] ⊥ 0-D spatial region [018] |

Function ⊑ disposition, so function ⊥ role follows from pair 4.

**Not asserted, and so outside E1's scope:**
- object [030] / fiat object part [024] / object aggregate [027];
- temporal instant [203] / temporal interval [202] (entailed via pair 15, since they sit under [148] and [038]);
- history [182] (a subclass of process, not disjoint from it);
- relational quality [145] vs. other qualities.

### Table 0.2 — Relations used by the codes (from `bfo-core.owl`; verified)

GDC = generically dependent continuant; SDC = specifically dependent continuant; IC = independent continuant; SR = spatial region.

| Relation | IRI | Domain | Range |
|---|---|---|---|
| inheres in | BFO_0000197 | SDC | IC ⊓ ¬SR |
| bearer of | BFO_0000196 | IC ⊓ ¬SR | SDC |
| specifically depends on | BFO_0000195 | SDC | SDC ⊔ (IC ⊓ ¬SR) |
| realizes | BFO_0000055 | process | realizable entity |
| has realization | BFO_0000054 | realizable entity | process |
| participates in | BFO_0000056 | SDC ⊔ GDC ⊔ (IC ⊓ ¬SR) | process |
| has participant | BFO_0000057 | process | SDC ⊔ GDC ⊔ (IC ⊓ ¬SR) |
| concretizes | BFO_0000059 | process ⊔ SDC | GDC |
| is concretized by | BFO_0000058 | GDC | process ⊔ SDC |
| generically depends on | BFO_0000084 | GDC | IC ⊓ ¬SR |
| is carrier of | BFO_0000101 | IC ⊓ ¬SR | GDC |
| continuant part of | BFO_0000176 | continuant | continuant |
| has continuant part | BFO_0000178 | continuant | continuant |
| occurrent part of | BFO_0000132 | occurrent | occurrent |
| has occurrent part | BFO_0000117 | occurrent | occurrent |
| has temporal part | BFO_0000121 | occurrent | occurrent |
| occurs in | BFO_0000066 | process ⊔ process boundary | site ⊔ material entity |
| located in | BFO_0000171 | IC ⊓ ¬SR | IC ⊓ ¬SR |
| occupies temporal region | BFO_0000199 | process ⊔ process boundary | temporal region |
| has material basis | BFO_0000218 | disposition | material entity |

**Universal class restrictions in `bfo-core.owl` that strengthen E5:**
- continuant ⊑ ∀ continuant part of . continuant
- material entity ⊑ ∀ continuant part of . material entity
- process ⊑ ∀ has occurrent part . (process ⊔ process boundary)
- process ⊑ ∀ occurrent part of . process
- temporal region ⊑ ∀ occurrent part of . temporal region
- process boundary ⊑ ∀ occurrent part of . (process ⊔ process boundary)

### Table 0.2b — The 24 relations in classic `bfo.owl` absent from `bfo-core.owl` (B2 scope)

These were verified by direct diff of the two files. All are "at all times", "proper", or "some time proper" variants:

BFO_0000082 located in at all times · 110 has continuant part at all times · 111 has proper continuant part at all times · 113 has material basis at all times · 118 has proper occurrent part · 136 proper temporal part of · 137 proper continuant part of at all times · 138 proper occurrent part of · 163 material basis of at all times · 164 concretizes at all times · 165 is concretized by at all times · 166 participates in at all times · 167 has participant at all times · 170 location of at all times · 172 has member part at all times · 173 member part of at all times · 174 has proper continuant part at some time · 175 proper continuant part of at some time · 177 continuant part of at all times · 181 has proper temporal part · 211 occupies spatial region at all times · 217 spatially projects onto at all times · 219 generically depends on at all times · 220 is carrier of at all times.

---

## 0.3 — Identifier mapping across OWL, CLIF and Prover9

**Counts (corrected).**
- *CLIF:* 367 axiom entries carrying a short code, 354 unique codes (some axioms repeat across modules and the temporal profile).
- *Prover9:* 380 labels, 366 unique.
- *Matching:* by exact normalized description, 367 Prover9 entries match a CLIF entry. The 13 that do not are listed below.

**The 13 unmatched Prover9 labels.** Some bear on codes:

| Prover9 label | Bears on | Note |
|---|---|---|
| `definition-of-independent-continuant` | **E8** | **No CLIF counterpart found in the same-date CLIF files.** Cite to Prover9 and to OWL `[017-BFO]` only. |
| `s-depends-means-bearer-exists-when-dependent-exists` | **E3** | CLIF counterpart is `iyu-1`; unmatched only because the wording differs. |
| `participation-of-specific-dependent-continuant` (×2) | E5 (background) | Wording variant |
| `definition-of-temporal-part-spatiotemporal-regions`, `spatial-region-part-of-another-forever`, `occupies-spatial-region-exact`, `processes-occupy-spatiotemporal-regions`, `occupies-temporal-region-exact`, `occupies-spatiotemporal-region-exact`, `last-instant-for-temporal-regions-…`, `first-instant-for-temporal-regions-…`, `entity-predicate` | none | Spatial/temporal region theory |

**What the OWL identifier does and does not tag.**
- The `[nnn-BFO]` annotation tags a term's own definition or elucidation text.
- It does not tag structural OWL axioms: disjointness, domain/range, subclass.
- **Those structural axioms are nonetheless present in `bfo-core.owl`.**

Table 0.4 separates the two questions ("has an OWL identifier?" vs. "is the logical content in `bfo-core.owl`?").

### Table 0.4 — Axioms cited by the codebook

**In OWL?** column:
- **Yes** — the logical content is an OWL axiom in `bfo-core.owl`.
- **Partial** — OWL captures only part (e.g. domain/range, not the full biconditional).
- **Text** — OWL carries only the natural-language definition as an annotation.
- **No** — first-order only.

| Code(s) | Content | OWL identifier | In OWL? | CLIF | Prover9 label |
|---|---|---|---|---|---|
| E1 | continuant ⊥ occurrent | — | Yes | `wrf-2` | `continuant+occurrent-are-mutually-disjoint` |
| E1, E8 | SDC ⊥ IC ⊥ GDC | — | Yes | `cig-1` | `specifically-dependent-continuant+independent-continuant+generically-dependent-continuant-are-mutually-disjoint` |
| E1 | process ⊥ spatiotemporal region ⊥ process boundary ⊥ temporal region | — | Yes | `mem-1` | `process+spatiotemporal-region+process-boundary+temporal-region-are-mutually-disjoint` |
| E1 | site ⊥ spatial region ⊥ continuant fiat boundary | — | Yes | `twc-1` | `site+spatial-region+continuant-fiat-boundary-are-mutually-disjoint` |
| E1 | 0-/1-/2-/3-D spatial regions mutually disjoint | — | Yes | `luc-1` | `zero-dimensional-spatial-region+one-dimensional-spatial-region+two-dimensional-spatial-region+three-dimensional-spatial-region-are-mutually-disjoint` |
| E1 | fiat surface ⊥ fiat line ⊥ fiat point | — | Yes | `sjf-1` | `fiat-surface+fiat-line+fiat-point-are-mutually-disjoint` |
| E1, E6 | quality ⊥ realizable entity | — | Yes | `ksk-2` | `quality+realizable-entity-are-mutually-disjoint` |
| E1, E6 | disposition ⊥ role | — | Yes | `bwk-2` | `disposition+role-are-mutually-disjoint` |
| E1, E8 | material entity ⊥ immaterial entity | — | Yes | `sij-2` | `material-entity+immaterial-entity-are-mutually-disjoint` |
| E1 | 1-D ⊥ 0-D temporal region | — | Yes | `zkj-2` | `one-dimensional-temporal-region+zero-dimensional-temporal-region-are-mutually-disjoint` |
| E2 | No role changes type during its existence | — | No | `bks-2` | `all-role-types-are-rigid` |
| E2 | Role rigidity | — | No | `hxo-1` | `role-is-rigid` |
| E3 | Definition of SDC | `050-BFO` | Text | `akq-1` | `definition-of-specifically-dependent-continuant` |
| E3 | Definition of inheres in | `051-BFO` | Partial (domain/range) | `tht-1` | `inheres-in-definition` |
| E3 | s-depends ⟹ bearer exists whenever dependent exists | — | No | `iyu-1` | `s-depends-means-bearer-exists-when-dependent-exists` |
| E3, E5 | specifically depends on: domain/range | — | Yes | `kkl-1` | `specifically-depends-on-domain-range` |
| E4 | GDC participation ⟹ concretization/bearer-participation disjunction | — | No | `fmm-1` | `participation-of-generically-dependent-continuant` |
| E4, E8 | A GDC is always concretized by something | — | No | `ibk-1` | `g-depends-concretized-at-least-once` |
| E4, E5 | concretizes: domain/range | — | Yes | `rog-1` | `concretizes-domain-range` |
| E4 | Occurrent types are rigid | — | No | `ayr-2` | `all-occurrent-types-are-rigid` |
| E4, E8 | SDC concretizing a GDC ⟹ GDC generically depends on the SDC's bearer | — | No | `cik-1` | `sdc-concretizes-means-bearer-generically-depends` |
| E4, E8 | Definition of generically depends on | `252-BFO` | Partial (domain/range) | `otx-1` | `g-depends-on-means-theres-a-sdc-that-concretizes-it` |
| E5 | continuant part of: domain/range | — | Yes | `bdd-1` | `continuant-part-of-domain-range` |
| E5 | occurrent part of: domain/range | — | Yes | `zmr-1` | `occurrent-part-of-domain-range` |
| E5 | participates in: domain/range | — | Yes | `ild-2` | `participates-in-domain-range` |
| E5, E8 | generically depends on: domain/range | — | Yes | `ekp-1` | `generically-depends-on-domain-range` |
| E5 | occurs in: domain/range | — | Yes | `tfw-1` | `occurs-in-domain-range` |
| E5, E8 | located in: domain/range | — | Yes | `bge-1` | `located-in-domain-range` |
| E5 | occupies temporal region: domain/range | — | Yes | `lyx-2` | `occupies-temporal-region-domain-range` |
| E5, E6 | has material basis: domain/range | — | Yes | `cfs-1` | `has-material-basis-domain-range` |
| E5, E6 | realizes: domain/range | — | Yes | `oot-1` | `realizes-domain-range` |
| E6 | function ⊑ disposition | — | Yes | `lnj-1` | `function-isa-disposition` |
| E7 | Universals are not particulars | — | No | `qkp-1` | `universals-particulars-disjoint` |
| E7 | instance-of: relata are particular, universal, time | — | No | `lqn-1` | `instance-of-domain-range` |
| E8 | Definition of independent continuant | `017-BFO` | Text | **none found** | `definition-of-independent-continuant` |
| E8 | GDC rigidity | — | No | `iup-1` | `generically-dependent-continuant-is-rigid` |
| E9 | BFO universals pairwise distinct | — | No | `xtf-1` | `universals-all-different` |

**Reading the table.**
- The structural axioms E1 and E5 depend on are all present in OWL. This is why those two codes can be Tier A.
- The first-order-only content is concentrated in rigidity, concretization and participation-of-GDCs, and universal/particular. These are exactly the commitments behind the Tier C and realist-practice codes.
- **Only the "No" rows** support the claim that a commitment is axiomatized but not expressible in `bfo-core.owl`.

---

## 0.4 — Test-theory package (ARCHIVED, v12)

*Superseded: this package existed to supply faithfulness evidence for Tier C codes, all of which are archived. Retained for provenance and for any later paper that revives them.*

This was unchanged in intent: per-code Prover9 positives (expect `$F`) and Mace4 near-miss negatives (expect a model). They use only the modules each code needs, after a baseline check against the shipped consistency model.

Two v7 additions:
1. **Build from the Prover9 files, not CLIF,** since the two diverge (§0.3).
2. **Test only commitments tagged "No" or "Partial" in Table 0.4.** "Yes" rows are already covered by OWL reasoning in the detectors, so first-order tests add nothing there.

---

## 0.5 — IOF Core (B2), release 202603

`core/Core.rdf`, versionIRI `https://spec.industrialontologies.org/ontology/202603/core/Core/`. All claims in this section were verified by parsing the file.

**BFO import.** IOF imports classic `bfo.owl`, not `bfo-core.owl`. Its term set is identical to `bfo-core.owl`'s 36 classes, plus the 24 relations in Table 0.2b.

**BFO-namespace additions.**
- IOF declares one BFO-namespace class absent from BFO 2020: `obo:BFO_0000144` *process profile*, sourced by IOF from BFO 2.0 (`iof-av:directSource`).
- It is also the **only** BFO IRI on which IOF asserts logical axioms: `rdfs:subClassOf`, `owl:disjointWith` (with history [182]) and `owl:equivalentClass`.

**Construct namespace.** 90 classes and 81 object properties. Of the classes, **41 are defined** (`owl:equivalentClass`), including role-based types such as *buyer*, *customer* and *consumable*. **None has two or more asserted named superclasses.**

**Information content entities (verified OWL structure).**

```
InformationContentEntity ⊑ GDC [031]
├── DirectiveInformationContentEntity ≡ ICE ⊓ ∃prescribes.entity[001]
├── DescriptiveInformationContentEntity   (defined)
├── DesignativeInformationContentEntity   (defined)
├── MeasurementInformationContentEntity
├── ActionSpecification
├── ObjectiveSpecification
├── PlanSpecification ⊑ ICE ⊓ ∃BFO_0000110.ActionSpecification ⊓ ∃BFO_0000110.ObjectiveSpecification
└── RequirementSpecification ⊑ ICE ⊓ ∃isAbout.ObjectiveSpecification
PlannedProcess ≡ process[015] ⊓ ∃prescribedBy.PlanSpecification
```

**Correction to v4–v6.** `PlanSpecification` carries IOF synonyms *work instruction*, *process specification* and *process design*, and is marked `iof-av:isPrimitive true`.
- Its link to `prescribes` exists only in an `iof-av:firstOrderLogicAxiom` annotation, which OWL reasoners ignore.
- A reasoner therefore **never** infers `PlanSpecification ⊑ DirectiveInformationContentEntity`.
- Any E4 detection aid keyed on `DirectiveInformationContentEntity` alone misses IOF's own work-instruction class.

`prescribes`: domain ICE, range entity; a subproperty of `isAbout`.

**IOF places `ProcessCharacteristic` directly under `continuant` [002].** This is relevant only if §4.6.2's "lowest suitable level" requirement is ever operationalised (§3, item 14).

---

## 1. Summary

### 1.1 Outcomes

Columns added in v12: **Now** (current number, or ARCHIVED), **Loop** (whether the code's detector output is inside the iteration feedback payload), **Sub-ont.** (whether the eligibility predicate is closed within a single D1 sub-ontology, and so whether the code can be read for integration loss).

| Code | Name | V1 tier | Family | Commitment type | Now | Loop | Sub-ont. |
|---|---|---|---|---|---|---|---|
| E1 | Disjoint-category co-subsumption | **A** | BFO commitment | OWL axiom | **E1** | **Coupled** | Closed |
| E2 | Role-bearing type asserted as primitive material subtype | **C** | Realist practice | Principle (§3.5 supporting evidence only; ISO grading rejected as circular, v8) | ARCHIVED | — | — |
| E3 | Specifically dependent continuant without bearer | **B** | BFO commitment | Axiom (underspecification relative to it) | **E2** | Held out | **Not closed** — bearer may sit in another sub-ontology |
| E4 | Directive content / process conflation (focal) | **C** | BFO commitment | OWL disjointness + first-order concretization/rigidity; heuristic detection | ARCHIVED | — | — |
| E5 | Core relation signature violation | **A** | BFO commitment | OWL axiom | **E3** | **Coupled** | Partially — cross-genre signature clashes appear only post-merge |
| E6 | Quality / realizable misassignment | **C** | BFO commitment | Elucidation (single misplacement); restriction forms go to E5 | ARCHIVED | — | — |
| E7 | Universal–particular conflation | **B** | Realist practice | Principle informed by `qkp-1`; not an entailed violation | **E4** | Held out | Closed |
| E8 | Information content / material carrier conflation | **C** | BFO commitment | OWL disjointness + first-order dependence; heuristic detection | ARCHIVED | — | — |
| E9 | Upper-level tampering and vocabulary fabrication | **B** | ISO conformance | Conformance (§4.6; §4.8.2.5 by analogy) | **E5** | Held out | Closed |
| E10 | Nominal grounding | **C** | Realist practice | Principle | ARCHIVED | — | — |
| E11 | Multiple asserted parents without defined-class status | **B** | ISO conformance | Conformance (§4.6.2) | **E6** | Held out | Closed |

**Tiers:** A = 2 (E1, E5); B = 4 (E3, E7, E9, E11); C = 5 (E2, E4, E6, E8, E10) — the Tier C set is archived, leaving the two Tier A and four Tier B codes live.
**Families:** BFO commitment = 6 (E1, E3, E4, E5, E6, E8); realist practice = 3 (E2, E7, E10); ISO conformance = 2 (E9, E11). Each code sits in exactly one family. Sub-pattern grounding differences are stated inside the code entries rather than by splitting codes across families.

### 1.2 Counting and validity rules (apply to all codes)

**R1 — Condition-invariant eligibility.** A code's eligibility predicate must be evaluable identically on B1 and B2 artefacts, using only the artefact's own terms and BFO-level typing.
- IOF-derived signals (subsumption under IOF classes) may be used by *detectors*, never by *eligibility predicates*.
- Every code using an IOF detection aid reports B2 detection rates both with and without the aid, as a pre-registered sensitivity analysis.
- *Rationale:* uniform misclassification attenuates a condition comparison, but condition-linked differential error can reverse it. Eligibility that differs by condition is differential by construction.

**R2 — Root counting for unsatisfiability.** For Tier A codes, count only root unsatisfiable classes: a class is a root if it is unsatisfiable and none of its asserted superclasses is. Subclasses of an unsatisfiable class inherit its unsatisfiability and are not counted again.

**R3 — E1/E5 attribution.**
- A domain or range axiom never causes unsatisfiability by itself; it types, and the clash comes from disjointness. Every E5 justification therefore also contains a Table 0.1 axiom.
- **Rule:** a root unsatisfiable class is attributed to **E5** if *any* of its minimal justifications contains a domain, range or universal-restriction axiom from Tables 0.2/0.2b. Otherwise it is attributed to **E1**.
- Each root is attributed to exactly one of the two.

**R4 — Lexicon/injection separation and stratification (Tier C; revised v8). ARCHIVED, v12: applies only to archived codes.**
- Each Tier C code has a frozen *detector lexicon* and a separately frozen *injection sampling frame*.
- Each code's mutants are stratified **50/50**: half target classes whose labels match the detector lexicon; half target classes whose labels do not, including opaque or code-like names. With 200 mutants per code, that is 100 per stratum.
- **Per-stratum sensitivity** is the primary V2 report (worst-case 95% CI ≈ ±10 points).
- **Pooled sensitivity** is a weighted average of the strata. The weights are the proportions of lexical-match and non-lexical-match class names observed among eligible sites in the generated B1 and B2 artefacts, pooled across conditions.
  - This weighting rule is pre-registered; the proportion is measured once artefacts exist.
  - If the proportion differs between B1 and B2 by more than 10 points, condition-specific pooled sensitivities are also reported.

**R5 — Discrimination check.** Before any condition comparison uses a code, report its positive rate per condition.
- A code whose positive rate exceeds 95% or falls below 5% of eligible sites in **every** condition is reported descriptively but excluded from inferential comparisons.
- E3 is the code most at risk.

**R7 — Denominators (new, v12).** Every code is reported as a detection *rate* over the eligible-site denominator stated in its §2 entry, never as a bare count. Artefact size varies systematically with grounding level, so a count comparison is partly a size comparison. Count models in the overview's statistical plan carry a matching `log(denominator)` offset. R5's positive-rate thresholds are evaluated on these same denominators.

**R8 — Loop status (new, v12).** The iteration feedback payload includes the reasoner report, so the detector output for current E1 and E3 reaches the generator. Those two are confirmatory at R0 and reported as process evidence for R1–R9. The held-out codes carry the round-related inference. §1.1 records the status per code.

**R9 — Sub-ontology closure (new, v12).** Where the battery is run over D1's persisting sub-ontologies to compute integration loss, only codes whose eligibility is closed within a sub-ontology are interpretable. §1.1 records this per code; current E2 is not closed and its pre-merge rate is reported as descriptive only.

**R6 — Asserted vs. inferred.** Each code states which graph it reads:
- E1, E5: classified merge.
- E3: asserted + inferred union.
- E4, E6, E8: inferred BFO-level typing, asserted labels.
- E2, E7, E9, E10, E11: asserted graph.

### 1.3 Findings that change the overview

1. **E4 is Tier C** and carries V2, V3 and V5 in the main results.
2. **Tier distribution is 2 / 4 / 5**, against v4's expectation of three to five Tier A codes.
3. **V2 budget (restored):** five Tier C codes × 50 mutants × 2 styles × 2 seeds = 1,000 mutants + 1,000 clean runs, against v4's worked 800 + 800. R4 splits each code's 200 mutants into 100 lexical and 100 non-lexical, without changing the total. *(ARCHIVED, v12: no Tier C codes remain.)*
4. **E1 is the category-violation probe;** merge with v4 §4.5.
5. **Three families,** reported separately; only the BFO-commitment family should be described as measuring BFO modelling error.
6. **Cut subfamily:** function vs. disposition (`lnj-1`).
7. **B2 baselines are mandatory** for E5 (Table 0.2b scope), E9 (BFO_0000144 term *and* axioms) and E11 (asserted hierarchy). Without them, IOF's own content produces systematic false positives before any generator acts.
8. **Condition-invariant eligibility (R1)** replaces the v4–v6 approach, which built IOF signals into E4 and E8 eligibility.
9. **E11** captures §4.6.2's single-inheritance requirement, which no other code reaches when the parents are not disjoint.
10. **Paper 1 §4.8.6** can cite two concrete instances of why release checking matters: `BFO_0000144`, and the `PlanSpecification`/`prescribes` gap.

### 1.4 Overlaps (codes are not mutually exclusive)

Each code is scored over its own eligibility predicate. No aggregate hygiene score is computed; if one is ever reported, it counts flagged sites, not code hits.

| Pair | When both fire | Handling |
|---|---|---|
| E1 & E4 | Directive class asserted under both GDC and process | Both recorded; E4 rate includes it |
| E5 & E4 | Directive class under GDC with `has occurrent part` / `has temporal part` / `occupies temporal region` | Both recorded (R3 assigns the root to E5) |
| E1 & E8 | Information class asserted under both GDC and material entity | Both recorded |
| E5 & E8 | Information class under GDC with `located in` / `occupies spatial region` / `continuant part of` a material entity | Both recorded |
| E1 & E6 | Class asserted under both quality and realizable entity, or disposition and role | Both recorded |
| **E5 & E6** | `has realization` restriction on a quality class; `has material basis` on a role class | Both recorded (**new, v7**) |
| **E1 & E9** | Added axiom on a BFO term makes it unsatisfiable (e.g. `role ⊑ quality`) | Both recorded (**new, v7**) |
| E1 & E11 | Two asserted parents that are disjoint | Both recorded; E11's distinct contribution is the non-disjoint case |
| E2 & E10 | Role term subsumed under a material type by string match | Both recorded; E10 requires the lexical criterion |
| E4 & E8 | Never at the same site | Partition: E4 = occurrent branch, E8 = independent-continuant branch |

### 1.5 Descriptive indicators (reported per condition; not used in inferential comparisons)

| ID | Indicator | Source | Why it is reported |
|---|---|---|---|
| I1 | E11-eligible classes defined only by a bare Boolean conjunction (`C ≡ A ⊓ B`, no relational restriction) | E11 script | Shows whether E11's permissive defined-class reading masks multiple inheritance differently by condition |
| I2 | Protected IRIs whose `rdfs:label` differs from the pinned release | E9 diff | Relabelling is formally conformant but may affect label-reading extraction in Paper 2; candidate covariate |
| I3 | Domain classes with an asserted `rdfs:subClassOf obo:BFO_0000001` (directly under *entity*) | Asserted-graph query | Exact operationalisation of §4.6.2's "in any case at a level below 'entity'" |
| I4 | IOF-only unsatisfiable classes (no justification contains a Table 0.1/0.2/0.2b axiom) | E1/E5 pipeline | Keeps B2 unsatisfiability caused by IOF axioms out of E1 and E5 |
| I5 | Use of B2-only upper-level terms (Table 0.2b relations, `BFO_0000144`) | E9 diff | Keeps E5/E9 B1-vs-B2 comparisons on a common inventory (R1) |

If a descriptive indicator reaches a prevalence that would plausibly affect a code's interpretation, the report says so in prose. None is promoted to a code post hoc.

---

## 2. The codes

Each entry has:
- a definition, positive examples, near-miss negatives and the downstream consequence;
- (1) commitment, (2) primary source, (3) formal expression and eligibility, (4) V1 tier, (5) detector, (6) limitations.

---

### E1 — Disjoint-category co-subsumption

**Current number: E1.** Retained. Tier A. Loop-coupled (R8). Sub-ontology closed (R9).

**Definition.** A domain class is inferred to be subsumed by two BFO classes asserted disjoint in Table 0.1.

**Positives.**
- `ReflowSolderingStep ⊑ process ⊓ material entity` (pair 1).
- `ReflowPeakBoundary ⊑ process ⊓ process boundary` (pair 16).

**Near-miss negative.** `ReflowOven ⊑ object ⊓ ∃ participates in . ReflowSoldering`.

**Downstream consequence.** The class is unsatisfiable; any Paper 2 instance typed with it makes the KG inconsistent.

1. **Commitment.** For each Table 0.1 pair (X, Y): `X ⊓ Y ⊑ ⊥`.
2. **Primary source.**
   - `bfo-core.owl` disjointness axioms (Table 0.1).
   - CL counterparts (maintained axiomatization): `wrf-2`, `cig-1`, `mem-1`, `twc-1`, `luc-1`, `sjf-1`, `ksk-2`, `bwk-2`, `sij-2`, `zkj-2`.
   - ISO/IEC 21838-2:2021 §4.3 (OWL formalization); §4.6.2(a) (the merge must be consistent).
   - Arp et al., Continuants (pp. 85–120) and Occurrents (pp. 121–150) *(prov.)*.
3. **Formal expression.**
   - Merge the artefact with the pinned BFO file (`bfo-core.owl` for B1; classic `bfo.owl` + IOF Core for B2) and classify.
   - Positive: a **root** unsatisfiable domain class (R2) attributed to E1 under R3.
   - Eligibility: all named domain classes.
   - Detection rate: E1 roots / domain classes.
   - The instrument also reports, per root, the disjoint pair(s) in its justification. That breakdown is the v4 §4.5 probe output.
4. **V1 tier: A.** The reasoner is detector and oracle. Report reasoner, version, versionIRIs and timeout.
5. **Detector.** OWL 2 DL classification (HermiT or equivalent) with justification extraction. Parameters: timeout; justification cap.
6. **Limitations.**
   - Misses pairs not asserted disjoint, and all single misplacements (E4, E6, E8).
   - A timeout is a missing value, not a negative.
   - In B2 a class can be unsatisfiable through IOF axioms alone. If no justification contains a Table 0.1 or 0.2/0.2b axiom, record the class as "IOF-only unsatisfiable" (descriptive indicator I4), outside E1 and E5.

---

### E2 — Role-bearing type asserted as primitive material subtype

**ARCHIVED (v12).** Tier C; heuristic detection required the removed V2 apparatus. Entry retained for provenance.

**Definition.** A class denoting an entity in virtue of a role it bears is asserted as a primitive subclass of a material-entity class, with no role anchoring it.

**Positive.** `Operator ⊑ object`, with no restriction through `bearer of` to a role.

**Near-miss negatives.**
- `Operator ≡ Person ⊓ ∃ bearer of . OperatorRole`, with `OperatorRole ⊑ role`.
- In B2, IOF's own defined role-based types (*buyer*, *customer*), which are declared by `owl:equivalentClass`.

**Downstream consequence.** A role change forces retyping of the individual. This breaks temporal provenance in Paper 2 and personnel-linked RCA paths in Paper 3.

1. **Commitment.** A role exists because its bearer is in circumstances it need not be in, and losing it does not physically change the bearer (`[061-BFO]`). A type whose instances qualify only by bearing a role is non-rigid; asserted primitive subsumption under a material kind treats it as rigid.
2. **Primary source.**
   - BFO 2020 `[061-BFO]`.
   - No OWL, CLIF or Prover9 axiom reaches the rigidity of domain types: `bks-2` and `hxo-1` constrain role instances only.
   - ISO/IEC 21838-2:2021 §3.5 (defined class), whose *lathe operator* example is this code's near-miss pattern.
   - Arp et al., Terms, Definitions and Classification (pp. 59–84) and Continuants (pp. 85–120) *(prov.)*.
   - Benson et al. (2025), the *Student* misclassification (GPT-4 placed Student under material entity).
   - *Grading decision (v8):* §3.5 lists role-based terms (*lathe operator*, *mortgagee*) among its examples of defined classes, which supports E2's commitment. It does not make E2 an ISO-conformance code:
     - `Operator ⊑ object` satisfies §4.6.2(b1), a unique is_a chain;
     - no clause states that primitive assertion of such a term is non-conformant;
     - treating it as non-conformant presupposes that *Operator* is not a universal, which is the realist principle this code encodes.
3. **Formal expression.**
   - Eligibility: named class `C` with `C ⊑ BFO_0000040` in the inferred closure, and no `owl:equivalentClass`.
   - Positive: (a) the label or definition matches the role lexicon, **and** (b) there is no restriction `∃ BFO_0000196 . R` with `R ⊑ BFO_0000023` on `C` or any asserted superclass.
   ```sparql
   ASK { ?C rdfs:subClassOf+ obo:BFO_0000040 .
         FILTER NOT EXISTS { ?C owl:equivalentClass ?e }
         FILTER NOT EXISTS { ?C rdfs:subClassOf* ?S . ?S rdfs:subClassOf ?r .
                             ?r owl:onProperty obo:BFO_0000196 ;
                                owl:someValuesFrom/rdfs:subClassOf* obo:BFO_0000023 }
         ?C rdfs:label ?l . FILTER(regex(?l, $ROLE_LEXICON, "i")) }
   ```
4. **V1 tier: C.** Primitive subsumption is consistent, and detection depends on the lexicon. R4 applies. Injection operator: replace a role-anchored definition with a primitive material subsumption.
5. **Detector.** Structural SPARQL plus a versioned role lexicon; a judge from a model family distinct from the generator. Parameters: lexicon version; judge threshold.
6. **Limitations.**
   - Principle, not axiom, and not ISO conformance. Grounding E2 in §3.5 + §4.6.2 would be circular, because classifying *Operator* as a defined class rather than a universal is itself the realist judgement E2 applies. State this in Paper 1.
   - Misses: role terms outside the lexicon; status terms (`ReworkedBoard`); role anchoring expressed inside an equivalence rather than a subclass restriction (which is excluded by eligibility anyway).
   - Over-flags: role-like labels for rigid kinds (`Controller` meaning a device).

---

### E3 — Specifically dependent continuant without bearer

**Current number: E2.** Retained. Tier B. Held out of the feedback loop (R8). **Not sub-ontology closed** (R9): a bearer may sit in another genre's sub-ontology, so pre-merge rates are descriptive only.

**Definition.** A domain class under SDC has no asserted or inherited restriction identifying the category of its bearer.

**Positive.** `SolderJointVoidRatio ⊑ quality`, with no `∃ inheres in . X` on it or any non-BFO superclass.

**Near-miss negative.** `SolderJointVoidRatio ⊑ quality ⊓ ∃ inheres in . SolderJoint`.

**Downstream consequence.** Paper 2 extraction cannot determine what a measured value is a property of.

1. **Commitment.** Every SDC specifically depends on some independent continuant that is not a spatial region (`[050-BFO]`). Inherence is that dependence on a bearer (`[051-BFO]`). The bearer exists whenever the dependent does (`iyu-1`).
2. **Primary source.**
   - `[050-BFO]` / `akq-1`; `[051-BFO]` / `tht-1`; `iyu-1`; `kkl-1`.
   - ISO/IEC 21838-2:2021 §4.3 for the OWL domain/range of `inheres in`; §4.4 for the requirement of a CL layer.
   - Arp et al., Continuants (pp. 85–120) *(prov.)*.
3. **Formal expression.**
   - Eligibility: named domain class `C` with `C ⊑ BFO_0000020` in the inferred closure.
   - Positive: no axiom on `C` or any non-BFO superclass of the form `⊑ ∃ BFO_0000197 . X`, or `⊑ ∃ BFO_0000195 . X` with `X ⊑ IC`, and no equivalence entailing one.
   - Implemented as a SHACL node shape over the asserted + inferred union.
4. **V1 tier: B.** Under OWL's open-world semantics, a missing restriction is not an inconsistency, so the shape defines the code.
5. **Detector.** `E3-sdc-bearer.ttl`. No parameters.
6. **Limitations.**
   - Underspecification, not contradiction: BFO requires a bearer to exist, not that the ontology state its category.
   - **R5 applies with particular force.** LLM ontologies may omit bearer restrictions almost universally, which would make E3 non-discriminating.
   - Over-flags deliberately general SDC classes. Misses wrong-category bearers (E5).
   - `has material basis` relates a disposition to part of its bearer, and does not satisfy the shape.

---

### E4 — Directive content / process conflation (focal)

**ARCHIVED (v12).** Tier C; was the focal code under the v4–v6 design. Entry retained for provenance.

**Definition.**
- **E4a.** A class denoting directive content (work instruction, procedure, process specification, routing, recipe, programme, control plan) is placed in the occurrent branch or given occurrent-only relations.
- **E4b.** A process class is placed under GDC because it shares a name with the directive that prescribes it.

**Positives.**
- E4a: `ReflowProfileSpecification ⊑ process`.
- E4a: `WorkInstruction_WI-204 ⊑ ∃ has occurrent part . PlacementStep` (also E5).
- E4b: `StencilPrinting ⊑ iof:PlanSpecification`, used as the type of logged print events.

**Near-miss negatives.**
- `ReflowProfileSpecification ⊑ GDC`, concretized by an SDC realized in `ReflowSoldering ⊑ process`.
- `WorkInstruction ⊑ ∃ participates in . Assembly` — permitted, since GDC is in the domain of `participates in`.
- `WorkInstruction ⊑ ∃ is concretized by . InstructionPerformance` — permitted, since the range of `is concretized by` includes process.
- *B2:* `SolderProfilePlan ⊑ iof:PlanSpecification ⊓ ∃ BFO_0000110 . ReflowActionSpecification`.
- *B2:* `ReflowSoldering ⊑ iof:PlannedProcess` — a process correctly linked to a plan specification via `prescribedBy`.

**Downstream consequence.** Paper 2 cannot separate as-planned from as-executed structure. Paper 3 RCA retrieves prescribed steps as if they had occurred. The pure form is invisible to reasoners.

1. **Commitment.**
   - Continuant ⊥ occurrent (pair 1).
   - Directive content is generically dependent (`[074-BFO]`).
   - A process is an occurrent with temporal parts and a material participant (`[083-BFO]`).
   - Occurrent types are rigid (`ayr-2`).
   - A GDC participating in a process does so via concretization or its bearer (`fmm-1`), and is always concretized (`ibk-1`).
   - Directive and process are linked by concretization and realization, not identity.
2. **Primary source.**
   - BFO 2020: pair 1; `[074-BFO]`; `[083-BFO]`; domains of BFO_0000117/121/199; `rog-1`.
   - Maintained CL axiomatization: `fmm-1`, `ibk-1`, `ayr-2`, `cik-1`, `otx-1` (Table 0.4: `rog-1` Yes, `otx-1` Partial, the rest No).
   - IOF Core 202603: `InformationContentEntity`, `DirectiveInformationContentEntity`, `PlanSpecification`, `ActionSpecification`, `PlannedProcess`, `prescribes` (§0.5).
   - ISO/IEC 21838-2:2021 §4.3; §4.4 for the CL-layer requirement.
   - Arp et al., Continuants (pp. 85–120) and Occurrents (pp. 121–150) *(prov.)*.
3. **Formal expression.**
   - **Eligibility (condition-invariant, R1):** named domain class `C` whose label or definition matches the directive lexicon, **or** that is inferred under `BFO_0000031` with a directive-lexicon match on any asserted superclass label. No IOF term appears in eligibility.
   - **E4a positive:** eligible, and (i) `C ⊑ BFO_0000003` in the inferred closure, or (ii) `C ⊑ ∃ BFO_0000117/121/199 . ⊤`.
   - **E4b positive:** `C ⊑ BFO_0000031` inferred; process signal (event lexicon, or `has participant` / `occurs in` restrictions); and no distinct process class linked to `C` by concretization or realization.
   - **Detection aid (B2 only, sensitivity analysis per R1):** subsumption under `iof:DirectiveInformationContentEntity ⊔ iof:PlanSpecification ⊔ iof:ActionSpecification` counts as directive signal for *detection*. A class linked by `iof:prescribedBy` to a plan specification counts as a distinct process class for the E4b exclusion.
   - **Excluded from positives:** GDC `participates in` process; GDC `is concretized by` process; correct IOF plan-specification and planned-process patterns.
   - Detection rate: (E4a + E4b positives) / eligible classes, reported with and without the B2 detection aid.
4. **V1 tier: C.** The pure misplacement is consistent, and detection relies on lexical and structural signal. Inconsistent forms are also independently caught by E1 and E5. R4 applies. Carries V2, V3 and V5 in the main results.
   - Injection operators: E4a moves a directive class from GDC to process and rewires its concretization edge; E4b moves a process class under GDC.
5. **Detector (V3 pair).**
   - **S**, structural: asserted graph, lexicon, hierarchy position, property slots, plus the B2 detection aid.
   - **I**, inferential: inferred closure only.
   - Pre-registered primary: S.
   - Parameters: lexicon version; judge threshold if used.
6. **Limitations.**
   - B2 over-flag risk: `RequirementSpecification` uses `isAbout`, not `prescribes`, and is non-directive despite a directive-sounding label. Pre-register it as an exception.
   - IOF's own `prescribes` link for plan specifications lives in a first-order annotation, not in OWL. Neither the detector nor the reasoner sees it, which is why the aid names `PlanSpecification` explicitly.
   - Misses non-lexical names (`WI-204`) unless R4's non-lexical stratum reveals otherwise; misses conflation expressed only in individuals.
   - Over-flags process classes named after a standard (`IPC-A-610Inspection`).

---

### E5 — Core relation signature violation

**Current number: E3.** Retained. Tier A. Loop-coupled (R8). Partially sub-ontology closed (R9): cross-genre signature clashes surface only post-merge.

**Definition.** A BFO relation is used between categories outside its domain, range or universal class restriction, so that classification makes a domain class unsatisfiable.

**Positives.**
- `SolderPaste ⊑ ∃ realizes . PrintingCapability` (domain of realizes = process; material entity ⊥ process via pair 1).
- `PlacementAccuracy ⊑ quality ⊓ ∃ inheres in . PlacementProcess`.
- `PCB ⊑ ∃ continuant part of . SMTLineRun`, with `SMTLineRun ⊑ process`.
- `ReflowProfileSpecification ⊑ GDC ⊓ ∃ located in . Oven`.

**Near-miss negatives.**
- `Stencil ⊑ ∃ participates in . StencilPrinting`.
- `ProcessSpecification ⊑ GDC ⊓ ∃ participates in . Audit`.
- `ReflowSoldering ⊑ ∃ occurs in . ReflowOven`.
- *B2:* `SolderProfilePlan ⊑ iof:PlanSpecification ⊓ ∃ BFO_0000110 . ReflowActionSpecification` (a Table 0.2b relation, legitimately in scope).

**Downstream consequence.** Paper 2 schema-constrained extraction rejects or mistypes triples; parthood errors corrupt part–assembly traversal.

1. **Commitment.** The domain/range axioms of Tables 0.2 and 0.2b, the universal restrictions under Table 0.2, and Table 0.1.
2. **Primary source.**
   - `bfo-core.owl` domain/range and class restrictions; classic `bfo.owl` for Table 0.2b.
   - Maintained CL counterparts: `bdd-1`, `zmr-1`, `ild-2`, `rog-1`, `ekp-1`, `tfw-1`, `bge-1`, `lyx-2`, `kkl-1`, `cfs-1`, `oot-1` (all "Yes" in Table 0.4).
   - ISO/IEC 21838-2:2021 §4.3; §4.6.2(a).
   - Arp et al., Continuants and Occurrents (pp. 85–150) *(prov.)*.
3. **Formal expression.**
   - Eligibility: every artefact axiom using a Table 0.2 relation (B1), or a Table 0.2 or 0.2b relation (B2).
   - Positive: the axiom's subject class is a **root** unsatisfiable class (R2) attributed to E5 under R3, where at least one minimal justification contains that axiom.
   - Detection rate: positive relation axioms / eligible relation axioms.
4. **V1 tier: A.** Domain/range axioms exist on every relation in scope, and mismatches collide with Table 0.1.
5. **Detector.** Shared classification pipeline with E1; attribution under R3. Parameters: timeout; justification cap.
6. **Limitations.**
   - A mismatch between categories BFO does not declare disjoint is not a violation.
   - Misses non-BFO relations (RO `part of` BFO_0000050, local properties): E9 if the IRI is in the BFO namespace, otherwise out of scope.
   - The B1 and B2 relation scopes differ, which affects the *denominator's composition*, not eligibility logic. Report B1-vs-B2 comparisons on Table 0.2 relations only, with Table 0.2b usage as a B2-only descriptive figure.

---

### E6 — Quality / realizable misassignment

**ARCHIVED (v12).** Tier C. Entry retained for provenance.

**Definition.**
- **(a)** A disposition or function typed as a quality.
- **(b)** A quality typed as a realizable entity.
- **(c)** A role typed as a disposition or function, or the reverse.

**Positives.**
- (a) `Solderability ⊑ quality`.
- (b) `BoardThickness ⊑ disposition`.
- (c) `ESDSensitivity ⊑ role`; `CertifiedOperatorRole ⊑ function`.

**Near-miss negatives.**
- `Solderability ⊑ disposition ⊓ ∃ has material basis . SurfaceFinishLayer`.
- `PumpingCapability ⊑ disposition` rather than function — **not a violation**, since function ⊑ disposition.

**Downstream consequence.** Qualities are not realized, so failure mechanisms that manifest in processes (moisture sensitivity → popcorning in reflow) become unrepresentable for Paper 3 RCA.

1. **Commitment.**
   - A quality needs no further process to be realized (`[055-BFO]`); quality ⊥ realizable entity (pair 21).
   - A disposition's loss physically changes its bearer (`[062-BFO]`).
   - A role's loss does not (`[061-BFO]`); disposition ⊥ role (pair 4).
   - A function is a disposition whose basis came about by design or evolution (`[064-BFO]`).
2. **Primary source.**
   - `[055-BFO]`, `[058-BFO]`, `[061-BFO]`, `[062-BFO]`, `[064-BFO]`, `[242-BFO]`; `ksk-2`, `bwk-2`, `lnj-1`, `oot-1`, `cfs-1`.
   - ISO/IEC 21838-2:2021 §4.3.
   - Arp et al., Continuants (pp. 85–120) *(prov.)*.
3. **Formal expression.**
   - Eligibility: domain classes under BFO_0000019 or BFO_0000017.
   - (a) Under quality with a dispositional signal: capacity/susceptibility lexicon, or a trigger condition in the definition.
   - (b) Under realizable entity with a categorical-magnitude signal.
   - (c) Under role with a physical-make-up signal, or under disposition/function with an institutional/assignment signal.
   - **Restriction forms** (`has realization` on a quality class; `has material basis` on a role class) make the class unsatisfiable. They are scored by E5 under R3, not here.
4. **V1 tier: C.** Every sub-pattern scored here is a consistent single misplacement, distinguishable only by BFO's elucidations. None is an OWL or first-order axiom violation. R4 applies. Injection: one operator per sub-pattern.
5. **Detector.** Lexicon and definition analysis plus a judge; reported per sub-pattern and pooled. Parameters: lexicon version; judge threshold.
6. **Limitations.**
   - Elucidation-based throughout. This corrects v6, which called (a)/(b) axiom-backed.
   - Pre-register an exclusion list for disputed cases (conductivity, hardness).
   - Misses correctly branched classes with wrong bearers (E3, E5).

---

### E7 — Universal–particular conflation

**Current number: E4.** Retained. Tier B. Held out of the feedback loop (R8). Sub-ontology closed (R9). Lexical criterion for (b) still to be frozen (checklist item 18).

**Definition.** A particular is represented as a class, or a single IRI is used both as a class and as an individual.

**Positives.**
- **(a) Punning:** an IRI in the domain namespace typed both `owl:Class` and `owl:NamedIndividual`, or used in both class and individual positions.
- **(b) Particular-as-class:** a leaf class with no subclasses and no instances whose label matches a particular-identifier pattern (asset tag, serial number, line/cell number, specific lot), e.g. `SMTLine3 ⊑ ProductionLine`.

**Near-miss negatives.**
- `SMTLine3 a ProductionLine` (an individual).
- `BoardRevisionC ⊑ PrintedCircuitBoard` (a revision type with many physical instances).
- `C ⊑ ∃ locatedIn . {Line3}` or `owl:hasValue :Line3` — **legitimate use of an individual in a restriction, not a violation** (corrects v6).

**Downstream consequence.** Paper 2 population re-instantiates particulars or cannot attach instances, and Paper 3 counting queries return wrong cardinalities.

1. **Commitment.** Universals and particulars are distinct categories, and instance-of relates a particular to a universal (§3.2, §3.6). The maintained CL axiomatization states this as `qkp-1` and `lqn-1`.
   - **v7 correction:** these axioms are not violated *by entailment* when an OWL artefact puns an IRI. Under OWL 2 punning the class reading and the individual reading denote distinct entities, which would translate to distinct first-order symbols.
   - E7 therefore records a departure from the realist intent behind those axioms, not a derivable contradiction.
2. **Primary source.**
   - ISO/IEC 21838-2:2021 §3.2 (universal), §3.6 (instance).
   - `qkp-1`, `lqn-1` (Table 0.4: No).
   - `[001-BFO]`, whose examples (*Julius Caesar*, *the Second World War*) are particulars.
   - Arp et al., What Is an Ontology? (pp. 1–26) *(prov.)*.
3. **Formal expression.**
   - Eligibility: all IRIs in the domain namespace.
   - (a) SPARQL over the asserted graph for IRIs with both class and individual declarations or usage.
   - (b) Leaf class, zero asserted instances, label matching the pre-registered identifier regex.
   - `owl:hasValue` fillers and nominals in restrictions are explicitly not positives.
4. **V1 tier: B.** (a) is an exact closed constraint. (b) is a pre-registered pattern constraint; if review judges it too heuristic, drop (b) rather than re-tier the code.
5. **Detector.** `E7-punning.rq`, `E7-identifier-class.rq`. Parameter: identifier regex.
6. **Limitations.**
   - Realist practice, not an entailed axiom violation (reverses v3–v6).
   - (b) over-flags variant/revision types with identifier-like names, and misses particulars with generic names.

---

### E8 — Information content / material carrier conflation

**ARCHIVED (v12).** Tier C. Entry retained for provenance.

**Definition.**
- **(a)** A class denoting information content (drawing, BOM, Gerber data, placement programme, specification, measurement record) placed under material entity.
- **(b)** A physical carrier placed under GDC.

**Positives.**
- (a) `BillOfMaterials ⊑ object`; `GerberFile ⊑ material entity`.
- (b) `TravelerSheet ⊑ GDC`, used as the physical sheet that accompanies a panel.
- (b, also E5) `TravelerSheet ⊑ GDC ⊓ ∃ located in . Panel`.

**Near-miss negatives.**
- `BillOfMaterials ⊑ GDC ⊓ ∃ generically depends on . DataStorageDevice`.
- `PrintedTraveler ⊑ object ⊓ ∃ is carrier of . TravelerContent`.

**Downstream consequence.** Copies of one BOM become distinct BOMs, so Paper 2 revision tracking fails; physical-document provenance is lost.

1. **Commitment.**
   - A GDC is content shared by copies (`[074-BFO]`; BFO's example is *the pdf file on your laptop*).
   - An independent continuant has neither specific nor generic dependence (`[017-BFO]`); IC ⊥ GDC (pair 8).
   - Content relates to its carrier by generic dependence, grounded in a concretizing SDC (`otx-1`, `cik-1`).
   - GDC status is rigid (`iup-1`).
2. **Primary source.**
   - `[074-BFO]`, `[017-BFO]` (first-order form: Prover9 `definition-of-independent-continuant` only; no counterpart found in the same-date CLIF, §0.3), `[019-BFO]`.
   - `cig-1`, `otx-1`, `cik-1`, `ekp-1`, `iup-1`.
   - ISO/IEC 21838-2:2021 §4.3; §4.4 for the CL-layer requirement.
   - IOF Core `InformationContentEntity ⊑ GDC` (§0.5).
   - Arp et al., Continuants (pp. 85–120) *(prov.)*.
3. **Formal expression.**
   - **Eligibility (condition-invariant, R1):** named domain class whose label or definition matches the information lexicon, or with such a match on any asserted superclass label.
   - (a) Eligible, `C ⊑ BFO_0000040` inferred, and no `∃ BFO_0000101 . X`.
   - (b) `C ⊑ BFO_0000031` inferred, a physical signal (mass/dimension restriction, `located in`, `occupies spatial region`, `continuant part of` a material entity), and no `∃ BFO_0000084 . X`.
   - **Detection aid (B2 only, sensitivity analysis per R1):** subsumption under `iof:InformationContentEntity` counts as information signal for detection.
   - Detection rate: positives / eligible classes, with and without the aid.
4. **V1 tier: C.** Single misplacements are consistent. Double typing goes to E1; location/parthood forms go to E5. R4 applies. Injection operators: move a GDC information class under material entity and delete its carrier restriction, and the reverse.
5. **Detector.** Lexicon and restriction checks; a judge for ambiguous document terms. Parameters: lexicon version; judge threshold.
6. **Limitations.**
   - Over-flag risk: a legitimate document-as-physical-object reading without a carrier restriction.
   - Misses non-lexical data class names.

---

### E9 — Upper-level tampering and vocabulary fabrication

**Current number: E5.** Retained. Tier B. Held out of the feedback loop (R8). Sub-ontology closed (R9). B2 baseline-exclusion list required (checklist item 19). Note: "below *entity*" remains indicator I3 and is **not** part of this code — overview v11.3's attempt to fold it in is withdrawn in v12.

**Definition.**
- **(a)** An IRI in a protected namespace absent from the pinned term inventory.
- **(b)** A logical axiom added with a protected IRI as subject.
- **(c)** A changed definition of a protected term.

Label-only changes with the IRI preserved are not positives.

**Positives.**
- (a) `obo:BFO_0000999` used as a class; RO `obo:BFO_0000050` "part of" used as though it were a BFO 2020 relation.
- (b) `role ⊑ quality` added (also E1).
- (c) `skos:definition` of BFO_0000015 replaced with different content.

**Near-miss negatives.**
- *B1 and B2:* a domain class subclassing a BFO class; an unmodified import; a changed or added `rdfs:label` / `skos:altLabel` on a BFO term with its IRI unchanged.
- *B2:* use of `obo:BFO_0000144` and IOF's own axioms on it; use of Table 0.2b relations; use of any IOF 202603 construct term.

**Downstream consequence.** The reference axiomatization is silently altered for every other code, and cross-artefact comparability breaks.

1. **Commitment.**
   - A conformant domain ontology uses the terms of its upper ontology with their specified content, and adds no axioms that change what is derivable about them.
   - §4.6.5.1 requires that BFO remain logically interpretable within the conformant ontology; added axioms on BFO terms threaten that.
   - Relabelling is excluded by analogy to §4.8.2.5, which permits relabelling with IRIs preserved for BFO profiles. Definition changes are not relabelling and remain in scope.
2. **Primary source.**
   - ISO/IEC 21838-2:2021 §4.6 (domain-ontology conformance), §4.6.5.1 (validation), §4.8.2.5 (relabelling; *by analogy*, since §4.8.2 governs BFO profiles).
   - Term inventory — **B1:** `bfo-core.owl` (36 classes, 40 relations). **B2:** classic `bfo.owl` (36 + 64) ∪ `BFO_0000144` ∪ IOF Core 202603 (90 classes, 81 object properties).
   - Axiom baseline for (b) in B2: IOF's `rdfs:subClassOf`, `owl:disjointWith` and `owl:equivalentClass` axioms on `BFO_0000144`.
   - Arp et al., BFO at Work (pp. 151–172) and Domain Ontology Design (pp. 43–58) *(prov.)*.
   - Benson et al. (2025) on invented relations.
3. **Formal expression.**
   - Eligibility: every IRI reference in `obo:BFO_` (B1, B2) and `iof:` (B2).
   - (a) IRI not in the applicable inventory.
   - (b) Axiom with a protected IRI as subject of `rdfs:subClassOf` / `owl:equivalentClass` / `owl:disjointWith` / `rdfs:domain` / `rdfs:range` / `rdfs:subPropertyOf`, absent from the applicable baseline.
   - (c) `skos:definition` or `IAO_0000115` on a protected IRI differing from the release.
   - Label annotations are ignored.
4. **V1 tier: B.** An exact set difference against enumerable, B1/B2-specific baselines.
5. **Detector.** `E9-release-diff.py`, diffing term inventories, logical axioms and definition annotations. Parameters: SHA-256 of `bfo-core.owl`, classic `bfo.owl` and `Core.rdf`.
6. **Limitations.**
   - The §4.8.2.5 exclusion is an interpretive analogy; state it as such in Paper 1.
   - Report per namespace; compare B1 and B2 on the `obo:BFO_` namespace against a **common** inventory (the 36 classes + Table 0.2 relations), and report B2-only terms descriptively (I5). This keeps the comparison condition-invariant (R1).
   - Misses semantic misuse of valid IRIs (E1, E5).
   - 2.0-only IRIs other than `BFO_0000144` count as fabrication.
   - Relabelling is not scored. The same diff reports protected-IRI labels that differ from the release as descriptive indicator I2 (§1.5), because Paper 2's extraction prompts read labels. No disclosure check is performed: no normative disclosure requirement applies to domain ontologies (v8 decision).

---

### E10 — Nominal grounding

**ARCHIVED (v12).** Tier C. Entry retained for provenance.

**Definition.** A subsumption edge to a BFO or IOF class justified only by string overlap between labels, not by subsumption of meaning.

**Positives.**
- `ProcessWindow ⊑ process`.
- `QualityInspection ⊑ quality`.
- `FunctionalTest ⊑ function`.
- `MaterialReviewBoard ⊑ material entity`.

**Near-miss negatives.**
- `ReflowProcess ⊑ process`.
- `SurfaceRoughness ⊑ quality`.

**Downstream consequence.** Superficially aligned structure inherits the wrong category's constraints. This is the error most likely to inflate the BFO alignment rate while degrading everything downstream.

1. **Commitment.** `A ⊑ B` holds only if every instance of A is an instance of B, stated by a genus–differentia definition with B as genus. Label overlap is not evidence.
2. **Primary source.**
   - Arp et al., Terms, Definitions and Classification (pp. 59–84) *(prov.)*.
   - BFO 2020 elucidations contradicted by nominal edges: `[083-BFO]`, `[055-BFO]`, `[064-BFO]`, `[019-BFO]`.
   - ISO/IEC 21838-2:2021 §4.6.2(b1) (is_a chains to BFO).
3. **Formal expression.**
   - Eligibility: every asserted `rdfs:subClassOf` edge `C ⊑ P` where `P` is a BFO class (B1 and B2). IOF parents are reported descriptively for B2 only (R1).
   - Positive if both hold: (a) `P`'s label or head token is contained in `C`'s normalized, stemmed label; (b) a judge given `C`'s label and definition and `P`'s `skos:definition` returns *not subsumed*. (a) alone is not positive.
4. **V1 tier: C.** R4 applies: the injection frame must include token-sharing re-parentings the lexical filter would catch, **and** synonym-based re-parentings it would not. Injection operator: re-parent a class to a token-sharing BFO class of a different category.
5. **Detector.** Lexical filter plus a judge from a distinct model family. Parameters: normalization rules; judge threshold.
6. **Limitations.**
   - Principle, not axiom.
   - Paired with the BFO alignment rate as a convergent measure (v4 §4.8.8); **pre-registered direction: positive τ**.
   - Misses synonym-driven nominal edges.
   - Overlaps E1, E6 and E8 when the edge lands in a disjoint or wrong branch.

---

### E11 — Multiple asserted parents without defined-class status

**Current number: E6.** Retained. Tier B. Held out of the feedback loop (R8). Sub-ontology closed (R9). B2 baseline-exclusion list required (checklist item 19).

**Definition.** A domain class has two or more asserted named superclasses, none of which is an asserted ancestor of another, and carries no `owl:equivalentClass` axiom.

**Positives.**
- `Fixture ⊑ object` and `Fixture ⊑ fiat object part` asserted as primitive edges. The two parents are not disjoint, so the merge stays consistent and E1 does not fire.
- `SolderPasteInspection ⊑ InspectionProcess` and `SolderPasteInspection ⊑ SMTProcess`, both domain classes. Multiple inheritance at the domain level is the common LLM pattern.

**Near-miss negatives.**
- `CompositeFixture ≡ object ⊓ fiat object part` (a defined class).
- A class whose second parent appears **only by inference** (e.g. it satisfies an IOF defined class). This is not a positive, because E11 reads the asserted graph.
- `C ⊑ A` and `C ⊑ B` where `A ⊑ B` is asserted (a redundant edge, not multiple inheritance).

**Downstream consequence.** An undeclared multi-parent class is ambiguous about which parent's constraints govern it. Where the parents differ in identity or mereological criteria (object vs. fiat object part), Paper 2 cannot determine which relation signatures apply, and Paper 3's category-keyed traversal becomes unreliable for that term.

1. **Commitment.** Every domain term either (b1) connects to BFO through a unique is_a chain, or (b2) is able to be defined from terms that do. "No term in the resulting ontology shall have more than one parent" (§4.6.2).
2. **Primary source.** ISO/IEC 21838-2:2021 §4.6.2, the (a)/(b1)/(b2) conditions and the single-inheritance sentence; §3.5 (defined class).
3. **Formal expression.**
   - Eligibility: every named domain class `C` (B1 and B2; IOF construct classes excluded as baseline).
   - Let `Par(C)` be the set of named classes `D` with an asserted `C rdfs:subClassOf D`, after removing any `D` that is an asserted ancestor of another member.
   - **Positive iff `|Par(C)| ≥ 2` and `C` has no `owl:equivalentClass` axiom.**
   - Detection rate: positives / eligible classes.
   - *Operationalisation note:* §4.6.2(b2) says "able to be defined", which is modal. The detector uses the syntactic proxy "is declared with `owl:equivalentClass`". A primitive multi-parent class that *could* be rewritten as a definition is counted as a positive; state this in Paper 1.
   - *Defined-class reading (v8 decision):* **any** `owl:equivalentClass` axiom satisfies the proxy, including a bare Boolean conjunction such as `C ≡ A ⊓ B`. This follows the standard's own defined-class example (§4.8.2.4: *attribute* ≡ quality or realizable entity, a bare Boolean). Bare-conjunction definitions among E11-eligible classes are counted per condition as descriptive indicator I1.
4. **V1 tier: B.** A closed, exact query over the asserted graph. Unsatisfiable classes are still evaluated, because the asserted graph is unaffected by classification.
5. **Detector.** SPARQL/script over the asserted graph. No lexicon, no judge.
   - **B2 baseline verified:** IOF Core 202603 has zero classes with two or more asserted named parents, so IOF contributes no false positives.
6. **Limitations.**
   - Overlaps E1 when the parents are disjoint.
   - The permissive defined-class reading can be gamed: rewriting a multi-parent class as `C ≡ A ⊓ B` removes the positive. I1 makes that visible. If I1 differs sharply between conditions, interpret E11's condition difference with that in view.
   - Misses under-classification (an applicable parent omitted).
   - §4.6.2's separate level requirement is handled in two parts (v8 decision):
     - "below *entity*" is reported exactly as descriptive indicator I3;
     - "lowest suitable level" is not operationalised beyond what E6, E8 and E10 approximate, because a strict version would penalise B2 artefacts that follow IOF's own `ProcessCharacteristic ⊑ continuant` placement.

---

## 3. OOPS! pitfall-overlap mapping

Overview v12 feeds the OOPS! report back to the generator each round and holds the structural instruments out. Coupling propagates if a fed-back pitfall mechanically moves a held-out measure, so the catalogue is walked once against the six retained codes and the OntoQA metrics, and any overlapping pitfall is suppressed from the *fed-back* report while still being computed for scoring. Suppression is per pitfall, not per instrument.

**Status: open.** The audit is Part VI item 6a of the overview and must be settled before the pilot, since it changes what the generator sees. Candidates identified in advance, to be confirmed or dismissed by the audit:

| OOPS! pitfall (candidate) | Overlaps | Why |
|---|---|---|
| Missing domain or range in properties | Current E3 | Remediation adds signatures, which is what E3 scores against |
| Missing disjointness | Current E1 | Adding disjointness axioms changes which classes become unsatisfiable |
| Defining multiple domains / ranges | Current E3 | Same surface as a signature violation |
| Missing equivalent properties / classes | Current E6 | E6's defined-class exemption keys on `owl:equivalentClass` |
| Merging different concepts in the same class; unconnected ontology elements; cycles in the hierarchy | OntoQA inheritance, relationship and attribute richness; orphan rate | Remediation directly moves structural profile values |

The confirmed suppression list is recorded here, hashed, and reported in Paper 1 §7.1.

---

## 4. Outstanding checklist

| # | Item | Blocks | Status |
|---|---|---|---|
| 1 | BFO 2020 disjointness axioms | E1 | Closed |
| 2 | Relation IRIs; domain/range existence | E5 tier; E3/E4/E8 | Closed |
| 3 | GDC participation and concretization signatures | E4 negatives | Closed |
| 4 | Three-system identifier mapping | Citations | Closed (counts corrected v7) |
| 5 | IOF Core pin; ICE/plan IRIs; B2 inventories and baselines | E4/E5/E8/E9/E11 in B2 | Closed (PlanSpecification corrected v7) |
| 6 | ISO/IEC 21838 clause citations | All | Closed (scope corrected v7) |
| 7 | Build the Prover9 test-theory package | Faithfulness evidence | **Closed as overtaken (v12): Tier C archived; no heuristic code remains to calibrate** |
| 8 | Author and freeze detector lexicons **and** separate, 50/50-stratified injection sampling frames (R4) | E2, E4, E6, E7(b), E8, E10 | **Closed as overtaken (v12)**, except for current E4 (historical E7(b)), whose lexical criterion still needs freezing — carried as item 18 |
| 9 | Obtain the 2021 CLIF release if ISO-exact first-order citations are required | Citation precision | Open, optional |
| 10 | Arp et al.: verify chapter numbering against the print contents; exact in-chapter pages | Citations | Open, low priority (deferred by user) |
| 11 | §3.5: does a bare `owl:equivalentClass` conjunction count as a defined class? | E11 (b2 proxy) | **Closed (v8): yes, permissive reading; I1 safeguard** |
| 12 | Grade E2 as principle or ISO conformance (§3.5 + §4.6.2 argument) | E2 family assignment | **Closed (v8): principle; ISO grading circular** |
| 13 | Whether undisclosed relabelling warrants a separate documentation-fidelity signal | Scope | **Closed (v8): no code; I2 descriptive count** |
| 14 | Whether to operationalise §4.6.2's "lowest suitable level, below entity" requirement (IOF itself places `ProcessCharacteristic` under `continuant`) | Scope | **Closed (v8): split; "below entity" as I3, "lowest suitable level" left to E6/E8/E10** |
| 15 | Proportion of non-lexical mutants in R4 | V2 design | **Closed (v8): 50/50 stratification; prevalence-weighted pooling** |
| 16 | Release reconciliation paragraph for Paper 1 methods | Citation defensibility | Open, low effort (text drafted in §0.1) |
| 17 | Update overview v4: E1–E10 → E1–E11; merge §4.5 probes into E1; add R1–R6 and I1–I5; restate the V2 design as 50/50 strata | Overview consistency | **Closed as overtaken (v12): the design reduced to six codes rather than expanding to eleven; overview v12 now cites R1–R9 and I1–I5** |
| 18 | Freeze the lexical criterion for current E4 (historical E7(b)) | E4 detector | Open |
| 19 | Build the B2 baseline-exclusion lists for current E3 (Table 0.2b scope), E5 (`BFO_0000144` term and axioms) and E6 (asserted hierarchy) | Any B2 measurement on those codes | Open — prerequisite for the pilot's B2 arm |
| 20 | Run the OOPS! pitfall-overlap audit and freeze the suppression list (§3) | Feedback payload contents | Open — before the pilot |
| 21 | Confirm per-code denominators against R7 and record the offset variable for each | Statistical plan | Open, low effort |
