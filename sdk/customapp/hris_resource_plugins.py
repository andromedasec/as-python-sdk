"""
HRIS Resource Plugins for Custom App CSV ingestion.

Each plugin mirrors one resource type from the Go ingester's
``services/ingester/pkg/inventory/datasources/customapp/resources/`` directory.

All plugin classes are defined inside ``HrisPlugins``, which also provides
a built-in registry and helper methods to resolve plugin lists by name.

Usage::

    from sdk.customapp.hris_resource_plugins import HrisPlugins

    # All default plugins (users first, then resource types, then enrichment)
    plugins = HrisPlugins.get_default_plugins()

    # Specific plugins by short name
    plugins = HrisPlugins.get_plugins_by_names(["users", "roles", "assignments"])
"""

from __future__ import annotations

import abc
import datetime
import logging
from typing import Dict, List, Optional

from sdk.customapp.custom_app_models import (
    CustomAppGroupV2,
    CustomAppInventory,
    CustomAppNhiV2,
    CustomAppPermissionV2,
    CustomAppRole,
    CustomAppRoleAssignmentV2,
    CustomAppScopeV2,
    CustomAppUserV2,
    CustomAppUserHRISAttributes,
    HrType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HR_CATEGORY_MAP = {
    "employee": "EMPLOYEE",
    "contingent worker": "CONTINGENT_WORKER",
    "third party": "THIRD_PARTY",
    "contractor": "CONTINGENT_WORKER",
    "vendor": "THIRD_PARTY",
    "intern": "CONTINGENT_WORKER",
    "temp": "CONTINGENT_WORKER",
}

STATUS_ENABLED = "ENABLED"
STATUS_DEACTIVATED = "DEACTIVATED"


# ---------------------------------------------------------------------------
# Field-map aware CSV accessor
# ---------------------------------------------------------------------------

class CsvFieldAccessor:
    """Resolves a logical attribute name to the actual CSV column value."""

    def __init__(self, field_map: Dict[str, str]) -> None:
        self.field_map = field_map

    def get(self, row: dict, attr: str, default: str = "") -> str:
        col = self.field_map.get(attr, attr)
        return row.get(col, default).strip()

    def has_any(self, headers: List[str], *attrs: str) -> bool:
        """Return True if any of *attrs* resolve to a column present in *headers*."""
        for attr in attrs:
            col = self.field_map.get(attr, attr)
            if col in headers:
                return True
        return False


# ---------------------------------------------------------------------------
# Shared parsing utilities
# ---------------------------------------------------------------------------

def parse_hr_type(category: str) -> Optional[HrType]:
    if not category:
        return None
    name = HR_CATEGORY_MAP.get(category.strip().lower())
    return HrType(name) if name else None


def parse_active_status(active: str) -> str:
    if active.strip().lower() in ("true", "1", "yes", "active"):
        return STATUS_ENABLED
    return STATUS_DEACTIVATED


def format_timestamp(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y"):
        try:
            dt = datetime.datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    logger.warning("Could not parse date: %s", date_str)
    return None


def _split_list(value: str) -> List[str]:
    """Split a pipe- or comma-separated string into a list, stripping blanks."""
    if not value:
        return []
    sep = "|" if "|" in value else ","
    return [v.strip() for v in value.split(sep) if v.strip()]


# ---------------------------------------------------------------------------
# Plugin base class
# ---------------------------------------------------------------------------

class HrisResourcePlugin(abc.ABC):
    """Base class for HRIS resource plugins.

    Each plugin corresponds to one resource type in the ingester's
    ``customapp/resources/`` directory.  Plugins run in the order they
    appear in the plugin list; ``Users`` must come first since downstream
    plugins may reference user identifiers.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable plugin name (used in logs)."""

    @property
    @abc.abstractmethod
    def required_columns(self) -> List[str]:
        """Logical attribute names the plugin needs (checked against field map)."""

    def can_run(self, headers: List[str], accessor: CsvFieldAccessor) -> bool:
        """Return True if the CSV has at least one column this plugin needs."""
        return accessor.has_any(headers, *self.required_columns)

    @abc.abstractmethod
    def process(
        self,
        rows: List[dict],
        inventory: CustomAppInventory,
        accessor: CsvFieldAccessor,
    ) -> None:
        """Read *rows* and mutate *inventory* in place."""


# ═══════════════════════════════════════════════════════════════════════════
# HrisPlugins — contains all plugin implementations + registry
# ═══════════════════════════════════════════════════════════════════════════

class HrisPlugins:
    """Namespace for all HRIS resource plugin implementations and their registry.

    Plugin classes are nested inside this class.  The class-level ``REGISTRY``
    maps short names to singleton instances.  Use ``get_default_plugins()``
    or ``get_plugins_by_names(...)`` to obtain an ordered plugin list.
    """

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Users  (customapp/resources/users.go)
    # ───────────────────────────────────────────────────────────────────

    class Users(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppUserV2`` with full HRIS attributes.

        Mirrors: ``resources/users.go`` → JSON key ``"users"``
        """

        @property
        def name(self) -> str:
            return "Users"

        @property
        def required_columns(self) -> List[str]:
            return ["user_id", "email", "username"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                user = self._build_user(row, accessor)
                if user is not None:
                    inventory.users[user.username] = user
            logger.info("[%s] Produced %d users", self.name, len(inventory.users))

        @staticmethod
        def _build_user(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppUserV2]:
            user_id = a.get(row, "user_id")
            if not user_id:
                return None

            first_name = a.get(row, "first_name")
            last_name = a.get(row, "last_name")
            email = a.get(row, "email")
            username = a.get(row, "username") or email or user_id

            hris_attrs = CustomAppUserHRISAttributes(
                email=email or None,
                org_name=a.get(row, "org_name") or a.get(row, "department") or None,
                business_title=a.get(row, "business_title") or None,
                manager_id=a.get(row, "manager_id") or None,
                manager_name=a.get(row, "manager_name") or None,
                position_title=a.get(row, "position_title") or None,
                division=a.get(row, "division") or None,
                city=a.get(row, "city") or None,
                state=a.get(row, "state") or None,
                country=a.get(row, "country") or None,
                hire_date=format_timestamp(a.get(row, "hire_date")),
                termination_date=format_timestamp(a.get(row, "termination_date")),
            )

            return CustomAppUserV2(
                id=user_id,
                username=username,
                name=f"{first_name} {last_name}".strip() or username,
                status=parse_active_status(a.get(row, "active", "true")),
                hr_type=parse_hr_type(a.get(row, "category")),
                hris_attributes=hris_attrs,
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: NHIs  (customapp/resources/nhis.go)
    # ───────────────────────────────────────────────────────────────────

    class Nhis(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppNhiV2`` service-identity objects.

        Mirrors: ``resources/nhis.go`` → JSON key ``"nhis"``
        """

        @property
        def name(self) -> str:
            return "NHIs"

        @property
        def required_columns(self) -> List[str]:
            return ["nhi_id", "nhi_username"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                nhi = self._build_nhi(row, accessor)
                if nhi is not None:
                    inventory.nhis[nhi.username] = nhi
            logger.info("[%s] Produced %d NHIs", self.name, len(inventory.nhis))

        @staticmethod
        def _build_nhi(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppNhiV2]:
            nhi_id = a.get(row, "nhi_id")
            nhi_username = a.get(row, "nhi_username")
            if not nhi_id or not nhi_username:
                return None
            return CustomAppNhiV2(
                id=nhi_id,
                username=nhi_username,
                name=a.get(row, "nhi_name") or nhi_username,
                owner_id=a.get(row, "nhi_owner_id") or None,
                custodian_id=a.get(row, "nhi_custodian_id") or None,
                status=a.get(row, "nhi_status") or STATUS_ENABLED,
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Groups  (customapp/resources/groups.go + group_memberships.go)
    # ───────────────────────────────────────────────────────────────────

    class Groups(HrisResourcePlugin):
        """Reads explicit group rows from CSV.

        Mirrors: ``resources/groups.go`` + ``resources/group_memberships.go``
        → JSON key ``"groups"``
        """

        @property
        def name(self) -> str:
            return "Groups"

        @property
        def required_columns(self) -> List[str]:
            return ["group_id", "group_name"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                grp = self._build_group(row, accessor)
                if grp is not None:
                    inventory.groups[grp.id] = grp
            logger.info("[%s] Produced %d explicit groups", self.name, len(inventory.groups))

        @staticmethod
        def _build_group(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppGroupV2]:
            gid = a.get(row, "group_id")
            gname = a.get(row, "group_name")
            if not gid:
                return None
            return CustomAppGroupV2(
                id=gid,
                name=gname or gid,
                member_user_ids=_split_list(a.get(row, "group_member_user_ids")),
                member_subgroup_ids=_split_list(a.get(row, "group_member_subgroup_ids")),
                member_nhi_ids=_split_list(a.get(row, "group_member_nhi_ids")),
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Roles  (customapp/resources/roles.go)
    # ───────────────────────────────────────────────────────────────────

    class Roles(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppRole`` objects.

        Mirrors: ``resources/roles.go`` → JSON key ``"roles"``
        """

        @property
        def name(self) -> str:
            return "Roles"

        @property
        def required_columns(self) -> List[str]:
            return ["role_id", "role_name"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                role = self._build_role(row, accessor)
                if role is not None:
                    inventory.roles[role.id] = role
            logger.info("[%s] Produced %d roles", self.name, len(inventory.roles))

        @staticmethod
        def _build_role(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppRole]:
            rid = a.get(row, "role_id")
            rname = a.get(row, "role_name")
            if not rid:
                return None
            return CustomAppRole(
                id=rid,
                name=rname or rid,
                type=a.get(row, "role_type") or "CUSTOM_APP_ROLE",
                permissions=_split_list(a.get(row, "role_permissions")),
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Assignments  (customapp/resources/assignments.go)
    # ───────────────────────────────────────────────────────────────────

    class Assignments(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppRoleAssignmentV2`` bindings.

        Mirrors: ``resources/assignments.go`` → JSON key ``"assignments"``
        """

        @property
        def name(self) -> str:
            return "Assignments"

        @property
        def required_columns(self) -> List[str]:
            return ["principal_id", "assignment_role_id"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                asgn = self._build_assignment(row, accessor)
                if asgn is not None:
                    inventory.assignments[asgn.id] = asgn
            logger.info("[%s] Produced %d assignments", self.name, len(inventory.assignments))

        @staticmethod
        def _build_assignment(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppRoleAssignmentV2]:
            principal = a.get(row, "principal_id")
            role_id = a.get(row, "assignment_role_id")
            if not principal or not role_id:
                return None
            aid = a.get(row, "assignment_id") or f"{principal}_{role_id}"
            return CustomAppRoleAssignmentV2(
                id=aid,
                principal_id=principal,
                principal_type=a.get(row, "principal_type") or "HUMAN",
                role_id=role_id,
                scope_id=a.get(row, "scope_id") or None,
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Scopes  (customapp/resources/scopes.go)
    # ───────────────────────────────────────────────────────────────────

    class Scopes(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppScopeV2`` objects.

        Mirrors: ``resources/scopes.go`` → JSON key ``"scopes"``
        """

        @property
        def name(self) -> str:
            return "Scopes"

        @property
        def required_columns(self) -> List[str]:
            return ["scope_id"]

        def can_run(self, headers: List[str], accessor: CsvFieldAccessor) -> bool:
            col = accessor.field_map.get("scope_id", "scope_id")
            col_name = accessor.field_map.get("scope_name", "scope_name")
            col_type = accessor.field_map.get("scope_type", "scope_type")
            return col in headers and (col_name in headers or col_type in headers)

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                scope = self._build_scope(row, accessor)
                if scope is not None:
                    inventory.scopes[scope.id] = scope
            logger.info("[%s] Produced %d scopes", self.name, len(inventory.scopes))

        @staticmethod
        def _build_scope(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppScopeV2]:
            sid = a.get(row, "scope_id")
            sname = a.get(row, "scope_name")
            stype = a.get(row, "scope_type")
            if not sid or (not sname and not stype):
                return None
            return CustomAppScopeV2(
                id=sid,
                name=sname or sid,
                type=stype or "PROVIDER",
                parent_scope_id=a.get(row, "parent_scope_id") or None,
            )

    # ───────────────────────────────────────────────────────────────────
    # Plugin: Permissions  (customapp/resources/permissions.go)
    # ───────────────────────────────────────────────────────────────────

    class Permissions(HrisResourcePlugin):
        """Transforms CSV rows into ``CustomAppPermissionV2`` objects.

        Mirrors: ``resources/permissions.go`` → JSON key ``"permissions"``
        """

        @property
        def name(self) -> str:
            return "Permissions"

        @property
        def required_columns(self) -> List[str]:
            return ["permission_name"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            for row in rows:
                perm = self._build_permission(row, accessor)
                if perm is not None:
                    inventory.permissions[perm.name] = perm
            logger.info("[%s] Produced %d permissions", self.name, len(inventory.permissions))

        @staticmethod
        def _build_permission(row: dict, a: CsvFieldAccessor) -> Optional[CustomAppPermissionV2]:
            name = a.get(row, "permission_name")
            if not name:
                return None
            return CustomAppPermissionV2(
                name=name,
                access_level=a.get(row, "access_level") or None,
                service_name=a.get(row, "service_name") or None,
            )

    # ───────────────────────────────────────────────────────────────────
    # HRIS auto-derive enrichment plugins
    # ───────────────────────────────────────────────────────────────────

    class DepartmentGroups(HrisResourcePlugin):
        """Auto-derives department groups from users' ``org_name``/``department`` field."""

        @property
        def name(self) -> str:
            return "DepartmentGroups"

        @property
        def required_columns(self) -> List[str]:
            return ["org_name", "department"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            dept_members: Dict[str, List[str]] = {}
            for row in rows:
                uid = accessor.get(row, "username") or accessor.get(row, "email") or accessor.get(row, "user_id")
                dept = accessor.get(row, "org_name") or accessor.get(row, "department")
                if uid and dept:
                    dept_members.setdefault(dept, []).append(uid)
            for dept_name, members in dept_members.items():
                gid = f"dept:{dept_name}"
                inventory.groups[gid] = CustomAppGroupV2(
                    id=gid, name=dept_name,
                    member_user_ids=sorted(set(members)),
                )
            logger.info("[%s] Produced %d department groups", self.name, len(dept_members))

    class DivisionGroups(HrisResourcePlugin):
        """Auto-derives division groups from users' ``division`` field."""

        @property
        def name(self) -> str:
            return "DivisionGroups"

        @property
        def required_columns(self) -> List[str]:
            return ["division"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            div_members: Dict[str, List[str]] = {}
            for row in rows:
                uid = accessor.get(row, "username") or accessor.get(row, "email") or accessor.get(row, "user_id")
                div = accessor.get(row, "division")
                if uid and div:
                    div_members.setdefault(div, []).append(uid)
            for div_name, members in div_members.items():
                gid = f"div:{div_name}"
                inventory.groups[gid] = CustomAppGroupV2(
                    id=gid, name=div_name,
                    member_user_ids=sorted(set(members)),
                )
            logger.info("[%s] Produced %d division groups", self.name, len(div_members))

    class ManagerHierarchyGroups(HrisResourcePlugin):
        """Creates a group per manager containing their direct reports."""

        @property
        def name(self) -> str:
            return "ManagerHierarchyGroups"

        @property
        def required_columns(self) -> List[str]:
            return ["manager_id"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            mgr_reports: Dict[str, List[str]] = {}
            mgr_names: Dict[str, str] = {}
            for row in rows:
                uid = accessor.get(row, "username") or accessor.get(row, "email") or accessor.get(row, "user_id")
                mgr_id = accessor.get(row, "manager_id")
                if uid and mgr_id:
                    mgr_reports.setdefault(mgr_id, []).append(uid)
                    mgr_name = accessor.get(row, "manager_name")
                    if mgr_name and mgr_id not in mgr_names:
                        mgr_names[mgr_id] = mgr_name
            for mgr_id, reports in mgr_reports.items():
                gid = f"mgr:{mgr_id}"
                display = mgr_names.get(mgr_id, mgr_id)
                inventory.groups[gid] = CustomAppGroupV2(
                    id=gid, name=f"Reports to: {display}",
                    member_user_ids=sorted(set(reports)),
                )
            logger.info("[%s] Produced %d manager groups", self.name, len(mgr_reports))

    class CostCenterGroups(HrisResourcePlugin):
        """Auto-derives cost-center groups from users' ``cost_center`` field."""

        @property
        def name(self) -> str:
            return "CostCenterGroups"

        @property
        def required_columns(self) -> List[str]:
            return ["cost_center"]

        def process(self, rows: List[dict], inventory: CustomAppInventory,
                    accessor: CsvFieldAccessor) -> None:
            cc_members: Dict[str, List[str]] = {}
            for row in rows:
                uid = accessor.get(row, "username") or accessor.get(row, "email") or accessor.get(row, "user_id")
                cc = accessor.get(row, "cost_center")
                if uid and cc:
                    cc_members.setdefault(cc, []).append(uid)
            for cc_name, members in cc_members.items():
                gid = f"cc:{cc_name}"
                inventory.groups[gid] = CustomAppGroupV2(
                    id=gid, name=f"Cost Center: {cc_name}",
                    member_user_ids=sorted(set(members)),
                )
            logger.info("[%s] Produced %d cost-center groups", self.name, len(cc_members))

    # ───────────────────────────────────────────────────────────────────
    # Registry
    # ───────────────────────────────────────────────────────────────────

    REGISTRY: Dict[str, HrisResourcePlugin] = {
        "users": Users(),
        "nhis": Nhis(),
        "groups": Groups(),
        "roles": Roles(),
        "assignments": Assignments(),
        "scopes": Scopes(),
        "permissions": Permissions(),
        "departments": DepartmentGroups(),
        "divisions": DivisionGroups(),
        "managers": ManagerHierarchyGroups(),
        "cost_centers": CostCenterGroups(),
    }

    @classmethod
    def get_default_plugins(cls) -> List[HrisResourcePlugin]:
        """Return the full ordered plugin list for HRIS ingestion.

        Order: users first, then remaining ingester resource types, then
        auto-derive enrichment plugins.
        """
        return [
            cls.REGISTRY["users"],
            cls.REGISTRY["nhis"],
            cls.REGISTRY["groups"],
            cls.REGISTRY["roles"],
            cls.REGISTRY["assignments"],
            cls.REGISTRY["scopes"],
            cls.REGISTRY["permissions"],
            cls.REGISTRY["departments"],
            cls.REGISTRY["divisions"],
            cls.REGISTRY["managers"],
            cls.REGISTRY["cost_centers"],
        ]

    @classmethod
    def get_plugins_by_names(cls, names: List[str]) -> List[HrisResourcePlugin]:
        """Resolve a caller-supplied list of plugin short names.

        Always prepends ``users`` if not already present.
        """
        if "users" not in names:
            names = ["users"] + list(names)
        plugins: List[HrisResourcePlugin] = []
        for n in names:
            key = n.strip().lower()
            if key not in cls.REGISTRY:
                raise KeyError(
                    f"Unknown plugin '{key}'. Available: {', '.join(cls.REGISTRY)}"
                )
            plugins.append(cls.REGISTRY[key])
        return plugins
