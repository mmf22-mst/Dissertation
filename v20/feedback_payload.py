"""
Feedback payload rendering under a pinned allotment — overview v20,
Paper 1 §4.2 ("Feedback allotment and truncation rule") and §4.4.

The iteration prompt carries the six-item feedback payload in a pinned
FEEDBACK allotment, the fourth allotment beside injection, window and
chunk.  This module is the only place the payload is rendered.

Rules implemented here (all pre-registered):

  * Fixed item order:
      0. (D1 only) issues routed to this sub-ontology
      1. reasoner report
      2. OWL 2 DL profile report
      3. OOPS! pitfall report
      4. conformance report (alignment rates)
      5. salient-term coverage report (missing terms by genre)
      6. genre coverage balance report
  * The summary line(s) of every item are always present.
  * Only the list-valued parts can grow: unsatisfiable classes, profile
    violations, pitfalls, missing terms, routed defects.  Each list is
    truncated to a per-item cap (FeedbackCaps, pinned with the
    allotments before the pilot) in a deterministic order:
      - pitfalls: severity (critical > important > minor), then id, then
        first affected IRI
      - missing terms: salience rank (inventory order), then genre
      - routed defects: severity, then defect_id
      - everything else: IRI (string sort)
  * Every truncated list ends with "... and N more (omitted)".
  * Truncation events and omitted counts are returned in a log for the
    per-round record (tokens, per-item omitted counts, overflow steps).
  * Allotment guard: caps are pinned so the rendered payload fits the
    allotment in the worst case.  If it still does not (very long IRIs,
    say), every cap is halved and the payload re-rendered, deterministically,
    until it fits; the number of halving steps is logged and is expected
    to be zero in the pilot (smoke test: overflow_steps == 0 everywhere).

Nothing here depends on rdflib; the reports are plain dataclasses from
battery.py.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Callable, Dict, List, Optional, Sequence


# ── Pinned caps ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class FeedbackCaps:
    """
    Per-item list caps.  Pinned once with the allotments (task 0c) and
    recorded in the campaign manifest.  The defaults are placeholders
    for smoke tests, not the pinned values.
    """

    unsatisfiable_classes: int = 20
    profile_violations: int = 10
    pitfalls: int = 15
    pitfall_affected_elements: int = 5
    missing_terms_per_genre: int = 15
    routed_defects: int = 20

    def halved(self) -> "FeedbackCaps":
        """Deterministic reduction step for the allotment guard (min 1)."""
        return FeedbackCaps(
            **{k: max(1, v // 2) for k, v in asdict(self).items()}
        )

    def as_dict(self) -> Dict[str, int]:
        return asdict(self)


# ── Result ──────────────────────────────────────────────────────────


@dataclass
class FeedbackRender:
    """Rendered payload plus the truncation log for the round record."""

    text: str
    tokens: int
    caps_used: Dict[str, int]
    omitted: Dict[str, int]            # item → entries omitted (0 if none)
    truncated_items: List[str]         # items with omitted > 0, in order
    overflow_steps: int                # halving steps taken by the guard
    flagged_counts: Dict[str, int]     # item → total entries before caps

    def log_record(self) -> Dict[str, Any]:
        return {
            "feedback_tokens": self.tokens,
            "feedback_caps_used": self.caps_used,
            "feedback_flagged_counts": self.flagged_counts,
            "feedback_omitted": self.omitted,
            "feedback_truncated_items": self.truncated_items,
            "feedback_overflow_steps": self.overflow_steps,
        }


# ── Ordering helpers ────────────────────────────────────────────────

_SEVERITY_RANK = {"critical": 0, "important": 1, "minor": 2, "info": 3}


def _sev(s: Optional[str]) -> int:
    return _SEVERITY_RANK.get((s or "").lower(), 9)


def _pitfall_key(p: Dict[str, Any]) -> tuple:
    affected = sorted(str(x) for x in p.get("affected_elements", []) or [])
    return (_sev(p.get("severity")), str(p.get("id", "")), affected[0] if affected else "")


def _cap_list(
    items: Sequence[Any],
    cap: int,
    render: Callable[[Any], str],
    lines: List[str],
    omitted: Dict[str, int],
    flagged: Dict[str, int],
    item_name: str,
) -> None:
    """Append up to `cap` rendered entries; record omitted count."""
    flagged[item_name] = flagged.get(item_name, 0) + len(items)
    shown = list(items)[:cap]
    for it in shown:
        lines.append(render(it))
    n_omitted = len(items) - len(shown)
    omitted[item_name] = omitted.get(item_name, 0) + n_omitted
    if n_omitted > 0:
        lines.append(f"  ... and {n_omitted} more (omitted)")


# ── Rendering ───────────────────────────────────────────────────────


def render_feedback(
    reasoner: Any,
    oops: Any,
    structural: Any,
    alignment: Any,
    coverage: Any,
    caps: FeedbackCaps,
    routed_defects: Optional[Sequence[Any]] = None,
    routed_genre_key: Optional[str] = None,
    omit_conformance: bool = False,
) -> tuple[str, Dict[str, int], Dict[str, int]]:
    """
    Render the payload once at the given caps.

    omit_conformance drops item 4 for the conformance-channel ablation
    (overview Paper 1 §7.1: B2D0, three seeds).  The ceiling is unchanged.

    Returns (text, omitted_by_item, flagged_by_item).  Coupled instruments
    only; CQ answerability is never included.  No round counter, no history.
    """
    lines: List[str] = []
    omitted: Dict[str, int] = {}
    flagged: Dict[str, int] = {}

    # 0. Routed defects (D1 only) — position 0 so the sub-ontology's own
    #    issues come first, as the v16+ routing design intends.
    if routed_defects is not None and routed_genre_key is not None:
        lines.append(f"### Issues specific to this sub-ontology ({routed_genre_key})")
        ordered = sorted(routed_defects, key=lambda d: (_sev(d.severity), d.defect_id))
        if not ordered:
            lines.append("No issues routed specifically to this sub-ontology.")
        _cap_list(
            ordered, caps.routed_defects,
            lambda d: f"- [{d.severity}] {d.description}",
            lines, omitted, flagged, "routed_defects",
        )
        lines.append("")

    # 1. Reasoner report
    lines.append("### 1. Reasoner Report")
    lines.append(
        "The ontology is consistent." if reasoner.consistent
        else "WARNING: The ontology is INCONSISTENT."
    )
    unsat = sorted(str(c) for c in reasoner.unsatisfiable_classes)
    if unsat:
        lines.append(f"Unsatisfiable classes ({len(unsat)}):")
        _cap_list(unsat, caps.unsatisfiable_classes, lambda c: f"  - {c}",
                  lines, omitted, flagged, "unsatisfiable_classes")
    else:
        lines.append("No unsatisfiable classes.")
        flagged["unsatisfiable_classes"] = 0
        omitted["unsatisfiable_classes"] = 0

    # 2. OWL 2 DL profile
    lines.append("\n### 2. OWL 2 DL Profile Report")
    if reasoner.owl2dl_conformant:
        lines.append("The ontology conforms to the OWL 2 DL profile.")
        flagged["profile_violations"] = 0
        omitted["profile_violations"] = 0
    else:
        violations = sorted(str(v) for v in reasoner.profile_violations)
        lines.append(f"Profile violations ({len(violations)}):")
        _cap_list(violations, caps.profile_violations, lambda v: f"  - {v}",
                  lines, omitted, flagged, "profile_violations")

    # 3. OOPS! pitfalls
    lines.append("\n### 3. OOPS! Pitfall Report")
    lines.append(
        f"Critical: {oops.critical_count}, Important: {oops.important_count}, "
        f"Minor: {oops.minor_count}"
    )
    pitfalls = sorted(oops.pitfalls, key=_pitfall_key)

    def _render_pitfall(p: Dict[str, Any]) -> str:
        affected = sorted(str(x) for x in p.get("affected_elements", []) or [])
        shown = affected[: caps.pitfall_affected_elements]
        extra = len(affected) - len(shown)
        tail = f" (+{extra} more)" if extra > 0 else ""
        return (
            f"  [{p.get('severity', '?')}] {p.get('id', '?')}: {p.get('name', '?')} — "
            f"affects: {', '.join(shown)}{tail}"
        )

    _cap_list(pitfalls, caps.pitfalls, _render_pitfall,
              lines, omitted, flagged, "pitfalls")

    # 4. Conformance (summary only — never grows)
    if not omit_conformance:
        lines.append("\n### 4. Conformance Report")
        lines.append(
            f"BFO-aligned: {alignment.bfo_aligned_rate:.1%}, "
            f"IOF-aligned: {alignment.iof_aligned_rate:.1%}, "
            f"Unaligned: {alignment.unaligned_rate:.1%} "
            f"(of {alignment.total_domain_classes} domain classes)"
        )
        if alignment.contamination_flag:
            lines.append("NOTE: Unexpected alignment detected (>5%).")

    # 5. Salient-term coverage — per-genre summary always present; the
    #    missing-term lists are the growing part.  Inventory order is the
    #    salience rank, so no re-sort within a genre; genres sort by key.
    lines.append("\n### 5. Salient-Term Coverage Report")
    lines.append(f"Overall coverage: {coverage.salient_term_coverage:.1%}")
    for genre, cov in sorted(coverage.per_genre_coverage.items()):
        lines.append(f"  {genre}: {cov:.1%}")
    lines.append("\nMissing high-salience terms by genre:")
    any_missing = False
    for genre, terms in sorted(coverage.missing_terms_by_genre.items()):
        if not terms:
            continue
        any_missing = True
        lines.append(f"  {genre} ({len(terms)} missing):")
        _cap_list(list(terms), caps.missing_terms_per_genre,
                  lambda t: f"    - {t}",
                  lines, omitted, flagged, "missing_terms")
    if not any_missing:
        lines.append("  (none)")
        flagged.setdefault("missing_terms", 0)
        omitted.setdefault("missing_terms", 0)

    # 6. Genre coverage balance (summary only)
    lines.append("\n### 6. Genre Coverage Balance")
    lines.append(
        f"Normalised entropy: {coverage.genre_coverage_balance:.3f} "
        f"(1.0 = perfectly balanced)"
    )

    return "\n".join(lines), omitted, flagged


def render_feedback_within_allotment(
    reasoner: Any,
    oops: Any,
    structural: Any,
    alignment: Any,
    coverage: Any,
    caps: FeedbackCaps,
    token_counter: Optional[Callable[[str], int]] = None,
    feedback_allotment: Optional[int] = None,
    routed_defects: Optional[Sequence[Any]] = None,
    routed_genre_key: Optional[str] = None,
    max_overflow_steps: int = 8,
    omit_conformance: bool = False,
) -> FeedbackRender:
    """
    Render at the pinned caps, then apply the allotment guard.

    If no token_counter/allotment is supplied (pilot without pinned
    values), the payload is rendered once at the caps and tokens is -1.
    """
    steps = 0
    current = caps
    while True:
        text, omitted, flagged = render_feedback(
            reasoner, oops, structural, alignment, coverage, current,
            routed_defects=routed_defects, routed_genre_key=routed_genre_key,
            omit_conformance=omit_conformance,
        )
        if token_counter is None or feedback_allotment is None:
            tokens = -1
            break
        tokens = token_counter(text)
        if tokens <= feedback_allotment or steps >= max_overflow_steps:
            break
        current = current.halved()
        steps += 1

    truncated = [k for k, v in omitted.items() if v > 0]
    return FeedbackRender(
        text=text,
        tokens=tokens,
        caps_used=current.as_dict(),
        omitted=omitted,
        truncated_items=truncated,
        overflow_steps=steps,
        flagged_counts=flagged,
    )
