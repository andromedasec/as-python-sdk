"""
Custom App Inventory Transformer

This module provides functionality to transform CSV inventory files into
a standardized JSON format for custom applications.
"""

import os
import argparse
import logging
import datetime
import json
from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional



mock_data = {
 "groups": {
    "Group A": {
      "id": "Group A",
      "memberUserIds": [
        "chip.brown@beatles.ai",
        "kieran.juarez@beatles.ai",
        "devin.chapman@beatles.ai"
      ],
      "name": "Group A"
    },
    "Group B": {
      "id": "Group B",
      "memberUserIds": [
        "bobbie.laundry@beatles.ai"
      ],
      "name": "Group B"
    },
    "Group C": {
      "id": "Group C",
      "memberUserIds": [
        "abby.palmer@beatles.ai"
      ],
      "name": "Group C"
    },
    "Group D": {
      "id": "Group D",
      "memberUserIds": [
        "john.smith@beatles.ai",
        "jane.doe@beatles.ai"
      ],
      "name": "Group D"
    },
    "Group E": {
      "id": "Group E",
      "memberUserIds": [
        "mike.richard@beatles.ai"
      ],
      "name": "Group E"
    }
  },
  "users": {
    "matt.james@beatles.ai": {
      "id": "matt.james@beatles.ai",
      "username": "matt.james@beatles.ai",
      "name": "Matt James",
      "status": "ENABLED"
    },
    "marcus.smith@beatles.ai": {
      "id": "marcus.smith@beatles.ai",
      "username": "marcus.smith@beatles.ai",
      "name": "Marcus Smith",
      "status": "ENABLED"
    },
    "matt.cooper@beatles.ai": {
      "id": "matt.cooper@beatles.ai",
      "username": "matt.cooper@beatles.ai",
      "name": "Matt Cooper",
      "status": "ENABLED"
    },
    "fred.marsh@beatles.ai": {
      "id": "fred.marsh@beatles.ai",
      "username": "fred.marsh@beatles.ai",
      "name": "Fred Marsh",
      "status": "ENABLED"
    },
    "richar.Mike@beatles.ai": {
      "id": "richar.Mike@beatles.ai",
      "username": "richar.Mike@beatles.ai",
      "name": "Richard Mike",
      "status": "ENABLED"
    },
    "samy.joseph@beatles.ai": {
      "id": "samy.joseph@beatles.ai",
      "username": "samy.joseph@beatles.ai",
      "name": "Samy Joseph",
      "status": "ENABLED"
    },
    "hail.mary@beatles.ai": {
      "id": "hail.mary@beatles.ai",
      "username": "hail.mary@beatles.ai",
      "name": "Hail Mary",
      "status": "ENABLED"
    },
    "abby.palmer@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "abby.palmer@beatles.ai",
      "name": "Abby Palmer",
      "status": "ENABLED",
      "username": "abby.palmer@beatles.ai"
    },
    "bobbie.laundry@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "bobbie.laundry@beatles.ai",
      "name": "Bobbie Laundry",
      "status": "ENABLED",
      "username": "bobbie.laundry@beatles.ai"
    },
    "chip.brown@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "chip.brown@beatles.ai",
      "name": "Brown Chip",
      "status": "ENABLED",
      "username": "chip.brown@beatles.ai"
    },
    "devin.chapman@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "devin.chapman@beatles.ai",
      "name": "Devin Chapman",
      "status": "ENABLED",
      "username": "devin.chapman@beatles.ai"
    },
    "jane.doe@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "jane.doe@beatles.ai",
      "name": "Jane Doe",
      "status": "ENABLED",
      "username": "jane.doe@beatles.ai"
    },
    "john.smith@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "john.smith@beatles.ai",
      "name": "John Smith",
      "status": "ENABLED",
      "username": "john.smith@beatles.ai"
    },
    "kieran.juarez@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "kieran.juarez@beatles.ai",
      "name": "Kieran Juarez",
      "status": "ENABLED",
      "username": "kieran.juarez@beatles.ai"
    },
    "mike.richard@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "mike.richard@beatles.ai",
      "name": "Mike Richard",
      "status": "ENABLED",
      "username": "mike.richard@beatles.ai"
    },
    "ashley.porter@beatles.ai": {
      "hrType": "EMPLOYEE",
      "id": "ashley.porter@beatles.ai",
      "name": "Ashley Porter",
      "status": "ENABLED",
      "username": "ashley.porter@beatles.ai"
    }
  },

  "nhis": {
    "application-1": {
      "id": "app-uuid-00001",
      "username": "application-1",
      "name": "Application 1 Service Identity",
      "ownerId": "matt.james@beatles.ai",
      "custodianId": "marcus.smith@beatles.ai",
      "status": "ENABLED"
    },
    "application-2": {
      "id": "app-uuid-00002",
      "username": "application-2",
      "name": "Application 2 Service Identity",
      "ownerId": "matt.james@beatles.ai",
      "custodianId": "marcus.smith@beatles.ai",
      "status": "ENABLED"
    },
    "application-3": {
      "id": "app-uuid-00003",
      "username": "application-3",
      "name": "Application 3 Service Identity",
      "ownerId": "matt.cooper@beatles.ai",
      "custodianId": "matt.james@beatles.ai",
      "status": "ENABLED"
    },
    "application-4": {
      "id": "app-uuid-00004",
      "username": "application-4",
      "name": "Application 4 Service Identity",
      "ownerId": "matt.cooper@beatles.ai",
      "custodianId": "marcus.smith@beatles.ai",
      "status": "DISABLED"
    },
    "application-5": {
      "id": "app-uuid-00005",
      "username": "application-5",
      "name": "Application 5 Service Identity",
      "ownerId": "marcus.smith@beatles.ai",
      "custodianId": "matt.cooper@beatles.ai",
      "status": "ENABLED"
    }
  },
  "scopes": {
    "Server A": {
      "id": "Server A",
      "name": "Server A",
      "type": "FOLDER"
    },
    "Server A/Drive:\\location\\finance\\Reports": {
      "id": "Server A/Drive:\\location\\finance\\Reports",
      "name": "Drive:\\location\\finance\\Reports",
      "parentScopeId": "Server A",
      "type": "ACCOUNT"
    },
    "Server A/Drive:\\location\\general\\Team Folder": {
      "id": "Server A/Drive:\\location\\general\\Team Folder",
      "name": "Drive:\\location\\general\\Team Folder",
      "parentScopeId": "Server A",
      "type": "ACCOUNT"
    },
    "Server B": {
      "id": "Server B",
      "name": "Server B",
      "type": "FOLDER"
    },
    "Server B/Drive:\\projects\\Engineering": {
      "id": "Server B/Drive:\\projects\\Engineering",
      "name": "Drive:\\projects\\Engineering",
      "parentScopeId": "Server B",
      "type": "ACCOUNT"
    }
  },
  "roles": {
    "beatles-matt-cooper-role": {
      "id": "beatles-matt-cooper-role",
      "name": "beatles-matt-cooper-role",
      "type": "CUSTOM_APP_USER_ROLE",
      "permissions": [
        "pManageUsers",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewBank",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pDataEntry",
        "pViewCheckReports",
        "pViewTxnReports",
        "pMergeRecords",
        "pImpersonation",
        "pDoCsEmulation",
        "pManualCharges",
        "pAccessToHighSecurityPartnersData",
        "pAccessHIPAAOrgs",
        "pViewRiskProfile",
        "pVirtualCardPFY",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "enabedBillbaseUI",
        "enabledNewSuperOrgPage"
      ]
    },
    "riskops_manager": {
      "id": "riskops_manager",
      "name": "riskops_manager",
      "type": "CUSTOM_APP_ROLE",
      "permissions": [
        "pModifyData",
        "pModifyBank",
        "pModifyVerify",
        "pModifyBilling",
        "pPrintChecks",
        "pViewOrg",
        "pViewACH",
        "pViewBank",
        "pViewPositivePay",
        "pViewBilling",
        "pViewVerify",
        "pViewCheckInfo",
        "pEnterVoidChecks",
        "pViewCheckImage",
        "pModifyCheckImage",
        "pDataEntry",
        "pViewCheckFiles",
        "pViewCheckReports",
        "pViewTxnReports",
        "pEditFraudControl",
        "pModifyFundingBank",
        "pMergeRecords",
        "pModifyEmail",
        "pImpersonation",
        "pDoCsEmulation",
        "pARApproval",
        "pViewTaxIdReports",
        "pUpdateOrgBilling",
        "pManualCharges",
        "pManualRefunds",
        "pAccessToHighSecurityPartnersData",
        "pManageIntlPayments",
        "pModifyPayment",
        "pAccessToTinEin",
        "pPhotoIDVerification",
        "pAccessHIPAAOrgs",
        "pManageWalletBalance",
        "pViewRiskProfile",
        "pViewComplianceFields",
        "pEditComplianceFields",
        "pVirtualCardPFY",
        "pViewChecks"
      ]
    },
    "processing_l1": {
      "id": "processing_l1",
      "name": "processing_l1",
      "type": "CUSTOM_APP_ROLE",
      "permissions": [
        "pModifyData",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewBank",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pDataEntry",
        "pViewTxnReports",
        "pMergeRecords",
        "pModifyEmail",
        "pImpersonation",
        "pDoCsEmulation",
        "pUpdateOrgBilling",
        "pManualCharges",
        "pManualRefunds",
        "pPhotoIDVerification",
        "pEditTaxExempt",
        "pAccessHIPAAOrgs",
        "pEditPaymentStatus",
        "pManageBillingDiscounts",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "enabedBillbaseUI",
        "enabledNewSuperOrgPage"
      ]
    },
    "partner_support_l1": {
      "id": "partner_support_l1",
      "name": "partner_support_l1",
      "type": "CUSTOM_APP_ROLE",
      "permissions": [
        "pModifyData",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewBank",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pDataEntry",
        "pViewCheckReports",
        "pViewTxnReports",
        "pMergeRecords",
        "pImpersonation",
        "pDoCsEmulation",
        "pManualCharges",
        "pAccessToHighSecurityPartnersData",
        "pAccessHIPAAOrgs",
        "pViewRiskProfile",
        "pVirtualCardPFY",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "enabedBillbaseUI",
        "enabledNewSuperOrgPage"
      ]
    },
    "internal_support_l1": {
      "id": "internal_support_l1",
      "name": "internal_support_l1",
      "type": "CUSTOM_APP_ROLE",
      "permissions": [
        "pModifyData",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewACH",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pModifyCheckImage",
        "pDataEntry",
        "pViewCheckReports",
        "pViewTxnReports",
        "pMergeRecords",
        "pModifyEmail",
        "pImpersonation",
        "pDoCsEmulation",
        "pSyncTools",
        "pUpdateOrgBilling",
        "pSyncConfig",
        "pAccessHIPAAOrgs",
        "pViewRiskProfile",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "enabedBillbaseUI"
      ]
    },
    "tech_support_l1": {
      "id": "tech_support_l1",
      "name": "tech_support_l1",
      "type": "CUSTOM_APP_ROLE",
      "permissions": [
        "pModifyData",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewACH",
        "pViewBank",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pModifyCheckImage",
        "pDataEntry",
        "pViewCheckReports",
        "pViewTxnReports",
        "pMergeRecords",
        "pModifyEmail",
        "pImpersonation",
        "pDoCsEmulation",
        "pSyncTools",
        "pUpdateOrgBilling",
        "pSyncConfig",
        "pAccessToHighSecurityPartnersData",
        "pManageFederatedDomains",
        "pAccessHIPAAOrgs",
        "pViewRiskProfile",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "pManageStripeAccount",
        "enabedBillbaseUI",
        "enabledNewSuperOrgPage",
        "pModifyData",
        "pModifyBank",
        "pModifyBilling",
        "pViewOrg",
        "pViewACH",
        "pViewBank",
        "pViewBilling",
        "pViewCheckInfo",
        "pViewCheckImage",
        "pModifyCheckImage",
        "pDataEntry",
        "pViewCheckReports",
        "pViewTxnReports",
        "pMergeRecords",
        "pModifyEmail",
        "pImpersonation",
        "pDoCsEmulation",
        "pSyncTools",
        "pUpdateOrgBilling",
        "pSyncConfig",
        "pAccessToHighSecurityPartnersData",
        "pManageFederatedDomains",
        "pAccessHIPAAOrgs",
        "pViewRiskProfile",
        "pViewChecks",
        "pManageVendorsAdvanced",
        "pManageStripeAccount",
        "enabedBillbaseUI",
        "enabledNewSuperOrgPage"
      ]
    },
    "Modify": {
      "id": "Modify",
      "name": "Modify",
      "type": "CUSTOM_APP_ROLE"
    },
    "Modify-S": {
      "id": "Modify-S",
      "name": "Modify-S",
      "type": "CUSTOM_APP_ROLE"
    },
    "Read": {
      "id": "Read",
      "name": "Read",
      "type": "CUSTOM_APP_ROLE"
    }
  },
  "assignments": {
    "fred.marsh@beatles.ai_partner_support_l1": {
      "id": "fred.marsh@beatles.ai_partner_support_l1",
      "principalId": "fred.marsh@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "partner_support_l1"
    },
    "matt.cooper@beatles.ai_beatles-matt-cooper-role": {
      "id": "matt.cooper@beatles.ai_beatles-matt-cooper-role",
      "principalId": "matt.cooper@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "beatles-matt-cooper-role"
    },
    "richar.Mike@beatles.ai_tech_support_l1": {
      "id": "richar.Mike@beatles.ai_tech_support_l1",
      "principalId": "richar.Mike@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "tech_support_l1"
    },
    "marcus.smith@beatles.ai_processing_l1": {
      "id": "marcus.smith@beatles.ai_processing_l1",
      "principalId": "marcus.smith@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "processing_l1"
    },
    "matt.james@beatles.ai_tech_support_l1": {
      "id": "matt.james@beatles.ai_tech_support_l1",
      "principalId": "matt.james@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "tech_support_l1"
    },
    "matt.james@beatles.ai_riskops_manager": {
      "id": "matt.james@beatles.ai_riskops_manager",
      "principalId": "matt.james@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "riskops_manager"
    },
    "samy.joseph@beatles.ai_internal_support_l1": {
      "id": "samy.joseph@beatles.ai_internal_support_l1",
      "principalId": "samy.joseph@beatles.ai",
      "principalType": "HUMAN",
      "roleId": "internal_support_l1"
    },
    "netapp_beatles|Group A|Modify|Server A/Drive:\\location\\general\\Team Folder": {
      "id": "netapp_beatles|Group A|Modify|Server A/Drive:\\location\\general\\Team Folder",
      "principalId": "Group A",
      "principalType": "GROUP",
      "roleId": "Modify",
      "scopeId": "Server A/Drive:\\location\\general\\Team Folder"
    },
    "netapp_beatles|Group B|Modify-S|Server A/Drive:\\location\\finance\\Reports": {
      "id": "netapp_beatles|Group B|Modify-S|Server A/Drive:\\location\\finance\\Reports",
      "principalId": "Group B",
      "principalType": "GROUP",
      "roleId": "Modify-S",
      "scopeId": "Server A/Drive:\\location\\finance\\Reports"
    },
    "netapp_beatles|Group C|Read|Server A/Drive:\\location\\finance\\Reports": {
      "id": "netapp_beatles|Group C|Read|Server A/Drive:\\location\\finance\\Reports",
      "principalId": "Group C",
      "principalType": "GROUP",
      "roleId": "Read",
      "scopeId": "Server A/Drive:\\location\\finance\\Reports"
    },
    "netapp_beatles|Group D|Modify|Server B/Drive:\\projects\\Engineering": {
      "id": "netapp_beatles|Group D|Modify|Server B/Drive:\\projects\\Engineering",
      "principalId": "Group D",
      "principalType": "GROUP",
      "roleId": "Modify",
      "scopeId": "Server B/Drive:\\projects\\Engineering"
    },
    "netapp_beatles|Group D|Read|Server B/Drive:\\projects\\Engineering": {
      "id": "netapp_beatles|Group D|Read|Server B/Drive:\\projects\\Engineering",
      "principalId": "Group D",
      "principalType": "GROUP",
      "roleId": "Read",
      "scopeId": "Server B/Drive:\\projects\\Engineering"
    },
    "netapp_beatles|Group E|Read|Server A/Drive:\\location\\general\\Team Folder": {
      "id": "netapp_beatles|Group E|Read|Server A/Drive:\\location\\general\\Team Folder",
      "principalId": "Group E",
      "principalType": "GROUP",
      "roleId": "Read",
      "scopeId": "Server A/Drive:\\location\\general\\Team Folder"
    }
  }
}

