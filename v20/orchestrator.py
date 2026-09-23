"""
Run orchestrator — the top-level loop from the architecture sketch §2.

For every (seed, condition) pair:
  Phase 1: Construct the ontology from corpus chunks (produces R0)
  Phase 2: Iterate with feedback (produces R1–R_MAX)

Checkpoint and evaluate at every round state.

v20 (overview Part I §5, Paper 1 §4.2, §5.3):
  * The feedback payload is rendered under the pinned FEEDBACK allotment
    by the battery (feedback_payload.py); under D1 it is re-rendered per
    sub-ontology with that sub-ontology's routed defects at position 0, so
    every iteration call sits under the same ceiling.  Tokens, omitted
    counts and truncation events are logged per call.
  * Added/removed axiom and entity counts from patch-merge are logged for
    every call, construction and iteration, so the pilot can report the
    unintended-deletion rate under full-view regeneration.
  * Under D1 the sub-ontology battery (integration loss) runs only at the
    checkpoint rounds in RunConfig.checkpoint_rounds — 720 runs, not 1,800.

v19 concurrency (overview Paper 1 §4.5.3): under D1 the genre
sub-ontologies are independent until integration, so they are built in
parallel at R0 and iterated in parallel within each round.  Each genre's
own chunk sequence stays strictly sequential, and results are reassembled
in genre order before integration, so outputs are identical to sequential
execution under batch-invariant decoding.  Runs themselves are executed
concurrently by the campaign scheduler (campaign.py).

Dependencies: all pipeline modules
"""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from rdflib import URIRef

from .battery import Battery, BatteryResult
from .checkpoint import CheckpointStore, RunConfig
from .chunker import Chunk, chunk_d0, chunk_d1, chunking_stats_d0, chunking_stats_d1
from .corpus import CorpusDocument, Genre, order_documents, resolve_genre_order
from .defect_routing import route_defects
from .injection import InjectionResult, render_injection
from .integration import IntegrationResult, integrate
from .llm import LLMCaller, LLMResult
from .ontology_model import (
    Condition,
    DecompositionLevel,
    GroundingLevel,
    ManagedOntology,
)
from .patch_merge import apply_patch, replace_full
from .prompt import build_construction_prompt, build_iteration_prompt
from .windowing import WindowResult, select_window

log = logging.getLogger(__name__)


# ── Orchestrator ────────────────────────────────────────────────────


