"""In-memory data store backing the mock server, loaded from a customapp mock JSON file."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "customapp" / "mock_data_v3.json"

SECTIONS = [
    "users", "nhis", "groups", "scopes", "roles",
    "permissions", "assignments", "resources", "agents",
]


class DataStore:  # pylint: disable=too-few-public-methods
    """Serves filtered, paginated slices of the mock inventory data."""

    def __init__(self, data_file: str | None = None):
        path = Path(data_file) if data_file else DEFAULT_DATA_FILE
        with open(path, encoding="utf-8") as f:
            self._data = json.load(f)
        logger.info("Loaded mock data from %s: %s", path,
                    {s: len(self._data.get(s, {})) for s in SECTIONS})

    @staticmethod
    def _item_key(item: dict) -> str:
        # permissions have no id field; their name is the identifier
        return item.get("id") or item.get("name") or ""

    def query(  # pylint: disable=too-many-arguments
            self, section: str, *, item_id: str | None = None,
            name: str | None = None, ids: list[str] | None = None,
            page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        """Return (items_for_page, total_matching) for a section."""
        items = list(self._data.get(section, {}).values())

        if item_id is not None:
            items = [i for i in items if self._item_key(i) == item_id]
        if ids:
            id_set = set(ids)
            items = [i for i in items if self._item_key(i) in id_set]
        if name is not None:
            needle = name.lower()
            items = [i for i in items if needle in (i.get("name") or "").lower()]

        total = len(items)
        start = (page - 1) * page_size
        logger.debug("query section=%s item_id=%s name=%s ids=%s page=%d page_size=%d -> total=%d",
                     section, item_id, name, ids, page, page_size, total)
        return items[start:start + page_size], total
