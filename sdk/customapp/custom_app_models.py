# Data Classes that are used for Custom Application
# The custom application downloader or translator files
# can use these data files to


from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List
import re
import logging


# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"

def _camel_to_snake(data: str) -> str:
    # Inserts an underscore before any capital letter that is NOT at the start
    # Then converts the entire string to lowercase
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', data).lower()

def _transform_deprecated_kwargs(kwargs: dict, deprecated_attrs: dict) -> dict:
    """Transform deprecated camelCase kwargs to snake_case.

    Args:
        kwargs: The keyword arguments dictionary
        deprecated_attrs: Mapping of deprecated camelCase names to snake_case names

    Returns:
        Transformed kwargs dictionary with camelCase params converted to snake_case
    """
    deleted_keys = set()
    updated_values = {}
    for k, v in kwargs.items():
        snake_key = _camel_to_snake(k)
        if k in deprecated_attrs or k != snake_key:
            # it needs to be updated
            if k in deprecated_attrs:
                deleted_keys.add(k)
                if deprecated_attrs[k] not in kwargs:
                    updated_values[deprecated_attrs[k]] = v
            elif k != snake_key:
                deleted_keys.add(k)
                updated_values[snake_key] = v
    for k in deleted_keys:
        del kwargs[k]
    kwargs.update(updated_values)
    return kwargs

class CustomAppType(Enum):
    """ Custom Application Types"""
    UNSPECIFIED = "UNSPECIFIED"
    ANDROMEDA_INVENTORY_JSON = "ANDROMEDA_INVENTORY_JSON"
    CUSTOM_INVENTORY_WITH_SCRIPT = "CUSTOM_INVENTORY_WITH_SCRIPT"
    CUSTOM_INVENTORY_SCRIPT_FOR_DOWNLOAD = "CUSTOM_INVENTORY_SCRIPT_FOR_DOWNLOAD"


class CustomAppInventoryType(Enum):
    """ Custom Application Inventory Type"""
    WORKDAY_CSV = "WORKDAY_CSV"
    ANDROMEDA_INVENTORY_JSON = "ANDROMEDA_INVENTORY_JSON"
    CUSTOM_TYPE1_INVENTORY_CSV = "CUSTOM_TYPE1_INVENTORY_CSV"
    CUSTOM_INVENTORY_JSON = "CUSTOM_INVENTORY_JSON"

class CustomAppInventoryScriptType(Enum):
    """ Custom Application Inventory Type"""
    UNSPECIFIED = "UNSPECIFIED"
    INVENTORY_TRANSLATOR_FILE_PYTHON = "INVENTORY_TRANSLATOR_FILE_PYTHON"
    INVENTORY_DOWNLOADER_FILE_PYTHON = "INVENTORY_DOWNLOADER_FILE_PYTHON"

class UserStatus(Enum):
    """Represents a user status in the custom application inventory."""
    ENABLED = "ENABLED"
    DEACTIVATED = "DEACTIVATED"
    IDENTITY_STATUS_UNRESOLVED = "IDENTITY_STATUS_UNRESOLVED"
    SUSPENDED = "SUSPENDED"

class PrincipalType(Enum):
    """Represents a principal type in the custom application inventory."""
    HUMAN = "HUMAN"
    NHI = "NHI"
    GROUP = "GROUP"

class RoleType(Enum):
    """Represents a role type in the custom application inventory."""
    CUSTOM_APP_ROLE = "CUSTOM_APP_ROLE"
    CUSTOM_APP_USER_ROLE = "CUSTOM_APP_USER_ROLE"

