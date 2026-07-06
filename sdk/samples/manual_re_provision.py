# Copyright 2025 Andromeda Security, Inc.
#
"""
List failed JIT access requests (provisioning / deprovisioning) from GraphQL, filter by
how long ago the status last transitioned, then optionally retrigger processing via the
bulk retrigger REST API (admin only).

Run from the lib/python directory (same as other sdk samples):

    cd lib/python
    python3 sdk/samples/manual_re_provision.py \\
        --api https://api.staging.andromedasecurity.com \\
        --access_key '<access-key-code>' \\
        --until 60

**Multi-tenant:** pass a JSON file mapping display names to access keys (chmod 600; do not
commit). Example ``tenants.json``::

    {"Acme Corp": "<access-key-code>", "Contoso": "<access-key-code>"}

    python3 sdk/samples/manual_re_provision.py \\
        --api https://api.staging.andromedasecurity.com \\
        --until 60 \\
        --multiple-tenants tenants.json \\
        --dry-run

With ``--multiple-tenants``, unset ``AS_API_TOKEN`` and do not pass ``--access_key``; keys
come only from the JSON file. Modes:

- **Neither** ``--dry-run`` nor ``--retrigger``: interactive ``y/N`` per row (per tenant).
- **``--dry-run``**: list candidates only (no retrigger API).
- **``--retrigger``**: retrigger every matching row without prompts.
- **Both** flags: ``--dry-run`` wins; a warning is printed on stderr.

``--api`` and optional ``--gql`` are **scheme://host:port** only (no path). GraphQL is always
requested at ``{that}/graphql``. If ``--gql`` is omitted, the GraphQL host is the same as ``--api``.

``--until`` is the number of whole minutes to subtract from **current UTC time** to form a
cutoff instant ``cutoff = now_utc - until``. A request is included iff
``transitionedAt`` (parsed as UTC) is **``>= cutoff``** — i.e. equal to that instant or
later (same instant “or more” in the sense of a greater / same timestamp).

Environment (optional): ``AS_API_ENDPOINT`` and ``AS_API_TOKEN`` default ``--api`` and
``--access_key`` when those flags are omitted (single-tenant only; not used with
``--multiple-tenants``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import urllib3

# APIUtils may use verify=False against test/staging; avoid urllib3 TLS noise on stderr.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from sdk.api_utils import APIUtils

ACCESS_REQUEST_QUERY = """
query FailedAccessRequests($skip: Int!) {
  AccessManagement {
    accessRequests(
      filters: { status: { in: [DEPROVISIONING_FAILED, PROVISIONING_FAILED] } }
      pageArgs: { pageSize: 50, skip: $skip }
    ) {
      edges {
        node {
          requestId
          status {
            status
            transitionedAt
          }
        }
      }
      pageInfo {
        count
      }
    }
  }
}
"""


@dataclass(frozen=True)
class FailedRequestRow:
    request_id: str
    status: str
    transitioned_at_raw: str
    transitioned_at: datetime | None
    processing_state: str


def _api_base(arg: str | None) -> str:
    """REST base: scheme://host:port with no path (trailing slashes stripped)."""
    base = (arg or os.environ.get("AS_API_ENDPOINT", "")).rstrip("/")
    if not base:
        raise SystemExit("Andromeda API base URL is required (--api or AS_API_ENDPOINT).")
    return base


def _graphql_url(host_port: str) -> str:
    """GraphQL is always at {scheme://host:port}/graphql."""
    return f"{host_port.rstrip('/')}/graphql"


def _resolve_gql_url(gql_host: str | None, api_base: str) -> str:
    return _graphql_url(gql_host if gql_host else api_base)


