"""
Transforms PIM assignments (from main.py output) into Andromeda eligibility payloads.

Reads a JSON file of PIM assignments (typically name_input.json),
converts them to eligibility payloads matching the Andromeda POST
/providers/{id}/eligibilities API, and writes to name_output.json.

Usage:
    python transformer.py <input_file_path>
    python transformer.py output/migration-2026-03-12/migration-2026-03-12_input.json
    # Output: output/migration-2026-03-12/migration-2026-03-12_output.json

The output contains a list of eligibility objects. Provider IDs must be
supplied when making actual API calls (providerId is a placeholder in payloads).
"""

import argparse
import json
import logging
import secrets
import sys
from collections import defaultdict
from pathlib import Path

from andromeda import _normalize_role_definition_id as normalize_role_id
from andromeda import resolve_andromeda_access_key, resolve_external_ids_to_andromeda

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Placeholders when provider IDs not provided; replace before API calls
DEFAULT_ENTRA_PROVIDER_ID = "<REPLACE_WITH_ENTRA_PROVIDER_ID>"
DEFAULT_AZURE_PROVIDER_ID = "<REPLACE_WITH_AZURE_PROVIDER_ID>"
PLACEHOLDER_ANDROMEDA_PROVIDER_ID = "REPLACE_WITH_ANDROMEDA_PROVIDER_ID"

# Value used in payload when an external ID could not be resolved in Andromeda
NOT_FOUND = "NOT_FOUND"


def _unique_eligibility_name(base: str) -> str:
    """Append a random hex suffix so eligibility names stay unique when the base label duplicates."""
    return f"{base} {secrets.token_hex(4)}"


def _resolve_or_not_found(
    external_id: str,
    provider_id: str,
    id_map: dict[tuple[str, str], str],
) -> str:
    """Return Andromeda ID if resolved for given provider, else NOT_FOUND."""
    return id_map.get((external_id, provider_id)) or NOT_FOUND


def _split_principals_by_type(
    principal_ids: list[str],
    id_map: dict[tuple[str, str], str],
    principal_id_type: dict[str, str],
    entra_provider_id: str,
) -> tuple[list[str], list[str]]:
    """Split principal IDs into eligibleUserIds and eligibleGroupIds. Principals are always Entra."""
    user_ids: list[str] = []
    group_ids: list[str] = []
    for pid in principal_ids:
        resolved = id_map.get((pid, entra_provider_id)) or NOT_FOUND
        if principal_id_type.get(pid) == "GROUP":
            group_ids.append(resolved)
        else:
            user_ids.append(resolved)
    return user_ids, group_ids


def _output_path(input_path: str) -> str:
    """Given input path (e.g. name_input.json), return name_output.json."""
    p = Path(input_path)
    stem = p.stem.replace("_input", "_output")
    return str(p.parent / f"{stem}.json")


def _transform_role_assignments(
    assignments: list[dict],
    provider_id: str,
    id_map: dict[tuple[str, str], str],
    principal_id_type: dict[str, str],
) -> list[dict]:
    """Aggregate Role (Entra directory role) assignments by roleDefinitionId. Uses id_map for resolution; NOT_FOUND for unresolved IDs."""
    by_role: dict[str, list[str]] = defaultdict(list)
    role_names: dict[str, str] = {}
    for a in assignments:
        if a.get("type") != "Role":
            continue
        rid = a.get("roleDefinitionId")
        pid = a.get("principalId")
        if rid and pid:
            by_role[rid].append(pid)
            if rid not in role_names and a.get("roleDisplayName"):
                role_names[rid] = a["roleDisplayName"]

    eligibilities = []
    for role_id, principal_ids in by_role.items():
        andromeda_role_id = _resolve_or_not_found(normalize_role_id(role_id), provider_id, id_map)
        eligible_user_ids, eligible_group_ids = _split_principals_by_type(
            list(dict.fromkeys(principal_ids)), id_map, principal_id_type, provider_id
        )
        eligibilities.append({
            "providerId": provider_id,
            "eligibilityType": "ROLE_ELIGIBILITY",
            "eligibilityConstraint": {"scopeType": "PROVIDER"},
            "eligibilityScope": {
                "scopeType": "PROVIDER",
                "scopeId": provider_id,
            },
            "roleEligibilityData": {"roleIds": [andromeda_role_id]},
            "eligibleUserIds": eligible_user_ids,
            "eligibleGroupIds": eligible_group_ids,
            "status": "INACTIVE",
            "name": _unique_eligibility_name(role_names.get(role_id, f"PIM role {role_id}")),
        })
    return eligibilities


