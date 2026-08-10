"""Checkpoint management so an interrupted download can resume where it left off."""

import json
import logging
import shutil
from pathlib import Path

from sdk.customapp.inventorydownloader.model_types import ModelType

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"

_EMPTY_STATE = {
    "status": STATUS_PENDING,
    "items_consumed": 0,
    "items_succeeded": 0,
    "items_failed": 0,
}


class ProgressTracker:
    """Tracks per-model download progress in {output_dir}/.progress.json.

    Successfully downloaded items are persisted as plain dicts under
    {output_dir}/.partial/{model}.json so a restarted run reloads them and
    resumes the generator at offset = items_consumed.
    """

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.progress_file = self.output_dir / ".progress.json"
        self.partial_dir = self.output_dir / ".partial"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.partial_dir.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, dict] = self._load_state()

    def _load_state(self) -> dict[str, dict]:
        if self.progress_file.exists():
            try:
                with open(self.progress_file, encoding="utf-8") as f:
                    state = json.load(f)
                logger.debug("Loaded progress checkpoint from %s: %s",
                             self.progress_file, state)
                return state
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not read progress file %s (%s); starting fresh",
                               self.progress_file, e)
        return {}

    def _flush_state(self) -> None:
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)
        logger.debug("Wrote progress checkpoint: %s", self._state)

    def _partial_file(self, model_type: ModelType) -> Path:
        return self.partial_dir / f"{ModelType(model_type).value}.json"

    def get(self, model_type: ModelType) -> dict:
        """Return the checkpoint state for a model (pending state if never started)."""
        return self._state.get(ModelType(model_type).value, dict(_EMPTY_STATE))

    def save_items(self, model_type: ModelType, item_dicts: list[dict],
                   items_consumed: int, items_failed: int) -> None:
        """Checkpoint the successfully downloaded items and progress counts for a model."""
        model = ModelType(model_type).value
        with open(self._partial_file(model_type), "w", encoding="utf-8") as f:
            json.dump(item_dicts, f)
        self._state[model] = {
            "status": STATUS_IN_PROGRESS,
            "items_consumed": items_consumed,
            "items_succeeded": len(item_dicts),
            "items_failed": items_failed,
        }
        self._flush_state()
        logger.debug("Checkpointed %s: consumed=%d succeeded=%d failed=%d",
                     model, items_consumed, len(item_dicts), items_failed)

    def mark_completed(self, model_type: ModelType) -> None:
        """Mark a model's download as fully finished."""
        model = ModelType(model_type).value
        state = self._state.get(model, dict(_EMPTY_STATE))
        state["status"] = STATUS_COMPLETED
        self._state[model] = state
        self._flush_state()

    def load_partial(self, model_type: ModelType) -> list[dict]:
        """Return the item dicts checkpointed for a model by a previous run."""
        partial = self._partial_file(model_type)
        if partial.exists():
            try:
                with open(partial, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not read partial file %s (%s); re-downloading model",
                               partial, e)
        return []

    def reset(self) -> None:
        """Clear all checkpoint state (fresh download)."""
        self._state = {}
        if self.progress_file.exists():
            self.progress_file.unlink()
        if self.partial_dir.exists():
            shutil.rmtree(self.partial_dir)
        self.partial_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Progress checkpoint reset (%s)", self.output_dir)
