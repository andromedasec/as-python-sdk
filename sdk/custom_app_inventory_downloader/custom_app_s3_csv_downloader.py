"""
Custom App S3 CSV Downloader — Full HRIS Provider Support

Downloads a CSV file from S3 using static IAM user credentials,
transforms it into the standardized CustomApp JSON format for ingestion.

Uses a plugin architecture that mirrors every resource type the ingester
supports (``services/ingester/pkg/inventory/datasources/customapp/resources``):

  * users        → CustomAppUserV2   (with full HRIS attributes)
  * nhis         → CustomAppNhiV2
  * groups       → CustomAppGroupV2  (+ auto-derived department / division groups)
  * roles        → CustomAppRole
  * assignments  → CustomAppRoleAssignmentV2
  * scopes       → CustomAppScopeV2
  * permissions  → CustomAppPermissionV2

(``group_memberships`` are embedded in groups via ``member_user_ids`` /
``member_subgroup_ids`` — no separate top-level key.)

Each plugin checks whether the CSV contains the columns it needs.
If the data is present it ingests; otherwise it logs and skips.

Auth config (via AS_CUSTOM_APP_AUTH_JSON env var):
{
    "aws_access_key_id": "AKIA...",
    "aws_secret_access_key": "...",
    "aws_region": "us-west-2",
    "s3_bucket": "my-bucket",
    "s3_key": "folder/path/users.csv"
}

Example:
    python3 custom_app_s3_csv_downloader.py --app_name=acme --output_dir=/tmp/customapp_export
"""

from __future__ import annotations

import os
import argparse
import logging
import json
import tempfile
from typing import Dict, List, Optional

from sdk.customapp.csv_transformer import CustomAppCsvTransformer
from sdk.customapp.hris_resource_plugins import (
    CsvFieldAccessor,
    HrisPlugins,
    HrisResourcePlugin,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME_PREFIX = "test"

# Default CSV column → HRIS attribute mapping.
# Overridable via ``hris_field_map`` in AS_CUSTOM_APP_METADATA.
DEFAULT_FIELD_MAP: Dict[str, str] = {
    # --- user fields ---
    "user_id": "user_id",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "username": "username",
    "active": "active",
    "category": "category",
    "org_name": "org_name",
    "business_title": "business_title",
    "manager_id": "super_ref",
    "manager_name": "managername",
    "position_title": "position_title",
    "division": "division",
    "city": "city",
    "state": "state",
    "country": "country",
    "hire_date": "hire_date",
    "termination_date": "termination_date",
    "cost_center": "cost_center",
    "department": "department",
    "team": "team",
    # --- nhi fields ---
    "nhi_id": "nhi_id",
    "nhi_username": "nhi_username",
    "nhi_name": "nhi_name",
    "nhi_owner_id": "nhi_owner_id",
    "nhi_custodian_id": "nhi_custodian_id",
    "nhi_status": "nhi_status",
    # --- role fields ---
    "role_id": "role_id",
    "role_name": "role_name",
    "role_type": "role_type",
    "role_permissions": "role_permissions",
    # --- assignment fields ---
    "assignment_id": "assignment_id",
    "principal_id": "principal_id",
    "principal_type": "principal_type",
    "assignment_role_id": "assignment_role_id",
    "scope_id": "scope_id",
    # --- scope fields ---
    "scope_name": "scope_name",
    "scope_type": "scope_type",
    "parent_scope_id": "parent_scope_id",
    # --- permission fields ---
    "permission_name": "permission_name",
    "access_level": "access_level",
    "service_name": "service_name",
    # --- group fields (explicit CSV columns) ---
    "group_id": "group_id",
    "group_name": "group_name",
    "group_member_user_ids": "group_member_user_ids",
    "group_member_subgroup_ids": "group_member_subgroup_ids",
    "group_member_nhi_ids": "group_member_nhi_ids",
}


# ═══════════════════════════════════════════════════════════════════════════
# Transformer (plugin-driven)
# ═══════════════════════════════════════════════════════════════════════════

class CustomAppInventoryTransformer(CustomAppCsvTransformer):
    """Plugin-driven transformer that extends ``CustomAppCsvTransformer``.

    Reuses the base class's CSV batch reader, validation, and export
    infrastructure from ``sdk.customapp.csv_transformer``, while adding a
    plugin-per-resource architecture for HRIS ingestion.

    Each plugin checks if its required columns are present in the CSV.
    If data is present it processes; otherwise it logs and skips.
    """

    def __init__(self, app_name: str, inventory_file: str,
                 output_dir: str = DEFAULT_OUTPUT_DIR,
                 plugins: Optional[List[HrisResourcePlugin]] = None,
                 field_map: Optional[Dict[str, str]] = None) -> None:
        super().__init__(app_name=app_name, inventory_file=inventory_file,
                         output_dir=output_dir)
        self.plugins = plugins or HrisPlugins.get_default_plugins()
        self.accessor = CsvFieldAccessor(field_map or dict(DEFAULT_FIELD_MAP))

    def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]) -> None:
        """Not used — plugin-driven transform() overrides the row-by-row pattern."""

    def transform(self) -> List[Dict[str, str]]:
        """Override base transform to use plugin architecture instead of row-by-row."""
        rows: List[dict] = []
        for batch in self.csv_batch_reader(self.inventory_file):
            rows.extend(batch)

        if not rows:
            logger.warning("CSV file is empty: %s", self.inventory_file)
            return []

        headers = list(rows[0].keys())
        logger.info("Read %d CSV rows from %s (columns: %s)",
                     len(rows), self.inventory_file, ", ".join(headers))

        for plugin in self.plugins:
            if plugin.can_run(headers, self.accessor):
                logger.info("Running plugin: %s", plugin.name)
                plugin.process(rows, self.inventory, self.accessor)
            else:
                logger.info("Skipping plugin %s — required columns not found in CSV",
                            plugin.name)

        logger.info(
            "Transformation complete: %d users, %d nhis, %d groups, "
            "%d roles, %d assignments, %d scopes, %d permissions",
            len(self.inventory.users), len(self.inventory.nhis),
            len(self.inventory.groups), len(self.inventory.roles),
            len(self.inventory.assignments), len(self.inventory.scopes),
            len(self.inventory.permissions),
        )
        return []