def _transform_group_assignments(
    assignments: list[dict],
    provider_id: str,
    id_map: dict[tuple[str, str], str],
    principal_id_type: dict[str, str],
) -> list[dict]:
    """Aggregate Group (PIM for groups) assignments by groupId. Uses id_map for resolution; NOT_FOUND for unresolved IDs."""
    by_group: dict[str, list[str]] = defaultdict(list)
    group_names: dict[str, str] = {}
    for a in assignments:
        if a.get("type") != "Group":
            continue
        gid = a.get("groupId")
        pid = a.get("principalId")
        if gid and pid:
            by_group[gid].append(pid)
            if gid not in group_names and a.get("groupDisplayName"):
                group_names[gid] = a["groupDisplayName"]

    eligibilities = []
    for group_id, principal_ids in by_group.items():
        andromeda_group_id = _resolve_or_not_found(group_id, provider_id, id_map)
        eligible_user_ids, eligible_group_ids = _split_principals_by_type(
            list(dict.fromkeys(principal_ids)), id_map, principal_id_type, provider_id
        )
        eligibilities.append({
            "providerId": provider_id,
            "eligibilityType": "GROUP_ELIGIBILITY",
            "eligibilityConstraint": {"scopeType": "PROVIDER"},
            "eligibilityScope": {
                "scopeType": "PROVIDER",
                "scopeId": provider_id,
            },
            "accessGroupMatch": {
                "groupIdsMatch": {"groupIds": [andromeda_group_id]},
            },
            "eligibleUserIds": eligible_user_ids,
            "eligibleGroupIds": eligible_group_ids,
            "status": "INACTIVE",
            "name": _unique_eligibility_name(group_names.get(group_id, f"PIM group {group_id}")),
        })
    return eligibilities


def _is_subscription_scope(scope: str) -> bool:
    """True if scope is exactly /subscriptions/{id} (subscription-level)."""
    if not scope:
        return False
    parts = scope.rstrip("/").split("/")
    return len(parts) == 3 and parts[1] == "subscriptions"

_MG_SCOPE_PREFIX = "/providers/Microsoft.Management/managementGroups/"


def _is_management_group_scope(scope: str) -> bool:
    """True if scope is /providers/Microsoft.Management/managementGroups/{name} (management group level)."""
    if not scope:
        return False
    p = scope.rstrip("/")
    if not p.startswith(_MG_SCOPE_PREFIX):
        return False
    name = p[len(_MG_SCOPE_PREFIX) :]
    return bool(name) and "/" not in name

def _is_resource_group_scope(scope: str) -> bool:
    """True if scope is /subscriptions/{id}/resourceGroups/{name} (resource group level)."""
    if not scope or not scope.startswith("/subscriptions/"):
        return False
    parts = scope.rstrip("/").split("/")
    return len(parts) == 5 and parts[3] == "resourceGroups"


