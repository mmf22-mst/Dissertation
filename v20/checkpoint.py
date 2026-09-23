"""
Checkpoint store — saves and loads round-state directories.

Directory layout:
    campaign/
      manifest.json
      runs/
        seed_03_B2D1/
          config.json
          R00/
            ontology.owl
            battery.json
            feedback_payload.txt
            prompt_hash.txt
            response_hash.txt
            sub_ontologies/        (D1 only)
              genre_0_ncr.owl
              ...
            integration_log.json   (D1 only)
            iri_provenance.json    (D1 only)
          R01/
            ...
          construction_log.jsonl
          iteration_log.jsonl
          run_summary.json

Dependencies: rdflib (via ontology_model)
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional, Sequence

from .ontology_model import Condition, ManagedOntology


# ── Run configuration ──────────────────────────────────────────────


def checkpoint_rounds_for(r_max: int, n_after_r0: int = 3) -> Tuple[int, ...]:
    """
    The v20 checkpoint rule: R0 plus n_after_r0 rounds evenly spaced to the
    terminal round.  checkpoint_rounds_for(9) == (0, 3, 6, 9).  The count
    is fixed; the positions follow r_max if the pilot moves it.
    """
    if r_max <= 0:
        return (0,)
    pts = [0] + [round(i * r_max / n_after_r0) for i in range(1, n_after_r0 + 1)]
    return tuple(dict.fromkeys(pts))   # de-duplicate, preserve order


@dataclass
class RunConfig:
    """Immutable configuration for a single run."""

    seed: int
    condition: Condition
    r_max: int
    window_allotment: int
    chunk_allotment: int
    injection_allotment: int
    sim_threshold: float
    fan_out_cap: int
    embedding_model: str
    logmap_confidence: float
    model_id: str
    context_window: int
    thinking_mode: bool = False  # pinned in the model manifest (v19)
    # v20: fourth pinned allotment (overview Paper 1 §4.2); None disables
    # the guard in the iteration prompt (pilot before pinning only)
    feedback_allotment: Optional[int] = None
    # v20: checkpoint rounds = R0 plus three evenly spaced to r_max
    # (overview Part I §5, "Checkpoint rule"); see checkpoint_rounds_for()
    checkpoint_rounds: Tuple[int, ...] = ()

    @property
    def run_id(self) -> str:
        return f"seed_{self.seed:02d}_{self.condition.label}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["condition"] = self.condition.label
        d["run_id"] = self.run_id
        return d


# ── Checkpoint I/O ──────────────────────────────────────────────────


class CheckpointStore:
    """
    Manages the on-disk checkpoint layout for one campaign.

    All writes are explicit — nothing is written automatically.

    Thread-safe for the v19 concurrent execution model: many runs execute
    at once, and D1 genre sub-ontologies within a run are built and
    iterated in parallel.  Log appends are serialised with a lock, so each
    JSONL record is written whole.  Record order within a log file may
    differ between executions; every record carries enough keys (genre,
    chunk_index, round, target) to be sorted deterministically afterwards.
    """

    def __init__(self, campaign_dir: Path):
        self.campaign_dir = campaign_dir
        self.runs_dir = campaign_dir / "runs"
        self._log_lock = threading.Lock()

    # ── Path helpers ────────────────────────────────────────────

    def run_dir(self, config: RunConfig) -> Path:
        return self.runs_dir / config.run_id

    def round_dir(self, config: RunConfig, round_num: int) -> Path:
        return self.run_dir(config) / f"R{round_num:02d}"

    def sub_ontology_dir(self, config: RunConfig, round_num: int) -> Path:
        return self.round_dir(config, round_num) / "sub_ontologies"

    # ── Campaign-level ──────────────────────────────────────────

    def write_manifest(self, manifest: Dict[str, Any]) -> Path:
        self.campaign_dir.mkdir(parents=True, exist_ok=True)
        path = self.campaign_dir / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    # ── Run-level ───────────────────────────────────────────────

    def init_run(self, config: RunConfig) -> Path:
        """Create the run directory and write config.json."""
        d = self.run_dir(config)
        d.mkdir(parents=True, exist_ok=True)
        cfg_path = d / "config.json"
        cfg_path.write_text(
            json.dumps(config.to_dict(), indent=2), encoding="utf-8"
        )
        return d

    # ── Round-level ─────────────────────────────────────────────

    def save_round(
        self,
        config: RunConfig,
        round_num: int,
        ontology: ManagedOntology,
        battery: Dict[str, Any],
        feedback_payload: str,
        prompt_hash: str,
        response_hash: str,
        sub_ontologies: Optional[Dict[str, ManagedOntology]] = None,
        integration_log: Optional[Dict[str, Any]] = None,
        iri_provenance: Optional[Dict[str, Any]] = None,
        sub_battery: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Path:
        """Write a complete round checkpoint."""
        rd = self.round_dir(config, round_num)
        rd.mkdir(parents=True, exist_ok=True)

        # Main ontology
        owl_path = rd / "ontology.owl"
        owl_path.write_text(ontology.serialise("xml"), encoding="utf-8")

        # Battery scores
        (rd / "battery.json").write_text(
            json.dumps(battery, indent=2), encoding="utf-8"
        )

        # Feedback payload (what the model sees next round)
        (rd / "feedback_payload.txt").write_text(
            feedback_payload, encoding="utf-8"
        )

        # Hashes
        (rd / "prompt_hash.txt").write_text(prompt_hash, encoding="utf-8")
        (rd / "response_hash.txt").write_text(response_hash, encoding="utf-8")

        # D1-specific
        if sub_ontologies is not None:
            sod = self.sub_ontology_dir(config, round_num)
            sod.mkdir(parents=True, exist_ok=True)
            for genre_key, sub_onto in sorted(sub_ontologies.items()):
                sub_path = sod / f"{genre_key}.owl"
                sub_path.write_text(sub_onto.serialise("xml"), encoding="utf-8")

        if integration_log is not None:
            (rd / "integration_log.json").write_text(
                json.dumps(integration_log, indent=2), encoding="utf-8"
            )

        # v20: per-genre sub-ontology battery scores, checkpoint rounds only
        if sub_battery is not None:
            (rd / "sub_battery.json").write_text(
                json.dumps(sub_battery, indent=2), encoding="utf-8"
            )

        if iri_provenance is not None:
            (rd / "iri_provenance.json").write_text(
                json.dumps(iri_provenance, indent=2, default=_json_default),
                encoding="utf-8",
            )

        return rd

    # ── Log appending ───────────────────────────────────────────

    def append_construction_log(
        self, config: RunConfig, record: Dict[str, Any]
    ) -> None:
        path = self.run_dir(config) / "construction_log.jsonl"
        line = json.dumps(record, default=_json_default) + "\n"
        with self._log_lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line)

    def append_iteration_log(
        self, config: RunConfig, record: Dict[str, Any]
    ) -> None:
        path = self.run_dir(config) / "iteration_log.jsonl"
        line = json.dumps(record, default=_json_default) + "\n"
        with self._log_lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line)

    def write_run_summary(
        self, config: RunConfig, summary: Dict[str, Any]
    ) -> None:
        path = self.run_dir(config) / "run_summary.json"
        path.write_text(
            json.dumps(summary, indent=2, default=_json_default),
            encoding="utf-8",
        )

    # ── Reading ─────────────────────────────────────────────────

    def load_ontology(self, config: RunConfig, round_num: int) -> ManagedOntology:
        path = self.round_dir(config, round_num) / "ontology.owl"
        return ManagedOntology.from_file(path)

    def load_battery(self, config: RunConfig, round_num: int) -> Dict[str, Any]:
        path = self.round_dir(config, round_num) / "battery.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def load_config(self, run_id: str) -> Dict[str, Any]:
        path = self.runs_dir / run_id / "config.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> List[str]:
        if not self.runs_dir.exists():
            return []
        return sorted(
            d.name for d in self.runs_dir.iterdir() if d.is_dir()
        )


def _json_default(obj: Any) -> Any:
    """JSON serialiser fallback for sets, Paths, etc."""
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