# Data Classes that
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
    """Represents a scope type in the custom application inventory."""
    UNSPECIFIED = "UNSPECIFIED"
    PROVIDER = "PROVIDER"
    FOLDER = "FOLDER"
    ACCOUNT = "ACCOUNT"
    RESOURCE_GROUP = "RESOURCE_GROUP"

class HrType(StrEnum):
    """Represents a HR type in the custom application inventory."""
    HR_TYPE_UNSPECIFIED = ""
    EMPLOYEE = "EMPLOYEE"
    CONTINGENT_WORKER = "CONTINGENT_WORKER"
    THIRD_PARTY = "THIRD_PARTY"

class NhiType(Enum):
    """Represents a service identity type in the custom application inventory."""
    CUSTOM_APP_NHI = "CUSTOM_APP_NHI"

@dataclass
class CustomAppUser:
    """Represents a user in the custom application inventory."""
    username: str
    name: str
    id: str
    status: Optional[str] = UserStatus.ENABLED.name
    hrType: Optional[str] = None

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



# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 100
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME_PREFIX = "test"
DEFAULT_INVENTORY_TYPE = "CUSTOM_TYPE1_INVENTORY_CSV"

# CSV field mappings
NON_PERMISSIONS_KEYS = {
    'id', 'isActive', 'firstName', 'lastName', 'email', 'opRoleId',
    'employeeId', 'Manager', 'Department', 'total active dates',
    'createdDate', 'updatedDate', 'Total active permissions'
}

