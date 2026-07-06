"""
Idempotent apply against output/<run>_eligibilities.json (state file).

On POST/PUT 400 with "The users(s) (...) ... not assignable" or "The groups(s) (...) ... not assignable",
the script removes those IDs from eligibleUserIds / eligibleGroupIds and retries (bounded attempts).
If no principals remain after pruning, PUT deletes the eligibility; POST skips create and drops local state,
or deletes by saved id when present.

Match each desired eligibility from *_output.json to the state file using a stable identity:
provider, eligibility type, eligibility scope, constraint (e.g. resource group), role/policy
tuple, and group access match — excluding eligibleUserIds / eligibleGroupIds, name, status.

- Same identity and saved row has id → GET then PUT (eligible lists and status taken from desired when set).
- No match → POST create.
- Rewrites the state file with merged records; rows not present in this run’s desired list
  are kept so Andromeda objects remain tracked until cleanup.

cleanup=true in main DELETEs each row via API and rewrites the state file without
successfully removed (or 404) rows.
"""

from __future__ import annotations

import copy
import json
import logging
import re
from pathlib import Path

import requests

from andromeda import (
    _get_response_error_details,
    create_policy_eligibility_mapping,
    delete_policy_eligibility_mapping,
    get_policy_eligibility_mapping,
    update_policy_eligibility_mapping,
)

logger = logging.getLogger(__name__)

# API message (400): "The users(s) (uuid,...) in the eligibility were not found or are not assignable ..."
_UNASSIGNABLE_USERS_RE = re.compile(
    r"The users\(s\)\s*\(([^)]+)\)\s+in the eligibility were not found or are not assignable",
    re.IGNORECASE,
)
# Same shape with title "groups" from JitPolicyEligibilityNotAssignableError.
_UNASSIGNABLE_GROUPS_RE = re.compile(
    r"The groups\(s\)\s*\(([^)]+)\)\s+in the eligibility were not found or are not assignable",
    re.IGNORECASE,
)

# Servers validate users then groups; allow multiple strip rounds in one sync step.
_MAX_UNASSIGNABLE_STRIP_ATTEMPTS = 8


def _parse_unassignable_user_ids_from_error(exc: BaseException) -> list[str]:
    """
    Extract user UUIDs from a 400 response that lists users not found / not assignable.
    Returns [] if the error does not match that pattern.
    """
    chunks: list[str] = [str(exc)]
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        chunks.append(_get_response_error_details(exc.response))
        try:
            chunks.append(exc.response.text or "")
        except Exception:
            pass
    combined = " ".join(chunks)
    m = _UNASSIGNABLE_USERS_RE.search(combined)
    if not m:
        return []
    inner = (m.group(1) or "").strip()
    if not inner:
        return []
    return [p.strip() for p in inner.split(",") if p.strip()]


def _parse_unassignable_group_ids_from_error(exc: BaseException) -> list[str]:
    """
    Extract group UUIDs from a 400 response that lists groups not found / not assignable.
    Returns [] if the error does not match that pattern.
    """
    chunks: list[str] = [str(exc)]
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        chunks.append(_get_response_error_details(exc.response))
        try:
            chunks.append(exc.response.text or "")
        except Exception:
            pass
    combined = " ".join(chunks)
    m = _UNASSIGNABLE_GROUPS_RE.search(combined)
    if not m:
        return []
    inner = (m.group(1) or "").strip()
    if not inner:
        return []
    return [p.strip() for p in inner.split(",") if p.strip()]


def _remove_user_ids_from_eligible_user_ids(payload: dict, bad_ids: list[str]) -> int:
    """Remove bad_ids from payload['eligibleUserIds']. Returns how many entries were removed."""
    bad = {str(x).strip() for x in bad_ids if x}
    if not bad:
        return 0
    eu = payload.get("eligibleUserIds")
    if not isinstance(eu, list) or not eu:
        return 0
    before = len(eu)
    payload["eligibleUserIds"] = [x for x in eu if str(x).strip() not in bad]
    return before - len(payload["eligibleUserIds"])