class PermissionAccessLevel(Enum):
    """Represents a permission access level in the custom application inventory."""
    UNSPECIFIED = "ACCESS_LEVEL_UNSPECIFIED"
    LIST = "ACCESS_LEVEL_LIST"
    WRITE_TAG = "ACCESS_LEVEL_WRITE_TAG"
    DELETE_TAG = "ACCESS_LEVEL_DELETE_TAG"
    READ_METADATA = "ACCESS_LEVEL_READ_METADATA"
    READ_DATA = "ACCESS_LEVEL_READ_DATA"
    WRITE_METADATA = "ACCESS_LEVEL_WRITE_METADATA"
    CREATE = "ACCESS_LEVEL_CREATE"
    WRITE_DATA = "ACCESS_LEVEL_WRITE_DATA"
    DELETE_DATA = "ACCESS_LEVEL_DELETE_DATA"
    DELETE = "ACCESS_LEVEL_DELETE"
    PERMISSIONS_MANAGEMENT = "ACCESS_LEVEL_PERMISSIONS_MANAGEMENT"

class ScopeType(Enum):
    """Represents a scope type in t
    he custom application inventory."""
    UNSPECIFIED = "UNSPECIFIED"
    PROVIDER = "PROVIDER"
    FOLDER = "FOLDER"
    ACCOUNT = "ACCOUNT"
    RESOURCE_GROUP = "RESOURCE_GROUP"


class HrType(str, Enum):
    """Represents a HR type in the custom application inventory."""
    HR_TYPE_UNSPECIFIED = ""
    EMPLOYEE = "EMPLOYEE"
    CONTINGENT_WORKER = "CONTINGENT_WORKER"
    THIRD_PARTY = "THIRD_PARTY"


class NhiType(Enum):
    """Represents a service identity type in the custom application inventory."""
    CUSTOM_APP_NHI = "CUSTOM_APP_NHI"

@dataclass
class CustomAppUserHRISAttributes:
    """HRIS attributes for a custom app user (matches CustomAppUserHRISAttributes proto)."""
    email: Optional[str] = None
    org_name: Optional[str] = None
    business_title: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    position_title: Optional[str] = None
    division: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None


@dataclass
class CustomAppUserV2:
    """Represents a user in the custom application inventory (matches CustomAppUser proto)."""
    id: str
    username: str
    name: str
    status: Optional[str] = UserStatus.ENABLED.value
    hr_type: Optional[HrType] = None
    hris_attributes: Optional[CustomAppUserHRISAttributes] = None

class CustomAppUser(CustomAppUserV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'hrType': 'hr_type'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppUser, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use hr_type instead)
    @property
    def hrType(self) -> Optional[HrType]:
        """Backward-compatible alias for hr_type.

        .. deprecated::
            Use `hr_type` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.hr_type

    @hrType.setter
    def hrType(self, value: Optional[HrType]) -> None:
        """Backward-compatible setter for hr_type.

        .. deprecated::
            Use `hr_type` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.hr_type = value


@dataclass
class CustomAppNhiV2:
    """Represents a NHI in the custom application inventory."""
    username: str
    name: str
    id: str
    type: Optional[str] = NhiType.CUSTOM_APP_NHI.name
    is_external_client: Optional[bool] = False
    owner_id: Optional[str] = None
    custodian_id: Optional[str] = None
    status: Optional[str] = None

