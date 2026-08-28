"""Unit tests for the ScopeUnion inline-fragment selection.

Scope is what separates two otherwise-identical assignments (same role, same policy,
one on a resource and one on the resource group above it). The member list used to be
hardcoded, and it had been copied from the UI's generated schema — which lags the
server's union — so an assignment scoped to a member the list had never heard of matched
no fragment and came back with no scope fields at all. That is indistinguishable
downstream from an unscoped grant, so the list is now read from the introspected schema.
"""
from unittest.mock import MagicMock

from graphql import build_schema, print_ast
from gql.dsl import DSLSchema

from sdk.as_inventory import AndromedaInventory

_SCOPE_FIELDS = "id: String name: String type: String isInherited: Boolean"

_SDL = f"""
type Query {{ dummy: String }}
type AccountScopeData {{ {_SCOPE_FIELDS} }}
type FolderScopeData {{ {_SCOPE_FIELDS} }}
type PopulationScopeData {{ {_SCOPE_FIELDS} }}
type AgentConnectionScopeData {{ {_SCOPE_FIELDS} }}
type IdpApplicationScopeData {{ {_SCOPE_FIELDS} }}
union ScopeUnion = AccountScopeData | FolderScopeData | PopulationScopeData
                 | AgentConnectionScopeData | IdpApplicationScopeData
"""


def _inventory(sdl=_SDL):
    schema = build_schema(sdl)
    inv = AndromedaInventory.__new__(AndromedaInventory)
    inv.gql_client = MagicMock()
    inv.gql_client.schema = schema
    return inv, DSLSchema(schema)


def _fragment_text(inv, ds):
    return [print_ast(f.ast_field) for f in inv._scope_selection(ds)]


def test_every_union_member_gets_a_fragment():
    """The three members the hardcoded list was missing are exactly the ones whose scope
    silently vanished: Population, AgentConnection and IdpApplication."""
    inv, ds = _inventory()

    types = [t for t in inv._scope_union_member_names()]

    assert set(types) == {
        "AccountScopeData", "FolderScopeData", "PopulationScopeData",
        "AgentConnectionScopeData", "IdpApplicationScopeData",
    }
    assert len(_fragment_text(inv, ds)) == 5


def test_a_member_added_to_the_schema_needs_no_code_change():
    sdl = _SDL.replace(
        "union ScopeUnion =",
        f"type FutureScopeData {{ {_SCOPE_FIELDS} }}\nunion ScopeUnion = FutureScopeData |",
    )
    inv, ds = _inventory(sdl)

    assert "FutureScopeData" in inv._scope_union_member_names()
    assert any("... on FutureScopeData" in text for text in _fragment_text(inv, ds))


def test_each_fragment_selects_the_scope_fields():
    inv, ds = _inventory()

    account = next(t for t in _fragment_text(inv, ds) if "on AccountScopeData" in t)

    assert account.split() == [
        "...", "on", "AccountScopeData", "{", "id", "name", "type", "isInherited", "}",
    ]


def test_a_member_missing_a_field_does_not_produce_an_invalid_query():
    """Selecting a field a member does not declare is a server-side error for the whole
    query, so a partial member must narrow the selection rather than break every caller."""
    sdl = _SDL.replace(
        "union ScopeUnion =",
        "type ThinScopeData { id: String name: String }\nunion ScopeUnion = ThinScopeData |",
    )
    inv, ds = _inventory(sdl)

    thin = next(t for t in _fragment_text(inv, ds) if "on ThinScopeData" in t)

    assert "id" in thin and "name" in thin
    assert "isInherited" not in thin and "type" not in thin


def test_a_schema_without_the_union_falls_back_to_the_static_list():
    """Older servers and hand-built client schemas in tests have no ScopeUnion; the
    fallback keeps them working instead of selecting nothing."""
    inv, _ = _inventory(f"type Query {{ dummy: String }}\ntype AccountScopeData {{ {_SCOPE_FIELDS} }}")

    assert inv._scope_union_member_names() == AndromedaInventory._SCOPE_UNION_TYPES


def test_the_static_fallback_covers_the_server_s_union():
    """If the fallback ever runs it must not reintroduce the six-member list that caused
    the original drift."""
    assert set(AndromedaInventory._SCOPE_UNION_TYPES) == {
        "AccountScopeData", "AgentConnectionScopeData", "FolderScopeData",
        "GroupScopeData", "IdpApplicationScopeData", "PopulationScopeData",
        "ProviderScopeData", "ResourceGroupScopeData", "ResourceScopeData",
    }
