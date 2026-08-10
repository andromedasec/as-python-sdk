"""Custom app inventory downloader for paginated REST APIs.

Single-file downloader intended to be uploaded to Andromeda as a customapp
inventory downloader file (INVENTORY_DOWNLOADER_FILE_PYTHON, via
customapp_transformer_uploader.py). It pages through an application's REST
inventory APIs, transforms each item into the customapp V2 models, and exports
a CustomAppInventory JSON file using the reusable downloader framework at
sdk/customapp/inventorydownloader/ (restartable progress, audit logging,
validation).

The expected REST contract per model type (see custom_app_mock_server for a
reference server):

    GET {server}/api/{section}?page=1&page_size=20[&id=X][&name=Y][&ids=a,b]

    -> {"data": [...], "page": 1, "page_size": 20, "total": 95, "has_next": true}

Configuration:
  - Local run:      python custom_app_rest_api_downloader.py --server http://localhost:5050 \\
                        --app_name mock_app --output_dir /tmp/mock_out
  - Uploaded run:   server URL and page size come from the AS_CUSTOM_APP_METADATA
                    env var, e.g. {"server_url": "https://app.example.com", "page_size": 100}

To adapt for a real application: point RestApiClient at the vendor's API and
replace the transform_* passthrough functions with real field mappings.
"""

import argparse
import json
import logging
import os
import sys
from collections.abc import Iterator
from pathlib import Path

import requests

# Allow running as a plain script: put lib/python on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# pylint: disable=wrong-import-position
from sdk.customapp.custom_app_models import (
    CustomAppAgent,
    CustomAppAgentLicenseProfile,
    CustomAppAgentModel,
    CustomAppGroupV2,
    CustomAppMcpServer,
    CustomAppNhiV2,
    CustomAppPermissionV2,
    CustomAppResource,
    CustomAppRole,
    CustomAppRoleAssignmentV2,
    CustomAppScopeV2,
    CustomAppUserHRISAttributes,
    CustomAppUserV2,
    Tag,
)
from sdk.customapp.inventorydownloader import (
    BaseInventoryDownloader,
    InventoryFilter,
    InventoryGeneratorRegistry,
    ItemError,
    ModelType,
    setup_logging,
)

logger = logging.getLogger(__name__)

DEFAULT_SERVER = "http://host.docker.internal:5050"
DEFAULT_OUTPUT_DIR = "/tmp/customapp_rest_export"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMEOUT_SECONDS = 30

METADATA_ENV_VAR = "AS_CUSTOM_APP_METADATA"


class RestApiClient:  # pylint: disable=too-few-public-methods
    """Thin requests wrapper around the app's paginated REST endpoints.

    All HTTP calls made by this downloader live here.
    """

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    def fetch_page(  # pylint: disable=too-many-arguments
            self, resource: str, page: int, page_size: int, *,
            item_id: str | None = None, name: str | None = None,
            ids: list[str] | None = None) -> dict:
        """GET /api/{resource} and return the pagination envelope dict."""
        params = {"page": page, "page_size": page_size}
        if item_id is not None:
            params["id"] = item_id
        if name is not None:
            params["name"] = name
        if ids:
            params["ids"] = ",".join(ids)

        url = f"{self.base_url}/api/{resource}"
        logger.debug("GET %s params=%s", url, params)
        response = self._session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        envelope = response.json()
        logger.debug("GET %s -> page=%s total=%s has_next=%s returned=%d",
                     url, envelope.get("page"), envelope.get("total"),
                     envelope.get("has_next"), len(envelope.get("data", [])))
        return envelope


# --- Transformers: one raw REST API item dict -> customapp V2 model. ---
# The mock server returns V2-shaped JSON already, so these are passthrough
# constructors; a real integration would map vendor fields here.

