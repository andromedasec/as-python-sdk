"""Core inventory downloader: consumes registered generators, tracks progress,
assembles a CustomAppInventory, validates it, and exports the JSON file.
"""

import datetime
import json
import logging
from dataclasses import asdict
from pathlib import Path

from sdk.customapp.custom_app_models import (
    CustomAppInventory,
    validate_inventory_consistency,
)
from sdk.customapp.custom_app_utils import convert_to_andromeda_dict
from sdk.customapp.inventorydownloader.filters import InventoryFilter
from sdk.customapp.inventorydownloader.logging_config import get_audit_logger
from sdk.customapp.inventorydownloader.model_types import (
    MODEL_TYPE_INFO,
    ModelType,
    construct_model,
)
from sdk.customapp.inventorydownloader.progress_tracker import (
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    ProgressTracker,
)
from sdk.customapp.inventorydownloader.registry import (
    InventoryGeneratorRegistry,
    ItemError,
)

logger = logging.getLogger(__name__)

DEFAULT_CHECKPOINT_INTERVAL = 100


class BaseInventoryDownloader:
    """Downloads custom app inventory through registered generators.

    App packages register one generator per model type (see registry.py for the
    contract); this class handles orchestration, restartable progress tracking,
    audit logging, inventory assembly, validation, and JSON export.
    """

    def __init__(  # pylint: disable=too-many-arguments
            self, app_name: str, registry: InventoryGeneratorRegistry,
            output_dir: str, checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
            log_dir: str | None = None):
        self.app_name = app_name
        self.registry = registry
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_interval = checkpoint_interval
        self.tracker = ProgressTracker(output_dir)
        self.audit = get_audit_logger(log_dir or str(self.output_dir / "logs"))

    def download(self, model_types: list[ModelType] | None = None,
                 filters: InventoryFilter | None = None) -> CustomAppInventory:
        """Download all requested model types into a CustomAppInventory.

        Completed models (from a previous interrupted run) are reloaded from the
        checkpoint; in-progress models resume their generator at the saved offset.
        """
        filters = filters or InventoryFilter()
        if model_types:
            types = [ModelType(mt) for mt in model_types]
        else:
            types = self.registry.registered_types()
        inventory = CustomAppInventory()

        for model_type in types:
            generator_fn = self.registry.get(model_type)
            if generator_fn is None:
                logger.warning("No generator registered for model type '%s'; skipping",
                               model_type.value)
                continue
            self._download_model(inventory, model_type, generator_fn, filters)

        return inventory

    def _download_model(  # pylint: disable=too-many-locals
            self, inventory: CustomAppInventory, model_type: ModelType,
            generator_fn, filters: InventoryFilter) -> None:
        info = MODEL_TYPE_INFO[model_type]
        target = getattr(inventory, info.inventory_attr)
        state = self.tracker.get(model_type)

        # Reload anything a previous run already downloaded
        item_dicts = []
        if state["status"] in (STATUS_IN_PROGRESS, STATUS_COMPLETED):
            item_dicts = self.tracker.load_partial(model_type)
            for data in item_dicts:
                model = construct_model(model_type, data)
                target[info.key_fn(model)] = model

        if state["status"] == STATUS_COMPLETED:
            logger.info("Model '%s' already completed (%d items); skipping download",
                        model_type.value, len(item_dicts))
            return

        consumed = state["items_consumed"]
        failed = state["items_failed"]
        succeeded = len(item_dicts)

        if state["status"] == STATUS_IN_PROGRESS:
            self.audit.info("%s MODEL_RESUMED offset=%d", model_type.value, consumed)
            logger.info("Resuming model '%s' at offset %d", model_type.value, consumed)
        else:
            self.audit.info("%s MODEL_STARTED", model_type.value)
            logger.info("Starting model '%s' download", model_type.value)

        try:
            for item in generator_fn(filters, consumed):
                consumed += 1
                if isinstance(item, ItemError):
                    failed += 1
                    self.audit.info('%s CREATE_FAILURE id=%s error="%s"',
                                    model_type.value, item.item_id, item.error)
                    logger.debug("Item failure in '%s': id=%s error=%s",
                                 model_type.value, item.item_id, item.error)
                else:
                    try:
                        key = info.key_fn(item)
                        target[key] = item
                        item_dicts.append(asdict(item))
                        succeeded += 1
                        self.audit.info("%s CREATE_SUCCESS id=%s", model_type.value, key)
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        failed += 1
                        self.audit.info('%s CREATE_FAILURE id=%s error="%s"',
                                        model_type.value, getattr(item, "id", "<unknown>"), e)
                        logger.debug("Item consume failure in '%s': %s", model_type.value, e)
                if consumed % self.checkpoint_interval == 0:
                    self.tracker.save_items(model_type, item_dicts, consumed, failed)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Generator-level failure (e.g. server unreachable): checkpoint what we
            # have so the next run resumes here, then surface the error.
            self.tracker.save_items(model_type, item_dicts, consumed, failed)
            self.audit.info('%s MODEL_FAILED offset=%d error="%s"', model_type.value, consumed, e)
            logger.error("Model '%s' download failed at offset %d: %s",
                         model_type.value, consumed, e)
            raise

        self.tracker.save_items(model_type, item_dicts, consumed, failed)
        self.tracker.mark_completed(model_type)
        self.audit.info("%s MODEL_COMPLETED total=%d success=%d failure=%d",
                        model_type.value, consumed, succeeded, failed)
        logger.info("Model '%s' completed: total=%d success=%d failure=%d",
                    model_type.value, consumed, succeeded, failed)

    def export(self, inventory: CustomAppInventory) -> str:
        """Validate and export the inventory to {output_dir}/{app_name}-{timestamp}.json."""
        errors = validate_inventory_consistency(inventory)
        if errors:
            self.audit.info("inventory VALIDATION_ERRORS count=%d", len(errors))
            for err in errors:
                self.audit.info('inventory VALIDATION_ERROR detail="%s"', err)
            logger.warning("Inventory validation reported %d error(s); exporting anyway",
                           len(errors))

        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        output_file = self.output_dir / f"{self.app_name}-{timestamp}.json"
        try:
            result_dict = convert_to_andromeda_dict(asdict(inventory))
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, indent=2)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.audit.info('inventory EXPORT_FAILURE error="%s"', e)
            logger.error("Inventory export failed: %s", e)
            raise

        self.audit.info("inventory EXPORT_SUCCESS file=%s", output_file)
        logger.info("Inventory exported to %s", output_file)
        summary = {mt.value: len(getattr(inventory, MODEL_TYPE_INFO[mt].inventory_attr))
                   for mt in ModelType}
        logger.info("Inventory summary: %s", json.dumps(summary))
        # The checkpoint only exists to recover interrupted runs; a successful
        # export means the next run should start fresh.
        self.tracker.reset()
        return str(output_file)

    def run(self, model_types: list[ModelType] | None = None,
            filters: InventoryFilter | None = None, reset: bool = False) -> str:
        """Full pipeline: (optional checkpoint reset) -> download -> validate -> export."""
        if reset:
            self.tracker.reset()
        inventory = self.download(model_types=model_types, filters=filters)
        return self.export(inventory)