def _parse_transitioned_at(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        # Epoch seconds or ms from JSON coercion
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    text = str(raw).strip()
    if not text:
        return None
    if len(text) >= 1 and text[-1] in "Zz":
        ns = text[:-1]
        if ns:
            text = ns + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _session(api_base: str, access_key: str) -> requests.Session:
    utils = APIUtils(api_endpoint=api_base)
    return utils.get_api_session_w_api_token(access_key)


def _fetch_failed_edges(session: requests.Session, gql_url: str) -> list[dict[str, Any]]:
    page_size = 50
    skip = 0
    out: list[dict[str, Any]] = []
    while True:
        resp = session.post(
            gql_url,
            json={"query": ACCESS_REQUEST_QUERY, "variables": {"skip": skip}},
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("errors"):
            raise RuntimeError(f"GraphQL errors: {json.dumps(body['errors'], indent=2)}")
        data = body.get("data") or {}
        am = data.get("AccessManagement") or {}
        conn = am.get("accessRequests") or {}
        edges = conn.get("edges") or []
        for edge in edges:
            node = edge.get("node")
            if node:
                out.append(node)
        if len(edges) < page_size:
            break
        skip += page_size
    return out


def _rows_from_nodes(nodes: list[dict[str, Any]]) -> list[FailedRequestRow]:
    rows: list[FailedRequestRow] = []
    for node in nodes:
        request_id = node.get("requestId") or ""
        st = (node.get("status") or {}) if isinstance(node.get("status"), dict) else {}
        status = st.get("status") or ""
        transitioned_raw = st.get("transitionedAt") or ""
        transitioned = _parse_transitioned_at(transitioned_raw)
        if status == "PROVISIONING_FAILED":
            proc = "PROVISIONING"
        elif status == "DEPROVISIONING_FAILED":
            proc = "DEPROVISIONING"
        else:
            proc = "STATE_UNSPECIFIED"
        rows.append(
            FailedRequestRow(
                request_id=request_id,
                status=status,
                transitioned_at_raw=transitioned_raw,
                transitioned_at=transitioned,
                processing_state=proc,
            )
        )
    return rows


def _filter_by_age(rows: list[FailedRequestRow], until_minutes: int, now: datetime) -> list[FailedRequestRow]:
    """Include a row iff transitioned_at_utc >= (now_utc - until_minutes).

    Steps: take current time in UTC, subtract ``until`` minutes → ``cutoff``;
    keep requests where ``transitionedAt`` is equal to ``cutoff`` or later (``>=``).
    """
    now_u = now.astimezone(timezone.utc)
    cutoff = now_u - timedelta(minutes=until_minutes)
    kept: list[FailedRequestRow] = []
    for r in rows:
        if r.transitioned_at is None:
            continue
        t = r.transitioned_at.astimezone(timezone.utc)
        if t >= cutoff:
            kept.append(r)
    return kept


def _print_table(rows: list[FailedRequestRow]) -> None:
    w_id, w_status, w_when = 38, 26, 32
    header = f"{'request_id':<{w_id}} {'status':<{w_status}} {'transitioned_at':<{w_when}}"
    print(header)
    print("-" * len(header))
    for r in rows:
        when = r.transitioned_at_raw or "(unknown)"
        print(f"{r.request_id:<{w_id}} {r.status:<{w_status}} {when:<{w_when}}")


def _retrigger(session: requests.Session, api_base: str, row: FailedRequestRow) -> tuple[bool, str]:
    url = f"{api_base}/accessrequests/retrigger-processing"
    body = {
        "retriggerProcessing": [
            {
                "accessRequestId": row.request_id,
                "processingState": row.processing_state,
            }
        ]
    }
    resp = session.post(
        url,
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    try:
        payload = resp.json()
    except ValueError:
        payload = {"raw": resp.text}
    if resp.status_code == 200 and payload.get("success") is True:
        return True, json.dumps(payload, indent=2)
    return False, f"HTTP {resp.status_code}: {json.dumps(payload, indent=2)}"


def _load_tenant_map(path: str) -> dict[str, str]:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise SystemExit(f"Multiple tenants file must be a JSON object (got {type(data).__name__}).")
    out: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str) or not v.strip():
            raise SystemExit("Each tenant entry must be a string key and non-empty string access key.")
        out[k] = v.strip()
    return out


def _resolve_effective_mode(*, dry_run: bool, retrigger: bool) -> tuple[str, str | None]:
    """Return (mode, stderr_warning_or_none). mode is dry_run | auto_retrigger | interactive."""
    if dry_run and retrigger:
        return (
            "dry_run",
            "Warning: --dry-run takes precedence over --retrigger; no retrigger calls will be made.",
        )
    if dry_run:
        return "dry_run", None
    if retrigger:
        return "auto_retrigger", None
    return "interactive", None


def _short_detail(text: str, max_len: int = 120) -> str:
    t = text.replace("\n", " ").strip()
    return t if len(t) <= max_len else t[: max_len - 3] + "..."


def _fetch_and_filter_for_tenant(
    *,
    api_base: str,
    gql_url: str,
    access_key: str,
    until_minutes: int,
    now: datetime,
) -> tuple[list[FailedRequestRow], int, str | None]:
    """Returns (filtered_rows, graphql_failed_row_count, tenant_error_or_none)."""
    try:
        session = _session(api_base, access_key)
        nodes = _fetch_failed_edges(session, gql_url)
        rows = _rows_from_nodes(nodes)
        filtered = _filter_by_age(rows, until_minutes, now)
        filtered.sort(key=lambda r: (r.status, r.transitioned_at_raw or ""))
        return filtered, len(rows), None
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        return [], 0, f"{type(e).__name__}: {e}"


def _print_candidate_summary(
    *,
    tenant_label: str | None,
    filtered: list[FailedRequestRow],
    graphql_failed_row_count: int,
    now: datetime,
    until_minutes: int,
) -> None:
    cutoff = now.astimezone(timezone.utc) - timedelta(minutes=until_minutes)
    prov = sum(1 for r in filtered if r.status == "PROVISIONING_FAILED")
    deprov = sum(1 for r in filtered if r.status == "DEPROVISIONING_FAILED")
    if tenant_label:
        print(f"=== Tenant: {tenant_label} ===")
    print("Summary")
    print(
        f"  Cutoff (UTC):            {cutoff.isoformat()}  "
        f"(now {now.isoformat()} minus {until_minutes} minutes)"
    )
    print(f"  PROVISIONING_FAILED:     {prov}")
    print(f"  DEPROVISIONING_FAILED:   {deprov}")
    print(
        f"  Total candidates:        {len(filtered)} "
        f"(transitionedAt >= cutoff); GraphQL failed rows (pre-filter): {graphql_failed_row_count}\n"
    )


def _print_combined_table(
    entries: list[tuple[str, FailedRequestRow, str | None, str | None]],
) -> None:
    """Each entry: (tenant_name, row, retrigger_ok_label or None, detail or None)."""
    w_t, w_id, w_status, w_when, w_ok, w_detail = 18, 36, 24, 28, 8, 40
    header = (
        f"{'tenant':<{w_t}} {'request_id':<{w_id}} {'status':<{w_status}} "
        f"{'transitioned_at':<{w_when}} {'ok?':<{w_ok}} {'detail':<{w_detail}}"
    )
    print(header)
    print("-" * len(header))
    for tenant, r, ok_lab, detail in entries:
        when = r.transitioned_at_raw or "(unknown)"
        ok_s = ok_lab if ok_lab is not None else "-"
        det = _short_detail(detail or "", w_detail) if detail else "-"
        print(
            f"{tenant:<{w_t}} {r.request_id:<{w_id}} {r.status:<{w_status}} "
            f"{when:<{w_when}} {ok_s:<{w_ok}} {det:<{w_detail}}"
        )


def _print_failures_section(failures: list[tuple[str, FailedRequestRow | None, str]]) -> None:
    if not failures:
        return
    print()
    print("=== FAILURES ===")
    rows_out: list[tuple[str, FailedRequestRow, str | None, str | None]] = []
    for tenant, row, msg in failures:
        if row is None:
            placeholder = FailedRequestRow(
                request_id="(none)",
                status="(n/a)",
                transitioned_at_raw="(n/a)",
                transitioned_at=None,
                processing_state="(n/a)",
            )
            rows_out.append((tenant, placeholder, "no", _short_detail(msg, 200)))
        else:
            rows_out.append((tenant, row, "no", _short_detail(msg, 200)))
    _print_combined_table(rows_out)


def _run_single_tenant(
    *,
    mode: str,
    api_base: str,
    gql_url: str,
    access_key: str,
    until_minutes: int,
    now: datetime,
) -> int:
    """Returns process exit code (0 or 1)."""
    cutoff = now.astimezone(timezone.utc) - timedelta(minutes=until_minutes)
    filtered, gql_count, terr = _fetch_and_filter_for_tenant(
        api_base=api_base,
        gql_url=gql_url,
        access_key=access_key,
        until_minutes=until_minutes,
        now=now,
    )
    if terr:
        print(terr)
        _print_failures_section([("-", None, terr)])
        return 1
    if not filtered:
        print(
            f"No matching requests "
            f"(GraphQL returned {gql_count} failed rows; "
            f"none with transitionedAt >= {cutoff.isoformat()} (UTC))."
        )
        return 0

    _print_candidate_summary(
        tenant_label=None,
        filtered=filtered,
        graphql_failed_row_count=gql_count,
        now=now,
        until_minutes=until_minutes,
    )
    _print_table(filtered)
    print()

    if mode == "dry_run":
        return 0

    session = _session(api_base, access_key)
    failures: list[tuple[str, FailedRequestRow | None, str]] = []

    if mode == "auto_retrigger":
        report_rows: list[tuple[str, FailedRequestRow, str | None, str | None]] = []
        for row in filtered:
            ok, detail = _retrigger(session, api_base, row)
            report_rows.append(("-", row, "yes" if ok else "no", detail if not ok else None))
            if not ok:
                failures.append(("-", row, detail))
        print("Retrigger results (all rows)")
        _print_combined_table(report_rows)
        _print_failures_section(failures)
        return 0 if not failures else 1

    # interactive
    for row in filtered:
        print("-" * 72)
        print(f"request_id:      {row.request_id}")
        print(f"status:          {row.status}")
        print(f"transitioned_at: {row.transitioned_at_raw}")
        print(f"retrigger state: {row.processing_state}")
        ans = input("Retrigger this access request? [y/N]: ").strip().lower()
        if ans != "y":
            print("Skipped.\n")
            continue
        ok, detail = _retrigger(session, api_base, row)
        if ok:
            print("Retrigger submitted successfully.")
            print(detail)
        else:
            print("Retrigger failed.")
            print(detail)
            failures.append(("-", row, detail))
        print()

    _print_failures_section(failures)
    return 0 if not failures else 1


def _run_multiple_tenants(
    *,
    mode: str,
    api_base: str,
    gql_url: str,
    tenants: dict[str, str],
    until_minutes: int,
    now: datetime,
) -> int:
    """Returns process exit code (0 or 1)."""
    cutoff = now.astimezone(timezone.utc) - timedelta(minutes=until_minutes)
    all_failures: list[tuple[str, FailedRequestRow | None, str]] = []
    combined_report: list[tuple[str, FailedRequestRow, str | None, str | None]] = []
    total_candidates = 0
    tenants_ok = 0

    print(
        f"Multi-tenant run — cutoff (UTC): {cutoff.isoformat()} "
        f"(now {now.isoformat()} minus {until_minutes} minutes)\n"
    )

    for tenant_name, access_key in tenants.items():
        filtered, gql_count, terr = _fetch_and_filter_for_tenant(
            api_base=api_base,
            gql_url=gql_url,
            access_key=access_key,
            until_minutes=until_minutes,
            now=now,
        )
        if terr:
            all_failures.append((tenant_name, None, terr))
            print(f"{tenant_name}: ERROR — {_short_detail(terr, 200)}")
            continue

        tenants_ok += 1
        total_candidates += len(filtered)
        print(f"{tenant_name}: {len(filtered)} candidate(s) after filter (GraphQL failed rows: {gql_count})")

        if mode == "dry_run":
            for r in filtered:
                combined_report.append((tenant_name, r, None, None))
            continue

        if mode == "auto_retrigger":
            session = _session(api_base, access_key)
            for row in filtered:
                ok, detail = _retrigger(session, api_base, row)
                combined_report.append((tenant_name, row, "yes" if ok else "no", detail if not ok else None))
                if not ok:
                    all_failures.append((tenant_name, row, detail))
            continue

        # interactive per tenant
        if not filtered:
            print(f"  (no candidates for {tenant_name})\n")
            continue
        _print_candidate_summary(
            tenant_label=tenant_name,
            filtered=filtered,
            graphql_failed_row_count=gql_count,
            now=now,
            until_minutes=until_minutes,
        )
        _print_table(filtered)
        print()
        session = _session(api_base, access_key)
        for row in filtered:
            print("-" * 72)
            print(f"tenant:          {tenant_name}")
            print(f"request_id:      {row.request_id}")
            print(f"status:          {row.status}")
            print(f"transitioned_at: {row.transitioned_at_raw}")
            print(f"retrigger state: {row.processing_state}")
            ans = input("Retrigger this access request? [y/N]: ").strip().lower()
            if ans != "y":
                print("Skipped.\n")
                continue
            ok, detail = _retrigger(session, api_base, row)
            if ok:
                print("Retrigger submitted successfully.")
                print(detail)
            else:
                print("Retrigger failed.")
                print(detail)
                all_failures.append((tenant_name, row, detail))
            print()

    if mode in ("dry_run", "auto_retrigger"):
        print()
        if not combined_report and not all_failures:
            print("No matching requests for any tenant (no failures).")
            return 0
        if combined_report:
            print("=== COMBINED CANDIDATES ===")
            _print_combined_table(combined_report)

    print()
    print("=== SUMMARY ===")
    print(f"  Tenants in file:           {len(tenants)}")
    print(f"  Tenants fetched OK:       {tenants_ok}")
    print(f"  Total candidates (sum):  {total_candidates}")
    print(f"  Mode:                      {mode}")

    _print_failures_section(all_failures)
    return 0 if not all_failures else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch PROVISIONING_FAILED / DEPROVISIONING_FAILED access requests, "
            "keep those with transitionedAt (UTC) >= (current UTC time - N minutes), then "
            "optionally retrigger processing (admin API)."
        )
    )
    parser.add_argument(
        "--api",
        default=os.environ.get("AS_API_ENDPOINT"),
        help="REST host, e.g. https://api.staging.andromedasecurity.com or http://localhost:8080 (no path; default: AS_API_ENDPOINT).",
    )
    parser.add_argument(
        "--gql",
        default=None,
        help="Optional GraphQL host if it differs from --api (same scheme://host:port form; path /graphql is appended).",
    )
    parser.add_argument(
        "--access_key",
        default=None,
        help="Access-key code for POST /login/access-key (default: AS_API_TOKEN). Not used with --multiple-tenants.",
    )
    parser.add_argument(
        "--until",
        type=int,
        required=True,
        help=(
            "Include requests where transitionedAt (UTC) >= (current UTC time minus this many minutes). "
            "Equality at that cutoff counts as included. Example: 60 → fail time within the last hour or exactly at the hour boundary."
        ),
    )
    parser.add_argument(
        "--multiple-tenants",
        metavar="PATH",
        default=None,
        help="JSON file: object mapping tenant_name -> access_key code. Unset AS_API_TOKEN; omit --access_key.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matching failed access requests only; do not call retrigger API.",
    )
    parser.add_argument(
        "--retrigger",
        action="store_true",
        help="Automatically retrigger every matching row (no y/N prompts).",
    )
    args = parser.parse_args()

    api_base = _api_base(args.api)
    if args.until < 0:
        raise SystemExit("--until must be non-negative.")

    mode, mode_warn = _resolve_effective_mode(dry_run=args.dry_run, retrigger=args.retrigger)
    if mode_warn:
        print(mode_warn, file=sys.stderr)

    gql_url = _resolve_gql_url(args.gql, api_base)
    now = datetime.now(timezone.utc)

    if args.multiple_tenants:
        if args.access_key:
            raise SystemExit(
                "With --multiple-tenants, do not pass --access_key; use only the JSON map for credentials."
            )
        if os.environ.get("AS_API_TOKEN"):
            raise SystemExit(
                "With --multiple-tenants, unset AS_API_TOKEN; use only the JSON map for credentials."
            )
        tenants = _load_tenant_map(args.multiple_tenants)
        code = _run_multiple_tenants(
            mode=mode,
            api_base=api_base,
            gql_url=gql_url,
            tenants=tenants,
            until_minutes=args.until,
            now=now,
        )
        raise SystemExit(code)

    access_key = (args.access_key or os.environ.get("AS_API_TOKEN") or "").strip()
    if not access_key:
        raise SystemExit("access_key is required (--access_key or AS_API_TOKEN).")

    code = _run_single_tenant(
        mode=mode,
        api_base=api_base,
        gql_url=gql_url,
        access_key=access_key,
        until_minutes=args.until,
        now=now,
    )
    raise SystemExit(code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