# Status constants
USER_STATUS_ENABLED = "ENABLED"
PRINCIPAL_TYPE_HUMAN = "HUMAN"
ROLE_TYPE_CUSTOM_APP = "CUSTOM_APP_ROLE"
ROLE_TYPE_CUSTOM_APP_USER = "CUSTOM_APP_USER_ROLE"


class CustomAppInventoryTransformer:
    """Transforms CSV inventory files into standardized JSON format."""

    def __init__(self):
        self.inventory = self.load_mock_data(mock_data)

    def load_mock_data(self, data: dict) -> CustomAppInventory:
        """
        Converts the mock data dictionary into a fully populated CustomAppInventory object.
        """
        # Parse users
        users: Dict[str, CustomAppUser] = {}
        for key, user_data in data.get("users", {}).items():
            users[key] = CustomAppUser(
                username=user_data["username"],
                name=user_data["name"],
                id=user_data["id"],
                status=user_data.get("status"),
                hrType=user_data.get("hrType"),
            )

        # Parse nhis
        nhis: Dict[str, CustomAppNhi] = {}
        for key, nhi_data in data.get("nhis", {}).items():
            nhis[key] = CustomAppNhi(
                username=nhi_data["username"],
                name=nhi_data["name"],
                id=nhi_data["id"],
                type=nhi_data.get("type"),
                is_external_client=nhi_data.get("is_external_client", False),
                ownerId=nhi_data.get("ownerId"),
                custodianId=nhi_data.get("custodianId"),
                status=nhi_data.get("status"),
            )

        # Parse groups
        groups: Dict[str, CustomAppGroup] = {}
        for key, group_data in data.get("groups", {}).items():
            groups[key] = CustomAppGroup(
                name=group_data["name"],
                id=group_data["id"],
                memberUserIds=group_data.get("memberUserIds", []),
                memberSubgroupIds=group_data.get("memberSubgroupIds", []),
            )

        # Parse scopes
        scopes: Dict[str, CustomAppScope] = {}
        for key, scope_data in data.get("scopes", {}).items():
            scopes[key] = CustomAppScope(
                id=scope_data["id"],
                name=scope_data["name"],
                type=scope_data["type"],
                parentScopeId=scope_data.get("parentScopeId"),
            )

        # Parse roles
        roles: Dict[str, CustomAppRole] = {}
        for key, role_data in data.get("roles", {}).items():
            roles[key] = CustomAppRole(
                name=role_data["name"],
                id=role_data["id"],
                type=role_data.get("type"),
                permissions=role_data.get("permissions", []),
            )

        # Parse assignments
        assignments: Dict[str, CustomAppRoleAssignment] = {}
        for key, assignment_data in data.get("assignments", {}).items():
            assignments[key] = CustomAppRoleAssignment(
                id=assignment_data["id"],
                principalId=assignment_data["principalId"],
                principalType=assignment_data["principalType"],
                roleId=assignment_data["roleId"],
                scopeId=assignment_data.get("scopeId"),
            )

        return CustomAppInventory(
            users=users,
            nhis=nhis,
            roles=roles,
            assignments=assignments,
            permissions={},  # No permissions in mock_data
            groups=groups,
            scopes=scopes,
        )


    def convert_to_andromeda_dict(self, obj: Any) -> Any:
        """
        Recursively convert dictionary keys from snake_case to camelCase.
        And removes empty values.
        Handles dictionaries, lists, and nested structures.
        """
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return {k: self.convert_to_andromeda_dict(v) for k, v in obj.items() if v}
        if isinstance(obj, list):
            return [self.convert_to_andromeda_dict(item) for item in obj if item]
        return obj


    def transform_and_export(self, app_name_prefix: str, output_dir: str) -> dict:
        """Transform inventory and export to JSON file."""
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Generate output filename
        timestamp = datetime.datetime.now().replace(microsecond=0, second=0).isoformat()
        output_file = Path(output_dir) / f"{app_name_prefix}-{timestamp}.json"

        try:
            # Convert to dictionary, camelize keys, and remove empty values
            inventory_dict = asdict(self.inventory)
            inventory_dict = self.convert_to_andromeda_dict(inventory_dict)
            with open(output_file, 'w', encoding="utf-8") as file:
                json.dump(inventory_dict, file, indent=2)
                logger.info("Written inventory to file %s", output_file)
        except Exception as e:
            logger.error("Error writing output file %s: %s", output_file, e)
            raise

        return mock_data



