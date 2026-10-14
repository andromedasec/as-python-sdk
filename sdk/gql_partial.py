"""Helpers for GraphQL reads that must keep working when one field fails.

gql raises TransportQueryError for any GraphQL error, even when the server returned most
of the data (for example, a nested resolver that answers NotFound for a deleted object,
or a field whose table is not migrated yet). These helpers keep that data and say which
fields are missing, recognise an unknown-id 404, and check whether the server's schema
has a field before a query asks for it (an older apiserver rejects unknown fields for the
whole request).
"""
from __future__ import annotations

import logging
from typing import Any

from gql import Client
from gql.transport.exceptions import TransportQueryError
from graphql import GraphQLSchema

logger = logging.getLogger(__name__)


def execute_allow_partial(client: Client, query: Any) -> tuple[dict, list[str]]:
    """Run `query` and return (data, incomplete_paths).

    A field that failed on the server is None in `data`, and its path (for example
    "JmlPolicyRuntimes.edges.0.node.jmlPolicy") is listed in `incomplete_paths`.
    Raises TransportQueryError when nothing came back at all.
    """
    try:
        return client.execute(query, get_execution_result=True).formatted["data"] or {}, []
    except TransportQueryError as exc:
        if exc.data and any(v is not None for v in exc.data.values()):
            logger.warning("partial GraphQL result: %s", exc.errors)
            paths = [".".join(str(p) for p in (e or {}).get("path") or [])
                     for e in exc.errors or [] if (e or {}).get("path")]
            return dict(exc.data), paths
        raise


def is_not_found(exc: Exception) -> bool:
    """True when the apiserver answered an unknown id with a GraphQL 404 error."""
    return isinstance(exc, TransportQueryError) and any(
        ((e or {}).get("extensions") or {}).get("code") == 404 for e in exc.errors or [])


def has_field(schema: GraphQLSchema | None, type_name: str, field_name: str) -> bool:
    """True when the server's schema has `type_name.field_name`."""
    gql_type = schema.get_type(type_name) if schema else None
    return bool(gql_type and field_name in (getattr(gql_type, "fields", None) or {}))
