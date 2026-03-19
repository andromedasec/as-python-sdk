# Data Classes that are used for Custom Application
# The custom application downloader or translator files
# can use these data files to


from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, List

import logging


# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"

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
    UNSPECIFIED = "UNSPECIFIED"
    LIST = "LIST"
    WRITE_TAG = "WRITE_TAG"
    DELETE_TAG = "DELETE_TAG"
    READ_METADATA = "READ_METADATA"
    READ_DATA = "READ_DATA"
    WRITE_METADATA = "WRITE_METADATA"
    CREATE = "CREATE"
    WRITE_DATA = "WRITE_DATA"
    DELETE_DATA = "DELETE_DATA"
    DELETE = "DELETE"
    PERMISSIONS_MANAGEMENT = "PERMISSIONS_MANAGEMENT"

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
class CustomAppUser:
    """Represents a user in the custom application inventory (matches CustomAppUser proto)."""
    id: str
    username: str
    name: str
    status: Optional[str] = UserStatus.ENABLED.value
    hrType: Optional[HrType] = None
    hris_attributes: Optional[CustomAppUserHRISAttributes] = None


@dataclass
class CustomAppNhi:
    """Represents a NHI in the custom application inventory."""
    username: str
    name: str
    id: str
    type: Optional[str] = NhiType.CUSTOM_APP_NHI.name
    is_external_client: Optional[bool] = False
    ownerId: Optional[str] = None
    custodianId: Optional[str] = None
    status: Optional[str] = None

@dataclass
class CustomAppGroup:
    """Represents a group in the custom application inventory."""
    name: str
    id: str
    memberUserIds: List[str] = field(default_factory=list)
    memberSubgroupIds: List[str] = field(default_factory=list)

@dataclass
class CustomAppScope:
    """Represents a scope in the custom application inventory."""
    id: str
    name: str
    type: str
    parentScopeId: Optional[str] = None

@dataclass
class CustomAppRole:
    """Represents a role in the custom application inventory."""
    name: str
    id: str
    type: Optional[str] = RoleType.CUSTOM_APP_ROLE.name
    permissions: List[str] = field(default_factory=list)

@dataclass
class CustomAppRoleAssignment:
    """Represents a role assignment in the custom application inventory."""
    id: str
    principalId: str
    principalType: str
    roleId: str
    scopeId: Optional[str] = None

@dataclass
class CustomAppPermission:
    """Represents a permission in the custom application inventory."""
    name: str
    accessLevel: Optional[str] = None
    serviceName: Optional[str] = None

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
