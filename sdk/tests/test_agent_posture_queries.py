"""The AI agent posture reads used by the Cosmos agent tools: each query must build and
validate against the repo's GraphQL schema, and each response must be shaped the way the
tools expect. No server needed.

Queries the repo schema may not have yet (policy usage, platform-discovered tools) are
checked only when the generated schema carries them; the tools gate them at runtime on
the live server's schema (has_agent_policy_usage / has_application_discovered_tools).
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from graphql import build_schema, print_ast, validate
from gql.transport.exceptions import TransportQueryError

from sdk.as_inventory import AGENT_LIST_FIELDS, AndromedaInventory

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _schema_or_skip():
    generated = sorted((_REPO_ROOT / "lib/go/api/graphql/schema").glob("*.graphqls"))
    if not generated:
        pytest.skip("generated GraphQL schema absent (make gen)")
    files = generated + sorted((_REPO_ROOT / "records/graphql").glob("*.graphqls"))
    return build_schema("type Query\n" + "\n".join(p.read_text() for p in files),
                        assume_valid_sdl=True)


def _inventory(data=None, error=None):
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = _schema_or_skip()
    if error is not None:
        inv.gql_client.execute.side_effect = error
    else:
        inv.gql_client.execute.return_value.formatted = {"data": data or {}}
    return inv


def _assert_valid(inv):
    query = inv.gql_client.execute.call_args[0][0]
    document = getattr(query, "document", query)
    errors = validate(inv.gql_client.schema, document)
    assert not errors, [str(e) for e in errors]


def _agent_node(**extra):
    node = {"id": "a1", "name": "Helper", "type": "GOOGLE_AGENT_ENGINE",
            "opsInsights": [{"type": "UNRESTRICTED_ACCESS", "level": "INSIGHT"}],
            "owners": {"edges": [{"node": {"identity": {"email": "o@x.com"}}}],
                       "pageInfo": {"count": 4}}}
    node.update(extra)
    return node


# ---------------------------------------------------------------------------
# Agents list
# ---------------------------------------------------------------------------


def test_agents_page_query_is_valid_and_carries_findings_and_owners():
    inv = _inventory({"Agents": {"edges": [{"node": _agent_node()}], "pageInfo": {"count": 9}}})
    rows, total, restricted = inv.fetch_agents_page(
        filters={"significance": {"in": ["EXCESSIVE_AGENCY"]}}, page_size=5, skip=10)
    _assert_valid(inv)
    assert total == 9 and restricted == []
    assert rows[0]["owners"] == ["o@x.com"] and rows[0]["owners_count"] == 4
    assert rows[0]["opsInsights"][0]["type"] == "UNRESTRICTED_ACCESS"


def test_agents_page_selects_every_list_field():
    inv = _inventory({"Agents": {"edges": [], "pageInfo": {"count": 0}}})
    inv.fetch_agents_page(filters=None, page_size=1)
    query = inv.gql_client.execute.call_args[0][0]
    text = print_ast(getattr(query, "document", query))
    for field in AGENT_LIST_FIELDS + ("opsInsights", "owners"):
        assert field in text, field


def test_a_field_the_role_may_not_read_is_reported_not_fatal():
    """A USER may not read opsInsights: the rows still come back, with the path listed."""
    partial = TransportQueryError(
        "denied", errors=[{"message": "insufficient permissions",
                           "path": ["Agents", "edges", 0, "node", "opsInsights"]}],
        data={"Agents": {"edges": [{"node": _agent_node(opsInsights=None)}],
                         "pageInfo": {"count": 1}}})
    inv = _inventory(error=partial)
    rows, total, restricted = inv.fetch_agents_page(filters=None, page_size=5)
    assert total == 1 and rows[0]["id"] == "a1"
    assert "opsInsights" in restricted


# ---------------------------------------------------------------------------
# One agent in depth
# ---------------------------------------------------------------------------


def test_agent_detail_query_is_valid_and_flattened():
    node = _agent_node(
        applications={"edges": [{"toolApplication": {"id": "t1", "name": "GitHub",
                                                      "toolType": "MCP_SERVER"},
                                 "agentApplicationInfo": {
                                     "connection": {"name": "default", "authType": "OAUTH"},
                                     "connectors": [{"name": "gh", "isShared": True}]}}],
                      "pageInfo": {"count": 3}},
        topTools={"tools": [{"toolName": "merge_pull_request", "callCount": 5}]},
        usersWithAccess={"edges": [{"node": {"username": "u@x.com"}}], "pageInfo": {"count": 12}},
        models={"edges": [{"node": {"name": "gemini", "version": "2.5"}}]},
        knowledgeBases={"edges": [{"node": {"name": "Drive", "type": "GOOGLE_DRIVE"}}],
                        "pageInfo": {"count": 1}},
        skills={"edges": [], "pageInfo": {"count": 0}},
        publishedChannels={"edges": [{"node": {"channelType": "TEAMS", "name": "HR"}}]},
    )
    inv = _inventory({"Agents": {"edges": [{"node": node}]}})
    agent, restricted = inv.fetch_agent_detail("a1")
    _assert_valid(inv)
    assert restricted == []
    assert agent["applications"][0]["name"] == "GitHub"
    assert agent["applications"][0]["connectors"][0]["isShared"] is True
    assert agent["applications_count"] == 3
    assert agent["topTools"][0]["toolName"] == "merge_pull_request"
    assert agent["usersWithAccess"] == ["u@x.com"] and agent["usersWithAccess_count"] == 12
    assert agent["models"] == [{"name": "gemini", "version": "2.5"}]
    assert agent["knowledgeBases"][0]["name"] == "Drive"
    assert agent["publishedChannels"][0]["channelType"] == "TEAMS"
    assert agent["owners"] == ["o@x.com"]


def test_agent_detail_unknown_id_is_none():
    inv = _inventory({"Agents": {"edges": []}})
    assert inv.fetch_agent_detail("missing") == (None, [])


# ---------------------------------------------------------------------------
# Freshness, gateway, policies, assignments, identities, events
# ---------------------------------------------------------------------------


def test_data_freshness_query_is_valid():
    inv = _inventory({"TenantData": {"processingStatus": {"dataFreshness": {
        "health": "BEHIND", "sources": [{"providerName": "GCP"}]}}}})
    assert inv.fetch_data_freshness()["health"] == "BEHIND"
    _assert_valid(inv)


def test_gateway_events_query_is_valid():
    inv = _inventory({"GatewayEvents": {"edges": [{"node": {"toolName": "x", "status": "DENY"}}],
                                        "pageInfo": {"count": 1}}})
    rows, total = inv.fetch_gateway_events_page(
        filters={"status": {"in": ["DENY"]},
                 "timestamp": {"greaterThanOrEquals": "2026-10-01T00:00:00Z"}},
        page_size=100)
    _assert_valid(inv)
    assert rows == [{"toolName": "x", "status": "DENY"}] and total == 1


def test_access_policies_query_is_valid():
    inv = _inventory({"AgentAppAccessPolicies": {"edges": [{"node": {"id": "p1"}}],
                                                 "pageInfo": {"count": 1}}})
    rows, total = inv.fetch_agent_access_policies_page(
        filters={"applicationId": {"equals": "t1"}}, page_size=10)
    _assert_valid(inv)
    assert rows == [{"id": "p1"}] and total == 1


def test_assignments_query_is_valid_and_lifts_the_application():
    inv = _inventory({"AgentConfiguredAssignments": {"edges": [{"node": {
        "policyName": "gh-read", "bindingSource": "DISCOVERED",
        "toolApplication": {"id": "t1", "name": "GitHub"}}}], "pageInfo": {"count": 1}}})
    rows, _ = inv.fetch_agent_assignments_page(
        filters={"bindingSource": {"in": ["DISCOVERED"]}}, page_size=10)
    _assert_valid(inv)
    assert rows[0]["applicationName"] == "GitHub" and "toolApplication" not in rows[0]


def test_agent_identities_query_is_valid_and_lifts_the_flags():
    inv = _inventory({"AgentIdentities": {"edges": [{"node": {
        "name": "sa-1", "significanceData": {"isSharedAcrossAgents": True}}}],
        "pageInfo": {"count": 1}}})
    rows, _ = inv.fetch_agent_identities_page(filters={"riskLevel": {"in": ["HIGH"]}},
                                              page_size=10)
    _assert_valid(inv)
    assert rows[0]["isSharedAcrossAgents"] is True


def test_events_query_is_valid():
    inv = _inventory({"AndromedaEvents": {"edges": [{"node": {"name": "X"}}],
                                          "pageInfo": {"count": 1}}})
    rows, total = inv.fetch_events_page(
        filters={"name": {"in": ["AGENT_APPLICATION_TOOL_DRIFT_DETECTED"]}}, page_size=10)
    _assert_valid(inv)
    assert rows == [{"name": "X"}] and total == 1


# ---------------------------------------------------------------------------
# Reads newer than some servers
# ---------------------------------------------------------------------------


def test_policy_usage_queries_are_valid_when_the_schema_has_them():
    inv = _inventory({"AgentAccessPolicyUsageSummaries": {"policies": []}})
    if not inv.has_agent_policy_usage():
        pytest.skip("generated schema predates agent policy usage")
    inv.fetch_agent_policy_usage_summaries("t1", 30)
    _assert_valid(inv)
    inv.gql_client.execute.return_value.formatted = {"data": {"AgentAccessPolicyUsage": {}}}
    inv.fetch_agent_policy_usage("p1", 30)
    _assert_valid(inv)


def test_discovered_tools_query_is_valid_when_the_schema_has_it():
    inv = _inventory({"ToolApplications": {"edges": [{"node": {"discoveredTools": {
        "edges": [{"node": {"name": "merge_pull_request", "agents": [{"name": "A"}]}}],
        "pageInfo": {"count": 1}}}}]}})
    if not inv.has_application_discovered_tools():
        pytest.skip("generated schema predates ToolApplication.discoveredTools")
    rows, total = inv.fetch_application_discovered_tools("t1")
    _assert_valid(inv)
    assert rows[0]["name"] == "merge_pull_request" and total == 1


# ---------------------------------------------------------------------------
# A USER's schema: the apiserver hides admin-only fields from that role's introspection
# ---------------------------------------------------------------------------

_USER_SDL = """
type Query { Agents(filters: AgentFilters, pageArgs: PageArgs): AgentsConnection }
input AgentFilters { id: Filter }
input Filter { equals: String }
input PageArgs { pageSize: Int, skip: Int }
type PageInfo { count: Int }
type AgentsConnection { edges: [AgentEdge!]!, pageInfo: PageInfo! }
type AgentEdge { node: Agent! }
type Agent { id: String, name: String, type: String, numUsers: Int,
             usersWithAccess(pageArgs: PageArgs): UserConnection }