class CustomAppNhi(CustomAppNhiV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'ownerId': 'owner_id',
        'custodianId': 'custodian_id'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppNhi, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use owner_id instead)
    @property
    def ownerId(self) -> Optional[str]:
        """Backward-compatible alias for owner_id.

        .. deprecated::
            Use `owner_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.owner_id

    @ownerId.setter
    def ownerId(self, value: Optional[str]) -> None:
        """Backward-compatible setter for owner_id.

        .. deprecated::
            Use `owner_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.owner_id = value

    # Backward-compatible camelCase alias (DEPRECATED: use custodian_id instead)
    @property
    def custodianId(self) -> Optional[str]:
        """Backward-compatible alias for custodian_id.

        .. deprecated::
            Use `custodian_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.custodian_id

    @custodianId.setter
    def custodianId(self, value: Optional[str]) -> None:
        """Backward-compatible setter for custodian_id.

        .. deprecated::
            Use `custodian_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.custodian_id = value

@dataclass
class CustomAppGroupV2:
    """Represents a group in the custom application inventory."""
    name: str
    id: str
    member_user_ids: List[str] = field(default_factory=list)
    member_subgroup_ids: List[str] = field(default_factory=list)

class CustomAppGroup(CustomAppGroupV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'memberUserIds': 'member_user_ids',
        'memberSubgroupIds': 'member_subgroup_ids'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppGroup, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use member_user_ids instead)
    @property
    def memberUserIds(self) -> List[str]:
        """Backward-compatible alias for member_user_ids.

        .. deprecated::
            Use `member_user_ids` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.member_user_ids

    @memberUserIds.setter
    def memberUserIds(self, value: List[str]) -> None:
        """Backward-compatible setter for member_user_ids.

        .. deprecated::
            Use `member_user_ids` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.member_user_ids = value

    # Backward-compatible camelCase alias (DEPRECATED: use member_subgroup_ids instead)
    @property
    def memberSubgroupIds(self) -> List[str]:
        """Backward-compatible alias for member_subgroup_ids.

        .. deprecated::
            Use `member_subgroup_ids` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.member_subgroup_ids

    @memberSubgroupIds.setter
    def memberSubgroupIds(self, value: List[str]) -> None:
        """Backward-compatible setter for member_subgroup_ids.

        .. deprecated::
            Use `member_subgroup_ids` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.member_subgroup_ids = value

@dataclass
class CustomAppScopeV2:
    """Represents a scope in the custom application inventory."""
    id: str
    name: str
    type: str
    parent_scope_id: Optional[str] = None

class CustomAppScope(CustomAppScopeV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'parentScopeId': 'parent_scope_id'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppScope, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use parent_scope_id instead)
    @property
    def parentScopeId(self) -> Optional[str]:
        """Backward-compatible alias for parent_scope_id.

        .. deprecated::
            Use `parent_scope_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.parent_scope_id

    @parentScopeId.setter
    def parentScopeId(self, value: Optional[str]) -> None:
        """Backward-compatible setter for parent_scope_id.

        .. deprecated::
            Use `parent_scope_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.parent_scope_id = value

@dataclass
class CustomAppRole:
    """Represents a role in the custom application inventory."""
    name: str
    id: str
    type: Optional[str] = RoleType.CUSTOM_APP_ROLE.name
    permissions: List[str] = field(default_factory=list)

@dataclass
class CustomAppRoleAssignmentV2:
    """Represents a role assignment in the custom application inventory."""
    id: str
    principal_id: str
    principal_type: str
    role_id: str
    scope_id: Optional[str] = None

