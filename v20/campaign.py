"""
Campaign runner — executes seeds × conditions.

Entry point for the full experimental campaign or a pilot subset.

v19 (overview Part I §12, Paper 1 §4.5.3):
  - Conditions are B0, B1, B2 × D0, D1 (six cells).  CCO is not a condition.
  - Runs execute concurrently (max_concurrent_runs; default all).  Each run
    is independent, so under batch-invariant decoding concurrency changes
    throughput, never outputs.  The determinism audit verifies this.
  - corpus_dir must point at the frozen construction sample (A), not the
    full collection.  Its sample manifest is recorded in the campaign
    manifest when corpus_sample_manifest is given.
  - Thinking mode and the serving configuration are pinned per campaign
    and written to the manifest.

Dependencies: all pipeline modules
"""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from rdflib import URIRef

from .battery import Battery
from .feedback_payload import FeedbackCaps
from .checkpoint import checkpoint_rounds_for
from .checkpoint import CheckpointStore, RunConfig
from .corpus import CorpusDocument, Genre, corpus_manifest, load_corpus
from .injection import render_injection
from .llm import LLMBackend, LLMCaller
from .ontology_model import ALL_CONDITIONS, Condition, GroundingLevel, ManagedOntology
from .orchestrator import RunOrchestrator

log = logging.getLogger(__name__)


# ── Campaign configuration ──────────────────────────────────────────


@dataclass
class CampaignConfig:
    """Top-level campaign parameters."""

    campaign_dir: Path
    corpus_dir: Path
    seeds: List[int]
    conditions: List[Condition]

    # Allotments
    window_allotment: int
    chunk_allotment: int
    injection_allotment: int
    sim_threshold: float
    fan_out_cap: int
    r_max: int

    # Model
    model_id: str
    context_window: int
    embedding_model: str

    # Injection sources
    bfo_core_path: Optional[Path] = None
    iof_core_path: Optional[Path] = None

    # v20: fourth pinned allotment and the per-item feedback caps
    # (overview Paper 1 §4.2).  Pinned in task 0c with the other
    # allotments; the pilot must show feedback_overflow_steps == 0.
    feedback_allotment: Optional[int] = None
    feedback_caps: Dict[str, int] = field(default_factory=dict)

    # Execution (v19)
    max_concurrent_runs: Optional[int] = None   # None → all runs at once
    max_genre_workers: Optional[int] = None     # None → all D1 genres at once
    thinking_mode: bool = False                  # pinned in the model manifest
    serving: Dict[str, Any] = field(default_factory=dict)
    # e.g. {"runtime": "vllm", "version": "...", "batch_invariant": True,
    #       "replicas": 8, "gpus_per_replica": 1, "dtype": "bfloat16",
    #       "prefix_caching": False, "hardware": "8xB200"}

    # Frozen construction sample (A) manifest, written by corpus.write_sample
    corpus_sample_manifest: Optional[Path] = None

    # Integration tools
    logmap_jar: Optional[Path] = None
    logmap_confidence: float = 0.5
    aml_jar: Optional[Path] = None


# ── Campaign runner ─────────────────────────────────────────────────


