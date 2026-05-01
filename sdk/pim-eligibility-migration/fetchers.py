"""
Azure PIM assignment fetchers.

Fetches PIM eligible assignments from Microsoft Graph and ARM APIs:
  - Entra directory role eligibilities
  - Group membership eligibilities (per groupId)
  - Azure resource role eligibilities (per subscription)
"""

import logging
import os

import requests
from azure.identity import ClientSecretCredential

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
ARM_SCOPE = "https://management.azure.com/.default"
ARM_BASE_URL = "https://management.azure.com"

# Retry Graph/ARM calls up to this many attempts only when the response is 401 / auth-related.
MAX_API_RETRIES = 3


def _is_unauthorized_response(resp: requests.Response) -> bool:
    """True if we should refresh the token and retry (401, or explicit unauthorized signal)."""
    if resp.status_code == 401:
        return True
    text = (resp.text or "").lower()
    if resp.status_code == 403 and "unauthorized" in text:
        return True
    return False

ROLE_ELIGIBILITY_URL = (
    f"{GRAPH_BASE_URL}/roleManagement/directory"
    f"/roleEligibilityScheduleInstances?$expand=roleDefinition"
)
GROUP_ELIGIBILITY_URL = (
    f"{GRAPH_BASE_URL}/identityGovernance/privilegedAccess/group"
    f"/eligibilityScheduleInstances?$expand=group"
)
GROUPS_URL = f"{GRAPH_BASE_URL}/groups?$select=id&$top=50"


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def get_graph_token(cfg: dict) -> str:
    entra = cfg["entraConfig"]
    client_id = os.environ.get("ENTRA_APP_ID", "")
    client_secret = os.environ.get("ENTRA_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("ENTRA_APP_ID and ENTRA_SECRET environment variables are required")

    credential = ClientSecretCredential(
        tenant_id=entra["azureTenantId"],
        client_id=client_id,
        client_secret=client_secret,
    )
    token = credential.get_token(GRAPH_SCOPE)
    return token.token


def get_arm_token(cfg: dict) -> str:
    azure_cfg = cfg["azureConfig"]
    client_id = os.environ.get("AZURE_APP_ID", "")
    client_secret = os.environ.get("AZURE_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("AZURE_APP_ID and AZURE_SECRET environment variables are required")

    credential = ClientSecretCredential(
        tenant_id=azure_cfg["azureTenantId"],
        client_id=client_id,
        client_secret=client_secret,
    )
    token = credential.get_token(ARM_SCOPE)
    return token.token


# ---------------------------------------------------------------------------
# Graph API helpers
# ---------------------------------------------------------------------------


def graph_get(url: str, cfg: dict, token: str | None = None) -> tuple[dict, str]:
    """
    GET Microsoft Graph. On 401 / unauthorized-style responses only, retry up to
    MAX_API_RETRIES times, refreshing the token via get_graph_token(cfg) before each retry.
    Other HTTP errors are raised immediately.
    Returns (json, bearer_token_used_for_success) for callers that paginate.
    """
    for attempt in range(MAX_API_RETRIES):
        if attempt > 0 or token is None:
            token = get_graph_token(cfg)
        assert token is not None
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json(), token
        if _is_unauthorized_response(resp) and attempt < MAX_API_RETRIES - 1:
            logger.warning(
                "Graph GET unauthorized (status %s), refreshing token (attempt %d/%d)",
                resp.status_code,
                attempt + 1,
                MAX_API_RETRIES,
            )
            continue
        raise RuntimeError(
            f"Graph API returned status {resp.status_code}: {resp.text}"
        )


def paginated_graph_get(url: str, cfg: dict, token: str | None = None) -> tuple[list[dict], str]:
    """Follows @odata.nextLink to collect all pages. Returns (items, last_token_used)."""
    items: list[dict] = []
    t = token
    while url:
        data, t = graph_get(url, cfg, token=t)
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return items, t


# ---------------------------------------------------------------------------
# ARM API helpers
# ---------------------------------------------------------------------------


def arm_get(url: str, cfg: dict, token: str | None = None) -> tuple[dict, str]:
    """
    GET Azure Resource Manager. Retries with get_arm_token(cfg) only on 401 / unauthorized,
    like graph_get.
    Returns (json, bearer_token_used_for_success).
    """
    for attempt in range(MAX_API_RETRIES):
        if attempt > 0 or token is None:
            token = get_arm_token(cfg)
        assert token is not None
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json(), token
        if _is_unauthorized_response(resp) and attempt < MAX_API_RETRIES - 1:
            logger.warning(
                "ARM GET unauthorized (status %s), refreshing token (attempt %d/%d)",
                resp.status_code,
                attempt + 1,
                MAX_API_RETRIES,
            )
            continue
        raise RuntimeError(
            f"ARM API returned status {resp.status_code}: {resp.text}"
        )


def paginated_arm_get(url: str, cfg: dict, token: str | None = None) -> tuple[list[dict], str]:
    """Follows nextLink to collect all ARM API pages. Returns (items, last_token_used)."""
    items: list[dict] = []
    t = token
    while url:
        data, t = arm_get(url, cfg, token=t)
        items.extend(data.get("value", []))
        url = data.get("nextLink")
    return items, t


# ---------------------------------------------------------------------------
# PIM assignment fetching
# ---------------------------------------------------------------------------


def fetch_role_eligibilities(cfg: dict, token: str | None = None) -> list[dict]:
    logger.info("Fetching role eligibility instances...")
    instances, _ = paginated_graph_get(ROLE_ELIGIBILITY_URL, cfg, token=token)

    assignments = []
    for inst in instances:
        a = {
            "type": "Role",
            "id": inst.get("id"),
            "principalId": inst.get("principalId"),
            "roleDefinitionId": inst.get("roleDefinitionId"),
            "directoryScopeId": inst.get("directoryScopeId"),
            "memberType": inst.get("memberType"),
            "startDateTime": inst.get("startDateTime"),
            "endDateTime": inst.get("endDateTime"),
            "roleEligibilityScheduleId": inst.get("roleEligibilityScheduleId"),
        }
        if inst.get("appScopeId"):
            a["appScopeId"] = inst["appScopeId"]

        role_def = inst.get("roleDefinition")
        if role_def:
            a["roleDisplayName"] = role_def.get("displayName")

        assignments.append(a)

    return assignments


def fetch_group_eligibilities_page_by_page(cfg: dict, graph_token: str | None = None) -> list[dict]:
    """Fetch groups 50 per page, then eligibilities for each page, then next page. Requires Group.Read.All."""
    all_assignments: list[dict] = []
    url = GROUPS_URL
    page_num = 0
    t = graph_token
    while url:
        page_num += 1
        data, t = graph_get(url, cfg, token=t)
        groups = data.get("value", [])
        group_ids = [g["id"] for g in groups if g.get("id")]
        logger.info("Page %d: fetched %d groups, checking eligibilities...", page_num, len(group_ids))
        if group_ids:
            page_assignments = fetch_group_eligibilities(cfg, group_ids, t)
            all_assignments.extend(page_assignments)
        url = data.get("@odata.nextLink")
    return all_assignments


def fetch_group_eligibilities(
    cfg: dict,
    group_ids: list[str],
    token: str | None = None,
) -> list[dict]:
    """Fetch PIM eligibility instances for each group ID."""
    assignments = []
    t = token
    for group_id in group_ids:
        logger.info("Fetching group eligibility instances for group %s", group_id)
        url = f"{GROUP_ELIGIBILITY_URL}&$filter=groupId eq '{group_id}'"
        try:
            instances, t = paginated_graph_get(url, cfg, token=t)
        except RuntimeError:
            logger.warning("Failed to fetch eligibilities for group %s", group_id)
            continue
        for inst in instances:
            a = {
                "type": "Group",
                "id": inst.get("id"),
                "principalId": inst.get("principalId"),
                "groupId": inst.get("groupId"),
                "accessId": inst.get("accessId"),
                "memberType": inst.get("memberType"),
                "startDateTime": inst.get("startDateTime"),
                "endDateTime": inst.get("endDateTime"),
            }
            group = inst.get("group")
            if group:
                a["groupDisplayName"] = group.get("displayName")
            assignments.append(a)

    return assignments


def list_subscriptions(cfg: dict, token: str | None = None) -> list[str]:
    """List all Azure subscriptions accessible to the service principal."""
    url = f"{ARM_BASE_URL}/subscriptions?api-version=2022-12-01"
    items, _ = paginated_arm_get(url, cfg, token=token)
    sub_ids = []
    logger.info("Discovered %d subscriptions", len(items))
    for sub in items:
        sub_id = sub.get("subscriptionId")
        state = sub.get("state", "")
        if sub_id and state == "Enabled":
            sub_ids.append(sub_id)
            logger.info(
                "Discovered subscription: %s (%s)",
                sub_id,
                sub.get("displayName", ""),
            )
        else:
            logger.debug(
                "Skipping subscription %s (state=%s)",
                sub_id,
                state,
            )
    return sub_ids


def fetch_azure_resource_eligibilities(
    cfg: dict,
    subscription_ids: list[str],
    token: str | None = None,
) -> list[dict]:
    """Fetch PIM role eligibility schedule instances for each subscription."""
    ARM_API_VERSION = "2020-10-01"
    assignments = []
    t = token

    for sub_id in subscription_ids:
        logger.info("Fetching Azure resource eligibility instances for subscription %s", sub_id)
        url = (
            f"{ARM_BASE_URL}/subscriptions/{sub_id}/providers/Microsoft.Authorization"
            f"/roleEligibilityScheduleInstances?api-version={ARM_API_VERSION}"
        )
        try:
            instances, t = paginated_arm_get(url, cfg, token=t)
        except RuntimeError:
            logger.warning("Failed to fetch eligibilities for subscription %s", sub_id)
            continue
        for inst in instances:
            props = inst.get("properties") or {}
            a = {
                "type": "AzureResource",
                "id": inst.get("id"),
                "subscriptionId": sub_id,
                "principalId": props.get("principalId"),
                "roleDefinitionId": props.get("roleDefinitionId"),
                "scope": props.get("scope"),
                "startDateTime": props.get("startDateTime"),
                "endDateTime": props.get("endDateTime"),
            }
            expanded = props.get("expandedProperties") or {}
            role_def = expanded.get("roleDefinition") or {}
            if role_def.get("displayName"):
                a["roleDisplayName"] = role_def["displayName"]
            principal = expanded.get("principal") or {}
            if principal.get("displayName"):
                a["principalDisplayName"] = principal["displayName"]
            assignments.append(a)

    return assignments


def fetch_pim_eligible_assignments(cfg: dict) -> list[dict]:
    """Fetch PIM eligible assignments based on entraConfig / azureConfig discovery flags.

    Controlled by config flags (all default to True):
      - entraConfig: entraRoleAssignmentsDiscoveryEnabled, groupAssignmentsDiscoveryEnabled
      - azureConfig: azureResourceAssignmentsDiscoveryEnabled
    """
    all_assignments: list[dict] = []
    entra_cfg = cfg.get("entraConfig", {}) or {}
    azure_cfg = cfg.get("azureConfig", {}) or {}

    entra_roles_enabled = entra_cfg.get("entraRoleAssignmentsDiscoveryEnabled", True)
    groups_enabled = entra_cfg.get("groupAssignmentsDiscoveryEnabled", True)
    azure_resources_enabled = azure_cfg.get("azureResourceAssignmentsDiscoveryEnabled", True)

    graph_token = get_graph_token(cfg)

    if entra_roles_enabled:
        role_assignments = fetch_role_eligibilities(cfg, graph_token)
        logger.info("Found %d role eligibility assignments", len(role_assignments))
        all_assignments.extend(role_assignments)
    else:
        logger.info("Entra role assignments discovery disabled, skipping")

    if groups_enabled:
        group_ids = entra_cfg.get("groupIds", [])
        if not group_ids:
            logger.info("No groupIds in config, fetching groups page-by-page (50 per page)...")
            group_assignments = fetch_group_eligibilities_page_by_page(cfg, graph_token)
        else:
            group_assignments = fetch_group_eligibilities(cfg, group_ids, graph_token)
        logger.info("Found %d group eligibility assignments", len(group_assignments))
        all_assignments.extend(group_assignments)
    else:
        logger.info("Group assignments discovery disabled, skipping")

    if azure_resources_enabled:
        arm_token = get_arm_token(cfg)
        subscription_ids = azure_cfg.get("subscriptionIds", [])
        if not subscription_ids:
            logger.info("No subscriptionIds configured, listing all accessible subscriptions...")
            subscription_ids = list_subscriptions(cfg, arm_token)
            logger.info("Discovered %d enabled subscriptions", len(subscription_ids))

        if subscription_ids:
            azure_assignments = fetch_azure_resource_eligibilities(cfg, subscription_ids, arm_token)
            logger.info("Found %d Azure resource eligibility assignments", len(azure_assignments))
            all_assignments.extend(azure_assignments)
        else:
            logger.info("No subscriptions found, skipping Azure resource eligibility fetch")
    else:
        logger.info("Azure resource assignments discovery disabled, skipping")

    return all_assignments
