import glob
import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from functools import partialmethod
from pathlib import Path

from sdk.customapp.custom_app_models import INVENTORY_SECTIONS as SECTIONS
from sdk.customapp.custom_app_utils import convert_to_andromeda_dict

DEFAULT_MAX_PART_BYTES = 8_000_000
MANIFEST_FILE = "data.manifest.json"


class InventoryWriter:
    """Write objects as they arrive, rotating complete JSON documents near the byte target.

    Exact file outputs use that path; directory outputs use app_name and a timestamp.
    empty_section declares a completed empty section when no objects were written.
    """

    def __init__(self, output, *, max_part_bytes=DEFAULT_MAX_PART_BYTES, app_name="inventory", empty_section=None):
        if max_part_bytes < 2:
            raise ValueError("max_part_bytes must fit an empty JSON object")
        if empty_section is not None and empty_section not in SECTIONS:
            raise ValueError(f"unknown inventory section {empty_section!r}")
        self._empty_section = empty_section
        self._target = None if os.path.isdir(output) else output
        self._dir = output if self._target is None else (os.path.dirname(output) or ".")
        self._cap, self._app = max_part_bytes, app_name
        self._parts = []
        self._file = self._section = None
        self._size, self._seen, self._closed = 0, set(), False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self.close()
        else:
            self._abort()

    def add(self, section, obj, key=None):
        if self._closed:
            raise RuntimeError("writer is closed")
        if section not in SECTIONS:
            raise ValueError(f"unknown inventory section {section!r}")
        value = convert_to_andromeda_dict(asdict(obj)) if is_dataclass(obj) else obj
        key = key or (value.get("id") if isinstance(value, dict) else None)
        if not key:
            raise ValueError(f"object in {section!r} has no id; pass key= explicitly")

        entry = json.dumps(str(key)) + ":" + json.dumps(value, separators=(",", ":"))
        header = json.dumps(section) + ":{"
        if self._file is None:
            self._open()

        changing = section != self._section
        separator = "" if changing else ","
        prefix = (("}," if self._section else "") + header) if changing else ""
        if (changing and section in self._seen) or (
            self._section is not None and self._size + len(prefix + separator + entry) + 2 > self._cap
        ):
            self._finish_part()
            self._open()
            changing, separator, prefix = True, "", header
        if changing:
            self._write(prefix)
            self._section = section
            self._seen.add(section)
        self._write(separator + entry)

    add_user = partialmethod(add, "users")
    add_nhi = partialmethod(add, "nhis")
    add_group = partialmethod(add, "groups")
    add_role = partialmethod(add, "roles")
    add_assignment = partialmethod(add, "assignments")
    add_permission = partialmethod(add, "permissions")
    add_scope = partialmethod(add, "scopes")
    add_resource = partialmethod(add, "resources")
    add_agent = partialmethod(add, "agents")
    add_child_application = partialmethod(add, "child_applications")

    def close(self):
        if self._closed:
            return list(self._parts)
        self._closed = True
        if self._file is None:
            self._open()
            if self._empty_section is not None:
                self._write(json.dumps(self._empty_section) + ":{}")
        self._finish_part()
        if len(self._parts) == 1:
            target = self._target or os.path.join(
                self._dir, f"{self._app}-{datetime.now().isoformat(timespec='seconds')}.json"
            )
            os.replace(self._parts[0], target)
            self._parts = [target]
            # A previous multipart run must not shadow the newly published single file.
            for stale in glob.glob(os.path.join(self._dir, "data.part-*.json")) + [os.path.join(self._dir, MANIFEST_FILE)]:
                if stale != target:
                    Path(stale).unlink(missing_ok=True)
        else:
            with open(os.path.join(self._dir, MANIFEST_FILE), "w", encoding="utf-8") as manifest:
                json.dump({"schema": 1, "parts": [os.path.basename(p) for p in self._parts]}, manifest)
        return list(self._parts)

    def _open(self):
        path = os.path.join(self._dir, f"data.part-{len(self._parts) + 1:04d}.json")
        self._file = open(path, "w", encoding="utf-8")
        self._parts.append(path)
        self._size, self._section, self._seen = 1, None, set()
        self._file.write("{")

    def _write(self, text):
        self._file.write(text)
        self._size += len(text)

    def _finish_part(self):
        self._file.write("}}" if self._section else "}")
        self._file.close()
        self._file, self._section = None, None

    def _abort(self):
        self._closed = True
        if self._file:
            self._file.close()
        for path in self._parts:
            try:
                os.remove(path)
            except OSError:
                pass
        self._file, self._parts = None, []
