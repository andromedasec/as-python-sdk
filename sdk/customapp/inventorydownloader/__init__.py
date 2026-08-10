"""Custom app inventory downloader framework.

App packages register one generator per model type; the core handles
orchestration, restartable progress tracking, audit logging, inventory
assembly, validation, and export. See IMPLEMENTATION_PROMPT.md.
"""

from sdk.customapp.inventorydownloader.downloader import BaseInventoryDownloader
from sdk.customapp.inventorydownloader.filters import InventoryFilter
from sdk.customapp.inventorydownloader.logging_config import (
    get_audit_logger,
    setup_logging,
)
from sdk.customapp.inventorydownloader.model_types import ModelType
from sdk.customapp.inventorydownloader.registry import (
    InventoryGeneratorRegistry,
    ItemError,
)

__all__ = [
    "BaseInventoryDownloader",
    "InventoryFilter",
    "InventoryGeneratorRegistry",
    "ItemError",
    "ModelType",
    "get_audit_logger",
    "setup_logging",
]