def setup_logging() -> None:
    """Setup logging configuration."""
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    help_text = """
    This script converts different CSV imports into Andromeda custom inventory format.

    Example:
        python3 custom_app_inventory_transformer.py --inventory_type=CUSTOM_TYPE1_INVENTORY_CSV --inventory_file=<file> --output_dir=<dir>
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=help_text
    )

    parser.add_argument(
        '--app_name',
        help='Application name',
        default=DEFAULT_APP_NAME_PREFIX
    )

    parser.add_argument(
        '--output_dir',
        help='Output directory',
        default=DEFAULT_OUTPUT_DIR
    )

    parser.add_argument(
        '--inventory_type',
        help='Inventory type',
        default=DEFAULT_INVENTORY_TYPE
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    setup_logging()
    args = parse_arguments()

    try:
        # Print the environment variables
        try:
            auth_json = os.environ.get('AS_CUSTOM_APP_AUTH_JSON', '')
            logger.info("Auth JSON Environment Variable: %s", auth_json)
            if auth_json:
                # load the auth JSON as a dictionary
                auth_json_dict = json.loads(auth_json)
                logger.info("Auth JSON: %s", json.dumps(auth_json_dict, indent=2))
            else:
                logger.info("No auth JSON found")

            metadata_str = os.environ.get('AS_CUSTOM_APP_METADATA', '')
            if metadata_str:
                metadata = json.loads(metadata_str)
                logger.info("Metadata %s", metadata)
            else:
                logger.info("no metadata passed")
        except Exception as e:
            logger.info("exception %s", e)


        transformer = CustomAppInventoryTransformer()
        transformer.transform_and_export(
            app_name_prefix=args.app_name.strip(),
            output_dir=args.output_dir.strip()
        )
        logger.info("Transformation completed successfully")
    except Exception as e:
        logger.error("Transformation failed: %s", e)
        raise


if __name__ == '__main__':
    main()
