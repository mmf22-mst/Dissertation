"""
Prompt assembly for construction and iteration calls.

Two prompt structures:
  1. Construction: injection + ontology view + corpus chunk
  2. Iteration: injection + ontology view + 6-item feedback payload

Four pinned allotments (overview v20, Paper 1 §4.2): injection, window,
chunk (construction calls) and feedback (iteration calls).  A construction
call carries the first three; an iteration call replaces the chunk with
the feedback payload, which feedback_payload.py has already rendered
under the FEEDBACK allotment.  Template text differs only in the
manipulated injection block.

The prompts contain no few-shot exemplars (overview Paper 1 §4.2, "No
exemplars"): apart from the chunk or the feedback, the only vocabulary
the generator receives is the Factor B injection.

Output form: the model outputs the complete revised ontology (or, when
windowing has fired, the complete revised view); the pipeline differences
it against what was shown (patch_merge.py).  The model never emits a
patch format.  Output length therefore grows with the artefact up to the
window allotment — the sizing term Part I §12 flags for the benchmark.

Dependencies: none beyond stdlib (uses string formatting)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


# ── Prompt result ───────────────────────────────────────────────────


@dataclass
class PromptResult:
    """Assembled prompt and its metadata."""

    text: str
    token_count: int
    injection_tokens: int
    ontology_tokens: int
    chunk_or_feedback_tokens: int
    # v20: which slot the fourth part occupied ("chunk" or "feedback")
    fourth_slot: str = "chunk"


# ── Construction prompt ─────────────────────────────────────────────

# The system prompt is the same for all conditions.  Only the injection
# block (between the markers) varies with Factor B.

SYSTEM_PROMPT_CONSTRUCT = """\
You are an ontology engineer building an OWL 2 DL ontology for \
electronics manufacturing from source documents.

Your task: read the corpus text provided and extend the current \
ontology to cover the concepts, relations, and constraints described \
in the text. Output the complete updated ontology in RDF/XML format.

Rules:
- Every class must have an rdfs:label and a skos:definition.
- Every object property must have an rdfs:label, rdfs:domain, and rdfs:range.
- Maintain OWL 2 DL compliance.
- Do not remove existing classes or relations unless they are incorrect.
- Do not invent concepts not supported by the source text.
- Output ONLY the RDF/XML ontology, with no other text.
"""

CONSTRUCT_TEMPLATE = """\
{system_prompt}

{injection_block}

## Current Ontology

{ontology_view}

## Source Text

{chunk_text}

Extend the ontology above to cover the concepts in the source text. \
Output the complete updated ontology in RDF/XML format.
"""


def build_construction_prompt(
    injection_text: str,
    ontology_view: str,
    chunk_text: str,
    token_counter: Callable[[str], int],
) -> PromptResult:
    """
    Assemble the construction prompt for one chunk.

    Parameters
    ----------
    injection_text
        The Factor B injection block (empty string for B0).
    ontology_view
        The serialised ontology (full or windowed).
    chunk_text
        The corpus chunk text.
    token_counter
        Callable: str → int.

    Returns
    -------
    PromptResult with the assembled text and token breakdown.
    """
    prompt = CONSTRUCT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT_CONSTRUCT,
        injection_block=injection_text if injection_text else "## (No upper ontology supplied)",
        ontology_view=ontology_view if ontology_view else "## (Empty — first chunk)",
        chunk_text=chunk_text,
    )

    return PromptResult(
        text=prompt,
        token_count=token_counter(prompt),
        injection_tokens=token_counter(injection_text) if injection_text else 0,
        ontology_tokens=token_counter(ontology_view) if ontology_view else 0,
        chunk_or_feedback_tokens=token_counter(chunk_text),
    )


# ── Iteration prompt ───────────────────────────────────────────────

SYSTEM_PROMPT_ITERATE = """\
You are an ontology engineer improving an OWL 2 DL ontology for \
electronics manufacturing. You have received automated feedback \
on the current ontology.

Your task: revise the ontology to address the issues identified \
in the feedback. Output the complete updated ontology in RDF/XML format.

Rules:
- Fix the issues identified in the feedback.
- Do not introduce new problems while fixing existing ones.
- Maintain OWL 2 DL compliance.
- Output ONLY the RDF/XML ontology, with no other text.
"""

ITERATE_TEMPLATE = """\
{system_prompt}

{injection_block}

## Current Ontology

{ontology_view}

## Feedback on Current Ontology

{feedback_payload}

Revise the ontology above to address the feedback. \
Output the complete updated ontology in RDF/XML format.
"""


class FeedbackAllotmentExceeded(ValueError):
    """The rendered payload is over the pinned FEEDBACK allotment.  The
    guard in feedback_payload.py should make this unreachable; if it
    fires, the caps were not pinned to fit."""


def build_iteration_prompt(
    injection_text: str,
    ontology_view: str,
    feedback_payload: str,
    token_counter: Callable[[str], int],
    feedback_allotment: Optional[int] = None,
) -> PromptResult:
    """
    Assemble the iteration prompt for one round.

    The feedback payload contains the 6-item battery output (plus, under
    D1, the defects routed to this sub-ontology at position 0):
      1. Reasoner report (consistency, unsatisfiable classes)
      2. OWL 2 DL profile report
      3. OOPS! pitfall report
      4. Conformance report (alignment rates)
      5. Salient-term coverage report (missing terms by genre)
      6. Genre coverage balance report

    No round counter, no history from prior rounds.  When the pinned
    feedback_allotment is supplied, the payload is checked against it;
    rendering under the allotment is feedback_payload.py's job, so an
    overflow here is a configuration error, not a runtime condition.
    """
    feedback_tokens = token_counter(feedback_payload)
    if feedback_allotment is not None and feedback_tokens > feedback_allotment:
        raise FeedbackAllotmentExceeded(
            f"feedback payload is {feedback_tokens} tokens; allotment is "
            f"{feedback_allotment}"
        )
    prompt = ITERATE_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT_ITERATE,
        injection_block=injection_text if injection_text else "## (No upper ontology supplied)",
        ontology_view=ontology_view,
        feedback_payload=feedback_payload,
    )

    return PromptResult(
        text=prompt,
        token_count=token_counter(prompt),
        injection_tokens=token_counter(injection_text) if injection_text else 0,
        ontology_tokens=token_counter(ontology_view),
        chunk_or_feedback_tokens=feedback_tokens,
        fourth_slot="feedback",
    )
