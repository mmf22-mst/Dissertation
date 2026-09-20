"""
structural_profile.py — OntoQA structural metrics and OOPS! pitfall scanning.

Part of the dissertation evaluation battery (Paper 1 §3.4, Part I §5.4).
Computes seven OntoQA metrics (Tartir et al. 2005) over an OWL ontology
and wraps the OOPS! REST web service for pitfall detection.

Dependencies:
    pip install rdflib requests

Usage:
    from structural_profile import compute_ontoqa, scan_oops, full_profile

    # OntoQA metrics only
    metrics = compute_ontoqa("my_ontology.owl")

    # OOPS! scan only
    pitfalls = scan_oops("my_ontology.owl")

    # Full structural profile (both)
    profile = full_profile("my_ontology.owl")
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import rdflib
from rdflib import OWL, RDF, RDFS
from rdflib.term import URIRef

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# OOPS! severity classification from the catalogue (April 2023 revision).
# Keys are pitfall codes; values are severity levels.
OOPS_SEVERITY: dict[str, str] = {
    "P01": "critical",  "P02": "minor",     "P03": "critical",
    "P04": "minor",     "P05": "critical",  "P06": "critical",
    "P07": "minor",     "P08": "minor",     "P09": "minor",
    "P10": "important", "P11": "important", "P12": "important",
    "P13": "minor",     "P14": "critical",  "P15": "critical",
    "P16": "critical",  "P17": "important", "P18": "important",
    "P19": "critical",  "P20": "minor",     "P21": "minor",
    "P22": "minor",     "P23": "important", "P24": "important",
    "P25": "important", "P26": "important", "P27": "critical",
    "P28": "critical",  "P29": "critical",  "P30": "important",
    "P31": "critical",  "P32": "minor",     "P33": "minor",
    "P34": "important", "P35": "important", "P36": "minor",
    "P37": "critical",  "P38": "important", "P39": "critical",
    "P40": "critical",  "P41": "important",
}

# Pitfalls actually implemented by the OOPS! web service (per their docs).
# The catalogue lists 41 but the scanner only checks these 21.
OOPS_IMPLEMENTED: set[str] = {
    "P02", "P03", "P04", "P05", "P06", "P07", "P08",
    "P10", "P11", "P12", "P13",
    "P19", "P20", "P21", "P22",
    "P24", "P25", "P26", "P27", "P28", "P29",
}

OOPS_ENDPOINT = "https://oops.linkeddata.es/rest"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class OntoQAMetrics:
    """Seven OntoQA structural metrics (Tartir et al. 2005)."""

    class_count: int = 0
    inheritance_richness: float = 0.0   # mean subclasses per class
    relationship_richness: float = 0.0  # non-subClassOf / total relations
    attribute_richness: float = 0.0     # datatype properties / classes
    max_depth: int = 0
    mean_depth: float = 0.0
    orphan_rate: float = 0.0            # classes with no named super / total

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class OOPSPitfall:
    """A single pitfall instance returned by OOPS!."""

    code: str = ""
    name: str = ""
    description: str = ""
    severity: str = ""                         # from OOPS_SEVERITY lookup
    affected_elements: list[str] = field(default_factory=list)


@dataclass
class OOPSResult:
    """Aggregated OOPS! scan results."""

    pitfalls: list[OOPSPitfall] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    suggestions: list[dict] = field(default_factory=list)

    # Counts by severity, for the battery
    @property
    def count_critical(self) -> int:
        return sum(1 for p in self.pitfalls if p.severity == "critical")

    @property
    def count_important(self) -> int:
        return sum(1 for p in self.pitfalls if p.severity == "important")

    @property
    def count_minor(self) -> int:
        return sum(1 for p in self.pitfalls if p.severity == "minor")

    @property
    def total(self) -> int:
        return len(self.pitfalls)

    def summary(self) -> dict:
        """Return the counts the battery records per round."""
        return {
            "total_pitfalls": self.total,
            "critical": self.count_critical,
            "important": self.count_important,
            "minor": self.count_minor,
            "pitfall_codes": sorted({p.code for p in self.pitfalls}),
            "warnings": len(self.warnings),
            "suggestions": len(self.suggestions),
        }


@dataclass
class StructuralProfile:
    """Combined OntoQA + OOPS! profile for one ontology state."""

    ontoqa: OntoQAMetrics
    oops: OOPSResult | None       # None if scan was skipped or failed
    source_path: str = ""
    error: str = ""               # non-empty if something went wrong


# ---------------------------------------------------------------------------
# OntoQA computation
# ---------------------------------------------------------------------------

def _load_graph(source: str | Path) -> rdflib.Graph:
    """Load an ontology into an rdflib Graph, auto-detecting format."""
    g = rdflib.Graph()
    path = Path(source)
    fmt = None
    suffix = path.suffix.lower()
    if suffix in (".ttl",):
        fmt = "turtle"
    elif suffix in (".n3",):
        fmt = "n3"
    elif suffix in (".nt",):
        fmt = "nt"
    elif suffix in (".jsonld", ".json"):
        fmt = "json-ld"
    # .owl, .rdf, .xml → RDF/XML (rdflib default)
    g.parse(str(path), format=fmt)
    return g


def _named_classes(
    g: rdflib.Graph,
    exclude_ns: set[str] | None = None,
) -> set[URIRef]:
    """Return the set of named OWL classes, optionally excluding namespaces.

    A class is included if it appears as:
      - (C, rdf:type, owl:Class)  or
      - (C, rdf:type, rdfs:Class) or
      - (C, rdfs:subClassOf, _)   or
      - (_, rdfs:subClassOf, C)

    owl:Thing and owl:Nothing are always excluded.
    """
    candidates: set[URIRef] = set()

    # Explicitly typed
    for s in g.subjects(RDF.type, OWL.Class):
        if isinstance(s, URIRef):
            candidates.add(s)
    for s in g.subjects(RDF.type, RDFS.Class):
        if isinstance(s, URIRef):
            candidates.add(s)

    # Appearing in subClassOf (catches untyped but used classes — P34 aside,
    # a generated ontology will usually have these typed, but we're robust)
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef):
            candidates.add(s)
        if isinstance(o, URIRef):
            candidates.add(o)

    # Remove owl:Thing, owl:Nothing
    candidates.discard(OWL.Thing)
    candidates.discard(OWL.Nothing)

    # Namespace exclusion
    if exclude_ns:
        candidates = {
            c for c in candidates
            if not any(str(c).startswith(ns) for ns in exclude_ns)
        }

    return candidates


def _subclass_edges(
    g: rdflib.Graph,
    classes: set[URIRef],
) -> list[tuple[URIRef, URIRef]]:
    """Return (child, parent) pairs for named subClassOf edges within the
    class set, excluding owl:Thing parents."""
    edges = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if (
            isinstance(s, URIRef)
            and isinstance(o, URIRef)
            and s in classes
            and o in classes
        ):
            edges.append((s, o))
    return edges


def _object_properties(g: rdflib.Graph) -> set[URIRef]:
    """Named object properties declared in the ontology."""
    props: set[URIRef] = set()
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        if isinstance(s, URIRef):
            props.add(s)
    return props


def _datatype_properties(g: rdflib.Graph) -> set[URIRef]:
    """Named datatype properties declared in the ontology."""
    props: set[URIRef] = set()
    for s in g.subjects(RDF.type, OWL.DatatypeProperty):
        if isinstance(s, URIRef):
            props.add(s)
    return props


def _compute_depths(
    classes: set[URIRef],
    subclass_edges: list[tuple[URIRef, URIRef]],
) -> dict[URIRef, int]:
    """Compute the depth of every class via BFS from roots.

    Depth of a root (no named superclass in the set) = 0.
    Depth of a class = 1 + max depth among its parents.

    For classes in cycles (which OOPS! P06 flags), depth is set to -1
    to avoid infinite loops; these are counted but excluded from
    max/mean depth calculations.
    """
    # Build parent → children and child → parents maps
    children_of: dict[URIRef, set[URIRef]] = defaultdict(set)
    parents_of: dict[URIRef, set[URIRef]] = defaultdict(set)
    for child, parent in subclass_edges:
        children_of[parent].add(child)
        parents_of[child].add(parent)

    # Roots: classes with no named parent in the class set
    roots = {c for c in classes if not parents_of.get(c)}

    # BFS from roots
    depths: dict[URIRef, int] = {}
    queue = list(roots)
    for r in queue:
        depths[r] = 0

    visited = set(roots)
    while queue:
        current = queue.pop(0)
        current_depth = depths[current]
        for child in children_of.get(current, set()):
            new_depth = current_depth + 1
            if child not in depths or new_depth > depths[child]:
                depths[child] = new_depth
            if child not in visited:
                visited.add(child)
                queue.append(child)

    # Any class not reached (isolated or in a pure cycle) gets depth -1
    for c in classes:
        if c not in depths:
            depths[c] = -1

    return depths


def compute_ontoqa(
    source: str | Path,
    exclude_ns: set[str] | None = None,
) -> OntoQAMetrics:
    """Compute all seven OntoQA metrics for an ontology file.

    Parameters
    ----------
    source : path to the ontology file (.owl, .rdf, .ttl, etc.)
    exclude_ns : optional set of namespace prefixes to exclude from
        class counting (e.g. {"http://purl.obolibrary.org/obo/BFO_"})
        to restrict metrics to domain classes only.

    Returns
    -------
    OntoQAMetrics dataclass with all seven values.
    """
    g = _load_graph(source)
    classes = _named_classes(g, exclude_ns)
    n_classes = len(classes)

    if n_classes == 0:
        return OntoQAMetrics()

    # --- Inheritance Richness: mean subclasses per class ---
    sc_edges = _subclass_edges(g, classes)
    # Count how many subclasses each class has
    subclass_count: dict[URIRef, int] = defaultdict(int)
    for child, parent in sc_edges:
        subclass_count[parent] += 1
    ir = len(sc_edges) / n_classes

    # --- Relationship Richness ---
    obj_props = _object_properties(g)
    n_obj_props = len(obj_props)
    n_sc_edges = len(sc_edges)
    total_relations = n_obj_props + n_sc_edges
    rr = n_obj_props / total_relations if total_relations > 0 else 0.0

    # --- Attribute Richness ---
    dt_props = _datatype_properties(g)
    ar = len(dt_props) / n_classes

    # --- Depth metrics ---
    depths = _compute_depths(classes, sc_edges)
    valid_depths = [d for d in depths.values() if d >= 0]
    max_depth = max(valid_depths) if valid_depths else 0
    mean_depth = sum(valid_depths) / len(valid_depths) if valid_depths else 0.0

    # --- Orphan Rate ---
    # A class is an orphan if it has no named superclass within the class set.
    # Classes whose only parent is owl:Thing (excluded from the set) count
    # as orphans — they have no *named domain* superclass.
    parents_of: dict[URIRef, set[URIRef]] = defaultdict(set)
    for child, parent in sc_edges:
        parents_of[child].add(parent)

    orphans = sum(1 for c in classes if not parents_of.get(c))
    orphan_rate = orphans / n_classes

    return OntoQAMetrics(
        class_count=n_classes,
        inheritance_richness=round(ir, 4),
        relationship_richness=round(rr, 4),
        attribute_richness=round(ar, 4),
        max_depth=max_depth,
        mean_depth=round(mean_depth, 4),
        orphan_rate=round(orphan_rate, 4),
    )


# ---------------------------------------------------------------------------
# OOPS! web service client
# ---------------------------------------------------------------------------

def _build_oops_request_body(
    ontology_content: str | None = None,
    ontology_uri: str | None = None,
    pitfalls: str = "",
    output_format: str = "XML",
) -> str:
    """Build the XML request body for the OOPS! REST endpoint."""
    content_block = ""
    uri_block = ""
    if ontology_content:
        content_block = f"<![CDATA[{ontology_content}]]>"
    if ontology_uri:
        uri_block = ontology_uri

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<OOPSRequest>\n"
        f"  <OntologyUrl>{uri_block}</OntologyUrl>\n"
        f"  <OntologyContent>{content_block}</OntologyContent>\n"
        f"  <Pitfalls>{pitfalls}</Pitfalls>\n"
        f"  <OutputFormat>{output_format}</OutputFormat>\n"
        "</OOPSRequest>"
    )


def _parse_oops_xml(xml_text: str) -> OOPSResult:
    """Parse the OOPS! XML response into an OOPSResult."""
    result = OOPSResult()

    # The OOPS! XML uses its own namespace
    ns = {"oops": "http://www.oeg-upm.net/oops"}

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return result

    # Pitfalls
    for pitfall_el in root.findall(".//oops:Pitfall", ns):
        code_el = pitfall_el.find("oops:Code", ns)
        name_el = pitfall_el.find("oops:Name", ns)
        desc_el = pitfall_el.find("oops:Description", ns)

        code = (code_el.text or "").strip() if code_el is not None else ""
        # Normalise code to Pxx format
        if code and not code.startswith("P"):
            code = f"P{int(code):02d}"

        affected = []
        affects_el = pitfall_el.find("oops:Affects", ns)
        if affects_el is not None:
            for ae in affects_el.findall("oops:AffectedElement", ns):
                if ae.text:
                    affected.append(ae.text.strip())

        result.pitfalls.append(OOPSPitfall(
            code=code,
            name=(name_el.text or "").strip() if name_el is not None else "",
            description=(desc_el.text or "").strip() if desc_el is not None else "",
            severity=OOPS_SEVERITY.get(code, "unknown"),
            affected_elements=affected,
        ))

    # Warnings
    for warn_el in root.findall(".//oops:Warning", ns):
        name_el = warn_el.find("oops:Name", ns)
        affected = []
        affects_el = warn_el.find("oops:Affects", ns)
        if affects_el is not None:
            for ae in affects_el.findall("oops:AffectedElement", ns):
                if ae.text:
                    affected.append(ae.text.strip())
        result.warnings.append({
            "name": (name_el.text or "").strip() if name_el is not None else "",
            "affected_elements": affected,
        })

    # Suggestions
    for sugg_el in root.findall(".//oops:Suggestion", ns):
        name_el = sugg_el.find("oops:Name", ns)
        desc_el = sugg_el.find("oops:Description", ns)
        result.suggestions.append({
            "name": (name_el.text or "").strip() if name_el is not None else "",
            "description": (desc_el.text or "").strip() if desc_el is not None else "",
        })

    return result


def scan_oops(
    source: str | Path,
    timeout: int = 120,
) -> OOPSResult:
    """Submit an ontology to the OOPS! web service and return parsed results.

    The ontology content is sent inline (OntologyContent field) rather than
    by URI, so the ontology does not need to be published on the web.

    Parameters
    ----------
    source : path to the ontology file (any RDF serialisation that OOPS!
        accepts; RDF/XML is safest).
    timeout : HTTP timeout in seconds.

    Returns
    -------
    OOPSResult with pitfalls, warnings, and suggestions.

    Raises
    ------
    RuntimeError if the web service is unreachable or returns an error.

    Notes
    -----
    OOPS! only implements 21 of 41 catalogue pitfalls:
        P02–P08, P10–P13, P19–P22, P24–P29.
    The remaining 20 are defined in the catalogue but not scanned.
    This is a property of the service, not of this client.

    The full report is fed back to the generator with no pitfall
    suppression (v15 design decision).
    """
    import requests  # deferred so the module loads without requests installed

    content = Path(source).read_text(encoding="utf-8")
    body = _build_oops_request_body(ontology_content=content)

    resp = requests.post(
        OOPS_ENDPOINT,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/xml"},
        timeout=timeout,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"OOPS! returned HTTP {resp.status_code}: {resp.text[:500]}"
        )

    return _parse_oops_xml(resp.text)


# ---------------------------------------------------------------------------
# Combined profile
# ---------------------------------------------------------------------------

def full_profile(
    source: str | Path,
    exclude_ns: set[str] | None = None,
    skip_oops: bool = False,
    oops_timeout: int = 120,
) -> StructuralProfile:
    """Compute the full structural profile: OntoQA metrics + OOPS! scan.

    Parameters
    ----------
    source : path to the ontology file.
    exclude_ns : namespace prefixes to exclude from OntoQA class counting.
    skip_oops : if True, skip the OOPS! web service call (useful for
        offline development or when the service is down).
    oops_timeout : HTTP timeout for the OOPS! call.

    Returns
    -------
    StructuralProfile with both components.
    """
    source_str = str(source)
    oops_result = None
    error = ""

    # OntoQA
    metrics = compute_ontoqa(source, exclude_ns)

    # OOPS!
    if not skip_oops:
        try:
            oops_result = scan_oops(source, timeout=oops_timeout)
        except Exception as e:
            error = f"OOPS! scan failed: {e}"
            oops_result = None

    return StructuralProfile(
        ontoqa=metrics,
        oops=oops_result,
        source_path=source_str,
        error=error,
    )


# ---------------------------------------------------------------------------
# Feedback report rendering (for the generation loop)
# ---------------------------------------------------------------------------

def render_feedback_report(profile: StructuralProfile) -> str:
    """Render the OOPS! portion of the feedback payload for the generator.

    This is the report shown to the model each round. Per the v15 design,
    the full OOPS! report is fed back with no pitfall suppression. OntoQA
    metrics are NOT included in the feedback (they are computed for scoring
    but are loop-coupled through the OOPS! channel, not fed back directly).

    The feedback payload has four items (Paper 1 §4.4):
      1. Reasoner report          — handled elsewhere
      2. OWL 2 DL profile report  — handled elsewhere
      3. OOPS! pitfall report     — THIS FUNCTION
      4. Conformance report       — handled elsewhere
    """
    lines = ["## OOPS! Pitfall Report", ""]

    if profile.oops is None:
        lines.append("OOPS! scan was not available for this round.")
        return "\n".join(lines)

    oops = profile.oops

    if not oops.pitfalls:
        lines.append("No pitfalls detected.")
    else:
        lines.append(
            f"{oops.total} pitfall(s) detected: "
            f"{oops.count_critical} critical, "
            f"{oops.count_important} important, "
            f"{oops.count_minor} minor."
        )
        lines.append("")

        # Group by severity for readability
        for severity in ("critical", "important", "minor"):
            group = [p for p in oops.pitfalls if p.severity == severity]
            if not group:
                continue
            lines.append(f"### {severity.capitalize()}")
            lines.append("")
            for p in sorted(group, key=lambda x: x.code):
                lines.append(f"**{p.code}: {p.name}**")
                if p.description:
                    lines.append(f"  {p.description}")
                if p.affected_elements:
                    for el in p.affected_elements[:10]:  # cap for prompt size
                        lines.append(f"  - {el}")
                    if len(p.affected_elements) > 10:
                        lines.append(
                            f"  ... and {len(p.affected_elements) - 10} more"
                        )
                lines.append("")

    if oops.warnings:
        lines.append("### Warnings")
        lines.append("")
        for w in oops.warnings:
            lines.append(f"- {w['name']}")
        lines.append("")

    if oops.suggestions:
        lines.append("### Suggestions")
        lines.append("")
        for s in oops.suggestions:
            lines.append(f"- **{s['name']}**: {s['description']}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scoring record (for the battery output)
# ---------------------------------------------------------------------------

def scoring_record(profile: StructuralProfile) -> dict:
    """Return a flat dict suitable for appending to a CSV/JSON scoring log.

    This is what the battery records per ontology-state, per round.
    Both OntoQA and OOPS! values are recorded for scoring even though
    only OOPS! is fed back.
    """
    rec = {
        "source": profile.source_path,
        "error": profile.error,
    }

    # OntoQA
    rec.update({f"ontoqa_{k}": v for k, v in profile.ontoqa.as_dict().items()})

    # OOPS!
    if profile.oops is not None:
        summary = profile.oops.summary()
        rec.update({f"oops_{k}": v for k, v in summary.items()})
    else:
        rec["oops_error"] = profile.error or "scan_skipped"

    return rec


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Run the structural profile from the command line."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Compute OntoQA structural metrics and OOPS! pitfall scan."
    )
    parser.add_argument("ontology", help="Path to the ontology file")
    parser.add_argument(
        "--exclude-ns",
        nargs="*",
        default=None,
        help="Namespace prefixes to exclude from OntoQA (e.g. "
             "http://purl.obolibrary.org/obo/BFO_)",
    )
    parser.add_argument(
        "--skip-oops",
        action="store_true",
        help="Skip the OOPS! web service call",
    )
    parser.add_argument(
        "--oops-timeout",
        type=int,
        default=120,
        help="OOPS! HTTP timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--feedback",
        action="store_true",
        help="Print the feedback report (what the generator sees)",
    )
    args = parser.parse_args()

    exclude = set(args.exclude_ns) if args.exclude_ns else None
    profile = full_profile(
        args.ontology,
        exclude_ns=exclude,
        skip_oops=args.skip_oops,
        oops_timeout=args.oops_timeout,
    )

    # Print scoring record
    print(json.dumps(scoring_record(profile), indent=2, default=str))

    # Optionally print the feedback report
    if args.feedback:
        print("\n" + "=" * 60)
        print(render_feedback_report(profile))


if __name__ == "__main__":
    main()
