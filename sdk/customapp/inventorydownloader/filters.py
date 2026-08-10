"""Filter specification passed to inventory generators."""

from dataclasses import dataclass


@dataclass
class InventoryFilter:
    """Filters a generator must honor when producing inventory items.

    Attributes:
        id: Exact match on the item's primary identifier.
        name: Case-insensitive substring match on the item's name.
        ids: Exact match on any of the given identifiers.
    """
    id: str | None = None
    name: str | None = None
    ids: list[str] | None = None
