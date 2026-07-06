"""
# Copyright 2025 Andromeda Security, Inc.

Create GROUP_ELIGIBILITY records from a CSV file.

A group-membership eligibility grants members of an assignable group and/or a
named set of users JIT access to become members of one-or-more target provider
groups. This script is intentionally focused: it does not handle ROLE or
PROVIDER eligibilities.

CSV columns (header row required):
    provider                provider name (matched via GraphQL provider filter)
    eligible_group          assignable-group name whose members are eligible
    eligible_users          Andromeda usernames whose users are eligible; ';' separated
    access_group            target provider-group name(s); ';' separated
    access_profile_name     AccessRequestProfile name (optional; falls back to
                            the tenant default AccessRequestProfile if blank)
    description             Human-readable description used as the eligibility `name`
                            (optional; falls back to an auto-generated name)

Multiple rows targeting the same (access_group set, access_profile) are merged
into a single eligibility record. New principals (eligible groups / users) are
unioned into the existing record via PUT.

Auth (one of):
    export AS_SESSION_COOKIE=<session>
    export AS_API_TOKEN=<api token>

Example:
    python3 sdk/samples/as_create_group_eligibility.py \\
        --eligibility_file=/tmp/group_elig.csv \\
        --report_file=/tmp/group_elig_report.csv
    # dry run
    python3 sdk/samples/as_create_group_eligibility.py \\
        --eligibility_file=/tmp/group_elig.csv --dry_run
"""

import argparse
import csv
import logging
import os
from typing import Optional, Dict, Any, List, Tuple

import requests

from sdk.api_utils import APIUtils, InvalidInputException
from sdk.as_inventory import AndromedaInventory

logger = logging.getLogger(__name__)


ELIGIBILITY_TYPE = "GROUP_ELIGIBILITY"

LIST_SEP = ";"

CSV_COL_PROVIDER = "provider"
CSV_COL_ELIG_GROUP = "eligible_group"
CSV_COL_ELIG_USERS = "eligible_users"
CSV_COL_ACCESS_GROUP = "access_group"
CSV_COL_ACCESS_PROFILE = "access_profile_name"
CSV_COL_DESCRIPTION = "description"

REPORT_COLS = [
    "row",
    CSV_COL_PROVIDER,
    CSV_COL_ELIG_GROUP,
    CSV_COL_ELIG_USERS,
    CSV_COL_ACCESS_GROUP,
    CSV_COL_ACCESS_PROFILE,
    CSV_COL_DESCRIPTION,
    "eligibility_id",
    "action",
    "error",
]


def _setup_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__,
    )
    parser.add_argument('--as_api_endpoint',
                        default="https://api.live.andromedasecurity.com",
                        help='REST endpoint for the inventory')
    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')
    parser.add_argument('--eligibility_file', required=True,
                        help='path to the CSV eligibility file')
    parser.add_argument('--report_file',
                        default="/tmp/group_eligibility_report.csv",
                        help='path to write the per-row report CSV')
    parser.add_argument('--dry_run', action='store_true',
                        help='Dry run — do not POST/PUT anything')
    return parser.parse_args()


def _setup_logging() -> None:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(module)s:%(lineno)s: %(message)s'))
    logger.addHandler(handler)


def _get_api_session(api_endpoint: str) -> requests.Session:
    au = APIUtils(api_endpoint=api_endpoint)
    session_token = os.getenv("AS_SESSION_COOKIE", "")
    if session_token:
        return au.get_api_session_w_cookie(session_token)
    api_token = os.getenv("AS_API_TOKEN", "")
    if api_token:
        return au.get_api_session_w_api_token(api_token)
    raise InvalidInputException(
        "Either AS_API_TOKEN or AS_SESSION_COOKIE must be set")


def _split_list(cell: str) -> List[str]:
    if not cell:
        return []
    return [item.strip() for item in cell.split(LIST_SEP) if item.strip()]


