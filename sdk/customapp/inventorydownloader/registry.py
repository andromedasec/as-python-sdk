"""Generator registry: the contract between the core downloader and app packages."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from sdk.customapp.inventorydownloader.filters import InventoryFilter
from sdk.customapp.inventorydownloader.model_types import ModelType


@dataclass
class ItemError:
    """Yielded by a generator in place of a model when a single item fails to transform.

    Lets the core audit the failure (with its error message) and continue the batch
    instead of aborting the whole generator.
    """
    item_id: str
    error: str


# Generator contract implemented by app packages:
#   fn(filters: InventoryFilter, offset: int = 0) -> Iterator[V2Model | ItemError]
# `offset` is the count of items already consumed in a previous run; the generator
# must skip past them so an interrupted download can resume.
GeneratorFn = Callable[[InventoryFilter, int], Iterator[Any]]


class InventoryGeneratorRegistry:
    """Maps model types to the generator functions that produce their items."""

    def __init__(self):
        self._generators: dict[ModelType, GeneratorFn] = {}

    def register(self, model_type: ModelType, generator: GeneratorFn | None = None):
        """Register a generator for a model type.

        Usable directly — register(ModelType.USERS, fn) — or as a decorator:

            @registry.register(ModelType.USERS)
            def users_generator(filters, offset=0): ...
        """
        model_type = ModelType(model_type)
        if generator is not None:
            self._generators[model_type] = generator
            return generator

        def decorator(fn: GeneratorFn) -> GeneratorFn:
            self._generators[model_type] = fn
            return fn
        return decorator

    def get(self, model_type: ModelType) -> GeneratorFn | None:
        """Return the generator registered for a model type, or None."""
        return self._generators.get(ModelType(model_type))

    def registered_types(self) -> list[ModelType]:
        """Return registered model types in canonical ModelType declaration order."""
        return [mt for mt in ModelType if mt in self._generators]
