"""
Andromeda REST API client for PIM eligibility migration.

Contains all code that makes REST API calls to Andromeda services.
Uses cookie-based auth via POST /login/access-key (AccessKeyLogin).
Same pattern as lib/python/sdk/api_utils.py get_api_session_w_api_token.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional

import requests

logger = logging.getLogger(__name__)

# FindObjectInInventory SupportedObjectType enum values
API_TYPE_USER = 1
API_TYPE_GROUP = 2
API_TYPE_POLICY = 3
API_TYPE_SCOPE = 4

# Max external IDs per FindObjectInInventory request
RESOLVE_BATCH_SIZE = 30
RESOLVE_SCOPE_BATCH_SIZE = 5

# Page size for FindObjectInInventory (max 50 per proto validation)
FIND_OBJECT_PAGE_SIZE = 50

# Retry failed Andromeda HTTP calls this many times; call login() before each retry.
MAX_ANDROMEDA_RETRIES = 3

# Singleton Andromeda client (initialized in main.py)
_client: Optional["AndromedaClient"] = None


def resolve_andromeda_access_key(cfg: Optional[dict] = None) -> str:
    """Prefer ANDROMEDA_ACCESS_KEY; fall back to andromeda.accessKey in config when set."""
    env_key = (os.environ.get("ANDROMEDA_ACCESS_KEY") or "").strip()
    if env_key:
        return env_key
    if cfg:
        return ((cfg.get("andromeda") or {}).get("accessKey") or "").strip()
    return ""


def _maybe_use_sdk_login(api_endpoint: str, access_key: str) -> Optional[requests.Session]:
    """
    Reuse sdk.api_utils.APIUtils.get_api_session_w_api_token if available.
    Returns session with cookies from AccessKeyLogin, or None if SDK not importable.
    """
    try:
        _lib_python = Path(__file__).resolve().parent.parent.parent
        if str(_lib_python) not in sys.path:
            sys.path.insert(0, str(_lib_python))
        from sdk.api_utils import APIUtils

        api_utils = APIUtils(api_endpoint=api_endpoint)
        session = api_utils.get_api_session_w_api_token(access_key)
        if session:
            return session
    except Exception as e:
        logger.debug("Could not use SDK for login: %s", e)
    return None


class AndromedaClient:
    """
    Singleton Andromeda API client. Authenticates via AccessKeyLogin (POST /login/access-key).
    Response Set-Cookie headers are stored in the session; all subsequent requests use cookies.
    """

    def __init__(self, api_endpoint: str, access_key: str):
        self.api_endpoint = api_endpoint.rstrip("/")
        self.access_key = access_key
        self._session: Optional[requests.Session] = None

    def login(self) -> None:
        """Authenticate via POST /login/access-key. Stores cookies in session."""
        session = _maybe_use_sdk_login(self.api_endpoint, self.access_key)
        if session is None:
            session = requests.Session()
            url = f"{self.api_endpoint}/login/access-key"
            resp = session.post(
                url,
                json={"code": self.access_key},
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            resp.raise_for_status()
        self._session = session
        logger.info("Andromeda client authenticated (cookies stored)")

    def get_session(self) -> requests.Session:
        if self._session is None:
            raise RuntimeError("AndromedaClient not logged in; call login() first")
        return self._session

    def post(self, path: str, json: dict, **kwargs) -> requests.Response:
        url = f"{self.api_endpoint}{path}"
        return self.get_session().post(url, json=json, timeout=60, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.api_endpoint}{path}"
        return self.get_session().delete(url, timeout=60, **kwargs)

    def get(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.api_endpoint}{path}"
        return self.get_session().get(url, timeout=60, **kwargs)

    def put(self, path: str, json: dict, **kwargs) -> requests.Response:
        url = f"{self.api_endpoint}{path}"
        return self.get_session().put(url, json=json, timeout=60, **kwargs)


def init_client_and_login(api_endpoint: str, access_key: str) -> AndromedaClient:
    """Initialize singleton client and login. Must be called before any API usage."""
    global _client
    if not api_endpoint or not access_key:
        raise ValueError("api_endpoint and access_key are required")
    _client = AndromedaClient(api_endpoint, access_key)
    _client.login()
    return _client


def _get_response_error_details(resp: "requests.Response") -> str:
    """Extract status and body from a failed response for logging.
    Handles gRPC-gateway format where full message may be in details[].message (LocalizedMessage).
    """
    parts = [f"status={resp.status_code}"]
    try:
        body = resp.json()
        if isinstance(body, dict):
            # Prefer detailed message from gRPC details array (LocalizedMessage)
            detail_items = body.get("details") or []
            if isinstance(detail_items, list):
                for d in detail_items:
                    if isinstance(d, dict) and d.get("message"):
                        parts.append(f"details={d['message']}")
                        break
            # Fallback to top-level fields
            if len(parts) == 1:
                msg = (
                    body.get("message")
                    or body.get("error")
                    or body.get("errorMessage")
                    or (body.get("details") if isinstance(body.get("details"), str) else None)
                )
                if msg:
                    parts.append(f"body={msg}")
                else:
                    parts.append(f"body={body}")
        else:
            parts.append(f"body={body}")
    except Exception:
        text = (resp.text or "").strip()
        if text and len(text) <= 500:
            parts.append(f"body={text}")
        elif text:
            parts.append(f"body={text[:500]}...")
    return ", ".join(parts)


def get_client() -> AndromedaClient:
    if _client is None:
        raise RuntimeError("Andromeda client not initialized; call init_client_and_login() first")
    return _client


def _andromeda_request_with_retry(
    call: Callable[[], requests.Response],
    *,
    desc: str = "request",
) -> requests.Response:
    """
    Run an Andromeda HTTP call up to MAX_ANDROMEDA_RETRIES times. On failure (non-OK
    response or RequestException), call login() again (POST /login/access-key) then retry.
    """
    client = get_client()
    last_resp: Optional[requests.Response] = None
    last_exc: Optional[BaseException] = None
    for attempt in range(MAX_ANDROMEDA_RETRIES):
        try:
            if attempt > 0:
                logger.warning(
                    "Andromeda %s failed; re-authenticating via /login/access-key (attempt %d/%d)",
                    desc,
                    attempt + 1,
                    MAX_ANDROMEDA_RETRIES,
                )
                client.login()
            resp = call()
            if resp.ok:
                return resp
            last_resp = resp
            last_exc = None
        except requests.RequestException as e:
            last_exc = e
            last_resp = None
            if attempt == MAX_ANDROMEDA_RETRIES - 1:
                raise
    if last_exc is not None:
        raise last_exc
    assert last_resp is not None
    err_details = _get_response_error_details(last_resp)
    raise requests.HTTPError(f"{last_resp.reason} ({err_details})", response=last_resp)


def is_initialized() -> bool:
    return _client is not None and _client._session is not None


def _is_resource_group_scope(scope: str) -> bool:
    """True if scope is /subscriptions/{id}/resourceGroups/{name} (no further path segments)."""
    if not scope or not scope.startswith("/subscriptions/"):
        return False
    parts = scope.rstrip("/").split("/")
    return len(parts) == 5 and parts[3] == "resourceGroups"


# Azure role definition ARM path: .../providers/Microsoft.Authorization/roleDefinitions/{uuid}
_AZURE_ROLE_DEF_PREFIX = "/subscriptions/"
_AZURE_ROLE_DEF_SUFFIX = "/providers/Microsoft.Authorization/roleDefinitions/"


def _normalize_role_definition_id(rid: str) -> str:
    """Extract UUID from Azure role definition ARM path, or return as-is if already a UUID."""
    if not rid or not isinstance(rid, str):
        return rid
    if rid.startswith(_AZURE_ROLE_DEF_PREFIX) and _AZURE_ROLE_DEF_SUFFIX in rid:
        # .../roleDefinitions/{uuid} -> extract uuid
        idx = rid.rfind(_AZURE_ROLE_DEF_SUFFIX) + len(_AZURE_ROLE_DEF_SUFFIX)
        return rid[idx:].strip() or rid
    return rid


def _gather_external_ids(
    assignments: list[dict],
    entra_provider_id: str,
    azure_provider_id: str,
) -> tuple[set[str], set[str], dict[str, set[str]], set[str]]:
    """
    Collect user, group, role, and scope external IDs with provider context.
    Returns (user_ids, group_ids, role_ids_by_provider, scope_ids).
    role_ids_by_provider: provider_id -> set of role external IDs for that provider.
    scope_ids are Azure (subscription IDs and resource group ARM paths).
    """
    user_ids: set[str] = set()
    group_ids: set[str] = set()
    role_ids_entra: set[str] = set()
    role_ids_azure: set[str] = set()
    scope_ids: set[str] = set()
    for a in assignments:
        t = a.get("type")
        if t == "Role":
            if rid := a.get("roleDefinitionId"):
                role_ids_entra.add(_normalize_role_definition_id(rid))
            if pid := a.get("principalId"):
                user_ids.add(pid)
                group_ids.add(pid)
        elif t == "Group":
            if gid := a.get("groupId"):
                group_ids.add(gid)
            if pid := a.get("principalId"):
                user_ids.add(pid)
                group_ids.add(pid)  # Azure does not indicate if principal is user/group; try both
        elif t == "AzureResource":
            if rid := a.get("roleDefinitionId"):
                role_ids_azure.add(_normalize_role_definition_id(rid))
            if pid := a.get("principalId"):
                user_ids.add(pid)
                group_ids.add(pid)
            if sub_id := a.get("subscriptionId"):
                scope_ids.add(sub_id)  # Resolve subscription ID to Andromeda ACCOUNT id via inventory find
            if _is_resource_group_scope(a.get("scope") or ""):
                scope_ids.add((a.get("scope") or "").rstrip("/"))
    role_ids_by_provider = {entra_provider_id: role_ids_entra, azure_provider_id: role_ids_azure}
    return user_ids, group_ids, role_ids_by_provider, scope_ids


def find_object_inventory(object_type: int, external_ids: list[str]) -> list[dict]:
    """Call GET /inventory/find to resolve external IDs to Andromeda IDs. Uses global client.
    Makes paginated calls when total count exceeds page size."""
    type_names = {
        API_TYPE_USER: "USER",
        API_TYPE_GROUP: "GROUP",
        API_TYPE_POLICY: "POLICY",
        API_TYPE_SCOPE: "SCOPE",
    }
    type_str = type_names.get(object_type, str(object_type))
    all_results: list[dict] = []
    skip = 0

    while True:
        # Query keys follow gateway/proto field names (snake_case), not JSON body names.
        params = {
            "type": type_str,
            "external_ids": external_ids,
            "page_size": FIND_OBJECT_PAGE_SIZE,
            "skip": skip,
        }
        resp = _andromeda_request_with_retry(
            lambda p=params: get_client().get("/inventory/find", params=p),
            desc="GET /inventory/find",
        )
        data = resp.json()
        results = data.get("results", [])
        all_results.extend(results)

        page_info = data.get("pageInfo") or {}
        total_count = page_info.get("count", len(results))

        if len(results) < FIND_OBJECT_PAGE_SIZE or len(all_results) >= total_count:
            break
        skip += FIND_OBJECT_PAGE_SIZE

    logger.info(
        "FindObjectInInventory response: count=%d (total=%s)",
        len(all_results),
        (data.get("pageInfo") or {}).get("count", "?"),
    )
    return all_results


def resolve_external_ids_to_andromeda(
    assignments: list[dict],
    entra_provider_id: str,
    azure_provider_id: str,
) -> tuple[dict[tuple[str, str], str], dict[str, str], list[dict]]:
    """
    Resolve user, group, role, and scope external IDs to Andromeda IDs via FindObjectInInventory.
    Results can span multiple providers; we filter by provider_id to pick the correct object.
    Returns (id_map: (external_id, provider_id) -> andromeda_id, principal_id_type, not_found).
    Users/groups: Entra. Roles: Entra (Role/Group) or Azure (AzureResource). Scopes: Azure.
    """
    user_ids, group_ids, role_ids_by_provider, scope_ids = _gather_external_ids(
        assignments, entra_provider_id, azure_provider_id
    )
    id_map: dict[tuple[str, str], str] = {}  # (external_id, provider_id) -> andromeda_id
    principal_id_type: dict[str, str] = {}  # principalId -> "USER" | "GROUP" (only for principals)
    not_found: list[dict] = []

    def _resolve_batch(
        ext_ids: set[str],
        obj_type: int,
        type_name: str,
        provider_id: str,
        principal_ids: set[str] | None = None,
    ) -> None:
        """Resolve ext_ids for given provider. Filter FindObjectInInventory results by providerId."""
        ids_list = list(ext_ids)
        resolve_batch_size = RESOLVE_BATCH_SIZE
        if obj_type == API_TYPE_SCOPE:
            resolve_batch_size = RESOLVE_SCOPE_BATCH_SIZE
        for i in range(0, len(ids_list), resolve_batch_size):
            batch = ids_list[i : i + resolve_batch_size]
            try:
                results = find_object_inventory(obj_type, batch)
            except requests.RequestException as e:
                logger.error("FindObjectInInventory failed for %s batch: %s", type_name, e)
                for eid in batch:
                    if (eid, provider_id) not in id_map:
                        if principal_ids and type_name == "USER" and eid in principal_ids:
                            continue
                        not_found.append({
                            "type": type_name,
                            "externalId": eid,
                            "context": f"API error: {e!s}",
                        })
                continue
            for r in results:
                # Only use results for our provider (FindObjectInInventory returns across providers)
                r_provider = r.get("providerId")
                if r_provider != provider_id:
                    continue
                aid = r.get("id")
                if not aid:
                    continue
                result_identifiers: list[str] = []
                for key in ("externalId", "name"):
                    val = r.get(key)
                    if val and isinstance(val, str):
                        result_identifiers.append(val)
                for eid in batch:
                    if any(rid.lower() == eid.lower() for rid in result_identifiers):
                        id_map[(eid, provider_id)] = aid
            if principal_ids:
                for eid in batch:
                    if (eid, provider_id) in id_map and eid in principal_ids:
                        # Prefer USER over GROUP when both match (USER batch runs first)
                        if eid not in principal_id_type:
                            principal_id_type[eid] = type_name
            for eid in batch:
                if (eid, provider_id) not in id_map:
                    if principal_ids and type_name == "USER" and eid in principal_ids:
                        continue
                    not_found.append({
                        "type": type_name,
                        "externalId": eid,
                        "context": "NOT_FOUND",
                    })

    principal_ids = user_ids
    if principal_ids:
        logger.info("Resolving %d principal IDs as USER (Entra)", len(principal_ids))
        _resolve_batch(principal_ids, API_TYPE_USER, "USER", entra_provider_id, principal_ids)
    if group_ids:
        logger.info("Resolving %d group external IDs (Entra)", len(group_ids))
        _resolve_batch(group_ids, API_TYPE_GROUP, "GROUP", entra_provider_id, principal_ids)
    for prov_id, role_ids in role_ids_by_provider.items():
        if role_ids:
            logger.info("Resolving %d role/policy external IDs (provider=%s)", len(role_ids), prov_id[:8] + "...")
            _resolve_batch(role_ids, API_TYPE_POLICY, "POLICY", prov_id)
    if scope_ids:
        logger.info("Resolving %d scope external IDs (Azure)", len(scope_ids))
        _resolve_batch(scope_ids, API_TYPE_SCOPE, "SCOPE", azure_provider_id)

    return id_map, principal_id_type, not_found


def get_policy_eligibility_mapping(provider_id: str, eligibility_id: str) -> dict:
    """
    GET /providers/{provider_id}/eligibilities/{eligibility_id}.
    Returns PolicyEligibilityMapping JSON.
    """
    resp = _andromeda_request_with_retry(
        lambda: get_client().get(f"/providers/{provider_id}/eligibilities/{eligibility_id}"),
        desc=f"GET /providers/.../eligibilities/{eligibility_id}",
    )
    return resp.json()


def update_policy_eligibility_mapping(provider_id: str, eligibility_id: str, body: dict) -> dict:
    """
    PUT /providers/{provider_id}/eligibilities/{eligibility_id}.
    Body is the full PolicyEligibilityMapping (same shape as GET / create response).
    """
    resp = _andromeda_request_with_retry(
        lambda: get_client().put(
            f"/providers/{provider_id}/eligibilities/{eligibility_id}",
            json=body,
        ),
        desc=f"PUT /providers/.../eligibilities/{eligibility_id}",
    )
    return resp.json()


def create_policy_eligibility_mapping(provider_id: str, eligibility: dict) -> dict:
    """
    Create an eligibility via POST /providers/{provider_id}/eligibilities.
    Uses global Andromeda client. Returns the created PolicyEligibilityMapping from the response.
    """
    body = {k: v for k, v in eligibility.items() if k != "providerId"}
    resp = _andromeda_request_with_retry(
        lambda: get_client().post(f"/providers/{provider_id}/eligibilities", json=body),
        desc=f"POST /providers/{provider_id}/eligibilities",
    )
    return resp.json()


def delete_policy_eligibility_mapping(provider_id: str, eligibility_id: str) -> bool:
    """
    Delete an eligibility via DELETE /providers/{provider_id}/eligibilities/{eligibility_id}.
    Uses global Andromeda client. Logs but does not raise on failure.

    Returns True if the eligibility is gone (2xx or 404). Returns False on other errors.
    """
    path = f"/providers/{provider_id}/eligibilities/{eligibility_id}"
    client = get_client()
    last_resp: Optional[requests.Response] = None
    for attempt in range(MAX_ANDROMEDA_RETRIES):
        try:
            if attempt > 0:
                logger.warning(
                    "Andromeda DELETE %s failed; re-authenticating via /login/access-key (attempt %d/%d)",
                    path,
                    attempt + 1,
                    MAX_ANDROMEDA_RETRIES,
                )
                client.login()
            resp = get_client().delete(path)
            last_resp = resp
            if resp.status_code == 404:
                logger.info(
                    "Eligibility %s not found on provider %s (404); treating as already deleted",
                    eligibility_id,
                    provider_id,
                )
                return True
            if resp.ok:
                logger.info("Deleted eligibility %s from provider %s", eligibility_id, provider_id)
                return True
        except requests.RequestException as e:
            if attempt == MAX_ANDROMEDA_RETRIES - 1:
                logger.warning("Failed to delete eligibility %s: %s", eligibility_id, e)
                return False
    if last_resp is not None:
        err_details = _get_response_error_details(last_resp)
        logger.warning(
            "Failed to delete eligibility %s: %s %s",
            eligibility_id,
            last_resp.reason,
            err_details,
        )
    return False