class Resolver:
    """Resolves CSV names to Andromeda UUIDs, with per-run caches."""

    def __init__(self, as_inventory: AndromedaInventory,
                 api_session: requests.Session, as_api_endpoint: str):
        self.inv = as_inventory
        self.session = api_session
        self.endpoint = as_api_endpoint

        self._provider_by_name: Dict[str, dict] = {}
        self._assignable_group_id: Dict[Tuple[str, str], str] = {}
        self._provider_group_id: Dict[Tuple[str, str], str] = {}
        self._user_id: Dict[str, str] = {}
        self._access_profiles: Optional[Dict[str, dict]] = None
        self._tenant_default_profile_id: Optional[str] = None
        self._tenant_default_loaded = False

    def provider(self, name: str) -> dict:
        if name in self._provider_by_name:
            logger.debug("provider cache hit name=%s id=%s",
                         name, self._provider_by_name[name].get('id'))
            return self._provider_by_name[name]
        logger.debug("resolving provider name=%s", name)
        provider = next(self.inv.as_provider_itr(
            filters={"name": {"equals": name}}), None)
        if not provider:
            raise InvalidInputException(f"Provider '{name}' not found")
        logger.debug("resolved provider name=%s id=%s type=%s",
                     name, provider.get('id'), provider.get('type'))
        self._provider_by_name[name] = provider
        return provider

    def assignable_group_id(self, provider: dict, name: str) -> str:
        key = (provider['id'], name)
        if key in self._assignable_group_id:
            logger.debug("assignable_group cache hit provider=%s name=%s id=%s",
                         provider.get('name'), name, self._assignable_group_id[key])
            return self._assignable_group_id[key]
        logger.debug("resolving assignable_group provider=%s name=%s",
                     provider.get('name'), name)
        group = next(self.inv.provider_assignable_groups_itr(
            provider['id'], provider, filters={"name": {"equals": name}}), None)
        if not group:
            raise InvalidInputException(
                f"Assignable group '{name}' not found in provider '{provider['name']}'")
        group_id = (group.get('groupDetails') or {}).get('id') or group.get('id')
        if not group_id:
            raise InvalidInputException(
                f"Assignable group '{name}' has no id in provider '{provider['name']}'")
        logger.debug("resolved assignable_group provider=%s name=%s id=%s",
                     provider.get('name'), name, group_id)
        self._assignable_group_id[key] = group_id
        return group_id

    def provider_group_id(self, provider: dict, name: str) -> str:
        key = (provider['id'], name)
        if key in self._provider_group_id:
            logger.debug("provider_group cache hit provider=%s name=%s id=%s",
                         provider.get('name'), name, self._provider_group_id[key])
            return self._provider_group_id[key]
        logger.debug("resolving provider_group provider=%s name=%s",
                     provider.get('name'), name)
        group = next(self.inv.as_provider_groups_itr(
            provider['id'], provider, filters={"name": {"equals": name}}), None)
        if not group:
            raise InvalidInputException(
                f"Provider group '{name}' not found in provider '{provider['name']}'")
        group_id = group.get('id') or (group.get('groupDetails') or {}).get('id')
        if not group_id:
            raise InvalidInputException(
                f"Provider group '{name}' has no id in provider '{provider['name']}'")
        logger.debug("resolved provider_group provider=%s name=%s id=%s",
                     provider.get('name'), name, group_id)
        self._provider_group_id[key] = group_id
        return group_id

    def user_id(self, username: str) -> str:
        if username in self._user_id:
            logger.debug("user cache hit username=%s id=%s",
                         username, self._user_id[username])
            return self._user_id[username]
        logger.debug("resolving user username=%s", username)
        user = next(self.inv.as_users_itr(
            filters={"username": {"equals": username}}), None)
        if not user:
            raise InvalidInputException(f"User '{username}' not found")
        logger.debug("resolved user username=%s id=%s", username, user['id'])
        self._user_id[username] = user['id']
        return user['id']

    def _load_access_profiles(self) -> Dict[str, dict]:
        if self._access_profiles is not None:
            return self._access_profiles
        url = f"{self.endpoint}/accessrequestprofiles"
        logger.debug("fetching access request profiles from %s", url)
        resp = self.session.get(url)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, list):
            items = payload
            envelope = "list"
        elif isinstance(payload, dict):
            envelope = "dict"
            items = payload.get('accessRequestProfiles') or payload.get('items') or []
            if not items:
                for key, value in payload.items():
                    if isinstance(value, list):
                        items = value
                        envelope = f"dict[{key}]"
                        break
        else:
            items = []
            envelope = f"unknown({type(payload).__name__})"
        profiles: Dict[str, dict] = {}
        for profile in items:
            name = profile.get('name')
            if name:
                profiles[name] = profile
        logger.info("loaded %d AccessRequestProfiles (envelope=%s)",
                    len(profiles), envelope)
        if not profiles:
            logger.warning("no AccessRequestProfiles found — is the endpoint / "
                           "auth correct? payload keys=%s",
                           list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
        self._access_profiles = profiles
        return profiles

    def access_profile_id(self, name: str) -> str:
        profiles = self._load_access_profiles()
        profile = profiles.get(name)
        if not profile:
            logger.error("AccessRequestProfile '%s' not found among %d loaded profiles: %s",
                         name, len(profiles), sorted(profiles.keys()))
            raise InvalidInputException(
                f"AccessRequestProfile '{name}' not found")
        logger.debug("resolved access_profile name=%s id=%s", name, profile['id'])
        return profile['id']

    def tenant_default_access_profile_id(self) -> str:
        """Return the tenant-level default AccessRequestProfile id, or empty
        string if the tenant has none configured. The value is fetched once and
        cached for the lifetime of the resolver."""
        if self._tenant_default_loaded:
            return self._tenant_default_profile_id or ""
        self._tenant_default_loaded = True
        try:
            resp = self.session.get(f"{self.endpoint}/tenantsettings")
            resp.raise_for_status()
            settings = resp.json() or {}
            profile_id = (settings.get('defaultAccessRequestProfileId')
                          or settings.get('default_access_request_profile_id')
                          or "")
            self._tenant_default_profile_id = profile_id
            if profile_id:
                logger.info("Using tenant default AccessRequestProfile id=%s "
                            "for rows without access_profile_name", profile_id)
            else:
                logger.warning("Tenant has no default AccessRequestProfile; "
                               "rows without access_profile_name will be "
                               "created without one")
        except requests.RequestException as exc:
            logger.warning("Could not fetch tenant default AccessRequestProfile "
                           "(%s); proceeding without a default", exc)
            self._tenant_default_profile_id = ""
        return self._tenant_default_profile_id or ""


class EligibilityCache:
    """Caches existing GROUP_ELIGIBILITY records per provider so multiple CSV
    rows can merge into the same eligibility.

    Match key: (sorted target group ids, access_request_profile_id).
    """

    def __init__(self, as_inventory: AndromedaInventory,
                 api_session: requests.Session, as_api_endpoint: str):
        self.inv = as_inventory
        self.session = api_session
        self.endpoint = as_api_endpoint
        self._by_provider: Dict[str, List[dict]] = {}

    def _load_provider(self, provider: dict) -> List[dict]:
        provider_id = provider['id']
        if provider_id in self._by_provider:
            return self._by_provider[provider_id]
        logger.info("loading existing GROUP_ELIGIBILITY records for provider name=%s id=%s",
                    provider.get('name'), provider_id)
        eligibilities: List[dict] = []
        filters = {"eligibilityType": {"equals": ELIGIBILITY_TYPE}}
        stub_count = 0
        for stub in self.inv.provider_eligibilities_itr(
                provider_id, provider, filters=filters):
            stub_count += 1
            eligibility_id = stub.get('eligibilityId') or stub.get('id')
            if not eligibility_id:
                logger.debug("skipping eligibility stub with no id: %s", stub)
                continue
            full = self._fetch_full(provider_id, eligibility_id)
            if full and full.get('eligibilityType') == ELIGIBILITY_TYPE:
                eligibilities.append(full)
            else:
                logger.debug("skipping eligibility id=%s (missing or wrong type=%s)",
                             eligibility_id,
                             full.get('eligibilityType') if full else None)
        logger.info("provider=%s: loaded %d GROUP_ELIGIBILITY records (from %d stubs)",
                    provider.get('name'), len(eligibilities), stub_count)
        self._by_provider[provider_id] = eligibilities
        return eligibilities

    def _fetch_full(self, provider_id: str, eligibility_id: str) -> Optional[dict]:
        resp = self.session.get(
            f"{self.endpoint}/providers/{provider_id}/eligibilities/{eligibility_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _target_key(eligibility: dict) -> Tuple[str, ...]:
        group_ids = ((eligibility.get('accessGroupMatch') or {})
                     .get('groupIdsMatch') or {}).get('groupIds') or []
        return tuple(sorted(group_ids))

    def find_match(self, provider: dict, target_ids: List[str],
                   access_request_profile_id: str) -> Optional[dict]:
        target = tuple(sorted(target_ids))
        candidates = self._load_provider(provider)
        logger.debug("find_match provider=%s target=%s profile_id=%s candidates=%d",
                     provider.get('name'), target, access_request_profile_id, len(candidates))
        for eligibility in candidates:
            candidate_target = self._target_key(eligibility)
            candidate_profile = eligibility.get('accessRequestProfileId') or ""
            if candidate_target != target:
                logger.debug("  no match eligibility_id=%s target=%s (wanted %s)",
                             eligibility.get('eligibilityId') or eligibility.get('id'),
                             candidate_target, target)
                continue
            if candidate_profile != (access_request_profile_id or ""):
                logger.debug("  no match eligibility_id=%s profile=%s (wanted %s)",
                             eligibility.get('eligibilityId') or eligibility.get('id'),
                             candidate_profile, access_request_profile_id)
                continue
            logger.info("find_match: matched existing eligibility_id=%s",
                        eligibility.get('eligibilityId') or eligibility.get('id'))
            return eligibility
        logger.debug("find_match: no existing eligibility matches — will CREATE")
        return None

    def upsert(self, provider_id: str, eligibility: dict) -> None:
        eligibilities = self._by_provider.setdefault(provider_id, [])
        eligibility_id = eligibility.get('eligibilityId') or eligibility.get('id')
        for index, existing in enumerate(eligibilities):
            existing_id = existing.get('eligibilityId') or existing.get('id')
            if existing_id and existing_id == eligibility_id:
                eligibilities[index] = eligibility
                return
        eligibilities.append(eligibility)


def _build_new_eligibility(provider_id: str,
                           target_group_ids: List[str],
                           eligible_group_ids: List[str],
                           eligible_user_ids: List[str],
                           access_request_profile_id: str,
                           name: str) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "name": name,
        "providerId": provider_id,
        "eligibilityType": ELIGIBILITY_TYPE,
        "eligibilityConstraint": {"scopeType": "PROVIDER"},
        "eligibilityScope": {"scopeType": "PROVIDER", "scopeId": provider_id},
        "accessGroupMatch": {
            "groupIdsMatch": {"groupIds": sorted(set(target_group_ids))}
        },
        "eligibleGroupIds": sorted(set(eligible_group_ids)),
        "eligibleUserIds": sorted(set(eligible_user_ids)),
    }
    if access_request_profile_id:
        body["accessRequestProfileId"] = access_request_profile_id
    return body


def _merge_into_existing(existing: dict,
                         eligible_group_ids: List[str],
                         eligible_user_ids: List[str],
                         description: str) -> Tuple[dict, bool]:
    updated = dict(existing)
    current_groups = set(updated.get('eligibleGroupIds') or [])
    current_users = set(updated.get('eligibleUserIds') or [])
    new_groups = current_groups | set(eligible_group_ids)
    new_users = current_users | set(eligible_user_ids)
    changed = (new_groups != current_groups) or (new_users != current_users)
    updated['eligibleGroupIds'] = sorted(new_groups)
    updated['eligibleUserIds'] = sorted(new_users)
    if description and updated.get('name') != description:
        updated['name'] = description
        changed = True
    return updated, changed


def _default_name(provider_name: str, access_group_names: List[str],
                  access_profile_name: str) -> str:
    target = ",".join(access_group_names) if access_group_names else "group"
    suffix = f"@{access_profile_name}" if access_profile_name else ""
    return f"{provider_name}-group-{target}{suffix}"


def _empty_report_row(row: Dict[str, str], row_num: int) -> Dict[str, str]:
    report_row = {col: (row.get(col, "") or "") for col in REPORT_COLS if col in row}
    report_row["row"] = str(row_num)
    report_row["eligibility_id"] = ""
    report_row["action"] = ""
    report_row["error"] = ""
    return report_row


def _process_row(row: Dict[str, str], row_num: int,
                 resolver: Resolver, cache: EligibilityCache,
                 api_session: requests.Session, as_api_endpoint: str,
                 dry_run: bool) -> Dict[str, str]:
    logger.info("--- processing row %d ---", row_num)
    logger.debug("row %d raw: %s", row_num, row)
    report_row = _empty_report_row(row, row_num)

    provider_name = (row.get(CSV_COL_PROVIDER) or "").strip()
    eligible_group_name = (row.get(CSV_COL_ELIG_GROUP) or "").strip()
    eligible_user_names = _split_list(row.get(CSV_COL_ELIG_USERS) or "")
    access_group_names = _split_list(row.get(CSV_COL_ACCESS_GROUP) or "")
    access_profile_name = (row.get(CSV_COL_ACCESS_PROFILE) or "").strip()
    description = (row.get(CSV_COL_DESCRIPTION) or "").strip()
    report_row[CSV_COL_DESCRIPTION] = description
    logger.info("row %d parsed: provider=%r eligible_group=%r eligible_users=%r "
                "access_group=%r access_profile=%r description=%r",
                row_num, provider_name, eligible_group_name, eligible_user_names,
                access_group_names, access_profile_name, description)

    if not provider_name:
        report_row["action"] = "ERROR"
        report_row["error"] = "provider is required"
        return report_row
    if not access_group_names:
        report_row["action"] = "ERROR"
        report_row["error"] = "access_group is required"
        return report_row
    if not eligible_group_name and not eligible_user_names:
        report_row["action"] = "ERROR"
        report_row["error"] = "at least one of eligible_group / eligible_users required"
        return report_row

    provider = resolver.provider(provider_name)
    provider_id = provider['id']

    eligible_group_ids: List[str] = []
    if eligible_group_name:
        eligible_group_ids.append(
            resolver.assignable_group_id(provider, eligible_group_name))
    eligible_user_ids = [resolver.user_id(name) for name in eligible_user_names]
    target_group_ids = [resolver.provider_group_id(provider, name)
                        for name in access_group_names]

    if access_profile_name:
        access_request_profile_id = resolver.access_profile_id(access_profile_name)
    else:
        access_request_profile_id = resolver.tenant_default_access_profile_id()
        if access_request_profile_id:
            logger.info("row %d: no access_profile_name in CSV — using tenant default id=%s",
                        row_num, access_request_profile_id)
        else:
            logger.info("row %d: no access_profile_name in CSV and tenant has no default — "
                        "eligibility will be created without accessRequestProfileId", row_num)

    logger.info("row %d resolved ids: provider=%s eligible_groups=%s eligible_users=%s "
                "target_groups=%s access_request_profile=%s",
                row_num, provider_id, eligible_group_ids, eligible_user_ids,
                target_group_ids, access_request_profile_id or "(none)")

    existing = cache.find_match(
        provider, target_group_ids, access_request_profile_id)

    if existing:
        updated, changed = _merge_into_existing(
            existing, eligible_group_ids, eligible_user_ids, description)
        eligibility_id = updated.get('eligibilityId') or updated.get('id')
        report_row["eligibility_id"] = eligibility_id or ""
        if not changed:
            report_row["action"] = "SKIPPED"
            return report_row
        if dry_run:
            logger.info("Dry run PUT eligibility %s body=%s", eligibility_id, updated)
            report_row["action"] = "UPDATED"
            cache.upsert(provider_id, updated)
            return report_row
        resp = api_session.put(
            f"{as_api_endpoint}/providers/{provider_id}/eligibilities/{eligibility_id}",
            json=updated)
        resp.raise_for_status()
        cache.upsert(provider_id, resp.json())
        report_row["action"] = "UPDATED"
        return report_row

    name = description or _default_name(
        provider_name, access_group_names, access_profile_name)
    body = _build_new_eligibility(
        provider_id, target_group_ids,
        eligible_group_ids, eligible_user_ids,
        access_request_profile_id, name)
    if dry_run:
        logger.info("Dry run POST eligibility provider=%s body=%s", provider_id, body)
        report_row["action"] = "CREATED"
        cache.upsert(provider_id, body)
        return report_row
    resp = api_session.post(
        f"{as_api_endpoint}/providers/{provider_id}/eligibilities", json=body)
    resp.raise_for_status()
    created = resp.json()
    cache.upsert(provider_id, created)
    report_row["eligibility_id"] = created.get('eligibilityId') or created.get('id') or ""
    report_row["action"] = "CREATED"
    return report_row


def create_group_eligibilities(as_api_endpoint: str,
                               as_inventory: AndromedaInventory,
                               api_session: requests.Session,
                               eligibility_file: str,
                               report_file: str,
                               dry_run: bool = False) -> None:
    resolver = Resolver(as_inventory, api_session, as_api_endpoint)
    cache = EligibilityCache(as_inventory, api_session, as_api_endpoint)

    report_rows: List[Dict[str, str]] = []
    totals = {"CREATED": 0, "UPDATED": 0, "SKIPPED": 0, "ERROR": 0}

    logger.info("reading CSV file %s (dry_run=%s)", eligibility_file, dry_run)
    with open(eligibility_file, "r", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames:
            reader.fieldnames = [(name or "").strip() for name in reader.fieldnames]
        logger.info("CSV headers: %s", reader.fieldnames)
        expected = {CSV_COL_PROVIDER, CSV_COL_ELIG_GROUP, CSV_COL_ELIG_USERS,
                    CSV_COL_ACCESS_GROUP, CSV_COL_ACCESS_PROFILE}
        missing = expected - set(reader.fieldnames or [])
        if missing:
            logger.warning("CSV is missing expected columns %s — rows will be "
                           "processed with those fields blank", sorted(missing))
        row_count = 0
        for index, row in enumerate(reader, start=2):  # header is row 1
            row_count += 1
            try:
                result = _process_row(
                    row, index, resolver, cache,
                    api_session, as_api_endpoint, dry_run)
            except InvalidInputException as exc:
                result = _empty_report_row(row, index)
                result["action"] = "ERROR"
                result["error"] = str(exc)
                logger.error("row %d: %s", index, exc)
            except requests.HTTPError as exc:
                result = _empty_report_row(row, index)
                result["action"] = "ERROR"
                body = getattr(exc.response, "text", "") if exc.response is not None else ""
                status = exc.response.status_code if exc.response is not None else "?"
                result["error"] = f"HTTP {status}: {body[:400]}"
                logger.error("row %d: HTTP %s body=%s", index, status, body[:1000])
            except Exception as exc:
                # Catch-all so a single bad row doesn't silently abort the batch.
                result = _empty_report_row(row, index)
                result["action"] = "ERROR"
                result["error"] = f"{type(exc).__name__}: {exc}"
                logger.exception("row %d: unhandled exception", index)
            totals[result["action"]] = totals.get(result["action"], 0) + 1
            report_rows.append(result)
        logger.info("CSV read complete: %d data rows", row_count)
        if row_count == 0:
            logger.warning("CSV had zero data rows — is the file empty or has "
                           "only a header?")

    with open(report_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_COLS, extrasaction="ignore")
        writer.writeheader()
        for row in report_rows:
            writer.writerow(row)

    logger.info("Group eligibility processing complete: created=%d updated=%d skipped=%d errors=%d report=%s",
                totals["CREATED"], totals["UPDATED"], totals["SKIPPED"], totals["ERROR"], report_file)


if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    api_session = _get_api_session(args.as_api_endpoint)
    logger.info("Established session with %s", args.as_api_endpoint)
    as_inventory = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=args.as_api_endpoint, gql_endpoint=args.as_gql_endpoint)
    create_group_eligibilities(
        args.as_api_endpoint, as_inventory, api_session,
        args.eligibility_file, args.report_file, args.dry_run)
