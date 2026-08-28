"""Unit tests for the per-call fixed costs the SDK now caches.

Every AndromedaInventory construction used to pay for a full GraphQL introspection
query and a tenant-id REST call before any real query could run — the dominant cost
for short-lived callers like the agent's tools. These tests pin that behaviour, and
pin the part that must NOT be shared: one principal's schema is never handed to another.
"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from sdk.as_inventory import AndromedaInventory


@pytest.fixture(autouse=True)
def _clear_cache():
    AndromedaInventory.clear_schema_cache()
    yield
    AndromedaInventory.clear_schema_cache()


def _session(auth="Bearer abc"):
    s = requests.Session()
    s.headers["Authorization"] = auth
    return s


def _get_client(session, url="http://gql/graphql", credential_key=None):
    """Call get_gql_client with the network stubbed out."""
    with patch("sdk.as_inventory.Client") as client_cls, \
         patch("sdk.as_inventory.RequestsHTTPTransport"), \
         patch("sdk.as_inventory.build_client_schema", side_effect=lambda r, **kw: MagicMock()):
        client_cls.return_value = MagicMock()
        inv = AndromedaInventory.__new__(AndromedaInventory)
        inv.credential_key = credential_key
        return inv.get_gql_client(session, url), client_cls.return_value


def test_introspection_runs_once_per_endpoint_and_credential():
    session = _session()

    _, first = _get_client(session)
    _, second = _get_client(session)

    assert first.execute.call_count == 1
    assert second.execute.call_count == 0, "second client re-ran introspection"


def test_a_different_credential_does_not_reuse_the_cached_schema():
    """Introspection is authenticated, so a schema is only safe to reuse for the
    identity that fetched it."""
    _, first = _get_client(_session("Bearer abc"))
    _, second = _get_client(_session("Bearer xyz"))

    assert first.execute.call_count == 1
    assert second.execute.call_count == 1


def test_a_different_endpoint_does_not_reuse_the_cached_schema():
    session = _session()
    _, first = _get_client(session, "http://gql-a/graphql")
    _, second = _get_client(session, "http://gql-b/graphql")

    assert first.execute.call_count == 1
    assert second.execute.call_count == 1


def test_the_cache_key_holds_no_credential_material():
    session = _session("Bearer super-secret-token")
    key = AndromedaInventory._schema_cache_key("http://gql/graphql", session)

    assert "super-secret-token" not in str(key)
    assert key == AndromedaInventory._schema_cache_key("http://gql/graphql", session)


def test_a_credential_key_lets_two_fresh_sessions_share_a_schema():
    """Callers that build a session per request (the ai-agent's tools) pass an explicit
    credential key: an access-token login mints a new session cookie each time, so a
    session-derived key would miss on every call and re-run introspection."""
    _, first = _get_client(_session("Bearer login-1"), credential_key="principal-a")
    _, second = _get_client(_session("Bearer login-2"), credential_key="principal-a")

    assert first.execute.call_count == 1
    assert second.execute.call_count == 0, "the same principal should hit the cache"


def test_different_credential_keys_do_not_share_a_schema():
    session = _session()
    _, first = _get_client(session, credential_key="principal-a")
    _, second = _get_client(session, credential_key="principal-b")

    assert first.execute.call_count == 1
    assert second.execute.call_count == 1


def test_the_credential_key_is_not_stored_in_the_cache_key():
    session = _session()
    key = AndromedaInventory._schema_cache_key(
        "http://gql/graphql", session, credential_key="super-secret-token")

    assert "super-secret-token" not in str(key)


def test_clear_schema_cache_forces_a_refetch():
    session = _session()
    _get_client(session)
    AndromedaInventory.clear_schema_cache()
    _, after = _get_client(session)

    assert after.execute.call_count == 1


def test_the_cache_is_bounded():
    """The key includes a credential digest, so a process serving many principals adds
    an entry per token. Schemas are large and nothing here ever restarts, so an
    unbounded dict is a leak that grows with traffic."""
    with patch("sdk.as_inventory.MAX_SCHEMA_CACHE_ENTRIES", 3):
        for i in range(10):
            _get_client(_session(f"Bearer tok-{i}"))

        assert len(AndromedaInventory._schema_cache) == 3


def test_the_oldest_entry_is_evicted_first():
    with patch("sdk.as_inventory.MAX_SCHEMA_CACHE_ENTRIES", 2):
        _get_client(_session("Bearer a"))
        _get_client(_session("Bearer b"))
        _get_client(_session("Bearer c"))  # evicts a

        _, a_again = _get_client(_session("Bearer a"))
        _, c_again = _get_client(_session("Bearer c"))

    assert a_again.execute.call_count == 1, "the evicted credential should re-introspect"
    assert c_again.execute.call_count == 0, "the newest credential should still be cached"


def test_a_cache_hit_refreshes_recency():
    """Plain insertion-order eviction would drop the entry a busy caller keeps using."""
    with patch("sdk.as_inventory.MAX_SCHEMA_CACHE_ENTRIES", 2):
        _get_client(_session("Bearer a"))
        _get_client(_session("Bearer b"))
        _get_client(_session("Bearer a"))  # a is now the most recently used
        _get_client(_session("Bearer c"))  # so this evicts b, not a

        _, a_again = _get_client(_session("Bearer a"))
        _, b_again = _get_client(_session("Bearer b"))

    assert a_again.execute.call_count == 0, "a was used most recently and must survive"
    assert b_again.execute.call_count == 1, "b was least recently used and should be gone"


# ---------------------------------------------------------------------------
# tenant id — one REST call per session, not per construction
# ---------------------------------------------------------------------------


def test_tenant_id_is_fetched_once_per_session():
    session = _session()
    inv = AndromedaInventory.__new__(AndromedaInventory)

    with patch.object(AndromedaInventory, "_fetch_tenant_id", return_value="t-1") as fetch:
        assert inv.get_tenant_id(session, "http://api") == "t-1"
        assert inv.get_tenant_id(session, "http://api") == "t-1"
        # a second inventory over the same session must not re-ask either
        assert AndromedaInventory.__new__(AndromedaInventory).get_tenant_id(session, "http://api") == "t-1"

    assert fetch.call_count == 1


def test_tenant_id_is_per_endpoint():
    session = _session()
    inv = AndromedaInventory.__new__(AndromedaInventory)

    with patch.object(AndromedaInventory, "_fetch_tenant_id", side_effect=["t-1", "t-2"]) as fetch:
        assert inv.get_tenant_id(session, "http://api-a") == "t-1"
        assert inv.get_tenant_id(session, "http://api-b") == "t-2"

    assert fetch.call_count == 2


def test_tenant_id_is_not_shared_between_sessions():
    inv = AndromedaInventory.__new__(AndromedaInventory)

    with patch.object(AndromedaInventory, "_fetch_tenant_id", side_effect=["t-1", "t-2"]):
        assert inv.get_tenant_id(_session("Bearer a"), "http://api") == "t-1"
        assert inv.get_tenant_id(_session("Bearer b"), "http://api") == "t-2"
