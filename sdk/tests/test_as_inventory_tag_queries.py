"""SDK-level GQL tests for the tag-read methods on AndromedaInventory.

The tool-level tests mock these methods and only check normalisation, so a wrong
GQL root field or a dropped tags selection would ship undetected. These tests build
the query against a real (minimal) schema — so a wrong root/field raises at
construction — and assert the printed query hits the expected root and selects tags,
plus that each method parses the node out of the right response root.
"""
from unittest.mock import MagicMock

from graphql import build_schema, print_ast

from sdk.as_inventory import AndromedaInventory

_SDL = """
input IdEquals { equals: String }
input EntityFilters { id: IdEquals }
input PageArgs { pageSize: Int skip: Int }

type Tag { key: String value: String }
type ResourceGroupTag { key: String values: [String] }

type Resource { id: String name: String tags: [Tag] }
type ResourceEdge { node: Resource }
type ResourceConnection { edges: [ResourceEdge] }

type Group { id: String name: String tags: [Tag] }
type GroupDataEdge { node: Group }
type GroupsConnection { edges: [GroupDataEdge] }

type Policy { id: String name: String tags: [Tag] }
type PolicyEdge { node: Policy }
type PoliciesConnection { edges: [PolicyEdge] }
type Provider { policies(filters: EntityFilters pageArgs: PageArgs): PoliciesConnection }
type ProviderEdge { node: Provider }
type ProvidersConnection { edges: [ProviderEdge] }

type Account { id: String name: String tags: [String] }
type AccountEdge { node: Account }
type AccountsConnection { edges: [AccountEdge] }

type ResourceGroup { id: String name: String tags: [ResourceGroupTag] }
type ResourceGroupEdge { node: ResourceGroup }
type ResourceGroupConnection { edges: [ResourceGroupEdge] }

type Query {
  Resources(filters: EntityFilters pageArgs: PageArgs): ResourceConnection
  Groups(filters: EntityFilters pageArgs: PageArgs): GroupsConnection
  Providers(filters: EntityFilters pageArgs: PageArgs): ProvidersConnection
  Accounts(providerId: String filters: EntityFilters pageArgs: PageArgs): AccountsConnection
  ResourceGroups(providerId: String filters: EntityFilters pageArgs: PageArgs): ResourceGroupConnection
}
"""


def _inventory(formatted):
    """Inventory whose execute() returns the given `formatted` response dict."""
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = build_schema(_SDL)
    inv.gql_client.execute.return_value.formatted = formatted
    return inv


def _query_text(inv):
    query = inv.gql_client.execute.call_args[0][0]
    return print_ast(query)


def _edges(root, node):
    return {"data": {root: {"edges": [{"node": node}]}}}


# --- resource ---

def test_resource_query_root_and_parse():
    node = {"id": "r1", "name": "bucket", "tags": [{"key": "env", "value": "prod"}]}
    inv = _inventory(_edges("Resources", node))
    assert inv.get_resource_tags("r1") == node
    text = _query_text(inv)
    assert "Resources" in text and "tags" in text


def test_resource_empty_edges_is_none():
    inv = _inventory({"data": {"Resources": {"edges": []}}})
    assert inv.get_resource_tags("r1") is None


# --- group ---

def test_group_query_root_and_parse():
    node = {"id": "g1", "name": "admins", "tags": [{"key": "sox", "value": "true"}]}
    inv = _inventory(_edges("Groups", node))
    assert inv.get_group_tags("g1") == node
    assert "Groups" in _query_text(inv)


# --- policy (tuple: node, provider_found) ---

def _provider(policy_edges):
    return _edges("Providers", {"policies": {"edges": policy_edges}})


def test_policy_found_returns_node_and_provider_true():
    node = {"id": "p1", "name": "ReadOnly", "tags": [{"key": "gdpr", "value": "true"}]}
    inv = _inventory(_provider([{"node": node}]))
    assert inv.get_policy_tags("p1", "prov1") == (node, True)
    text = _query_text(inv)
    assert "Providers" in text and "policies" in text and "tags" in text


def test_policy_missing_under_existing_provider():
    assert _inventory(_provider([])).get_policy_tags("p1", "prov1") == (None, True)


def test_policy_provider_not_found():
    inv = _inventory({"data": {"Providers": {"edges": []}}})
    assert inv.get_policy_tags("p1", "bad") == (None, False)


# --- account ---

def test_account_query_root_and_parse():
    account = {"id": "a1", "name": "prod", "tags": ["env:prod"]}
    inv = _inventory(_edges("Accounts", account))
    assert inv.get_account_tags("a1", "prov1") == account
    assert "Accounts" in _query_text(inv)


def test_account_missing_is_none():
    inv = _inventory({"data": {"Accounts": {"edges": []}}})
    assert inv.get_account_tags("a1", "prov1") is None


# --- resource group ---

def test_resource_group_query_root_and_parse():
    node = {"id": "rg1", "name": "my-rg", "tags": [{"key": "env", "values": ["prod", "staging"]}]}
    inv = _inventory(_edges("ResourceGroups", node))
    assert inv.get_resource_group_tags("rg1", "prov1") == node
    text = _query_text(inv)
    assert "ResourceGroups" in text and "values" in text