def transform_user(raw: dict) -> CustomAppUserV2:
    """Transform a raw /api/users item into CustomAppUserV2."""
    data = raw.copy()
    if isinstance(data.get("hris_attributes"), dict):
        data["hris_attributes"] = CustomAppUserHRISAttributes(**data["hris_attributes"])
    return CustomAppUserV2(**data)


def transform_nhi(raw: dict) -> CustomAppNhiV2:
    """Transform a raw /api/nhis item into CustomAppNhiV2."""
    return CustomAppNhiV2(**raw)


def transform_group(raw: dict) -> CustomAppGroupV2:
    """Transform a raw /api/groups item into CustomAppGroupV2."""
    return CustomAppGroupV2(**raw)


def transform_scope(raw: dict) -> CustomAppScopeV2:
    """Transform a raw /api/scopes item into CustomAppScopeV2."""
    return CustomAppScopeV2(**raw)


def transform_role(raw: dict) -> CustomAppRole:
    """Transform a raw /api/roles item into CustomAppRole."""
    return CustomAppRole(**raw)


def transform_permission(raw: dict) -> CustomAppPermissionV2:
    """Transform a raw /api/permissions item into CustomAppPermissionV2."""
    return CustomAppPermissionV2(**raw)


def transform_assignment(raw: dict) -> CustomAppRoleAssignmentV2:
    """Transform a raw /api/assignments item into CustomAppRoleAssignmentV2."""
    return CustomAppRoleAssignmentV2(**raw)


def transform_resource(raw: dict) -> CustomAppResource:
    """Transform a raw /api/resources item into CustomAppResource."""
    data = raw.copy()
    if isinstance(data.get("tags"), list):
        data["tags"] = [Tag(**t) if isinstance(t, dict) else t for t in data["tags"]]
    return CustomAppResource(**data)


def transform_agent(raw: dict) -> CustomAppAgent:
    """Transform a raw /api/agents item into CustomAppAgent."""
    data = raw.copy()
    if isinstance(data.get("agent_model"), dict):
        data["agent_model"] = CustomAppAgentModel(**data["agent_model"])
    if isinstance(data.get("license_profiles"), list):
        data["license_profiles"] = [
            CustomAppAgentLicenseProfile(**p) if isinstance(p, dict) else p
            for p in data["license_profiles"]
        ]
    if isinstance(data.get("mcp_servers"), list):
        data["mcp_servers"] = [
            CustomAppMcpServer(**s) if isinstance(s, dict) else s
            for s in data["mcp_servers"]
        ]
    return CustomAppAgent(**data)


# --- Generators: fulfil the core inventorydownloader registry contract. ---

registry = InventoryGeneratorRegistry()


class _Config:  # pylint: disable=too-few-public-methods
    """Mutable module state: which server the generators talk to."""
    client: RestApiClient | None = None
    page_size: int = DEFAULT_PAGE_SIZE


def configure(base_url: str, page_size: int = DEFAULT_PAGE_SIZE) -> None:
    """Point the generators at a server. Must be called before download."""
    _Config.client = RestApiClient(base_url)
    _Config.page_size = page_size


def _paged_generator(resource: str, transform_fn):
    """Build a generator that pages through /api/{resource} honoring the resume offset."""

    def generate(filters: InventoryFilter, offset: int = 0) -> Iterator:
        client = _Config.client
        page_size = _Config.page_size
        if client is None:
            raise RuntimeError("configure(base_url) must be called before downloading")
        page = offset // page_size + 1
        skip_in_page = offset % page_size
        while True:
            envelope = client.fetch_page(
                resource, page, page_size,
                item_id=filters.id, name=filters.name, ids=filters.ids)
            for raw in envelope["data"][skip_in_page:]:
                try:
                    yield transform_fn(raw)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    failed_id = str(raw.get("id") or raw.get("name") or "<unknown>")
                    yield ItemError(item_id=failed_id, error=f"{type(e).__name__}: {e}")
            skip_in_page = 0
            if not envelope.get("has_next"):
                return
            page += 1

    return generate