# ═══════════════════════════════════════════════════════════════════════════
# I/O handler
# ═══════════════════════════════════════════════════════════════════════════

class CustomAppInventoryIOHandler:
    """Handles S3 download."""

    @staticmethod
    def download_csv_from_s3(auth_config: dict, metadata: dict) -> str:
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 downloads. Install it with: pip install boto3"
            )

        aws_access_key_id = auth_config.get("aws_access_key_id")
        aws_secret_access_key = auth_config.get("aws_secret_access_key")
        aws_region = metadata.get("aws_region")
        s3_bucket = metadata.get("s3_bucket")
        file_path = metadata.get("file_path")

        missing = [
            k for k, v in {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_region": aws_region,
                "s3_bucket": s3_bucket,
                "file_path": file_path,
            }.items() if not v
        ]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        logger.info("Downloading CSV from S3 bucket=%s file_path=%s region=%s",
                     s3_bucket, file_path, aws_region)

        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
        s3_client = session.client("s3")

        tmp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        try:
            s3_client.download_file(s3_bucket, file_path, tmp_file.name)
            logger.info("Downloaded CSV to %s", tmp_file.name)
            return tmp_file.name
        except Exception:
            os.unlink(tmp_file.name)
            raise


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def setup_logging() -> None:
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(
        "%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s"
    ))
    logger.addHandler(ch)


def parse_arguments() -> argparse.Namespace:
    help_text = f"""
    Downloads a CSV from S3 and transforms it into the Andromeda custom app
    inventory JSON format using a plugin-per-resource architecture.

    Plugins (one per ingester resource type + HRIS enrichment):

        {', '.join(HrisPlugins.REGISTRY.keys())}

    Each plugin auto-detects whether the CSV has the columns it needs.
    If present → ingest.  If absent → log and skip.

    Override via AS_CUSTOM_APP_METADATA:

        "enabled_plugins": ["users","departments","roles","assignments"]
        "hris_field_map":  {{"manager_id":"supervisorEId"}}
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=help_text,
    )
    parser.add_argument("--app_name", default=DEFAULT_APP_NAME_PREFIX,
                        help="Application name prefix for output file")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR,
                        help="Output directory for JSON file")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_arguments()
    csv_path = None

    try:
        auth_json_str = os.environ.get("AS_CUSTOM_APP_AUTH_JSON", "")
        if not auth_json_str:
            raise ValueError("AS_CUSTOM_APP_AUTH_JSON env var is required")
        auth_config: dict = json.loads(auth_json_str)
        logger.info("Auth JSON found for app: %s", args.app_name.strip())

        metadata_json_str = os.environ.get("AS_CUSTOM_APP_METADATA", "")
        if not metadata_json_str:
            raise ValueError(
                "AS_CUSTOM_APP_METADATA is required (s3_bucket, file_path, aws_region)"
            )
        metadata: dict = json.loads(metadata_json_str)
        logger.info("Metadata JSON found for app: %s", args.app_name.strip())

        # Resolve plugins
        enabled_names = metadata.get("enabled_plugins")
        if isinstance(enabled_names, list) and enabled_names:
            plugins = HrisPlugins.get_plugins_by_names(enabled_names)
            logger.info("Using configured plugins: %s", [p.name for p in plugins])
        else:
            plugins = HrisPlugins.get_default_plugins()
            logger.info("Using all default plugins: %s", [p.name for p in plugins])

        # Resolve field map overrides
        field_map = dict(DEFAULT_FIELD_MAP)
        overrides = metadata.get("hris_field_map") or metadata.get("hrisFieldMap") or {}
        if isinstance(overrides, dict):
            field_map.update(overrides)

        # Download CSV from S3 to a temp file
        csv_path = CustomAppInventoryIOHandler.download_csv_from_s3(auth_config, metadata)

        # Build transformer (extends CustomAppCsvTransformer)
        # and use inherited transform_and_export() for validation + export
        transformer = CustomAppInventoryTransformer(
            app_name=args.app_name.strip(),
            inventory_file=csv_path,
            output_dir=args.output_dir.strip(),
            plugins=plugins,
            field_map=field_map,
        )
        inventory_dict, output_file = transformer.transform_and_export()
        logger.info("Transformation completed successfully: %s", output_file)

    except Exception as e:
        logger.error("Transformation failed for app %s: %s", args.app_name.strip(), e)
        raise
    finally:
        if csv_path and os.path.exists(csv_path):
            os.unlink(csv_path)
            logger.info("Cleaned up temporary CSV file")


if __name__ == "__main__":
    main()
