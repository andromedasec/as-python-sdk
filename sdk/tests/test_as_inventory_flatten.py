"""Unit tests for the Users -> providers -> assignments flattening, and for the count
and UAR-activity queries on the same Identity/Users paths, and for the agent
tool-applications page.

No server needed: these exercise the pure response-shaping helper that decides how
much of a GraphQL response actually reaches the caller, and check the queries the
count methods build against the repo's GraphQL schema.
"""
import logging
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from graphql import build_schema, print_ast

from sdk.as_inventory import NESTED_PAGE_SIZE, AndromedaInventory


def _user_edge(provider_edges):
    return {"node": {"id": "u-1", "userProviderData": {"edges": provider_edges}}}


def _provider_edge(provider_id, provider_name, assignments):
    return {
        "node": {"id": provider_id, "name": provider_name},
        "userProviderData": {
            "userResolvedAssignments": {
                "edges": [{"node": a} for a in assignments],
            }
        },
    }


def test_every_provider_edge_is_kept():
    """Reading edges[0] dropped every provider but the first, which reads downstream
    as "no such access" rather than as a truncation."""
    edges = [_user_edge([
        _provider_edge("p-1", "Downloader Script", [{"roleName": "Modify"}]),
        _provider_edge("p-2", "Beatles Azure", [{"roleName": "Storage Account Contributor"}]),
    ])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert [a["providerName"] for a in result] == ["Downloader Script", "Beatles Azure"]
    assert [a["providerId"] for a in result] == ["p-1", "p-2"]


def test_every_user_edge_is_kept():
    """A Users query filtered by identityId matches one edge per incarnation."""
    edges = [
        _user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader"}])]),
        _user_edge([_provider_edge("p-2", "Azure", [{"roleName": "Contributor"}])]),
    ]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert [a["roleName"] for a in result] == ["Reader", "Contributor"]


def test_provider_tags_do_not_overwrite_the_assignment_s_own():
    edges = [_user_edge([
        _provider_edge("p-1", "Provider Node Name",
                       [{"roleName": "Modify", "providerName": "Assignment Name"}]),
    ])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert result[0]["providerName"] == "Assignment Name"
    assert result[0]["providerId"] == "p-1"


def test_empty_and_missing_levels_flatten_to_nothing():
    assert AndromedaInventory._flatten_user_provider_assignments([]) == []
    assert AndromedaInventory._flatten_user_provider_assignments(None) == []
    assert AndromedaInventory._flatten_user_provider_assignments([{"node": {}}]) == []
    assert AndromedaInventory._flatten_user_provider_assignments([_user_edge([])]) == []


# ---------------------------------------------------------------------------
# as_identity_resolved_assignments_itr — paging and truncation visibility
# ---------------------------------------------------------------------------


def _inventory():
    """An AndromedaInventory with no network: __init__ is skipped deliberately."""
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.default_page_size = 100
    return inv


def test_the_iterator_pages_over_users_and_flattens_each_page():
    """The Users dimension is what gets paged (one edge per incarnation); the nested
    provider/assignment connections come back whole."""
    inv = _inventory()
    pages = [
        [_user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader"}])]),
         _user_edge([_provider_edge("p-2", "Azure", [{"roleName": "Contributor"}])])],
        [_user_edge([_provider_edge("p-3", "GCP", [{"roleName": "Viewer"}])])],
    ]
    seen_skips = []

    def _base_fn(identity_id, assignment_filters, page_size, skip):
        seen_skips.append(skip)
        return pages[skip // page_size] if skip // page_size < len(pages) else []

    inv.as_identity_resolved_assignments_base_fn = _base_fn

    with patch("sdk.as_inventory.time.sleep"):
        result = list(inv.as_identity_resolved_assignments_itr("identity-1", page_size=2))

    assert [a["roleName"] for a in result] == ["Reader", "Contributor", "Viewer"]
    assert seen_skips == [0, 2], "expected a second page request at skip=2"


def test_the_iterator_stops_on_a_short_page():
    inv = _inventory()
    calls = []

    def _base_fn(identity_id, assignment_filters, page_size, skip):
        calls.append(skip)
        return [_user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader"}])])]

    inv.as_identity_resolved_assignments_base_fn = _base_fn

    result = list(inv.as_identity_resolved_assignments_itr("identity-1", page_size=10))

    assert len(result) == 1
    assert calls == [0], "a short page should end the iteration"


def test_the_iterator_returns_nothing_for_an_identity_with_no_users():
    inv = _inventory()
    inv.as_identity_resolved_assignments_base_fn = lambda *a, **k: []

    assert list(inv.as_identity_resolved_assignments_itr("identity-1")) == []


def test_a_full_nested_page_is_logged_rather_than_silently_truncated(caplog):
    """The nested connections are fetched in one page. If one fills up the answer may
    be incomplete, and an incomplete answer about someone's access must not look
    indistinguishable from a complete one."""
    from sdk.as_inventory import NESTED_PAGE_SIZE

    assignments = [{"roleName": f"role-{i}"} for i in range(NESTED_PAGE_SIZE)]
    edges = [_user_edge([_provider_edge("p-1", "Beatles Azure", assignments)])]

    with caplog.at_level(logging.WARNING, logger="sdk.as_inventory"):
        AndromedaInventory._warn_on_nested_page_cap("identity-1", edges)

    assert any("may be truncated" in r.getMessage() for r in caplog.records), caplog.text


def test_no_warning_when_the_nested_pages_are_not_full(caplog):
    edges = [_user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader"}])])]

    with caplog.at_level(logging.WARNING, logger="sdk.as_inventory"):
        AndromedaInventory._warn_on_nested_page_cap("identity-1", edges)

    assert caplog.records == []


# ---------------------------------------------------------------------------
# scope — what distinguishes two otherwise-identical assignments
# ---------------------------------------------------------------------------


def test_scope_is_flattened_onto_the_assignment():
    """Flattened, not nested: consumers render these as columns, and a nested object
    costs tokens in the agent's tool responses."""
    edges = [_user_edge([_provider_edge("p-1", "Beatles Azure", [{
        "roleName": "Storage Account Contributor",
        "scope": {"id": "s-1", "name": "Bealtes-Apps-RG",
                  "type": "RESOURCE_GROUP", "isInherited": False},
    }])])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert result[0]["scopeName"] == "Bealtes-Apps-RG"
    assert result[0]["scopeType"] == "RESOURCE_GROUP"
    assert result[0]["scopeIsInherited"] is False
    assert "scope" not in result[0]


def test_same_role_and_policy_at_different_scopes_are_both_kept():
    """Real shape from the Beatles tenant: one Storage Account Contributor grant on a
    single storage account, one on the resource group above it — same policyId. Merging
    them on (providerId, policyId) would drop the broader, riskier grant."""
    edges = [_user_edge([_provider_edge("p-azure", "Beatles Azure", [
        {"roleName": "Storage Account Contributor", "policyId": "pol-1", "blastRisk": 0,
         "scope": {"id": "s-1", "name": "beatleslogblobstore", "type": "RESOURCE"}},
        {"roleName": "Storage Account Contributor", "policyId": "pol-1", "blastRisk": 76,
         "scope": {"id": "s-2", "name": "Bealtes-Apps-RG", "type": "RESOURCE_GROUP"}},
    ])])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert len(result) == 2
    assert {r["scopeName"] for r in result} == {"beatleslogblobstore", "Bealtes-Apps-RG"}
    assert {r["scopeType"] for r in result} == {"RESOURCE", "RESOURCE_GROUP"}
    # The rows are indistinguishable without scope — that is the whole point.
    assert len({(r["policyId"], r["roleName"]) for r in result}) == 1


def test_an_assignment_without_a_scope_is_untouched():
    edges = [_user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader"}])])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert result[0] == {"roleName": "Reader", "providerId": "p-1", "providerName": "AWS"}


def test_provider_type_is_tagged_when_the_provider_node_has_one():
    edge = _provider_edge("p-1", "Entra", [{"roleName": "Reader"}])
    edge["node"]["type"] = "PROVIDER_TYPE_ENTRA"

    result = AndromedaInventory._flatten_user_provider_assignments([_user_edge([edge])])

    assert result[0]["providerType"] == "PROVIDER_TYPE_ENTRA"


def test_a_null_scope_does_not_leave_a_stray_key():
    edges = [_user_edge([_provider_edge("p-1", "AWS", [{"roleName": "Reader", "scope": None}])])]

    result = AndromedaInventory._flatten_user_provider_assignments(edges)

    assert "scope" not in result[0] and "scopeName" not in result[0]


# ---------------------------------------------------------------------------
# providers-with-assignments — account in a provider != assignment in it
# ---------------------------------------------------------------------------


def _provider_edge_with_count(provider_id, provider_name, count):
    return {
        "node": {"id": provider_id, "name": provider_name},
        "userProviderData": {
            "userResolvedAssignments": {"pageInfo": {"count": count}},
        },
    }


def _itr_over_pages(pages, page_size=2):
    """Run as_user_providers_with_assignments_itr over canned base_fn pages.

    Built on a bare instance so the iterator's real paging loop (as_gql_generic_itr)
    runs — that loop is what the page_size-termination bug lived in, so a test that
    stubbed it out could not see the regression.
    """
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.default_page_size = page_size
    calls = []

    # Signature mirrors the real base_fn: functools.partial binds user_id/username/
    # filters first, so page_size and skip arrive last.
    def _base_fn(user_id, username, filters, size, skip):
        calls.append(skip)
        index = skip // size
        return pages[index] if index < len(pages) else []

    inv.as_user_providers_with_assignments_base_fn = _base_fn
    providers = list(inv.as_user_providers_with_assignments_itr(
        "u-1", page_size=page_size))
    return providers, calls


def test_every_provider_row_is_returned_so_paging_can_terminate_correctly():
    """The base function must not filter: as_gql_generic_itr stops paging when a page
    comes back shorter than page_size, so dropping the empty providers here made a full
    page look like the last one and truncated everything after it."""
    edges = [_user_edge([
        _provider_edge_with_count("p-1", "Beatles Azure", 2),
        _provider_edge_with_count("p-2", "Beatles Entra", 0),
        _provider_edge_with_count("p-3", "Beatles Workday", 0),
    ])]

    result = AndromedaInventory._providers_with_assignment_counts(edges)

    assert [(p["name"], c) for p, c in result] == [
        ("Beatles Azure", 2), ("Beatles Entra", 0), ("Beatles Workday", 0),
    ]


def test_a_full_page_of_empty_providers_does_not_end_the_iteration():
    """The regression: a user with a full page of accounts none of which hold an
    assignment. Filtering in the base function returned zero rows, the paging loop read
    that as the last page, and every provider on page 2 was lost."""
    page_1 = [({"id": "p-1", "name": "Beatles Entra"}, 0),
              ({"id": "p-2", "name": "Beatles Workday"}, 0)]
    page_2 = [({"id": "p-3", "name": "Beatles Azure"}, 4)]

    providers, calls = _itr_over_pages([page_1, page_2])

    assert [p["name"] for p in providers] == ["Beatles Azure"]
    assert calls == [0, 2], "the iterator must have asked for the second page"


def test_providers_with_no_assignments_are_dropped_while_yielding():
    """Chip has accounts in Entra and Workday but holds nothing there. Reporting them
    tells the model he has access he does not have, and costs a query per empty
    provider to find out otherwise."""
    page = [({"id": "p-1", "name": "Beatles Azure"}, 2),
            ({"id": "p-2", "name": "Beatles Entra"}, 0)]

    providers, _ = _itr_over_pages([page])

    assert [p["name"] for p in providers] == ["Beatles Azure"]


def test_providers_are_deduped_across_pages_not_just_within_one():
    """A provider can appear under more than one incarnation, and the incarnations can
    straddle a page boundary — a `seen` set that resets per page yields it twice."""
    page_1 = [({"id": "p-1", "name": "Beatles Azure"}, 2),
              ({"id": "p-2", "name": "Downloader Script"}, 1)]
    page_2 = [({"id": "p-1", "name": "Beatles Azure"}, 2)]

    providers, _ = _itr_over_pages([page_1, page_2])

    assert [p["id"] for p in providers] == ["p-1", "p-2"]


def test_a_missing_count_is_treated_as_no_assignments():
    edges = [_user_edge([
        {"node": {"id": "p-1", "name": "No userProviderData"}},
        {"node": {"id": "p-2", "name": "Empty pageInfo"},
         "userProviderData": {"userResolvedAssignments": {}}},
    ])]

    rows = AndromedaInventory._providers_with_assignment_counts(edges)

    assert [c for _, c in rows] == [0, 0]
    providers, _ = _itr_over_pages([rows])
    assert providers == []


def test_no_users_means_no_providers():
    assert AndromedaInventory._providers_with_assignment_counts([]) == []
    assert AndromedaInventory._providers_with_assignment_counts(None) == []


# ---------------------------------------------------------------------------
# filter keys — the server ignores unknown ones instead of rejecting them
# ---------------------------------------------------------------------------


def test_no_query_filters_on_a_providerId_key():
    """`UserProviderDataFilters` and `IdentityProviderFilters` both expose `id`, not
    `providerId`. Passing `providerId` is not an error the server reports — it is
    silently ignored, so the query returns every provider and the caller cannot tell
    it got someone else's data. Nothing in the SDK may reintroduce that key.
    """
    import inspect
    import re

    from sdk import as_inventory

    source = inspect.getsource(as_inventory)
    # Match a filters dict literal keyed on providerId, in either quote style.
    offenders = re.findall(r"filters\s*=\s*\{\s*['\"]providerId['\"]", source)

    assert not offenders, (
        f"{len(offenders)} filter dict(s) keyed on 'providerId' — use 'id'"
    )


# ---------------------------------------------------------------------------
# Count queries behind get_identity_access_assignments' providers block
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _repo_schema_or_skip():
    """The GraphQL schema from the repo's schema files (generated by make gen)."""
    generated = sorted((_REPO_ROOT / "lib/go/api/graphql/schema").glob("*.graphqls"))
    if not generated:
        pytest.skip("generated GraphQL schema absent (make gen)")
    files = generated + sorted((_REPO_ROOT / "records/graphql").glob("*.graphqls"))
    return build_schema("type Query\n" + "\n".join(path.read_text() for path in files),
                        assume_valid_sdl=True)


def _count_inventory(data):
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = _repo_schema_or_skip()
    inv.gql_client.execute.return_value.formatted = {"data": data}
    return inv


def _printed(query):
    """An executed query as text, the same under gql 3 / graphql-core 3.2 and
    gql 4 / graphql-core 3.3: gql 4 wraps the DocumentNode in a GraphQLRequest,
    and graphql-core 3.3 prints inline objects as `{ a: 1 }` rather than `{a: 1}`."""
    text = print_ast(getattr(query, "document", query))
    while True:
        compact = re.sub(r"\{ ([^{}\n]*) \}", r"{\1}", text)
        if compact == text:
            return text
        text = compact


def _count_query(inv):
    return _printed(inv.gql_client.execute.call_args[0][0])


def _count_provider_edge(pid, name, ptype, count):
    return {"node": {"id": pid, "name": name, "type": ptype},
            "userProviderData": {"userResolvedAssignments": {"pageInfo": {"count": count}}}}


def test_totals_sum_incarnations_and_flag_truncation():
    inv = _count_inventory({"Users": {"edges": [
        {"node": {"userProviderData": {"edges": [
            _count_provider_edge("p-aws", "AWS", "PROVIDER_TYPE_AWS", NESTED_PAGE_SIZE + 5),
            _count_provider_edge("p-entra", "Entra", "PROVIDER_TYPE_ENTRA", 3),
        ]}}},
        {"node": {"userProviderData": {"edges": [
            _count_provider_edge("p-entra", "Entra", "PROVIDER_TYPE_ENTRA", 2),
        ]}}},
    ]}})
    totals = {t["providerId"]: t for t in inv.fetch_identity_assignment_totals(
        "idn-1", assignment_filters={"significance": {"in": ["ADMIN_PRIVILEGES"]}})}
    assert totals["p-aws"] == {"providerId": "p-aws", "providerName": "AWS",
                               "providerType": "PROVIDER_TYPE_AWS",
                               "total": NESTED_PAGE_SIZE + 5, "truncated": True}
    assert totals["p-entra"]["total"] == 5
    assert totals["p-entra"]["truncated"] is False
    query = _count_query(inv)
    assert "pageSize: 1" in query
    assert "ADMIN_PRIVILEGES" in query


def test_totals_with_no_users_is_empty():
    assert _count_inventory({"Users": {"edges": []}}).fetch_identity_assignment_totals("idn-1") == []


def test_indirect_counts_exclude_unified_types_in_the_request():
    inv = _count_inventory({"Identity": {"providersData": {"edges": [
        {"node": {"providerId": "p-aws",
                  "userResolvedAssignments": {"pageInfo": {"count": 7}}}},
    ]}}})
    counts = inv.fetch_identity_indirect_assignment_counts(
        "idn-1", exclude_provider_types=["PROVIDER_TYPE_ENTRA", "PROVIDER_TYPE_OKTA"])
    assert counts == {"p-aws": 7}
    query = _count_query(inv)
    assert "notIn: [PROVIDER_TYPE_ENTRA, PROVIDER_TYPE_OKTA]" in query
    assert "INDIRECT_ASSIGNMENT" in query
    assert "pageSize: 1" in query


def test_indirect_counts_with_null_identity_is_empty():
    inv = _count_inventory({"Identity": None})
    assert inv.fetch_identity_indirect_assignment_counts("idn-x", exclude_provider_types=[]) == {}


def _paged_count_inventory(pages):
    """An AndromedaInventory whose gql client answers each execute() with the next page's data."""
    inv = _count_inventory({})
    inv.gql_client.execute.side_effect = [MagicMock(formatted={"data": page}) for page in pages]
    return inv


def _count_user(uid, provider_edges, provider_count=None):
    return {"node": {"id": uid, "userProviderData": {
        "edges": provider_edges,
        "pageInfo": {"count": len(provider_edges) if provider_count is None else provider_count}}}}


def test_totals_read_every_users_page():
    first = [_count_user(f"u-{i}", [_count_provider_edge("p-aws", "AWS", "PROVIDER_TYPE_AWS", 1)])
             for i in range(NESTED_PAGE_SIZE)]
    inv = _paged_count_inventory([
        {"Users": {"edges": first, "pageInfo": {"count": NESTED_PAGE_SIZE + 1}}},
        {"Users": {"edges": [_count_user("u-last", [_count_provider_edge("p-aws", "AWS", "PROVIDER_TYPE_AWS", 4)])],
                   "pageInfo": {"count": NESTED_PAGE_SIZE + 1}}},
    ])
    totals = inv.fetch_identity_assignment_totals("idn-1")
    assert totals == [{"providerId": "p-aws", "providerName": "AWS", "providerType": "PROVIDER_TYPE_AWS",
                       "total": NESTED_PAGE_SIZE + 4, "truncated": False}]
    assert inv.gql_client.execute.call_count == 2
    assert f"skip: {NESTED_PAGE_SIZE}" in _count_query(inv)


def test_totals_count_providers_past_the_row_cap_and_flag_them_truncated():
    first = [_count_provider_edge(f"p-{i}", f"P{i}", "PROVIDER_TYPE_AWS", 1) for i in range(NESTED_PAGE_SIZE)]
    inv = _paged_count_inventory([
        {"Users": {"edges": [_count_user("u-1", first, provider_count=NESTED_PAGE_SIZE + 1)],
                   "pageInfo": {"count": 1}}},
        {"Users": {"edges": [_count_user("u-1", [_count_provider_edge("p-late", "Late", "PROVIDER_TYPE_AWS", 6)])]}},
    ])
    totals = {t["providerId"]: t for t in inv.fetch_identity_assignment_totals("idn-1")}
    assert len(totals) == NESTED_PAGE_SIZE + 1
    assert totals["p-late"]["total"] == 6
    assert totals["p-late"]["truncated"] is True  # the row query cannot return it
    assert totals["p-0"]["truncated"] is False
    query = _count_query(inv)
    assert 'id: {equals: "u-1"}' in query
    assert f"skip: {NESTED_PAGE_SIZE}" in query


def test_indirect_counts_read_every_providers_page():
    def edge(i):
        return {"node": {"providerId": f"p-{i}", "userResolvedAssignments": {"pageInfo": {"count": 1}}}}
    inv = _paged_count_inventory([
        {"Identity": {"providersData": {"edges": [edge(i) for i in range(NESTED_PAGE_SIZE)],
                                        "pageInfo": {"count": NESTED_PAGE_SIZE + 1}}}},
        {"Identity": {"providersData": {"edges": [edge("last")],
                                        "pageInfo": {"count": NESTED_PAGE_SIZE + 1}}}},
    ])
    counts = inv.fetch_identity_indirect_assignment_counts("idn-1", exclude_provider_types=[])
    assert len(counts) == NESTED_PAGE_SIZE + 1
    assert counts["p-last"] == 1
    assert f"skip: {NESTED_PAGE_SIZE}" in _count_query(inv)


# ---------------------------------------------------------------------------
# UAR activity of one identity (get_identity_uar_activity)
# ---------------------------------------------------------------------------


def test_uar_identity_queries_select_the_tool_fields():
    inv = _count_inventory({"Identity": None})
    inv.gql_client.execute.return_value = {"Identity": None}
    assert inv.fetch_identity_reviewer_campaigns("idn-1") is None
    reviewer = _printed(inv.gql_client.execute.call_args[0][0])
    for field in ("reviewerCampaigns(pageArgs: {pageSize: 25})", "reviewerStatus",
                  "reviewsGroupedByStatus", "targetCompletionTime"):
        assert field in reviewer
    assert inv.fetch_identity_owned_campaigns("idn-1") is None
    owner = _printed(inv.gql_client.execute.call_args[0][0])
    assert "campaignOwnersData" in owner and "campaigns(pageArgs: {pageSize: 25})" in owner


# ---------------------------------------------------------------------------
# Agent tool applications (get_tool_applications_list)
# ---------------------------------------------------------------------------


def test_tool_applications_page_flattens_rows_and_caps_owners():
    inv = _count_inventory({"ToolApplications": {"pageInfo": {"count": 1}, "edges": [{"node": {
        "id": "app-1", "name": "Jira MCP", "toolType": "MCP_SERVER",
        "agentAccessSummary": {"numAgents": 3, "maxRiskLevel": "HIGH"},
        "owners": {"pageInfo": {"count": 12}, "edges": [
            {"node": {"identity": {"id": "idn-1", "name": "Ana", "email": "ana@x.io"}}}]},
    }}]}})
    rows, total = inv.fetch_tool_applications_page(filters=None, page_size=10, skip=0)
    assert total == 1
    assert rows[0]["owners"] == [{"id": "idn-1", "name": "Ana", "email": "ana@x.io"}]
    assert rows[0]["owners_count"] == 12
    assert rows[0]["numAgents"] == 3
    assert rows[0]["maxRiskLevel"] == "HIGH"
    assert "agentAccessSummary" not in rows[0]
    assert "pageSize: 10" in _printed(inv.gql_client.execute.call_args[0][0])


def test_tool_applications_page_without_owners():
    inv = _count_inventory({"ToolApplications": {"pageInfo": {"count": 1}, "edges": [{"node": {
        "id": "app-2", "name": "Drive", "owners": None, "agentAccessSummary": None}}]}})
    rows, _ = inv.fetch_tool_applications_page(filters=None, page_size=10, skip=0)
    assert rows[0]["owners"] == []
    assert rows[0]["owners_count"] == 0