type UserConnection { edges: [UserEdge!]!, pageInfo: PageInfo! }
type UserEdge { node: User! }
type User { username: String }
"""


def _user_inventory(data):
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = build_schema(_USER_SDL)
    inv.gql_client.execute.return_value.formatted = {"data": data}
    return inv


def test_a_user_schema_gets_only_the_fields_it_shows_and_names_the_rest():
    inv = _user_inventory({"Agents": {"edges": [{"node": {"id": "a1", "name": "Mine"}}],
                                      "pageInfo": {"count": 1}}})
    rows, total, restricted = inv.fetch_agents_page(filters=None, page_size=5)
    _assert_valid(inv)
    text = print_ast(getattr(inv.gql_client.execute.call_args[0][0], "document",
                             inv.gql_client.execute.call_args[0][0]))
    assert "riskLevel" not in text and "opsInsights" not in text and "owners" not in text
    assert rows == [{"id": "a1", "name": "Mine"}] and total == 1
    assert {"riskLevel", "opsInsights", "owners"} <= set(restricted)


def test_a_user_detail_skips_hidden_nested_fields():
    inv = _user_inventory({"Agents": {"edges": [{"node": {
        "id": "a1", "usersWithAccess": {"edges": [{"node": {"username": "me@x.com"}}],
                                        "pageInfo": {"count": 1}}}}]}})
    agent, restricted = inv.fetch_agent_detail("a1")
    _assert_valid(inv)
    assert agent["usersWithAccess"] == ["me@x.com"]
    assert "applications" not in agent and "applications" in restricted


def test_a_query_the_role_cannot_see_is_skipped_without_a_request():
    inv = _user_inventory({})
    assert inv.fetch_gateway_events_page(filters=None, page_size=10) == ([], None)
    inv.gql_client.execute.assert_not_called()