class CustomAppRoleAssignment(CustomAppRoleAssignmentV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'principalId': 'principal_id',
        'principalType': 'principal_type',
        'roleId': 'role_id',
        'scopeId': 'scope_id'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppRoleAssignment, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use principal_id instead)
    @property
    def principalId(self) -> str:
        """Backward-compatible alias for principal_id.

        .. deprecated::
            Use `principal_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.principal_id

    @principalId.setter
    def principalId(self, value: str) -> None:
        """Backward-compatible setter for principal_id.

        .. deprecated::
            Use `principal_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.principal_id = value

    # Backward-compatible camelCase alias (DEPRECATED: use principal_type instead)
    @property
    def principalType(self) -> str:
        """Backward-compatible alias for principal_type.

        .. deprecated::
            Use `principal_type` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.principal_type

    @principalType.setter
    def principalType(self, value: str) -> None:
        """Backward-compatible setter for principal_type.

        .. deprecated::
            Use `principal_type` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.principal_type = value

    # Backward-compatible camelCase alias (DEPRECATED: use role_id instead)
    @property
    def roleId(self) -> str:
        """Backward-compatible alias for role_id.

        .. deprecated::
            Use `role_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.role_id

    @roleId.setter
    def roleId(self, value: str) -> None:
        """Backward-compatible setter for role_id.

        .. deprecated::
            Use `role_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.role_id = value

    # Backward-compatible camelCase alias (DEPRECATED: use scope_id instead)
    @property
    def scopeId(self) -> Optional[str]:
        """Backward-compatible alias for scope_id.

        .. deprecated::
            Use `scope_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.scope_id

    @scopeId.setter
    def scopeId(self, value: Optional[str]) -> None:
        """Backward-compatible setter for scope_id.

        .. deprecated::
            Use `scope_id` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.scope_id = value

@dataclass
class CustomAppPermissionV2:
    """Represents a permission in the custom application inventory."""
    name: str
    access_level: Optional[str] = None
    service_name: Optional[str] = None

class CustomAppPermission(CustomAppPermissionV2):
    """Deprecated class. Use only for backward compatibility"""
    _DEPRECATED_ATTRS = {
        'accessLevel': 'access_level',
        'serviceName': 'service_name'
    }

    def __init__(self, **kwargs):
        kwargs = _transform_deprecated_kwargs(kwargs, self._DEPRECATED_ATTRS)
        super(CustomAppPermission, self).__init__(**kwargs)

    # Backward-compatible camelCase alias (DEPRECATED: use access_level instead)
    @property
    def accessLevel(self) -> Optional[str]:
        """Backward-compatible alias for access_level.

        .. deprecated::
            Use `access_level` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.access_level

    @accessLevel.setter
    def accessLevel(self, value: Optional[str]) -> None:
        """Backward-compatible setter for access_level.

        .. deprecated::
            Use `access_level` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.access_level = value

    # Backward-compatible camelCase alias (DEPRECATED: use service_name instead)
    @property
    def serviceName(self) -> Optional[str]:
        """Backward-compatible alias for service_name.

        .. deprecated::
            Use `service_name` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        return self.service_name

    @serviceName.setter
    def serviceName(self, value: Optional[str]) -> None:
        """Backward-compatible setter for service_name.

        .. deprecated::
            Use `service_name` instead. This camelCase alias is maintained for backward
            compatibility only and will be removed in a future version.
        """
        self.service_name = value

@dataclass
class CustomAppInventory:
    """Container for all custom application inventory data."""
    users: Dict[str, CustomAppUser] = field(default_factory=dict)
    nhis: Dict[str, CustomAppNhi] = field(default_factory=dict)
    roles: Dict[str, CustomAppRole] = field(default_factory=dict)
    assignments: Dict[str, CustomAppRoleAssignment] = field(default_factory=dict)
    permissions: Dict[str, CustomAppPermission] = field(default_factory=dict)
    groups: Dict[str, CustomAppGroup] = field(default_factory=dict)
    scopes: Dict[str, CustomAppScope] = field(default_factory=dict)


def load_inventory_from_json(data: dict) -> CustomAppInventory:
    """Load CustomAppInventory from JSON dict with camelCase/snake_case support.

    Args:
        data: Dictionary from JSON.load() with inventory data

    Returns:
        CustomAppInventory instance

    Note:
        Supports both camelCase and snake_case keys due to dataclass constructors
    """
    inventory = CustomAppInventory()

    # Load users
    if 'users' in data:
        for user_id, user_data in data['users'].items():
            # Convert nested hris_attributes dict to CustomAppUserHRISAttributes instance
            if 'hris_attributes' in user_data and isinstance(user_data['hris_attributes'], dict):
                user_data = user_data.copy()  # Avoid modifying original data
                user_data['hris_attributes'] = CustomAppUserHRISAttributes(**user_data['hris_attributes'])
            inventory.users[user_id] = CustomAppUser(**user_data)

    # Load nhis
    if 'nhis' in data:
        for nhi_id, nhi_data in data['nhis'].items():
            inventory.nhis[nhi_id] = CustomAppNhi(**nhi_data)

    # Load groups
    if 'groups' in data:
        for group_id, group_data in data['groups'].items():
            inventory.groups[group_id] = CustomAppGroup(**group_data)

    # Load scopes
    if 'scopes' in data:
        for scope_id, scope_data in data['scopes'].items():
            inventory.scopes[scope_id] = CustomAppScope(**scope_data)

    # Load roles
    if 'roles' in data:
        for role_id, role_data in data['roles'].items():
            inventory.roles[role_id] = CustomAppRole(**role_data)

    # Load permissions
    if 'permissions' in data:
        for perm_name, perm_data in data['permissions'].items():
            inventory.permissions[perm_name] = CustomAppPermission(**perm_data)

    # Load assignments
    if 'assignments' in data:
        for assign_id, assign_data in data['assignments'].items():
            inventory.assignments[assign_id] = CustomAppRoleAssignment(**assign_data)

    return inventory


def _check_user_enums(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check user enum validations.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    if strict_enums:
        for user_id, user in inventory.users.items():
            if user.status and user.status not in [e.value for e in UserStatus]:
                errors.append(f"User '{user_id}' has invalid status: '{user.status}'")
            if user.hr_type and user.hr_type not in HrType:
                errors.append(f"User '{user_id}' has invalid hr_type: '{user.hr_type}'")
    return ("User Enum Validation", errors)


def _check_nhi_references(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check NHI references to users.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    for nhi_id, nhi in inventory.nhis.items():
        if nhi.owner_id and nhi.owner_id not in inventory.users:
            errors.append(f"NHI '{nhi_id}' owner_id '{nhi.owner_id}' not found in users")
        if nhi.custodian_id and nhi.custodian_id not in inventory.users:
            errors.append(f"NHI '{nhi_id}' custodian_id '{nhi.custodian_id}' not found in users")
    return ("NHI Reference Validation", errors)


def _check_group_references(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check group member references.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    for group_id, group in inventory.groups.items():
        for user_id in group.member_user_ids:
            if user_id not in inventory.users:
                errors.append(f"Group '{group_id}' member_user_id '{user_id}' not found in users")
        for subgroup_id in group.member_subgroup_ids:
            if subgroup_id not in inventory.groups:
                errors.append(f"Group '{group_id}' member_subgroup_id '{subgroup_id}' not found in groups")
    return ("Group Reference Validation", errors)


def _check_scope_references(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check scope parent references and enums.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    for scope_id, scope in inventory.scopes.items():
        if scope.parent_scope_id and scope.parent_scope_id not in inventory.scopes:
            errors.append(f"Scope '{scope_id}' parent_scope_id '{scope.parent_scope_id}' not found in scopes")
        if strict_enums and scope.type not in [e.value for e in ScopeType]:
            errors.append(f"Scope '{scope_id}' has invalid type: '{scope.type}'")
    return ("Scope Reference Validation", errors)


def _check_role_references(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check role permission references and enums.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    for role_id, role in inventory.roles.items():
        for permission in role.permissions:
            if permission not in inventory.permissions:
                errors.append(f"Role '{role_id}' permission '{permission}' not found in permissions")
        if strict_enums and role.type not in [e.value for e in RoleType]:
            errors.append(f"Role '{role_id}' has invalid type: '{role.type}'")
    return ("Role Reference Validation", errors)


def _check_permission_enums(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check permission enum validations.

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    if strict_enums:
        for perm_name, perm in inventory.permissions.items():
            if perm.access_level and perm.access_level not in [e.value for e in PermissionAccessLevel]:
                errors.append(f"Permission '{perm_name}' has invalid access_level: '{perm.access_level}'")
    return ("Permission Enum Validation", errors)


def _check_assignment_references(inventory: CustomAppInventory, strict_enums: bool) -> tuple:
    """Check assignment references (most complex check).

    Returns:
        Tuple of (check_name, list_of_errors)
    """
    errors = []
    for assign_id, assignment in inventory.assignments.items():
        # Validate role_id
        if assignment.role_id not in inventory.roles:
            errors.append(f"Assignment '{assign_id}' role_id '{assignment.role_id}' not found in roles")

        # Validate scope_id (optional)
        if assignment.scope_id and assignment.scope_id not in inventory.scopes:
            errors.append(f"Assignment '{assign_id}' scope_id '{assignment.scope_id}' not found in scopes")

        # Validate principal_type enum
        if strict_enums and assignment.principal_type not in [e.value for e in PrincipalType]:
            errors.append(f"Assignment '{assign_id}' has invalid principal_type: '{assignment.principal_type}'")

        # Validate principal_id based on principal_type
        if assignment.principal_type == PrincipalType.HUMAN.value:
            if assignment.principal_id not in inventory.users:
                errors.append(f"Assignment '{assign_id}' principal_id '{assignment.principal_id}' not found in users (type=HUMAN)")
        elif assignment.principal_type == PrincipalType.NHI.value:
            if assignment.principal_id not in inventory.nhis:
                errors.append(f"Assignment '{assign_id}' principal_id '{assignment.principal_id}' not found in nhis (type=NHI)")
        elif assignment.principal_type == PrincipalType.GROUP.value:
            if assignment.principal_id not in inventory.groups:
                errors.append(f"Assignment '{assign_id}' principal_id '{assignment.principal_id}' not found in groups (type=GROUP)")

    return ("Assignment Reference Validation", errors)


def validate_inventory_consistency(
    inventory: CustomAppInventory,
    strict_enums: bool = True
) -> List[str]:
    """Validate CustomAppInventory consistency and referential integrity.

    Args:
        inventory: CustomAppInventory to validate
        strict_enums: If True, validate enum values. If False, skip enum validation.

    Returns:
        List of validation error messages (empty if valid)
    """
    # Define all validation checks
    validation_checks = [
        _check_user_enums,
        _check_nhi_references,
        _check_group_references,
        _check_scope_references,
        _check_role_references,
        _check_permission_enums,
        _check_assignment_references,
    ]

    all_errors = []
    check_results = []

    # Run all checks
    for check_func in validation_checks:
        check_name, errors = check_func(inventory, strict_enums)
        check_results.append((check_name, len(errors), "PASS" if not errors else "FAIL"))
        all_errors.extend(errors)

    # Print summary report
    logger.info("=" * 70)
    logger.info("CustomAppInventory Validation Summary")
    logger.info("=" * 70)
    for check_name, error_count, status in check_results:
        status_symbol = "✅" if status == "PASS" else "❌"
        logger.info(f"{status_symbol} {check_name:.<45} {status} ({error_count} errors)")
    logger.info("=" * 70)
    logger.info(f"Total Checks: {len(check_results)} | Passed: {sum(1 for _, _, s in check_results if s == 'PASS')} | Failed: {sum(1 for _, _, s in check_results if s == 'FAIL')}")
    logger.info(f"Total Errors: {len(all_errors)}")
    logger.info("=" * 70)

    return all_errors


def validate_inventory_from_json(
    data: dict,
    strict_enums: bool = True
) -> CustomAppInventory:
    """Load and validate CustomAppInventory from JSON dict.

    Args:
        data: Dictionary from JSON.load() with inventory data
        strict_enums: If True, validate enum values. If False, skip enum validation.

    Returns:
        CustomAppInventory instance (only if validation passes)

    Raises:
        ValueError: If validation fails (includes all error messages)
    """
    # Load inventory
    inventory = load_inventory_from_json(data)

    # Validate consistency
    errors = validate_inventory_consistency(inventory, strict_enums=strict_enums)

    # Raise if errors found
    if errors:
        error_msg = f"CustomAppInventory validation failed with {len(errors)} error(s):\n"
        error_msg += "\n".join(f"  - {err}" for err in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("CustomAppInventory validation passed successfully")
    return inventory