def _transform_azure_resource_assignments(
    assignments: list[dict],
    provider_id: str,
    id_map: dict[tuple[str, str], str],
    principal_id_type: dict[str, str],
    entra_provider_id: str,
) -> list[dict]:
    """
    Transform AzureResource assignments. Supports:
    - Subscription or management group ARM scope: aggregate by (sub_id, role_id); emit ACCOUNT-scoped
      eligibility using the subscription as accountId (management-group PIM is modeled like subscription).
    - Resource group: aggregate by (sub_id, role_id, scope_path), with eligibilityConstraint.resourceGroupIdConstraint
    Other scopes are logged as errors and skipped.
    """
    # subscription- or management-group-scoped: key = (sub_id, role_id)
    sub_key_to_users: dict[tuple[str, str], list[str]] = defaultdict(list)
    sub_key_to_name: dict[tuple[str, str], str] = {}
    # resource-group-scoped: key = (sub_id, role_id, scope_path)
    rg_key_to_users: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    rg_key_to_name: dict[tuple[str, str, str], str] = {}
    for a in assignments:
        if a.get("type") != "AzureResource":
            continue
        sub_id = a.get("subscriptionId")
        rid = a.get("roleDefinitionId")
        pid = a.get("principalId")
        scope = (a.get("scope") or "").rstrip("/")
        if not sub_id or not rid or not pid:
            continue

        if (
            _is_subscription_scope(scope)
            or scope == f"/subscriptions/{sub_id}"
            or _is_management_group_scope(scope)
        ):
            key = (sub_id, rid)
            sub_key_to_users[key].append(pid)
            if key not in sub_key_to_name and a.get("roleDisplayName"):
                sub_key_to_name[key] = a["roleDisplayName"]
        elif _is_resource_group_scope(scope):
            key = (sub_id, rid, scope)
            rg_key_to_users[key].append(pid)
            if key not in rg_key_to_name and a.get("roleDisplayName"):
                rg_key_to_name[key] = a["roleDisplayName"]
        else:
            logger.error(
                "Unsupported Azure resource scope (skipping): scope=%s assignment_id=%s",
                scope or "(empty)",
                a.get("id", "?"),
            )

    eligibilities: list[dict] = []

    for (sub_id, role_id), principal_ids in sub_key_to_users.items():
        andromeda_role_id = _resolve_or_not_found(normalize_role_id(role_id), provider_id, id_map)
        andromeda_account_id = _resolve_or_not_found(sub_id, provider_id, id_map)
        eligible_user_ids, eligible_group_ids = _split_principals_by_type(
            list(dict.fromkeys(principal_ids)), id_map, principal_id_type, entra_provider_id
        )
        role_name = sub_key_to_name.get((sub_id, role_id)) or f"role {role_id}"
        eligibilities.append({
            "providerId": provider_id,
            "eligibilityType": "ROLE_ELIGIBILITY",
            "eligibilityConstraint": {"scopeType": "ACCOUNT"},
            "eligibilityScope": {
                "scopeType": "ACCOUNT",
                "scopeId": andromeda_account_id,
            },
            "accountId": andromeda_account_id,
            "roleEligibilityData": {"roleIds": [andromeda_role_id]},
            "eligibleUserIds": eligible_user_ids,
            "eligibleGroupIds": eligible_group_ids,
            "status": "INACTIVE",
            "name": _unique_eligibility_name(f"Azure eligible assignment for {role_name} @ {sub_id}"),
        })

    for (sub_id, role_id, scope_path), principal_ids in rg_key_to_users.items():
        andromeda_role_id = _resolve_or_not_found(normalize_role_id(role_id), provider_id, id_map)
        andromeda_scope_id = _resolve_or_not_found(scope_path, provider_id, id_map)
        andromeda_account_id = _resolve_or_not_found(sub_id, provider_id, id_map)
        eligible_user_ids, eligible_group_ids = _split_principals_by_type(
            list(dict.fromkeys(principal_ids)), id_map, principal_id_type, entra_provider_id
        )
        rg_name = scope_path.split("/")[-1] if scope_path else "?"
        role_name = rg_key_to_name.get((sub_id, role_id, scope_path)) or f"role {role_id}"
        eligibilities.append({
            "providerId": provider_id,
            "eligibilityType": "ROLE_ELIGIBILITY",
            "eligibilityConstraint": {
                "scopeType": "RESOURCE_GROUP",
                "resourceGroupIdConstraint": {
                    "resourceGroupIds": [andromeda_scope_id],
                },
            },
            "eligibilityScope": {
                "scopeType": "ACCOUNT",
                "scopeId": andromeda_account_id,
            },
            "accountId": andromeda_account_id,
            "roleEligibilityData": {"roleIds": [andromeda_role_id]},
            "eligibleUserIds": eligible_user_ids,
            "eligibleGroupIds": eligible_group_ids,
            "status": "INACTIVE",
            "name": _unique_eligibility_name(f"Azure eligible assignment for {role_name} @ {rg_name}"),
        })
    return eligibilities


