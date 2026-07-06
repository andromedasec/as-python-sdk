"""
Metadata decorators for RBAC role resolution.

Usage:
  @uses_iterators("as_humans_itr")            # on tools that call as_inventory methods

  @admin_tier                                 # on a tool — pin to admin-tier roles
  @uar_admin_tier                             # on a tool — admin tier + UAR_ADMIN
  @requires_roles(0, 1)                       # escape hatch — arbitrary role set
"""

from api.proto.andromeda.utils.api_pb2 import ApiRoleEnum

_ApiRole = ApiRoleEnum.ApiRole


def requires_roles(*role_ints: int):
    """Pin a tool's allowed role set; bypasses auto GQL/REST inference.

    Use when proto annotations are too permissive for a specific tool (e.g.,
    an admin-only tool whose underlying GQL query allows USER). The decorator
    sets fn.required_roles, which tool_roles_resolver consults first.
    """
    pinned = frozenset(role_ints)
    def decorator(fn):
        fn.required_roles = pinned
        return fn
    return decorator

admin_write_tier = requires_roles(
    _ApiRole.ANDROMEDA_ADMIN, _ApiRole.ADMIN,
)
"""Restrict a tool to the admin write tier: ANDROMEDA_ADMIN, ADMIN"""

admin_tier = requires_roles(
    _ApiRole.ANDROMEDA_ADMIN, _ApiRole.ADMIN, _ApiRole.ADMIN_READ_ONLY,
)
"""Restrict a tool to the admin tier: ANDROMEDA_ADMIN, ADMIN, ADMIN_READ_ONLY."""


uar_admin_tier = requires_roles(
    _ApiRole.ANDROMEDA_ADMIN, _ApiRole.ADMIN, _ApiRole.ADMIN_READ_ONLY, _ApiRole.UAR_ADMIN,
)
"""Admin tier plus UAR_ADMIN — for tools owned by the UAR management surface."""


def uses_iterators(*method_names: str):
    """Annotate a tool with the as_inventory method names it calls."""
    def decorator(fn):
        fn.uses_iterators = frozenset(method_names)
        return fn
    return decorator