def _remove_group_ids_from_eligible_group_ids(payload: dict, bad_ids: list[str]) -> int:
    """Remove bad_ids from payload['eligibleGroupIds']. Returns how many entries were removed."""
    bad = {str(x).strip() for x in bad_ids if x}
    if not bad:
        return 0
    eg = payload.get("eligibleGroupIds")
    if not isinstance(eg, list) or not eg:
        return 0
    before = len(eg)
    payload["eligibleGroupIds"] = [x for x in eg if str(x).strip() not in bad]
    return before - len(payload["eligibleGroupIds"])


def _eligible_principal_lists_empty(payload: dict) -> bool:
    """True when there are no eligible users and no eligible groups (missing or empty lists)."""
    u = payload.get("eligibleUserIds")
    g = payload.get("eligibleGroupIds")
    u_nonempty = isinstance(u, list) and len(u) > 0
    g_nonempty = isinstance(g, list) and len(g) > 0
    return not u_nonempty and not g_nonempty


# Proto EligibilityConfigurationType (numeric JSON) → name
_ELIGIBILITY_TYPE_NUM = {
    0: "ELIGIBILITY_CONFIGURATION_TYPE_UNSPECIFIED",
    1: "ROLE_ELIGIBILITY",
    4: "GROUP_ELIGIBILITY",
}

# ScopeTypeEnum
_SCOPE_TYPE_NUM = {
    0: "UNSPECIFIED",
    5: "PROVIDER",
    10: "FOLDER",
    15: "ACCOUNT",
    20: "RESOURCE_GROUP",
    21: "GROUP",
    50: "IDP_APPLICATION",
    51: "RESOURCE",
    52: "POPULATION",
}

# Strip output-only / server-owned fields. Keep updatedAt: apiserver requires it for optimistic concurrency on PUT.
_READ_ONLY_PUT_KEYS = frozenset({"tenantId", "createdAt"})

# Omit from GET vs PUT diff (identity / audit; not what the script mutates).
_DIFF_IGNORE_KEYS = frozenset({"id", "tenantId", "createdAt", "updatedAt"})


def _comparable_leaf(before: object, after: object) -> bool:
    if before is None and after is None:
        return True
    if isinstance(before, list) and isinstance(after, list):
        if all(isinstance(x, (str, int, float, bool)) or x is None for x in before + after):
            return sorted(str(x) for x in before) == sorted(str(x) for x in after)
        if len(before) != len(after):
            return False
        return all(_comparable_leaf(x, y) for x, y in zip(before, after))
    if isinstance(before, dict) and isinstance(after, dict):
        keys = set(before) | set(after)
        return all(
            k in _DIFF_IGNORE_KEYS or _comparable_leaf(before.get(k), after.get(k))
            for k in keys
        )
    return before == after


def _collect_eligibility_field_diffs(
    before: object,
    after: object,
    prefix: str,
    out: list[tuple[str, object, object]],
) -> None:
    if _comparable_leaf(before, after):
        return
    if isinstance(before, dict) and isinstance(after, dict):
        keys = set(before) | set(after)
        for k in sorted(keys):
            if k in _DIFF_IGNORE_KEYS:
                continue
            p = f"{prefix}.{k}" if prefix else k
            bv, av = before.get(k), after.get(k)
            if isinstance(bv, dict) and isinstance(av, dict):
                _collect_eligibility_field_diffs(bv, av, p, out)
            elif _comparable_leaf(bv, av):
                continue
            else:
                out.append((p, bv, av))
        return
    out.append((prefix or "(root)", before, after))


def _short_repr(val: object, max_len: int = 48) -> str:
    if val is None:
        return "null"
    if isinstance(val, list):
        if not val:
            return "[]"
        if all(isinstance(x, str) for x in val):
            n = len(val)
            if n <= 2:
                s = json.dumps(sorted(val))
            else:
                s = f"{n} ids"
        else:
            s = json.dumps(val, default=str)
    elif isinstance(val, dict):
        s = json.dumps(val, sort_keys=True, default=str)
    else:
        s = json.dumps(val, default=str) if not isinstance(val, str) else val
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _str_list_change_summary(ov: list, nv: list) -> str:
    """Compact summary for two string-id lists (order ignored for equality; delta for logging)."""
    bs = set(map(str, ov))
    afs = set(map(str, nv))
    removed = len(bs - afs)
    added = len(afs - bs)
    n_o, n_n = len(ov), len(nv)
    if removed == 0 and added == 0:
        return f"{n_o} ids"
    return f"{n_o}→{n_n} ids (−{removed}/+{added})"