class RunOrchestrator:
    """
    Executes one (seed, condition) run: construction + iteration.

    All configuration is in RunConfig.  All I/O goes through
    CheckpointStore.  The orchestrator owns no state beyond the
    current run.
    """

    def __init__(
        self,
        config: RunConfig,
        store: CheckpointStore,
        caller: LLMCaller,
        battery: Battery,
        documents: List[CorpusDocument],
        token_counter: Callable[[str], int],
        embed_fn: Callable[[List[str]], Any],
        injection: InjectionResult,
        injection_iris: Optional[Set[URIRef]] = None,
        logmap_jar: Optional[Path] = None,
        logmap_confidence: float = 0.5,
        aml_jar: Optional[Path] = None,
        term_extractor: Optional[Callable[[str], List[str]]] = None,
        max_genre_workers: Optional[int] = None,
    ):
        self.config = config
        # None → one worker per genre (all D1 genre streams in parallel);
        # 1 → sequential, for debugging.
        self.max_genre_workers = max_genre_workers
        self.store = store
        self.caller = caller
        self.battery = battery
        self.documents = documents
        self.token_counter = token_counter
        self.embed_fn = embed_fn
        self.injection = injection
        self.injection_iris = injection_iris or set()
        self.logmap_jar = logmap_jar
        self.logmap_confidence = logmap_confidence
        self.aml_jar = aml_jar
        self.term_extractor = term_extractor

    def run(self) -> Dict[str, Any]:
        """Execute the full run.  Returns a run summary dict."""
        log.info("Starting run %s", self.config.run_id)
        t0 = time.monotonic()

        self.store.init_run(self.config)

        # Resolve genre order
        genre_order = resolve_genre_order(
            self.config.seed, list(Genre)
        )
        ordered_docs = order_documents(
            self.documents, genre_order, self.config.seed
        )
        genre_keys = [g.value for g in genre_order]

        # ── Phase 1: Construction ───────────────────────────────
        if self.config.condition.D == DecompositionLevel.D0:
            ontology, sub_ontologies = self._construct_d0(ordered_docs)
        else:
            ontology, sub_ontologies = self._construct_d1(
                ordered_docs, genre_order, genre_keys
            )

        # Checkpoint R0
        battery_result = self.battery.run(ontology)
        self._log_feedback(0, "global", battery_result)
        self._checkpoint(0, ontology, battery_result, sub_ontologies)
        log.info("R0 checkpointed for %s", self.config.run_id)

        # ── Phase 2: Iteration ──────────────────────────────────
        for r in range(1, self.config.r_max + 1):
            log.info("Round %d/%d for %s", r, self.config.r_max, self.config.run_id)

            if self.config.condition.D == DecompositionLevel.D0:
                ontology = self._iterate_d0(r, ontology, battery_result)
            else:
                ontology, sub_ontologies = self._iterate_d1(
                    r, ontology, sub_ontologies, battery_result, genre_keys
                )

            battery_result = self.battery.run(ontology)
            self._log_feedback(r, "global", battery_result)
            self._checkpoint(r, ontology, battery_result, sub_ontologies)
            log.info("R%d checkpointed for %s", r, self.config.run_id)

        wall = time.monotonic() - t0
        summary = {
            "run_id": self.config.run_id,
            "condition": self.config.condition.label,
            "seed": self.config.seed,
            "rounds_completed": self.config.r_max,
            "wall_seconds": wall,
            "final_class_count": ontology.class_count,
            "final_triple_count": ontology.triple_count,
        }
        self.store.write_run_summary(self.config, summary)
        log.info("Run %s complete in %.1f s", self.config.run_id, wall)
        return summary

    # ── Phase 1: Construction ───────────────────────────────────

    def _construct_d0(
        self, ordered_docs: List[CorpusDocument]
    ) -> tuple[ManagedOntology, Optional[Dict[str, ManagedOntology]]]:
        """Monolithic construction: sequential accumulation over chunks."""
        chunks = chunk_d0(ordered_docs, self.config.chunk_allotment, self.token_counter)
        stats = chunking_stats_d0(chunks)
        log.info("D0: %d chunks, %d straddling", stats.total_chunks, stats.straddling_chunks)

        ontology = ManagedOntology()

        for chunk in chunks:
            ontology = self._process_chunk(chunk, ontology, "construct")

        return ontology, None

    def _construct_d1(
        self,
        ordered_docs: List[CorpusDocument],
        genre_order: List[Genre],
        genre_keys: List[str],
    ) -> tuple[ManagedOntology, Dict[str, ManagedOntology]]:
        """Hierarchical construction: per-genre + integration."""
        genre_chunks = chunk_d1(
            ordered_docs, genre_order,
            self.config.chunk_allotment, self.token_counter
        )

        def build_genre(genre: Genre) -> ManagedOntology:
            onto = ManagedOntology()
            for chunk in genre_chunks.get(genre, []):
                onto = self._process_chunk(chunk, onto, "construct")
            return onto

        workers = self.max_genre_workers or max(1, len(genre_order))
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix=f"{self.config.run_id}-g"
        ) as pool:
            futures = {g: pool.submit(build_genre, g) for g in genre_order}
            # Reassemble in genre order so every downstream dict matches
            # sequential execution (integrate() also sorts genre keys).
            sub_ontologies: Dict[str, ManagedOntology] = {
                g.value: futures[g].result() for g in genre_order
            }

        # Integration
        result = integrate(
            sub_ontologies,
            logmap_jar=self.logmap_jar,
            logmap_confidence=self.logmap_confidence,
            aml_jar=self.aml_jar,
        )

        self._log_integration(0, result)
        return result.integrated, sub_ontologies

    def _process_chunk(
        self,
        chunk: Chunk,
        current_ontology: ManagedOntology,
        phase: str,
    ) -> ManagedOntology:
        """Process one chunk: windowing → prompt → LLM → patch-merge."""
        # Windowing check
        ontology_serial = current_ontology.serialise("xml")
        if self.token_counter(ontology_serial) > self.config.window_allotment:
            window_result = select_window(
                ontology=current_ontology,
                chunk_text=chunk.text,
                window_allotment=self.config.window_allotment,
                sim_threshold=self.config.sim_threshold,
                fan_out_cap=self.config.fan_out_cap,
                embed_fn=self.embed_fn,
                token_counter=self.token_counter,
                term_extractor=self.term_extractor,
                injection_iris=self.injection_iris,
            )
            view_serial = window_result.window.serialise("xml")
            windowed = True
        else:
            window_result = None
            view_serial = ontology_serial
            windowed = False

        # Build prompt
        prompt_result = build_construction_prompt(
            injection_text=self.injection.text,
            ontology_view=view_serial,
            chunk_text=chunk.text,
            token_counter=self.token_counter,
        )

        # LLM call
        llm_result = self.caller.call(prompt_result.text)

        if not llm_result.parse_success or llm_result.ontology is None:
            log.warning(
                "Parse failure at chunk %d: %s — keeping current ontology",
                chunk.chunk_index, llm_result.parse_error,
            )
            self._log_chunk(chunk, windowed, window_result, llm_result, phase)
            return current_ontology

        # Patch-merge (or full replace)
        if windowed and window_result is not None:
            patch_result = apply_patch(
                current_ontology, window_result.window, llm_result.ontology
            )
            updated = patch_result.updated_ontology
        else:
            patch_result = replace_full(llm_result.ontology)
            updated = patch_result.updated_ontology
            # v20: entity delta logged for every call, windowed or not
            before = current_ontology.all_entities()
            after = updated.all_entities()
            patch_result.added_entities = len(after - before)
            patch_result.removed_entities = len(before - after)

        self._log_chunk(chunk, windowed, window_result, llm_result, phase, patch_result)
        return updated

    # ── Phase 2: Iteration ──────────────────────────────────────

    def _iterate_d0(
        self,
        round_num: int,
        ontology: ManagedOntology,
        battery_result: BatteryResult,
    ) -> ManagedOntology:
        """One iteration round under D0."""
        return self._iterate_single(
            round_num, ontology, battery_result.feedback_text, "iterate",
            feedback_render=battery_result.feedback_render,
        )

    def _iterate_d1(
        self,
        round_num: int,
        integrated: ManagedOntology,
        sub_ontologies: Dict[str, ManagedOntology],
        battery_result: BatteryResult,
        genre_keys: List[str],
    ) -> tuple[ManagedOntology, Dict[str, ManagedOntology]]:
        """One iteration round under D1: iterate sub-ontologies, re-integrate."""
        from .integration import IRIProvenance

        # Get the IRI provenance map from integration
        int_result = integrate(
            sub_ontologies,
            logmap_jar=self.logmap_jar,
            logmap_confidence=self.logmap_confidence,
        )

        # Route defects
        routing = route_defects(
            battery_result.defects, int_result.iri_map, genre_keys
        )

        self.store.append_iteration_log(self.config, {
            "phase": "routing", "round": round_num,
            "total_defects": routing.total_defects,
            "single_source": routing.single_source_total,
            "multi_source": routing.multi_source_total,
            "unroutable": len(routing.unroutable),
        })

        # Iterate each sub-ontology with its routed feedback (in parallel).
        # v20: the payload is re-rendered per sub-ontology under the same
        # pinned caps and allotment, with routed defects at position 0.
        def iterate_genre(genre_key: str) -> ManagedOntology:
            sub_onto = sub_ontologies[genre_key]
            routed = routing.routed.get(genre_key)
            routed_defects = routed.defects if routed else []
            if battery_result.reports is not None:
                render = self.battery.render_feedback(
                    battery_result.reports, routed_defects, genre_key
                )
                genre_feedback = render.text
            else:  # legacy battery without reports — global payload only
                render = None
                genre_feedback = battery_result.feedback_text
            return self._iterate_single(
                round_num, sub_onto, genre_feedback,
                f"iterate_sub:{genre_key}", feedback_render=render,
            )

        present = [k for k in genre_keys if sub_ontologies.get(k) is not None]
        workers = self.max_genre_workers or max(1, len(present))
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix=f"{self.config.run_id}-i"
        ) as pool:
            futures = {k: pool.submit(iterate_genre, k) for k in present}
            # Reassemble in genre order (see _construct_d1).
            updated_subs: Dict[str, ManagedOntology] = {
                k: futures[k].result() for k in present
            }

        # Re-integrate
        new_result = integrate(
            updated_subs,
            logmap_jar=self.logmap_jar,
            logmap_confidence=self.logmap_confidence,
            aml_jar=self.aml_jar,
        )
        self._log_integration(round_num, new_result)

        return new_result.integrated, updated_subs

    def _iterate_single(
        self,
        round_num: int,
        ontology: ManagedOntology,
        feedback_text: str,
        target: str,
        feedback_render=None,
    ) -> ManagedOntology:
        """Iterate one ontology (D0 whole, or one D1 sub-ontology)."""
        ontology_serial = ontology.serialise("xml")

        # Windowing check
        if self.token_counter(ontology_serial) > self.config.window_allotment:
            # Iteration-round windowing (overview Part I §5): the window is
            # seeded by the feedback payload rather than a corpus chunk, so
            # the view is built around the entities the feedback names.
            window_result = select_window(
                ontology=ontology,
                chunk_text=feedback_text,
                window_allotment=self.config.window_allotment,
                sim_threshold=self.config.sim_threshold,
                fan_out_cap=self.config.fan_out_cap,
                embed_fn=self.embed_fn,
                token_counter=self.token_counter,
                term_extractor=self.term_extractor,
                injection_iris=self.injection_iris,
            )
            view_serial = window_result.window.serialise("xml")
            windowed = True
        else:
            window_result = None
            view_serial = ontology_serial
            windowed = False

        # Build prompt (checked against the pinned feedback allotment)
        prompt_result = build_iteration_prompt(
            injection_text=self.injection.text,
            ontology_view=view_serial,
            feedback_payload=feedback_text,
            token_counter=self.token_counter,
            feedback_allotment=self.config.feedback_allotment,
        )

        # LLM call
        llm_result = self.caller.call(prompt_result.text)

        if not llm_result.parse_success or llm_result.ontology is None:
            log.warning(
                "Parse failure at round %d target %s: %s — keeping current",
                round_num, target, llm_result.parse_error,
            )
            self._log_iteration(round_num, target, windowed, llm_result,
                                window_result=window_result,
                                feedback_render=feedback_render)
            return ontology

        # Patch-merge: the model returned the complete revised view; the
        # pipeline differences it against what it was shown.
        if windowed and window_result is not None:
            patch_result = apply_patch(ontology, window_result.window, llm_result.ontology)
            updated = patch_result.updated_ontology
        else:
            patch_result = replace_full(llm_result.ontology)
            updated = patch_result.updated_ontology
            # replace_full reports no patch statistics; compute the entity
            # delta here so unintended deletions are visible at both levels.
            before = ontology.all_entities()
            after = updated.all_entities()
            patch_result.added_entities = len(after - before)
            patch_result.removed_entities = len(before - after)

        self._log_iteration(round_num, target, windowed, llm_result,
                            window_result=window_result,
                            patch_result=patch_result,
                            feedback_render=feedback_render)
        return updated

    # ── Logging helpers ─────────────────────────────────────────

    def _log_chunk(self, chunk, windowed, window_result, llm_result, phase, patch_result=None):
        record = {
            "seed": self.config.seed,
            "condition": self.config.condition.label,
            "phase": phase,
            "genre": chunk.genre.value if chunk.genre else None,
            "chunk_index": chunk.chunk_index,
            "chunk_tokens": chunk.token_count,
            "straddles_genre": chunk.straddles_genre,
            "windowed": windowed,
            "prompt_tokens": llm_result.prompt_tokens,
            "completion_tokens": llm_result.completion_tokens,
            "prompt_hash": llm_result.prompt_hash,
            "response_hash": llm_result.response_hash,
            "wall_seconds": llm_result.wall_seconds,
            "parse_success": llm_result.parse_success,
        }
        if windowed and window_result is not None:
            record.update({
                "window_classes_shown": len(window_result.selected_classes),
                "window_classes_total": window_result.total_classes,
                "visibility_ratio": window_result.visibility_ratio,
            })
        if patch_result is not None:
            record.update(_patch_fields(patch_result))
        self.store.append_construction_log(self.config, record)

    def _log_iteration(self, round_num, target, windowed, llm_result,
                       window_result=None, patch_result=None,
                       feedback_render=None):
        record = {
            "seed": self.config.seed,
            "condition": self.config.condition.label,
            "phase": "iterate",
            "round": round_num,
            "target": target,
            "windowed": windowed,
            "prompt_tokens": llm_result.prompt_tokens,
            "completion_tokens": llm_result.completion_tokens,
            "prompt_hash": llm_result.prompt_hash,
            "response_hash": llm_result.response_hash,
            "wall_seconds": llm_result.wall_seconds,
            "parse_success": llm_result.parse_success,
        }
        if windowed and window_result is not None:
            record.update({
                "window_classes_shown": len(window_result.selected_classes),
                "window_classes_total": window_result.total_classes,
                "visibility_ratio": window_result.visibility_ratio,
            })
        if patch_result is not None:
            record.update(_patch_fields(patch_result))
        if feedback_render is not None:
            record.update(feedback_render.log_record())
        self.store.append_iteration_log(self.config, record)

    def _log_feedback(self, round_num: int, target: str, battery_result: BatteryResult):
        """Log the global payload's truncation record at battery time (v20)."""
        if battery_result.feedback_render is None:
            return
        record = {
            "seed": self.config.seed,
            "condition": self.config.condition.label,
            "phase": "feedback_render",
            "round": round_num,
            "target": target,
        }
        record.update(battery_result.feedback_render.log_record())
        self.store.append_iteration_log(self.config, record)

    def _log_integration(self, round_num: int, result: IntegrationResult):
        record = {
            "seed": self.config.seed,
            "condition": self.config.condition.label,
            "phase": "integrate",
            "round": round_num,
            "alignments_found": result.alignments_found,
            "iris_redirected": result.iris_redirected,
            "logmap_aml_agreement": result.logmap_aml_agreement,
        }
        record.update(result.stats)
        self.store.append_iteration_log(self.config, record)

    def _checkpoint(
        self,
        round_num: int,
        ontology: ManagedOntology,
        battery_result: BatteryResult,
        sub_ontologies: Optional[Dict[str, ManagedOntology]] = None,
    ):
        # v20: sub-ontology battery at checkpoint rounds only (integration
        # loss is descriptive; overview Part I §5, Paper 1 §5.3).
        sub_battery = None
        if sub_ontologies and round_num in self.config.checkpoint_rounds:
            sub_battery = {
                genre_key: self.battery.run_sub(sub_onto, genre_key)
                for genre_key, sub_onto in sorted(sub_ontologies.items())
            }
        self.store.save_round(
            config=self.config,
            round_num=round_num,
            ontology=ontology,
            battery=battery_result.scores,
            feedback_payload=battery_result.feedback_text,
            prompt_hash="",  # filled from last LLM call in practice
            response_hash="",
            sub_ontologies=sub_ontologies,
            sub_battery=sub_battery,
        )


def _patch_fields(patch_result) -> Dict[str, Any]:
    """Patch statistics logged for every call (v20): axiom and entity deltas."""
    return {
        "patch_added_axioms": patch_result.added_axioms,
        "patch_removed_axioms": patch_result.removed_axioms,
        "patch_added_entities": patch_result.added_entities,
        "patch_removed_entities": patch_result.removed_entities,
        "patch_violations": len(patch_result.violations),
        "orphaned_references": patch_result.orphaned_references,
    }