def _resolve_provider_ids(
    entra_provider_id: str | None = None,
    azure_provider_id: str | None = None,
    config_path: str | None = None,
) -> tuple[str, str]:
    """Resolve provider IDs: explicit args > entraConfig/azureConfig andromedaProviderId > defaults."""
    entra = entra_provider_id
    azure = azure_provider_id
    if config_path:
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            ec = cfg.get("entraConfig", {}) or {}
            ac = cfg.get("azureConfig", {}) or {}
            if not entra and ec.get("andromedaProviderId"):
                entra = ec["andromedaProviderId"]
            if not azure and ac.get("andromedaProviderId"):
                azure = ac["andromedaProviderId"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return entra or DEFAULT_ENTRA_PROVIDER_ID, azure or DEFAULT_AZURE_PROVIDER_ID


def transform(
    input_path: str,
    entra_provider_id: str | None = None,
    azure_provider_id: str | None = None,
    config_path: str | None = None,
    dry_run: bool = True,
) -> str:
    """
    Read PIM assignments from input_path, convert to Andromeda eligibilities,
    write to {stem}_output.json. Returns the output file path.

    Before transformation, resolves external IDs (user, group, role) to Andromeda IDs
    via FindObjectInInventory API. Unresolved IDs appear as NOT_FOUND in payload fields.
    whatever is transformable is included; NOT_FOUND is used for IDs not found in Andromeda.
    """
    entra_prov_id, azure_prov_id = _resolve_provider_ids(
        entra_provider_id=entra_provider_id,
        azure_provider_id=azure_provider_id,
        config_path=config_path,
    )

    with open(input_path) as f:
        assignments = json.load(f)

    if not isinstance(assignments, list):
        raise ValueError("Input JSON must be a list of PIM assignments")

    id_map: dict[tuple[str, str], str] = {}
    not_found: list[dict] = []

    api_endpoint = ""
    access_key = ""
    cfg: dict | None = None
    if config_path:
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            andromeda = cfg.get("andromeda", {}) or {}
            api_endpoint = andromeda.get("apiEndpoint", "")
            access_key = resolve_andromeda_access_key(cfg)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    principal_id_type: dict[str, str] = {}
    if api_endpoint and access_key:
        id_map, principal_id_type, not_found = resolve_external_ids_to_andromeda(
            assignments, entra_prov_id, azure_prov_id
        )
        if not_found:
            if dry_run:
                logger.info("Resolved IDs: %d in map, %d NOT_FOUND (will appear in output)", len(id_map), len(not_found))
            else:
                logger.warning("Resolved IDs: %d in map, %d NOT_FOUND (skipped, failures accounted)", len(id_map), len(not_found))
    else:
        logger.warning(
            "Andromeda apiEndpoint or access key not configured (set ANDROMEDA_ACCESS_KEY or "
            "andromeda.accessKey); skipping ID resolution. Eligibilities require resolved Andromeda IDs."
        )

    all_eligibilities: list[dict] = []

    all_eligibilities.extend(_transform_role_assignments(assignments, entra_prov_id, id_map, principal_id_type))
    all_eligibilities.extend(_transform_group_assignments(assignments, entra_prov_id, id_map, principal_id_type))
    all_eligibilities.extend(
        _transform_azure_resource_assignments(
            assignments, azure_prov_id, id_map, principal_id_type, entra_prov_id
        )
    )

    output_path = _output_path(input_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if dry_run and not_found:
        output_data: dict = {"eligibilities": all_eligibilities, "notFound": not_found}
    else:
        output_data = all_eligibilities

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(
        "Transformed %d PIM assignments into %d eligibilities, wrote to %s",
        len(assignments),
        len(all_eligibilities),
        output_path,
    )
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Transform PIM assignments to Andromeda eligibilities")
    parser.add_argument(
        "input_path",
        help="Path to JSON file with PIM assignments (output of main.py)",
    )
    parser.add_argument(
        "--entra-provider-id",
        help="Entra provider ID for role/group eligibilities (overrides entraConfig.andromedaProviderId)",
    )
    parser.add_argument(
        "--azure-provider-id",
        help="Azure provider ID for Azure resource eligibilities (overrides azureConfig.andromedaProviderId)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json (default: config.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Include notFound in output (default: True)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Skip notFound in output, log failures only",
    )
    args = parser.parse_args()

    try:
        output = transform(
            args.input_path,
            entra_provider_id=args.entra_provider_id,
            azure_provider_id=args.azure_provider_id,
            config_path=args.config,
            dry_run=args.dry_run,
        )
        print(output)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.error("%s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