def eligibility_put_change_summary(before: dict, after: dict) -> str:
    """
    Compare remote GET payload to PUT body; return a single-line reason for logging.
    """
    diffs: list[tuple[str, object, object]] = []
    _collect_eligibility_field_diffs(before, after, "", diffs)
    if not diffs:
        return "no field changes"
    parts: list[str] = []
    for path, ov, nv in diffs:
        if isinstance(ov, list) and isinstance(nv, list) and all(
            isinstance(x, str) for x in ov + nv
        ):
            parts.append(f"{path}: {_str_list_change_summary(ov, nv)}")
        else:
            parts.append(f"{path}: {_short_repr(ov)} → {_short_repr(nv)}")
    return "; ".join(parts)


def _norm_eligibility_type(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return _ELIGIBILITY_TYPE_NUM.get(v, str(v))
    return str(v)


def _norm_scope_type(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return _SCOPE_TYPE_NUM.get(v, str(v))
    return str(v)


def _norm_scope(scope: dict | None) -> dict:
    if not scope:
        return {}
    return {
        "scopeType": _norm_scope_type(scope.get("scopeType")),
        "scopeId": scope.get("scopeId") or "",
    }


def _norm_constraint(c: dict | None) -> dict:
    if not c:
        return {}
    out: dict = {"scopeType": _norm_scope_type(c.get("scopeType"))}
    rgc = c.get("resourceGroupIdConstraint")
    if rgc and isinstance(rgc, dict):
        ids = rgc.get("resourceGroupIds") or []
        if isinstance(ids, list):
            out["resourceGroupIdConstraint"] = {"resourceGroupIds": sorted(str(x) for x in ids)}
        else:
            out["resourceGroupIdConstraint"] = {"resourceGroupIds": []}
    return out


def _norm_role_eligibility_data(red: dict | None) -> dict:
    if not red:
        return {}
    ids = red.get("roleIds") or []
    if not isinstance(ids, list):
        ids = []
    return {"roleIds": sorted(str(x) for x in ids)}


def _norm_access_group_match(agm: dict | None) -> dict:
    if not agm:
        return {}
    gim = agm.get("groupIdsMatch") or {}
    if not isinstance(gim, dict):
        return {}
    ids = gim.get("groupIds") or []
    if not isinstance(ids, list):
        ids = []
    return {"groupIdsMatch": {"groupIds": sorted(str(x) for x in ids)}}


def eligibility_identity_payload(el: dict) -> dict:
    """
    Structural identity for an eligibility: what must stay the same across runs.
    Excludes eligibleUserIds / eligibleGroupIds (updated via PUT), name, status, id.
    Covers Entra role (flat provider + role), group PIM (accessGroupMatch), Azure resource (account/RG + role).
    """
    pid = el.get("providerId")
    et = _norm_eligibility_type(el.get("eligibilityType"))
    out: dict = {
        "providerId": str(pid) if pid else "",
        "eligibilityType": et,
        "eligibilityConstraint": _norm_constraint(el.get("eligibilityConstraint")),  # type: ignore[arg-type]
        "eligibilityScope": _norm_scope(el.get("eligibilityScope")),  # type: ignore[arg-type]
    }
    red = el.get("roleEligibilityData")
    if red and isinstance(red, dict):
        out["roleEligibilityData"] = _norm_role_eligibility_data(red)
    aid = el.get("accountId")
    if aid:
        out["accountId"] = str(aid)
    agm = el.get("accessGroupMatch")
    if agm and isinstance(agm, dict):
        out["accessGroupMatch"] = _norm_access_group_match(agm)
    return out


def eligibility_identity_fingerprint(el: dict) -> str:
    return json.dumps(eligibility_identity_payload(el), sort_keys=True, separators=(",", ":"))


def _has_not_found(obj: object) -> bool:
    if obj == "NOT_FOUND":
        return True
    if isinstance(obj, dict):
        return any(_has_not_found(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_not_found(v) for v in obj)
    return False


def _record_id(rec: dict) -> str | None:
    rid = rec.get("id")
    return str(rid) if rid else None


def _record_provider_id(rec: dict) -> str | None:
    pid = rec.get("providerId")
    return str(pid) if pid else None


def _load_saved_by_fingerprint(path: Path) -> dict[str, dict]:
    """fingerprint -> latest record (last wins on duplicates)."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load %s: %s", path, e)
        return {}
    if not isinstance(raw, list):
        return {}
    out: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        fp = eligibility_identity_fingerprint(item)
        out[fp] = item
    return out


def _prepare_put_body(remote: dict, desired: dict) -> dict:
    body = copy.deepcopy(remote)
    for k in _READ_ONLY_PUT_KEYS:
        body.pop(k, None)
    body["eligibleUserIds"] = list(desired.get("eligibleUserIds") or [])
    body["eligibleGroupIds"] = list(desired.get("eligibleGroupIds") or [])
    if "status" in desired:
        body["status"] = desired["status"]
    return body


def apply_eligibilities_sync(
    output_path: str,
    eligibilities_path: Path,
    placeholder_provider_ids: frozenset[str],
) -> tuple[int, int, int, list[dict]]:
    """
    Read desired eligibilities from output JSON, upsert against eligibilities_path.
    Returns (created_count, updated_count, failed_count, merged_records_for_file).
    """
    with open(output_path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "eligibilities" in data:
        desired_list = data["eligibilities"]
    elif isinstance(data, list):
        desired_list = data
    else:
        raise ValueError("Output must be a list of eligibilities or {eligibilities: [...]}")

    merged_by_fp = _load_saved_by_fingerprint(eligibilities_path)

    created = 0
    updated = 0
    failed = 0

    for i, el in enumerate(desired_list):
        if not isinstance(el, dict):
            continue
        prov_id = el.get("providerId")
        if not prov_id or prov_id in placeholder_provider_ids:
            logger.warning("Skipping eligibility %d: placeholder or missing provider ID", i + 1)
            continue
        if _has_not_found(el):
            logger.warning("Skipping eligibility %d: payload contains NOT_FOUND (unresolved IDs)", i + 1)
            continue

        fp = eligibility_identity_fingerprint(el)
        existing = merged_by_fp.get(fp)
        existing_id = _record_id(existing) if existing else None

        name = el.get("name", "?")
        if existing and not existing_id:
            logger.warning(
                "Identity match in %s but no id on saved record; creating new (may duplicate): %s",
                eligibilities_path,
                name,
            )
        if existing_id:
            el_work = copy.deepcopy(el)
            attempt_idx = 0
            while attempt_idx < _MAX_UNASSIGNABLE_STRIP_ATTEMPTS:
                attempt_idx += 1
                try:
                    current = get_policy_eligibility_mapping(prov_id, existing_id)
                    body = _prepare_put_body(current, el_work)
                    result = update_policy_eligibility_mapping(prov_id, existing_id, body)
                    merged_by_fp[fp] = result
                    updated += 1
                    reason = eligibility_put_change_summary(current, body)
                    suffix = (
                        " [after stripping unassignable principals]"
                        if attempt_idx > 1
                        else ""
                    )
                    logger.info(
                        "Updated eligibility %d/%d: %s (%s)%s",
                        i + 1,
                        len(desired_list),
                        name,
                        reason,
                        suffix,
                    )
                    break
                except Exception as e:
                    bad_u = _parse_unassignable_user_ids_from_error(e)
                    bad_g = _parse_unassignable_group_ids_from_error(e)
                    ru = _remove_user_ids_from_eligible_user_ids(el_work, bad_u) if bad_u else 0
                    rg = _remove_group_ids_from_eligible_group_ids(el_work, bad_g) if bad_g else 0
                    if bad_u or bad_g:
                        if ru == 0 and rg == 0:
                            failed += 1
                            logger.error(
                                "Failed to update eligibility %d/%d %s: API reported unassignable "
                                "principals users=%s groups=%s but none matched eligible lists: %s",
                                i + 1,
                                len(desired_list),
                                name,
                                bad_u,
                                bad_g,
                                e,
                            )
                            break
                        logger.warning(
                            "Removing %d user(s) and %d group id(s) from eligibility (unassignable), retrying: "
                            "%s — users=%s groups=%s",
                            ru,
                            rg,
                            name,
                            bad_u,
                            bad_g,
                        )
                        if _eligible_principal_lists_empty(el_work):
                            logger.warning(
                                "No eligible users or groups remain after pruning; deleting eligibility %s",
                                name,
                            )
                            if delete_policy_eligibility_mapping(prov_id, existing_id):
                                merged_by_fp.pop(fp, None)
                                logger.info(
                                    "Deleted eligibility %d/%d: %s (no principals after pruning)",
                                    i + 1,
                                    len(desired_list),
                                    name,
                                )
                            else:
                                failed += 1
                                logger.error(
                                    "Failed to delete eligibility %d/%d %s after principals emptied",
                                    i + 1,
                                    len(desired_list),
                                    name,
                                )
                            break
                        continue
                    failed += 1
                    logger.error(
                        "Failed to update eligibility %d/%d %s: %s",
                        i + 1,
                        len(desired_list),
                        name,
                        e,
                    )
                    break
            else:
                failed += 1
                logger.error(
                    "Failed to update eligibility %d/%d %s: exhausted %d unassignable strip attempts",
                    i + 1,
                    len(desired_list),
                    name,
                    _MAX_UNASSIGNABLE_STRIP_ATTEMPTS,
                )
        else:
            payload = copy.deepcopy(el)
            attempt_idx = 0
            while attempt_idx < _MAX_UNASSIGNABLE_STRIP_ATTEMPTS:
                attempt_idx += 1
                try:
                    result = create_policy_eligibility_mapping(prov_id, payload)
                    merged_by_fp[fp] = result
                    created += 1
                    suffix = (
                        " [after stripping unassignable principals]"
                        if attempt_idx > 1
                        else ""
                    )
                    logger.info(
                        "Created eligibility %d/%d: %s%s",
                        i + 1,
                        len(desired_list),
                        name,
                        suffix,
                    )
                    break
                except Exception as e:
                    bad_u = _parse_unassignable_user_ids_from_error(e)
                    bad_g = _parse_unassignable_group_ids_from_error(e)
                    ru = _remove_user_ids_from_eligible_user_ids(payload, bad_u) if bad_u else 0
                    rg = _remove_group_ids_from_eligible_group_ids(payload, bad_g) if bad_g else 0
                    if bad_u or bad_g:
                        if ru == 0 and rg == 0:
                            failed += 1
                            logger.error(
                                "Failed to create eligibility %d/%d %s: API reported unassignable "
                                "principals users=%s groups=%s but none matched eligible lists: %s",
                                i + 1,
                                len(desired_list),
                                name,
                                bad_u,
                                bad_g,
                                e,
                            )
                            break
                        logger.warning(
                            "Removing %d user(s) and %d group id(s) before retry create: %s — users=%s groups=%s",
                            ru,
                            rg,
                            name,
                            bad_u,
                            bad_g,
                        )
                        if _eligible_principal_lists_empty(payload):
                            logger.warning(
                                "No principals remain after pruning; skipping create for eligibility %s",
                                name,
                            )
                            stale_id = _record_id(existing) if existing else None
                            if stale_id:
                                if delete_policy_eligibility_mapping(prov_id, stale_id):
                                    merged_by_fp.pop(fp, None)
                                    logger.info(
                                        "Deleted existing eligibility %d/%d: %s (no principals after pruning)",
                                        i + 1,
                                        len(desired_list),
                                        name,
                                    )
                                else:
                                    failed += 1
                                    logger.error(
                                        "Failed to delete eligibility %d/%d %s after empty principals",
                                        i + 1,
                                        len(desired_list),
                                        name,
                                    )
                            else:
                                merged_by_fp.pop(fp, None)
                            break
                        continue
                    failed += 1
                    logger.error(
                        "Failed to create eligibility %d/%d %s: %s",
                        i + 1,
                        len(desired_list),
                        name,
                        e,
                    )
                    break
            else:
                failed += 1
                logger.error(
                    "Failed to create eligibility %d/%d %s: exhausted %d unassignable strip attempts",
                    i + 1,
                    len(desired_list),
                    name,
                    _MAX_UNASSIGNABLE_STRIP_ATTEMPTS,
                )

    merged_records = list(merged_by_fp.values())
    return created, updated, failed, merged_records