registry.register(ModelType.USERS, _paged_generator("users", transform_user))
registry.register(ModelType.NHIS, _paged_generator("nhis", transform_nhi))
registry.register(ModelType.GROUPS, _paged_generator("groups", transform_group))
registry.register(ModelType.SCOPES, _paged_generator("scopes", transform_scope))
registry.register(ModelType.ROLES, _paged_generator("roles", transform_role))
registry.register(ModelType.PERMISSIONS, _paged_generator("permissions", transform_permission))
registry.register(ModelType.ASSIGNMENTS, _paged_generator("assignments", transform_assignment))
registry.register(ModelType.RESOURCES, _paged_generator("resources", transform_resource))
registry.register(ModelType.AGENTS, _paged_generator("agents", transform_agent))


# --- CLI / uploaded-execution entry point. ---

def _load_metadata() -> dict:
    """Parse the AS_CUSTOM_APP_METADATA env JSON set by the Andromeda execution env."""
    metadata_str = os.environ.get(METADATA_ENV_VAR, "")
    if not metadata_str:
        return {}
    try:
        return json.loads(metadata_str)
    except json.JSONDecodeError as e:
        logger.warning("Could not parse %s (%s); ignoring", METADATA_ENV_VAR, e)
        return {}


def parse_args():
    """Parse CLI arguments for the REST API inventory downloader."""
    parser = argparse.ArgumentParser(
        description="Download custom app inventory from a paginated REST API")
    parser.add_argument("--server", default=None,
                        help="Base URL of the inventory API server "
                             f"(default: {METADATA_ENV_VAR} server_url, else {DEFAULT_SERVER})")
    parser.add_argument("--app_name", default="mock_app")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--reset", action="store_true",
                        help="Discard the progress checkpoint and download from scratch")
    parser.add_argument("--models", default=None,
                        help="Comma-separated model types to download "
                             "(default: all registered)")
    parser.add_argument("--filter_id", default=None, help="Exact-match id filter")
    parser.add_argument("--filter_name", default=None,
                        help="Case-insensitive substring name filter")
    parser.add_argument("--filter_ids", default=None,
                        help="Comma-separated exact-match id list filter")
    parser.add_argument("--page_size", type=int, default=None,
                        help=f"Items per API page (default: {METADATA_ENV_VAR} page_size, "
                             f"else {DEFAULT_PAGE_SIZE})")
    parser.add_argument("--log_level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--log_dir", default=None,
                        help="Log directory (default: {output_dir}/logs)")
    return parser.parse_args()


def main():
    """Run the full download + export pipeline."""
    args = parse_args()
    log_dir = args.log_dir or str(Path(args.output_dir) / "logs")
    setup_logging(level=args.log_level, log_dir=log_dir)

    metadata = _load_metadata()
    server = args.server or metadata.get("server_url") or DEFAULT_SERVER
    page_size = args.page_size or metadata.get("page_size") or DEFAULT_PAGE_SIZE
    configure(server, page_size=int(page_size))
    logger.info("Downloading inventory from %s (page_size=%d)", server, int(page_size))

    model_types = None
    if args.models:
        model_types = [ModelType(m.strip()) for m in args.models.split(",") if m.strip()]

    filter_ids = None
    if args.filter_ids:
        filter_ids = [i.strip() for i in args.filter_ids.split(",") if i.strip()]

    filters = InventoryFilter(
        id=args.filter_id,
        name=args.filter_name,
        ids=filter_ids,
    )

    downloader = BaseInventoryDownloader(
        app_name=args.app_name,
        registry=registry,
        output_dir=args.output_dir,
        log_dir=log_dir,
    )
    output_file = downloader.run(model_types=model_types, filters=filters,
                                 reset=args.reset)
    logger.info("Done. Inventory file: %s", output_file)
    print(output_file)


if __name__ == "__main__":
    main()
