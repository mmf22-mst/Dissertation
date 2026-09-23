"""
Schema-constrained generative extraction — Paper 2 §4.2, §4.6.

For one checkpoint ontology-state, populate a KG from the population
sample (B).  Identical prompt template across conditions; only the
schema block varies.  The generator returns JSON lines, one assertion
per line, restricted to the schema's classes and properties; anything
outside the schema is dropped and counted (kg_model.assemble_kg).

Degenerate schemas (§4.6): an R0 ontology may have no properties, or no
classes.  With no properties nothing can be asserted, so the pipeline
returns an empty KG with `degenerate_schema` set — never an error.

The LLM is reached through the same LLMBackend abstraction as Paper 1
(llm.py: generate(prompt) -> (text, prompt_tokens, completion_tokens)),
so the serving, determinism and concurrency regime is shared.  Nothing
here parses OWL; the response is JSON lines.

Dependencies: rdflib (via kg_model), llm.LLMBackend (duck-typed).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from .chunker import chunk_d0
from .corpus import CorpusDocument
from .kg_model import ExtractedTriple, PopulatedKG, Schema, assemble_kg

SYSTEM_PROMPT_EXTRACT = """\
You are extracting facts from electronics-manufacturing documents into a \
knowledge graph. You may only use the classes and properties listed in the \
schema. Every fact must be supported by a sentence in the text.

Output one JSON object per line, and nothing else, with these keys:
  "subject": the entity mention as written in the text
  "subject_type": one class label from the schema
  "predicate": one property label from the schema
  "object": the entity mention as written, or the literal value for a datatype property
  "object_type": one class label from the schema, or null for a literal
  "evidence": the exact sentence from the text that supports the fact

Rules:
- Use only schema labels for subject_type, predicate and object_type, spelled exactly as listed.
- Do not invent entities or relations that the text does not state.
- If the text supports no facts under this schema, output nothing.
"""

EXTRACT_TEMPLATE = """\
{system_prompt}

# Schema

{schema_block}

# Text

{chunk_text}

# Facts (JSON lines)
"""


@dataclass
class ExtractionStats:
    chunks: int = 0
    calls: int = 0
    parse_failures: int = 0          # chunks whose response had no parseable line
    lines_total: int = 0
    lines_malformed: int = 0
    emitted: int = 0                 # well-formed assertions before conformance
    conformance: Dict[str, int] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    wall_seconds: float = 0.0
    corpus_tokens: int = 0
    degenerate_schema: bool = False
    prompt_hashes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        d["prompt_hashes"] = len(self.prompt_hashes)
        d["yield_per_1000_tokens"] = (1000.0 * self.conformance.get("kept", 0) / self.corpus_tokens) if self.corpus_tokens else 0.0
        return d


_REQUIRED = ("subject", "subject_type", "predicate", "object", "evidence")


def parse_extraction_response(text: str, doc_id: str, genre: str, chunk_index: int,
                              stats: ExtractionStats) -> List[ExtractedTriple]:
    """Parse JSON lines; tolerate fenced blocks and stray prose."""
    out: List[ExtractedTriple] = []
    body = re.sub(r"```(?:json)?", "", text)
    for raw in body.splitlines():
        line = raw.strip()
        if not line or not line.startswith("{"):
            continue
        stats.lines_total += 1
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            stats.lines_malformed += 1
            continue
        if not isinstance(d, dict) or any(k not in d or d[k] in (None, "") for k in _REQUIRED):
            stats.lines_malformed += 1
            continue
        obj_type = d.get("object_type")
        out.append(ExtractedTriple(
            subject=str(d["subject"]).strip(), predicate=str(d["predicate"]).strip(),
            obj=str(d["object"]).strip(), subject_type=str(d["subject_type"]).strip(),
            object_type=(str(obj_type).strip() if obj_type not in (None, "", "null") else None),
            evidence=str(d["evidence"]).strip(), doc_id=doc_id, genre=genre,
            chunk_index=chunk_index, is_literal=obj_type in (None, "", "null"),
        ))
        stats.emitted += 1
    return out


def build_extraction_prompt(schema_block: str, chunk_text: str) -> str:
    return EXTRACT_TEMPLATE.format(system_prompt=SYSTEM_PROMPT_EXTRACT,
                                   schema_block=schema_block, chunk_text=chunk_text)


def populate_state(
    ontology,
    documents: Sequence[CorpusDocument],
    backend,                                   # llm.LLMBackend: generate(prompt) -> (text, in, out)
    token_counter: Callable[[str], int],
    extraction_chunk_allotment: int,
    on_call: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> tuple[PopulatedKG, ExtractionStats]:
    """
    Populate one ontology-state from the population sample.

    Chunking reuses the Paper 1 chunker in genre-blocked order at a
    pinned extraction chunk allotment (independent of the Paper 1 chunk
    allotment; recorded in the manifest).  Each chunk is one call; the
    schema block is identical for every chunk of the state.
    """
    stats = ExtractionStats()
    schema = Schema.from_ontology(ontology)
    if schema.property_count == 0 or schema.class_count == 0:
        stats.degenerate_schema = True
        kg, tally = assemble_kg([], schema)
        stats.conformance = tally
        return kg, stats

    schema_block = schema.render()
    chunks = chunk_d0(documents, extraction_chunk_allotment, token_counter)
    stats.chunks = len(chunks)
    stats.corpus_tokens = sum(c.token_count for c in chunks)
    triples: List[ExtractedTriple] = []
    t0 = time.monotonic()
    for chunk in chunks:
        prompt = build_extraction_prompt(schema_block, chunk.text)
        text, p_tok, c_tok = backend.generate(prompt)
        stats.calls += 1
        stats.prompt_tokens += p_tok
        stats.completion_tokens += c_tok
        stats.prompt_hashes.append(hashlib.sha256(prompt.encode("utf-8")).hexdigest())
        doc_id = "+".join(chunk.source_doc_ids) if chunk.source_doc_ids else f"chunk{chunk.chunk_index}"
        genre = chunk.genre.value if chunk.genre else "+".join(chunk.genres_present)
        before = stats.emitted
        found = parse_extraction_response(text, doc_id, genre, chunk.chunk_index, stats)
        if stats.emitted == before and text.strip():
            stats.parse_failures += 1
        triples.extend(found)
        if on_call:
            on_call({"chunk_index": chunk.chunk_index, "genre": genre, "prompt_tokens": p_tok,
                     "completion_tokens": c_tok, "assertions": len(found)})
    stats.wall_seconds = time.monotonic() - t0
    kg, tally = assemble_kg(triples, schema)
    stats.conformance = tally
    return kg, stats
