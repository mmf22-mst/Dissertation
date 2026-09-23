"""
Evaluation battery — runs all instruments on one ontology state.

Instruments:
  Coupled (fed back):
    1. Reasoner: consistency, unsatisfiable classes, OWL 2 DL profile
    2. OOPS! pitfall counts by severity
    3. OntoQA structural profile
    4. Alignment rates (BFO-only, IOF, unaligned; CCO recorded as a
       pretraining-contamination signal only — no condition receives CCO)
    5. Salient-term coverage + genre coverage balance
  Held out (never fed back):
    6. CQ answerability — reported per stratum, with the primary aggregate
       over the relational and multi-hop strata (overview v20 Part I
       §6.2(c)).  The CQ scorer matches patterns against the normalised
       scoring label (label_normalisation.py), never against raw labels.

The battery produces:
  - battery.json  (all scores, for the checkpoint)
  - feedback text (coupled items only, rendered under the pinned FEEDBACK
                   allotment by feedback_payload.py — v20)
  - defect list   (for defect routing under D1)
  - sub-ontology scores at checkpoint rounds (run_sub — v20; integration
    loss is descriptive, so the full ten-round trace is not needed)

Dependencies: rdflib (via ontology_model), external tools
              (reasoner, OOPS! client, structural_profile, alignment_rate,
               salient_term_pipeline, cq_scorer)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .defect_routing import Defect
from .feedback_payload import FeedbackCaps, FeedbackRender, render_feedback_within_allotment
from .ontology_model import ManagedOntology


# ── Battery result ──────────────────────────────────────────────────


@dataclass
class BatteryReports:
    """The five coupled-instrument reports, kept so D1 can re-render the
    payload per sub-ontology with its routed defects (v20)."""

    reasoner: "ReasonerReport"
    oops: "OOPSReport"
    structural: "StructuralProfile"
    alignment: "AlignmentReport"
    coverage: "CoverageReport"


@dataclass
class BatteryResult:
    """Full battery output for one round-state."""

    scores: Dict[str, Any]       # flat dict for battery.json
    feedback_text: str            # coupled items, rendered for the prompt
    defects: List[Defect]         # for defect routing (D1)
    reports: Optional[BatteryReports] = None
    feedback_render: Optional[FeedbackRender] = None   # truncation log (v20)


# ── Instrument interfaces ──────────────────────────────────────────
# Each instrument is a callable with a standard interface.
# Implementations are plugged in by the orchestrator.


@dataclass
class ReasonerReport:
    consistent: bool
    unsatisfiable_classes: List[str]
    owl2dl_conformant: bool
    profile_violations: List[str]


@dataclass
class OOPSReport:
    pitfalls: List[Dict[str, Any]]   # [{id, name, severity, affected_elements}]
    critical_count: int
    important_count: int
    minor_count: int


@dataclass
class StructuralProfile:
    """OntoQA-family metrics."""
    metrics: Dict[str, float]        # RR, AR, IR, CR, etc.


@dataclass
class AlignmentReport:
    bfo_aligned_rate: float
    iof_aligned_rate: float
    unaligned_rate: float
    total_domain_classes: int
    contamination_flag: bool          # >5% unexpected alignment
    cco_aligned_rate: float = 0.0     # contamination only (v19)


@dataclass
class CoverageReport:
    salient_term_coverage: float
    genre_coverage_balance: float     # normalised entropy
    missing_terms_by_genre: Dict[str, List[str]]
    per_genre_coverage: Dict[str, float]


# Question types whose CQs form the primary held-out outcome (v19).  Their
# SPARQL must join at least two label-matched classes through an object
# property path, so answering them needs structure that the coverage
# feedback does not supply.
PRIMARY_CQ_TYPES = ("relational", "multi-hop")


@dataclass
class CQReport:
    answerability: float
    total_cqs: int
    answerable_cqs: int
    per_stratum: Dict[str, float]
    # Primary aggregate over PRIMARY_CQ_TYPES.  Populate with
    # primary_cq_aggregate(); None if the scorer does not supply it.
    primary_answerability: Optional[float] = None
    primary_total: int = 0
    primary_answerable: int = 0
    # v20 extended fields, populated by cq_scorer.CQScorer
    per_genre: Dict[str, float] = field(default_factory=dict)
    per_cq: Dict[str, bool] = field(default_factory=dict)
    normalisation_only_share: Optional[float] = None   # labelling-convention diagnostic
    normalisation_only_count: int = 0
    errors: int = 0                                     # CQs that failed to execute
    cq_set_sha256: str = ""
    injection_only_cqs: int = 0     # CQs whose only answers came from the injection (not counted)
    unjudgeable_rows: int = 0       # counted rows that projected no IRI


def primary_cq_aggregate(
    per_cq: Dict[str, "tuple[str, bool]"],
    primary_types: "tuple[str, ...]" = PRIMARY_CQ_TYPES,
) -> "tuple[Optional[float], int, int]":
    """
    Compute the primary CQ aggregate from per-CQ results.

    Parameters
    ----------
    per_cq
        Mapping cq_id -> (question_type, answered).  Question types use the
        cq_calibrate vocabulary: existential, relational, multi-hop,
        definitional.

    Returns
    -------
    (answerability, total, answerable) over the primary types; answerability
    is None when no primary CQs are present.
    """
    rows = [ans for (qtype, ans) in per_cq.values() if qtype in primary_types]
    total = len(rows)
    answerable = sum(1 for a in rows if a)
    return (answerable / total if total else None), total, answerable


# ── Battery runner ──────────────────────────────────────────────────


class Battery:
    """
    Configurable battery runner.

    Each instrument is a callable that takes a ManagedOntology and
    returns its report type.  Instruments are registered at init;
    the runner calls them and assembles the result.
    """

    def __init__(
        self,
        reasoner_fn: Callable[[ManagedOntology], ReasonerReport],
        oops_fn: Callable[[ManagedOntology], OOPSReport],
        structural_fn: Callable[[ManagedOntology], StructuralProfile],
        alignment_fn: Callable[[ManagedOntology], AlignmentReport],
        coverage_fn: Callable[[ManagedOntology], CoverageReport],
        cq_fn: Optional[Callable[[ManagedOntology], CQReport]] = None,
        feedback_caps: Optional[FeedbackCaps] = None,
        feedback_allotment: Optional[int] = None,
        token_counter: Optional[Callable[[str], int]] = None,
        coverage_by_genre_fn: Optional[Callable[[ManagedOntology, str], CoverageReport]] = None,
        omit_conformance_report: bool = False,
    ):
        self.reasoner_fn = reasoner_fn
        self.oops_fn = oops_fn
        self.structural_fn = structural_fn
        self.alignment_fn = alignment_fn
        self.coverage_fn = coverage_fn
        self.cq_fn = cq_fn  # held out — may be None during pilot
        # v20: pinned feedback allotment and caps (campaign manifest)
        self.feedback_caps = feedback_caps or FeedbackCaps()
        self.feedback_allotment = feedback_allotment
        self.token_counter = token_counter
        # v20: sub-ontology coverage is scored against that genre's
        # inventory, not the whole-corpus inventory (overview Paper 1 §5.3)
        self.coverage_by_genre_fn = coverage_by_genre_fn
        # Conformance-channel ablation (overview Paper 1 §7.1): drop item 4
        # from the rendered payload; scores and ceiling unchanged.
        self.omit_conformance_report = omit_conformance_report

    def run(self, ontology: ManagedOntology) -> BatteryResult:
        """Run the full battery and return scores, feedback text, and defects."""

        # Run all instruments
        reasoner = self.reasoner_fn(ontology)
        oops = self.oops_fn(ontology)
        structural = self.structural_fn(ontology)
        alignment = self.alignment_fn(ontology)
        coverage = self.coverage_fn(ontology)
        cq = self.cq_fn(ontology) if self.cq_fn else None

        # Assemble scores
        scores: Dict[str, Any] = {
            "consistency": reasoner.consistent,
            "unsatisfiable_classes": len(reasoner.unsatisfiable_classes),
            "owl2dl_conformant": reasoner.owl2dl_conformant,
            "oops_pitfall_counts": {
                "critical": oops.critical_count,
                "important": oops.important_count,
                "minor": oops.minor_count,
            },
            "ontoqa": structural.metrics,
            "bfo_alignment_rate": alignment.bfo_aligned_rate,
            "iof_alignment_rate": alignment.iof_aligned_rate,
            "cco_alignment_rate": alignment.cco_aligned_rate,
            "unaligned_rate": alignment.unaligned_rate,
            "salient_term_coverage": coverage.salient_term_coverage,
            "genre_coverage_balance": coverage.genre_coverage_balance,
            "class_count": ontology.class_count,
            "property_count": ontology.property_count,
            "triple_count": ontology.triple_count,
        }

        if cq is not None:
            scores["cq_answerability"] = cq.answerability
            scores["cq_total"] = cq.total_cqs
            scores["cq_answerable"] = cq.answerable_cqs
            scores["cq_per_stratum"] = cq.per_stratum
            scores["cq_answerability_primary"] = cq.primary_answerability
            scores["cq_primary_total"] = cq.primary_total
            scores["cq_primary_answerable"] = cq.primary_answerable
            # v20 (cq_scorer): descriptive extras and the diagnostic
            scores["cq_per_genre"] = cq.per_genre
            scores["cq_per_cq"] = cq.per_cq
            scores["cq_normalisation_only_share"] = cq.normalisation_only_share
            scores["cq_normalisation_only_count"] = cq.normalisation_only_count
            scores["cq_errors"] = cq.errors
            scores["cq_injection_only_cqs"] = cq.injection_only_cqs
            scores["cq_unjudgeable_rows"] = cq.unjudgeable_rows
            scores["cq_set_sha256"] = cq.cq_set_sha256

        # Build defects for routing
        defects = _extract_defects(reasoner, oops, alignment, coverage)

        # Render feedback text (coupled instruments only — NOT CQs) under
        # the pinned allotment (v20)
        reports = BatteryReports(reasoner, oops, structural, alignment, coverage)
        render = self.render_feedback(reports)

        return BatteryResult(
            scores=scores,
            feedback_text=render.text,
            defects=defects,
            reports=reports,
            feedback_render=render,
        )

    def render_feedback(
        self,
        reports: BatteryReports,
        routed_defects: Optional[List[Defect]] = None,
        routed_genre_key: Optional[str] = None,
    ) -> FeedbackRender:
        """
        Render the six-item payload under the pinned caps and allotment.

        Under D1 the orchestrator calls this once per sub-ontology with the
        defects routed to it, so every iteration call at either D level sits
        under the same ceiling (overview Paper 1 §4.2).
        """
        return render_feedback_within_allotment(
            reports.reasoner, reports.oops, reports.structural,
            reports.alignment, reports.coverage,
            caps=self.feedback_caps,
            token_counter=self.token_counter,
            feedback_allotment=self.feedback_allotment,
            routed_defects=routed_defects,
            routed_genre_key=routed_genre_key,
            omit_conformance=self.omit_conformance_report,
        )

    def run_sub(self, sub_ontology: ManagedOntology, genre_key: str) -> Dict[str, Any]:
        """
        Sub-ontology battery for the integration-loss measure (v20).

        Grounding-agnostic instruments only, no CQs, no feedback rendering.
        Called by the orchestrator at the checkpoint rounds only
        (RunConfig.checkpoint_rounds): 30 runs × 4 checkpoints × 6 genres.
        """
        reasoner = self.reasoner_fn(sub_ontology)
        oops = self.oops_fn(sub_ontology)
        structural = self.structural_fn(sub_ontology)
        alignment = self.alignment_fn(sub_ontology)
        if self.coverage_by_genre_fn is not None:
            coverage = self.coverage_by_genre_fn(sub_ontology, genre_key)
        else:
            coverage = self.coverage_fn(sub_ontology)
        return {
            "genre": genre_key,
            "consistency": reasoner.consistent,
            "unsatisfiable_classes": len(reasoner.unsatisfiable_classes),
            "owl2dl_conformant": reasoner.owl2dl_conformant,
            "oops_pitfall_counts": {
                "critical": oops.critical_count,
                "important": oops.important_count,
                "minor": oops.minor_count,
            },
            "ontoqa": structural.metrics,
            "bfo_alignment_rate": alignment.bfo_aligned_rate,
            "iof_alignment_rate": alignment.iof_aligned_rate,
            "unaligned_rate": alignment.unaligned_rate,
            "salient_term_coverage_genre": coverage.salient_term_coverage,
            "class_count": sub_ontology.class_count,
            "property_count": sub_ontology.property_count,
            "triple_count": sub_ontology.triple_count,
        }


# ── Feedback rendering ──────────────────────────────────────────────
# v20: rendering lives in feedback_payload.py (pinned allotment, fixed
# item order, per-item caps, omitted counts, truncation log).  This
# wrapper keeps the old call signature for scripts that only need text.


def render_feedback(
    reasoner: ReasonerReport,
    oops: OOPSReport,
    structural: StructuralProfile,
    alignment: AlignmentReport,
    coverage: CoverageReport,
    caps: Optional[FeedbackCaps] = None,
) -> str:
    """Render the payload at the given caps (no allotment guard)."""
    return render_feedback_within_allotment(
        reasoner, oops, structural, alignment, coverage,
        caps=caps or FeedbackCaps(),
    ).text


# ── Defect extraction ───────────────────────────────────────────────


def _extract_defects(
    reasoner: ReasonerReport,
    oops: OOPSReport,
    alignment: AlignmentReport,
    coverage: CoverageReport,
) -> List[Defect]:
    """Extract structured defects from battery reports for defect routing."""
    defects: List[Defect] = []
    idx = 0

    # Reasoner: unsatisfiable classes
    for cls in reasoner.unsatisfiable_classes:
        defects.append(Defect(
            defect_id=f"reasoner_{idx}",
            instrument="reasoner",
            description=f"Unsatisfiable class: {cls}",
            severity="critical",
            involved_iris={cls},
        ))
        idx += 1

    # OOPS! pitfalls
    for pitfall in oops.pitfalls:
        defects.append(Defect(
            defect_id=f"oops_{idx}",
            instrument="oops",
            description=f"{pitfall.get('id', '?')}: {pitfall.get('name', '?')}",
            severity=pitfall.get("severity", "minor"),
            involved_iris=set(pitfall.get("affected_elements", [])),
            raw_data=pitfall,
        ))
        idx += 1

    # Coverage: missing terms (routed to all — no specific IRIs)
    for genre, terms in coverage.missing_terms_by_genre.items():
        if terms:
            defects.append(Defect(
                defect_id=f"coverage_{idx}",
                instrument="coverage",
                description=f"Missing terms in {genre}: {', '.join(terms[:5])}",
                severity="info",
                involved_iris=set(),  # global — routes to all sub-ontologies
                raw_data={"genre": genre, "missing_terms": terms},
            ))
            idx += 1

    return defects
