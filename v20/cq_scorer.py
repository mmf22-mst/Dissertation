"""
CQ scorer — the held-out instrument (overview v20 Part I §6.2(c); Paper 1
§5.2, §5.4).  Todo task 1, code half.

What it does
------------
For one ontology state:

  1. Build a *scoring copy* of the graph (label_normalisation.scoring_copy):
     every non-injected entity with an rdfs:label gets scoring:normLabel
     (the pinned normalisation rule) and scoring:rawLabel (verbatim).
     The artefact is never modified.
  2. Rewrite each CQ so its label patterns match scoring:normLabel, run
     it, and call the CQ *answered* if the result set is non-empty.
  3. Report answerability overall, per stratum (existential, relational,
     multi-hop, definitional), per genre tag, and the **primary aggregate**
     over the relational and multi-hop strata — the sole primary outcome
     for H1a–H1f.
  4. Run each CQ a second time against scoring:rawLabel and report the
     normalisation-only share (answered through the normalised label but
     not the raw one): the per-condition labelling-convention diagnostic.

Injection-only answers do not count
-----------------------------------
The Factor B scaffolding (BFO for B1; BFO + IOF Core for B2) is present in
the artefact.  A schema-level CQ such as "which plan specifications
prescribe manufacturing processes?" can be answered by IOF Core's own
classes and properties with nothing built from the corpus, so without a
rule B2 would earn answerability from the injection itself, not from
construction.  The rule: a result row counts only if at least one of the
entities it projects is *constructed* (not injected); rows whose projected
entities are all injected are discarded, and a CQ is answered when at
least one row survives.  Reusing an injected class as one endpoint of a
relation, or as an intermediate on a multi-hop path, is allowed and
counted — that reuse is the grounding effect the design wants to see —
but the injection alone can never answer a CQ.  Under B0 there are no
injected entities and the rule is inert.

"Injected" means: in the campaign's injection_iris for the condition, or
in a BFO/IOF/CCO namespace (a condition-independent floor that also covers
spontaneously emitted BFO/IOF IRIs in B0, consistent with the
alignment-rate query).  Rows that project no IRI at all (literal-only
projections) cannot be judged; they count and are flagged, and the
authoring rule for the CQ set is that every query projects the class
variables it label-matches.  Pinned, declared, not tuned.

CQ answerability is never fed back (battery.py); this module must not be
called from the feedback path.

Asset format
------------
The frozen CQ set is the markdown file cq_calibrate.py reads: blocks of

    **CQ-NCR-R-01.** question text
    ```sparql
    SELECT ... WHERE { ... rdfs:label ... FILTER(REGEX(LCASE(STR(?l)), "...")) ... }
    ```

with `**CQ-XGN-M-01.** [NCR+FME] question` for cross-genre items.  The
same block regex is used here so the calibration report and the scorer
never disagree about what a CQ is.  A JSON list of
{cq_id, question, qtype, genre_tags, sparql} is accepted too.  Either way
the asset's SHA-256 is recorded so every battery record names the CQ set
it was scored against.

Usage
-----
    from pipeline.cq_scorer import CQSet, CQScorer
    cq_set = CQSet.from_markdown("cq_set_frozen.md")
    problems = cq_set.validate()          # do this before freezing
    battery = Battery(..., cq_fn=CQScorer(cq_set, injection_iris=iris))

    python -m pipeline.cq_scorer --cq-file cq_set_frozen.md --validate
    python -m pipeline.cq_scorer --cq-file cq_set_frozen.md --ontology R09/ontology.owl --out cq.json
    python -m pipeline.cq_scorer --cq-file cq_set_frozen.md --run-dir runs/seed_03_B2D1

Dependencies: rdflib.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from rdflib import Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, Namespace

from .battery import CQReport, PRIMARY_CQ_TYPES, primary_cq_aggregate
from .label_normalisation import (
    LABEL_NORMALISATION_RULE,
    SCORING_NS,
    rewrite_cq_query,
    scoring_copy,
)
from .ontology_model import BFO, CCO, IOF_AV, IOF_CONSTR, SKOS, ManagedOntology

# ── Asset format (shared with cq_calibrate.py) ──────────────────────

_CQ_BLOCK_RE = re.compile(
    r"""\*\*(?P<cq_id>CQ-[A-Z]{3}-[ERMD]-\d{2})\.\*\*\s*
        (?:\[(?P<genres>[^\]]+)\]\s*)?
        (?P<question>[^\n]+)\n+
        ```[^\n]*\n
        (?P<sparql>.*?)
        ```""",
    re.VERBOSE | re.DOTALL,
)
QTYPE_CODES = {"E": "existential", "R": "relational", "M": "multi-hop", "D": "definitional"}
STRATA = ("existential", "relational", "multi-hop", "definitional")

# Namespace prefixes treated as injected (condition-independent floor;
# see module docstring).
INJECTED_NAMESPACE_PREFIXES: tuple[str, ...] = (
    str(BFO), str(IOF_CONSTR), str(IOF_AV), str(CCO),
)

# Prefixes bound for queries written without PREFIX lines.
_INIT_NS = {
    "rdf": RDF, "rdfs": RDFS, "owl": OWL, "skos": SKOS,
    "scoring": Namespace(SCORING_NS),
    "bfo": BFO, "iof-constr": IOF_CONSTR, "iof-av": IOF_AV, "cco": CCO,
}

SLOW_QUERY_SECONDS = 5.0   # per-CQ warning threshold; logged, not enforced


@dataclass(frozen=True)
class CQItem:
    cq_id: str
    question: str
    qtype: str                 # one of STRATA
    genre_tags: tuple          # e.g. ("NCR",) or ("NCR", "FME")
    sparql: str

    @property
    def primary(self) -> bool:
        return self.qtype in PRIMARY_CQ_TYPES


@dataclass
class CQSet:
    """The frozen CQ asset."""

    items: List[CQItem]
    source: str = ""
    sha256: str = ""

    # ── construction ──
    @classmethod
    def from_markdown(cls, path: str | Path) -> "CQSet":
        text = Path(path).read_text(encoding="utf-8")
        items: List[CQItem] = []
        for m in _CQ_BLOCK_RE.finditer(text):
            cq_id = m.group("cq_id")
            parts = cq_id.split("-")               # ["CQ", "NCR", "R", "01"]
            genres_raw = m.group("genres")
            tags = tuple(t.strip() for t in genres_raw.split("+")) if genres_raw else (parts[1],)
            items.append(CQItem(
                cq_id=cq_id,
                question=m.group("question").strip(),
                qtype=QTYPE_CODES.get(parts[2], parts[2]),
                genre_tags=tags,
                sparql=m.group("sparql").strip(),
            ))
        return cls(items=items, source=str(path),
                   sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())

    @classmethod
    def from_json(cls, path: str | Path) -> "CQSet":
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        items = [CQItem(
            cq_id=d["cq_id"], question=d.get("question", ""), qtype=d["qtype"],
            genre_tags=tuple(d.get("genre_tags", ())), sparql=d["sparql"],
        ) for d in data]
        return cls(items=items, source=str(path),
                   sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest())

    @classmethod
    def load(cls, path: str | Path) -> "CQSet":
        return cls.from_json(path) if str(path).endswith(".json") else cls.from_markdown(path)

    # ── checks run before freezing ──
    def validate(self) -> List[Dict[str, str]]:
        """
        Return a list of problems (empty when the set is ready to freeze):
        duplicate ids, unknown strata, queries that fail to parse (in
        either rewritten form), and queries whose label patterns are not
        in normalised form.
        """
        from rdflib.plugins.sparql import prepareQuery
        from .label_normalisation import check_pattern_terms

        problems: List[Dict[str, str]] = []
        seen: Set[str] = set()
        for it in self.items:
            if it.cq_id in seen:
                problems.append({"cq_id": it.cq_id, "problem": "duplicate id"})
            seen.add(it.cq_id)
            if it.qtype not in STRATA:
                problems.append({"cq_id": it.cq_id, "problem": f"unknown stratum {it.qtype!r}"})
            for target in ("norm", "raw"):
                try:
                    prepareQuery(rewrite_cq_query(it.sparql, target), initNs=_INIT_NS)
                except Exception as exc:  # noqa: BLE001 — report, don't raise
                    problems.append({"cq_id": it.cq_id,
                                     "problem": f"SPARQL does not parse ({target}): {exc}"[:300]})
            terms = _pattern_terms(it.sparql)
            for term, normed in check_pattern_terms(terms):
                problems.append({"cq_id": it.cq_id,
                                 "problem": f"pattern term {term!r} is not in normalised form ({normed!r})"})
        counts = self.stratum_counts()
        if counts.get("relational", 0) + counts.get("multi-hop", 0) == 0:
            problems.append({"cq_id": "*", "problem": "no primary-stratum CQs in the set"})
        return problems

    def stratum_counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {s: 0 for s in STRATA}
        for it in self.items:
            out[it.qtype] = out.get(it.qtype, 0) + 1
        return out

    def manifest_record(self) -> Dict[str, Any]:
        return {
            "cq_set_source": self.source,
            "cq_set_sha256": self.sha256,
            "cq_total": len(self.items),
            "cq_by_stratum": self.stratum_counts(),
            "cq_primary": sum(1 for it in self.items if it.primary),
            "label_normalisation_rule": LABEL_NORMALISATION_RULE,
        }


_SPARQL_PATTERN_RE = re.compile(
    r"""(?:REGEX|CONTAINS)\s*\(\s*LCASE\s*\(\s*STR\s*\(\s*\?\w+\s*\)\s*\)\s*,\s*"([^"]+)\"""",
    re.VERBOSE | re.IGNORECASE,
)


def _pattern_terms(sparql: str) -> List[str]:
    """Label-pattern terms as written (alternations split), for the
    normalised-form check.  Regex anchors and metacharacters stripped."""
    terms: List[str] = []
    for m in _SPARQL_PATTERN_RE.finditer(sparql):
        raw = m.group(1).strip("^$()")
        for alt in raw.split("|"):
            alt = re.sub(r"[\\^$()*+?.\[\]{}]", "", alt).strip()
            if alt:
                terms.append(alt)
    return terms


# ── Scoring ─────────────────────────────────────────────────────────


@dataclass
class CQResult:
    cq_id: str
    qtype: str
    genre_tags: tuple
    answered: bool            # against scoring:normLabel — the instrument
    answered_raw: Optional[bool]   # against scoring:rawLabel — diagnostic only
    rows: int                 # rows that count (≥ 1 constructed entity projected)
    elapsed_s: float
    error: Optional[str] = None
    rows_injection_only: int = 0   # rows discarded: every projected entity injected
    rows_without_iri: int = 0      # rows counted but unjudgeable (no IRI projected)


class CQScorer:
    """
    Callable[[ManagedOntology], CQReport] — plug in as Battery(cq_fn=...).

    Parameters
    ----------
    cq_set
        The frozen CQ asset.
    injection_iris
        IRIs of the Factor B injection for this condition (campaign.py's
        _injection_iris[condition.B]).  Rows projecting only these do not
        count.  Optional: the namespace floor applies regardless.
    exclude_prefixes
        Namespace prefixes treated as injected (default: BFO, IOF, CCO).
        Pass () to disable the floor — not the campaign setting.
    diagnostic
        Also run every CQ against the raw label to compute the
        normalisation-only share.  Doubles query time; CQ queries are
        cheap, so on by default.
    """

    def __init__(
        self,
        cq_set: CQSet,
        injection_iris: Optional[Iterable[URIRef]] = None,
        exclude_prefixes: Sequence[str] = INJECTED_NAMESPACE_PREFIXES,
        diagnostic: bool = True,
    ):
        self.cq_set = cq_set
        self.injection_iris: Set[str] = {str(i) for i in (injection_iris or ())}
        self.exclude_prefixes = tuple(exclude_prefixes)
        self.diagnostic = diagnostic
        self.sha256 = cq_set.sha256
        # Pre-rewrite once; the rewrite is deterministic and the set is frozen.
        self._norm_queries = {it.cq_id: rewrite_cq_query(it.sparql, "norm") for it in cq_set.items}
        self._raw_queries = {it.cq_id: rewrite_cq_query(it.sparql, "raw") for it in cq_set.items}

    # Battery interface
    def __call__(self, ontology: ManagedOntology) -> CQReport:
        return self.score(ontology)

    def score(self, ontology: ManagedOntology) -> CQReport:
        return self.score_detailed(ontology)[0]

    def score_detailed(self, ontology: ManagedOntology) -> tuple[CQReport, List[CQResult]]:
        graph = scoring_copy(ontology)      # all labelled entities, injected included
        results = [self._run_one(graph, it) for it in self.cq_set.items]
        return self.report(results), results

    def _is_injected(self, iri: URIRef) -> bool:
        s = str(iri)
        return s in self.injection_iris or any(s.startswith(p) for p in self.exclude_prefixes)

    def _count_rows(self, result) -> tuple[int, int, int]:
        """Apply the injection-only rule.  Returns (counted, injection_only, without_iri)."""
        counted = injection_only = without_iri = 0
        for row in result:
            values = list(row) if not isinstance(row, bool) else []
            iris = [v for v in values if isinstance(v, URIRef)]
            if not iris:
                counted += 1; without_iri += 1
            elif any(not self._is_injected(v) for v in iris):
                counted += 1
            else:
                injection_only += 1
        return counted, injection_only, without_iri

    def _run_one(self, graph, it: CQItem) -> CQResult:
        t0 = time.perf_counter()
        inj_only = no_iri = 0
        try:
            rows, inj_only, no_iri = self._count_rows(
                graph.query(self._norm_queries[it.cq_id], initNs=_INIT_NS))
            answered = rows > 0
            error = None
        except Exception as exc:  # noqa: BLE001 — a broken CQ scores as unanswered, flagged
            rows, answered, error = 0, False, f"{type(exc).__name__}: {exc}"[:300]
        answered_raw: Optional[bool] = None
        if self.diagnostic and error is None:
            try:
                raw_rows, _, _ = self._count_rows(
                    graph.query(self._raw_queries[it.cq_id], initNs=_INIT_NS))
                answered_raw = raw_rows > 0
            except Exception:  # noqa: BLE001
                answered_raw = None
        elapsed = time.perf_counter() - t0
        if elapsed > SLOW_QUERY_SECONDS:
            print(f"WARNING: {it.cq_id} took {elapsed:.1f}s", file=sys.stderr)
        return CQResult(it.cq_id, it.qtype, it.genre_tags, answered, answered_raw, rows, elapsed, error,
                        rows_injection_only=inj_only, rows_without_iri=no_iri)

    def report(self, results: List[CQResult]) -> CQReport:
        total = len(results)
        answerable = sum(1 for r in results if r.answered)
        per_stratum: Dict[str, float] = {}
        for s in STRATA:
            rows = [r for r in results if r.qtype == s]
            per_stratum[s] = (sum(1 for r in rows if r.answered) / len(rows)) if rows else float("nan")
        per_cq = {r.cq_id: (r.qtype, r.answered) for r in results}
        prim_ans, prim_total, prim_answerable = primary_cq_aggregate(per_cq)

        # Per-genre (a cross-genre CQ counts toward each of its tags)
        genre_rows: Dict[str, List[bool]] = {}
        for r in results:
            for g in r.genre_tags:
                genre_rows.setdefault(g, []).append(r.answered)
        per_genre = {g: sum(v) / len(v) for g, v in sorted(genre_rows.items())}

        # Normalisation-only diagnostic
        diag_rows = [r for r in results if r.answered_raw is not None]
        norm_only = sum(1 for r in diag_rows if r.answered and not r.answered_raw)
        norm_answered = sum(1 for r in diag_rows if r.answered)
        norm_only_share = (norm_only / norm_answered) if norm_answered else 0.0

        rep = CQReport(
            answerability=(answerable / total) if total else 0.0,
            total_cqs=total,
            answerable_cqs=answerable,
            per_stratum=per_stratum,
            primary_answerability=prim_ans,
            primary_total=prim_total,
            primary_answerable=prim_answerable,
        )
        # Extended fields (battery.py v20)
        rep.per_genre = per_genre
        rep.per_cq = {r.cq_id: r.answered for r in results}
        rep.normalisation_only_share = norm_only_share if self.diagnostic else None
        rep.normalisation_only_count = norm_only
        rep.errors = sum(1 for r in results if r.error)
        rep.cq_set_sha256 = self.sha256
        rep.injection_only_cqs = sum(1 for r in results if not r.answered and r.rows_injection_only > 0)
        rep.unjudgeable_rows = sum(r.rows_without_iri for r in results)
        return rep


# ── CLI ─────────────────────────────────────────────────────────────


def _report_to_dict(rep: CQReport, results: List[CQResult]) -> Dict[str, Any]:
    return {
        "cq_answerability": rep.answerability,
        "cq_total": rep.total_cqs,
        "cq_answerable": rep.answerable_cqs,
        "cq_per_stratum": rep.per_stratum,
        "cq_answerability_primary": rep.primary_answerability,
        "cq_primary_total": rep.primary_total,
        "cq_primary_answerable": rep.primary_answerable,
        "cq_per_genre": rep.per_genre,
        "cq_normalisation_only_share": rep.normalisation_only_share,
        "cq_normalisation_only_count": rep.normalisation_only_count,
        "cq_errors": rep.errors,
        "cq_injection_only_cqs": rep.injection_only_cqs,
        "cq_unjudgeable_rows": rep.unjudgeable_rows,
        "cq_set_sha256": rep.cq_set_sha256,
        "label_normalisation_rule": LABEL_NORMALISATION_RULE,
        "per_cq": [
            {"cq_id": r.cq_id, "qtype": r.qtype, "genre_tags": list(r.genre_tags),
             "answered": r.answered, "answered_raw": r.answered_raw, "rows": r.rows,
             "rows_injection_only": r.rows_injection_only, "rows_without_iri": r.rows_without_iri,
             "elapsed_s": round(r.elapsed_s, 4), "error": r.error}
            for r in results
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Score CQ answerability on an ontology state.")
    ap.add_argument("--cq-file", required=True, help="frozen CQ set (.md or .json)")
    ap.add_argument("--validate", action="store_true", help="validate the set and exit")
    ap.add_argument("--ontology", help="one ontology file (RDF/XML)")
    ap.add_argument("--run-dir", help="a run directory; scores every R*/ontology.owl and writes cq.json beside each")
    ap.add_argument("--injection", help="injection source ontology (bfo-core.owl or Core.rdf); rows projecting only its entities do not count")
    ap.add_argument("--no-diagnostic", action="store_true")
    ap.add_argument("--out", help="output JSON (single-ontology mode)")
    args = ap.parse_args(argv)

    cq_set = CQSet.load(args.cq_file)
    print(json.dumps(cq_set.manifest_record(), indent=2), file=sys.stderr)
    if args.validate:
        problems = cq_set.validate()
        for p in problems:
            print(f"{p['cq_id']}: {p['problem']}")
        print(f"{len(problems)} problem(s)", file=sys.stderr)
        return 1 if problems else 0

    injection_iris: Set[URIRef] = set()
    if args.injection:
        injection_iris = ManagedOntology.from_file(Path(args.injection)).all_entities()
    scorer = CQScorer(cq_set, injection_iris=injection_iris, diagnostic=not args.no_diagnostic)

    if args.ontology:
        onto = ManagedOntology.from_file(Path(args.ontology))
        rep, results = scorer.score_detailed(onto)
        out = _report_to_dict(rep, results)
        text = json.dumps(out, indent=2)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0

    if args.run_dir:
        for owl in sorted(Path(args.run_dir).glob("R*/ontology.owl")):
            onto = ManagedOntology.from_file(owl)
            rep, results = scorer.score_detailed(onto)
            (owl.parent / "cq.json").write_text(json.dumps(_report_to_dict(rep, results), indent=2), encoding="utf-8")
            print(f"{owl.parent.name}: primary {rep.primary_answerability}, overall {rep.answerability:.3f}, "
                  f"norm-only {rep.normalisation_only_share}", file=sys.stderr)
        return 0

    ap.error("give --validate, --ontology or --run-dir")
    return 2


if __name__ == "__main__":
    sys.exit(main())
