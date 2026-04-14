"""
PIM Eligibility Migration Script

Reads configuration from config.json, obtains Microsoft Graph and ARM tokens using
ENTRA_* and AZURE_* environment variables, and fetches PIM eligible assignments.

Fetches three types of PIM eligibilities:
  1. Entra directory role eligibilities
  2. Group membership eligibilities (lists all groups, fetches per group)
  3. Azure resource role eligibilities (requires subscriptionIds in config)

Active assignments are skipped -- only eligible assignments are collected.
Results are written to output/<run_name>_input.json.
The transformer is then run to produce output/<run_name>_output.json.

When dryRun is False, eligibilities are created in Andromeda via POST
/providers/{provider_id}/eligibilities.

When migration.cleanup is True, the script deletes eligibilities listed in
output/<run_name>_eligibilities.json via the API and rewrites that file, dropping
rows that were removed (or already absent). It then exits without fetching,
transforming, or creating new eligibilities.

After each apply run (dryRun false), the same file is rewritten with the latest
API responses for every tracked eligibility (creates/updates merge in full
response bodies).

Sample usage:

```bash
AZURE_APP_ID=<azure_app_id> AZURE_SECRET=<azure_secret> ENTRA_APP_ID=<entra_app_id> ENTRA_SECRET=<entra_secret> ANDROMEDA_ACCESS_KEY=<andromeda_access_key> python3 main.py migration-2026-03-24
```

"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from andromeda import (
    delete_policy_eligibility_mapping,
    init_client_and_login,
    resolve_andromeda_access_key,
)
from eligibility_sync import apply_eligibilities_sync
from fetchers import fetch_pim_eligible_assignments
from transformer import (
    transform,
    DEFAULT_AZURE_PROVIDER_ID,
    DEFAULT_ENTRA_PROVIDER_ID,
    PLACEHOLDER_ANDROMEDA_PROVIDER_ID,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_PLACEHOLDER_PROVIDER_IDS = frozenset(
    {
        DEFAULT_ENTRA_PROVIDER_ID,
        DEFAULT_AZURE_PROVIDER_ID,
        PLACEHOLDER_ANDROMEDA_PROVIDER_ID,
    }
)

INPUT_CONFIG_PATH = Path("config.json")
OUTPUT_DIR = Path("output")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = json.load(f)

    from_input = cfg.get("migration", {}).get("skipIngestion", False)
    if not from_input:
        errors = []
        azure_cfg = cfg.get("azureConfig", {}) or {}
        entra_cfg = cfg.get("entraConfig", {}) or {}
        if not azure_cfg.get("azureTenantId"):
            errors.append("azureConfig.azureTenantId is required")
        if not entra_cfg.get("azureTenantId"):
            errors.append("entraConfig.azureTenantId is required")
        if not os.environ.get("AZURE_APP_ID"):
            errors.append("AZURE_APP_ID environment variable is required")
        if not os.environ.get("AZURE_SECRET"):
            errors.append("AZURE_SECRET environment variable is required")
        if not os.environ.get("ENTRA_APP_ID"):
            errors.append("ENTRA_APP_ID environment variable is required")
        if not os.environ.get("ENTRA_SECRET"):
            errors.append("ENTRA_SECRET environment variable is required")
        if errors:
            raise ValueError("; ".join(errors))

    return cfg


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_pim_assignments(assignments: list[dict], output_path: str):
    with open(output_path, "w") as f:
        json.dump(assignments, f, indent=2)


# ---------------------------------------------------------------------------
# Eligibility apply (see eligibility_sync)
# ---------------------------------------------------------------------------


def delete_existing_eligibilities(eligibilities_path: Path) -> tuple[int, int]:
    """
    DELETE each eligibility in the state file via API. Removes successfully deleted rows
    from the file (and rows already gone return True from API so they are removed too).

    Returns (removed_from_file_count, kept_in_file_count).
    """
    if not eligibilities_path.exists():
        return 0, 0
    try:
        with open(eligibilities_path) as f:
            saved = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load %s for delete: %s", eligibilities_path, e)
        return 0, 0
    if not isinstance(saved, list):
        logger.warning("Invalid eligibilities file format, expected array")
        return 0, 0

    remaining: list[dict] = []
    removed = 0
    for item in saved:
        if not isinstance(item, dict):
            remaining.append(item)  # preserve unexpected elements
            continue
        prov_id = item.get("providerId")
        el_id = item.get("id")
        if prov_id and el_id:
            if delete_policy_eligibility_mapping(prov_id, el_id):
                removed += 1
            else:
                remaining.append(item)
        else:
            remaining.append(item)

    try:
        with open(eligibilities_path, "w") as f:
            json.dump(remaining, f, indent=2)
    except OSError as e:
        logger.warning("Could not rewrite %s after cleanup: %s", eligibilities_path, e)

    if removed:
        logger.info("Removed %d eligibility record(s) from API and state file", removed)
    if remaining:
        logger.info("%d eligibility record(s) still listed in %s", len(remaining), eligibilities_path)
    return removed, len(remaining)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PIM Eligibility Migration Script")
    parser.add_argument("run_name", help="Name for this run (used for output directory and file)")
    args = parser.parse_args()

    run_name = args.run_name
    assignments_path = OUTPUT_DIR / f"{run_name}_input.json"
    assignments_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading configuration...")
    try:
        cfg = load_config("config.json")
    except (ValueError, FileNotFoundError) as e:
        logger.error("Failed to load config: %s", e)
        sys.exit(1)

    dry_run = cfg.get("migration", {}).get("dryRun", True)
    from_input = cfg.get("migration", {}).get("skipIngestion", False)
    cleanup = cfg.get("migration", {}).get("cleanup", False)
    azure_tid = cfg.get("azureConfig", {}).get("azureTenantId", "")
    entra_tid = cfg.get("entraConfig", {}).get("azureTenantId", "")
    logger.info(
        "Configuration loaded: dryRun=%s, skipIngestion=%s, cleanup=%s, azureTenantId=%s, entraTenantId=%s",
        dry_run,
        from_input,
        cleanup,
        azure_tid or "(skipped)",
        entra_tid or "(skipped)",
    )

    andromeda_cfg = cfg.get("andromeda", {}) or {}
    api_endpoint = andromeda_cfg.get("apiEndpoint", "")
    access_key = resolve_andromeda_access_key(cfg)

    # Cleanup-only mode: delete eligibilities from output/<run_name>_eligibilities.json, then exit
    if cleanup:
        if api_endpoint and access_key:
            init_client_and_login(api_endpoint, access_key)
            eligibilities_path = OUTPUT_DIR / f"{run_name}_eligibilities.json"
            removed, kept = delete_existing_eligibilities(eligibilities_path)
            logger.info(
                "Cleanup complete: removed %d from API and state file, %d remaining in %s",
                removed,
                kept,
                eligibilities_path,
            )
        else:
            logger.warning(
                "Andromeda not configured for cleanup (need andromeda.apiEndpoint and "
                "ANDROMEDA_ACCESS_KEY or andromeda.accessKey)."
            )

    if from_input:
        logger.info("skipIngestion=true: loading assignments from %s (skipping Azure fetch)", assignments_path)
        try:
            with open(assignments_path) as f:
                assignments = json.load(f)
        except FileNotFoundError:
            logger.error("Input file not found: %s. Run without skipIngestion first to fetch from Azure.", assignments_path)
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in input file %s: %s", assignments_path, e)
            sys.exit(1)
        if not isinstance(assignments, list):
            logger.error("Input file must contain a JSON list of PIM assignments")
            sys.exit(1)
        logger.info("Loaded %d assignments from input file", len(assignments))
    else:
        logger.info("Fetching PIM eligible assignments from Entra...")
        try:
            assignments = fetch_pim_eligible_assignments(cfg)
        except Exception as e:
            logger.error("Failed to fetch PIM assignments: %s", e)
            sys.exit(1)
        logger.info("Total eligible assignments found: %d", len(assignments))
        logger.info("Writing PIM assignments to %s...", assignments_path)
        write_pim_assignments(assignments, str(assignments_path))

    # Initialize Andromeda client (cookie-based auth) before transform and apply
    if api_endpoint and access_key:
        init_client_and_login(api_endpoint, access_key)

    logger.info("Transforming assignments to Andromeda eligibilities...")
    entra_provider_id = cfg.get("entraConfig", {}).get("andromedaProviderId")
    azure_provider_id = cfg.get("azureConfig", {}).get("andromedaProviderId")
    output_path = transform(
        str(assignments_path),
        entra_provider_id=entra_provider_id,
        azure_provider_id=azure_provider_id,
        config_path="config.json",
        dry_run=dry_run,
    )
    logger.info("Eligibilities written to %s", output_path)

    has_valid_provider = (
        (entra_provider_id and entra_provider_id not in _PLACEHOLDER_PROVIDER_IDS)
        or (azure_provider_id and azure_provider_id not in _PLACEHOLDER_PROVIDER_IDS)
    )
    if not dry_run and has_valid_provider:
        if api_endpoint and access_key:
            eligibilities_path = OUTPUT_DIR / f"{run_name}_eligibilities.json"
            created, updated, failed, merged = apply_eligibilities_sync(
                output_path,
                eligibilities_path,
                frozenset(_PLACEHOLDER_PROVIDER_IDS),
            )
            # Persist full state: each successful create/update stores the API response body.
            with open(eligibilities_path, "w") as f:
                json.dump(merged, f, indent=2)
            logger.info(
                "Saved %d eligibility record(s) to %s",
                len(merged),
                eligibilities_path,
            )
            logger.info(
                "Applied eligibilities: %d created, %d updated, %d failed",
                created,
                updated,
                failed,
            )
        else:
            logger.warning(
                "Andromeda not configured (andromeda.apiEndpoint and ANDROMEDA_ACCESS_KEY or "
                "andromeda.accessKey); skipping POST to create eligibilities."
            )

    logger.info("Done!")


if __name__ == "__main__":
    main()
