"""Unit tests for the Users -> providers -> assignments flattening.

No server needed: these exercise the pure response-shaping helper that decides how
much of a GraphQL response actually reaches the caller.
"""
import logging
from unittest.mock import patch

from sdk.as_inventory import AndromedaInventory


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