class CampaignRunner:
    """
    Runs the full campaign or a pilot subset.

    Usage:
        config = CampaignConfig(...)
        runner = CampaignRunner(config, backend, battery, ...)
        runner.run()
    """

    def __init__(
        self,
        config: CampaignConfig,
        backend: LLMBackend,
        battery: Battery,
        token_counter: Callable[[str], int],
        embed_fn: Callable[[List[str]], Any],
        term_extractor: Optional[Callable[[str], List[str]]] = None,
        genre_map: Optional[Dict[str, Genre]] = None,
    ):
        self.config = config
        self.backend = backend
        self.battery = battery
        self.token_counter = token_counter
        self.embed_fn = embed_fn
        self.term_extractor = term_extractor
        self.genre_map = genre_map

        self.store = CheckpointStore(config.campaign_dir)
        self.caller = LLMCaller(backend)
        if getattr(backend, "enable_thinking", config.thinking_mode) != config.thinking_mode:
            raise ValueError(
                "backend.enable_thinking does not match CampaignConfig.thinking_mode; "
                "thinking mode must be identical across all conditions"
            )

        # Pre-render injections (done once)
        self._injections: Dict[GroundingLevel, Any] = {}
        self._injection_iris: Dict[GroundingLevel, Set[URIRef]] = {}

    def run(self) -> Dict[str, Any]:
        """Execute the campaign.  Returns a campaign summary."""
        log.info("=== Campaign start ===")
        t0 = time.monotonic()

        # Load corpus
        documents = load_corpus(self.config.corpus_dir, self.genre_map)
        manifest_data = corpus_manifest(documents)
        log.info(
            "Corpus loaded: %d documents, %d tokens",
            manifest_data.total_documents,
            manifest_data.total_tokens,
        )

        # Pre-render injections
        self._prepare_injections()

        # v20: apply the pinned feedback allotment and caps to the battery
        if self.config.feedback_caps:
            self.battery.feedback_caps = FeedbackCaps(**self.config.feedback_caps)
        self.battery.feedback_allotment = self.config.feedback_allotment
        if self.battery.token_counter is None:
            self.battery.token_counter = self.token_counter

        # Write campaign manifest
        campaign_manifest = {
            "config": {
                "seeds": self.config.seeds,
                "conditions": [c.label for c in self.config.conditions],
                "window_allotment": self.config.window_allotment,
                "chunk_allotment": self.config.chunk_allotment,
                "injection_allotment": self.config.injection_allotment,
                "sim_threshold": self.config.sim_threshold,
                "fan_out_cap": self.config.fan_out_cap,
                "r_max": self.config.r_max,
                "model_id": self.config.model_id,
                "context_window": self.config.context_window,
                "embedding_model": self.config.embedding_model,
                "logmap_confidence": self.config.logmap_confidence,
                "thinking_mode": self.config.thinking_mode,
                "max_concurrent_runs": self.config.max_concurrent_runs,
                "max_genre_workers": self.config.max_genre_workers,
                # v20 pinned parameters
                "feedback_allotment": self.config.feedback_allotment,
                "feedback_caps": self.battery.feedback_caps.as_dict(),
                "checkpoint_rounds": list(checkpoint_rounds_for(self.config.r_max)),
                "few_shot_exemplars": 0,
                "label_normalisation_rule": _label_rule_version(),
                "coverage_match_level": "entity_label_only",
                # v20 (cq_scorer): which CQ asset the held-out instrument used
                "cq_set": _cq_set_record(self.battery),
            },
            "serving": self.config.serving,
            "corpus": {
                "total_documents": manifest_data.total_documents,
                "total_tokens": manifest_data.total_tokens,
                "genre_counts": manifest_data.genre_counts,
                "corpus_hash": manifest_data.corpus_hash,
            },
        }
        if self.config.corpus_sample_manifest is not None:
            campaign_manifest["corpus"]["sample_manifest"] = json.loads(
                Path(self.config.corpus_sample_manifest).read_text(encoding="utf-8")
            )
        self.store.write_manifest(campaign_manifest)

        # Build the job list in a fixed order (seed-major, then condition)
        jobs = [(seed, condition) for seed in self.config.seeds
                for condition in self.config.conditions]
        total_runs = len(jobs)

        def execute(seed: int, condition: Condition) -> Dict[str, Any]:
            run_config = RunConfig(
                seed=seed,
                condition=condition,
                r_max=self.config.r_max,
                window_allotment=self.config.window_allotment,
                chunk_allotment=self.config.chunk_allotment,
                injection_allotment=self.config.injection_allotment,
                sim_threshold=self.config.sim_threshold,
                fan_out_cap=self.config.fan_out_cap,
                embedding_model=self.config.embedding_model,
                logmap_confidence=self.config.logmap_confidence,
                model_id=self.config.model_id,
                context_window=self.config.context_window,
                thinking_mode=self.config.thinking_mode,
                feedback_allotment=self.config.feedback_allotment,
                checkpoint_rounds=checkpoint_rounds_for(self.config.r_max),
            )
            orchestrator = RunOrchestrator(
                config=run_config,
                store=self.store,
                caller=self.caller,
                battery=self.battery,
                documents=documents,
                token_counter=self.token_counter,
                embed_fn=self.embed_fn,
                injection=self._injections[condition.B],
                injection_iris=self._injection_iris[condition.B],
                logmap_jar=self.config.logmap_jar,
                logmap_confidence=self.config.logmap_confidence,
                aml_jar=self.config.aml_jar,
                term_extractor=self.term_extractor,
                max_genre_workers=self.config.max_genre_workers,
            )
            return orchestrator.run()

        # Execute concurrently.  A failed run is recorded and does not stop
        # the others; it can be re-run on its own from its seed.
        summaries: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []
        workers = self.config.max_concurrent_runs or max(1, total_runs)
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="run") as pool:
            futures = {pool.submit(execute, s, c): (s, c) for s, c in jobs}
            for fut in as_completed(futures):
                seed, condition = futures[fut]
                try:
                    summaries.append(fut.result())
                    log.info("--- Finished seed=%d %s (%d/%d) ---",
                             seed, condition.label, len(summaries), total_runs)
                except Exception as exc:  # noqa: BLE001 — record and continue
                    log.exception("Run seed=%d %s failed", seed, condition.label)
                    failures.append({"seed": seed, "condition": condition.label,
                                     "error": repr(exc)})

        # Deterministic ordering in the manifest regardless of finish order
        summaries.sort(key=lambda d: d["run_id"])
        failures.sort(key=lambda d: (d["seed"], d["condition"]))
        completed = len(summaries)

        wall = time.monotonic() - t0
        campaign_summary = {
            "total_runs": total_runs,
            "completed_runs": completed,
            "failed_runs": failures,
            "wall_seconds": wall,
            "run_summaries": summaries,
        }

        # Append to manifest
        manifest_path = self.config.campaign_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["campaign_summary"] = campaign_summary
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        log.info("=== Campaign complete: %d runs in %.1f s ===", completed, wall)
        return campaign_summary

    def _prepare_injections(self) -> None:
        """Pre-render injection blocks for each grounding level."""
        for level in GroundingLevel:
            result = render_injection(
                grounding=level,
                bfo_core_path=self.config.bfo_core_path,
                iof_core_path=self.config.iof_core_path,
                injection_allotment=self.config.injection_allotment,
                token_counter=self.token_counter,
            )
            self._injections[level] = result

            # Extract injection IRIs for windowing exclusion
            if level == GroundingLevel.B0:
                self._injection_iris[level] = set()
            elif level == GroundingLevel.B1:
                path = self.config.bfo_core_path
                if path:
                    source = ManagedOntology.from_file(path)
                    self._injection_iris[level] = source.all_entities()
                else:
                    self._injection_iris[level] = set()
            elif level == GroundingLevel.B2:
                path = self.config.iof_core_path
                if path:
                    source = ManagedOntology.from_file(path)
                    self._injection_iris[level] = source.all_entities()
                else:
                    self._injection_iris[level] = set()

            log.info(
                "%s injection: %d entries (%d included, truncated=%s)",
                level.value,
                result.entries_total,
                result.entries_included,
                result.truncated,
            )


def _label_rule_version() -> str:
    """Record the CQ label-normalisation rule version in the manifest."""
    try:
        from .label_normalisation import LABEL_NORMALISATION_RULE
        return LABEL_NORMALISATION_RULE
    except Exception:  # pragma: no cover
        return "unknown"


def _cq_set_record(battery: Battery) -> Optional[Dict[str, Any]]:
    """Manifest record of the frozen CQ set, if a CQScorer is plugged in."""
    fn = getattr(battery, "cq_fn", None)
    cq_set = getattr(fn, "cq_set", None)
    if cq_set is None or not hasattr(cq_set, "manifest_record"):
        return None
    rec = cq_set.manifest_record()
    rec["injection_iris_treated_as_injected"] = len(getattr(fn, "injection_iris", ()) or ())
    rec["injected_namespace_prefixes"] = list(getattr(fn, "exclude_prefixes", ()))
    return rec
