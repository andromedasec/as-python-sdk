# Custom App SDK

A Python SDK for transforming custom application inventory data (CSV exports) into Andromeda's standardized JSON format.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Custom App Models](#custom-app-models)
- [Utility Functions](#utility-functions)
- [Base Transformer Class](#base-transformer-class)
- [Creating a New Custom App Transformer](#creating-a-new-custom-app-transformer)
- [Examples](#examples)
- [Testing](#testing)

---

## Overview

The Custom App SDK provides a framework for ingesting access control data from custom applications that aren't natively supported by Andromeda. It enables you to:

- Transform CSV inventory exports into standardized JSON format
- Define users, roles, permissions, groups, and scopes
- Create role assignments with principal-based access control
- Validate inventory data before ingestion

**Key Benefits:**

- **Single Source of Truth**: All data models defined once in `custom_app_models.py`
- **Reusable Base Class**: Common CSV processing logic in `CustomAppCsvTransformer`
- **Type Safety**: Python dataclasses with type hints
- **Extensible**: Easy to add new custom applications

---

## Architecture

```text
sdk/customapp/
├── custom_app_models.py      # Data models and enums
├── custom_app_utils.py        # Utility functions
├── csv_transformer.py         # Base transformer class
├── mock_data.json             # Sample inventory data
└── README.md                  # This file
```

**Data Flow:**

```text
CSV File → CustomAppTransformer → Validate → Transform → Export JSON → processed by inventory
```

---

## Custom App Models

### Location

`sdk/customapp/custom_app_models.py`

### Enums

#### UserStatus

User account status in the application.

```python
class UserStatus(Enum):
    ENABLED = "ENABLED"
    DEACTIVATED = "DEACTIVATED"
    IDENTITY_STATUS_UNRESOLVED = "IDENTITY_STATUS_UNRESOLVED"
    SUSPENDED = "SUSPENDED"
```

#### PrincipalType

Type of principal in role assignments.

```python
class PrincipalType(Enum):
    HUMAN = "HUMAN"          # Human user
    NHI = "NHI"              # Non-human identity (service account)
    GROUP = "GROUP"          # Group of users
```

#### RoleType

Type of role in the application.

```python
class RoleType(Enum):
    CUSTOM_APP_ROLE = "CUSTOM_APP_ROLE"              # Standard application role
    CUSTOM_APP_USER_ROLE = "CUSTOM_APP_USER_ROLE"   # User-specific role
```

#### HrType

HR employment type for users.

```python
class HrType(StrEnum):
    HR_TYPE_UNSPECIFIED = ""
    EMPLOYEE = "EMPLOYEE"
    CONTINGENT_WORKER = "CONTINGENT_WORKER"
    THIRD_PARTY = "THIRD_PARTY"
```

#### ScopeType

Type of permission scope.

```python
class ScopeType(Enum):
    UNSPECIFIED = "UNSPECIFIED"
    PROVIDER = "PROVIDER"
    FOLDER = "FOLDER"
    ACCOUNT = "ACCOUNT"
    RESOURCE_GROUP = "RESOURCE_GROUP"
```

#### PermissionAccessLevel

Access level for permissions.

```python
class PermissionAccessLevel(Enum):
    UNSPECIFIED = "UNSPECIFIED"
    LIST = "LIST"
    READ_DATA = "READ_DATA"
    WRITE_DATA = "WRITE_DATA"
    DELETE_DATA = "DELETE_DATA"
    PERMISSIONS_MANAGEMENT = "PERMISSIONS_MANAGEMENT"
    # ... and more
```

#### NhiType

Type of non-human identity.

```python
class NhiType(Enum):
    CUSTOM_APP_NHI = "CUSTOM_APP_NHI"
```

### Data Classes

#### CustomAppUser

Represents a human user in the application.

```python
@dataclass
class CustomAppUser:
    id: str                    # Unique identifier
    username: str              # Username (typically email)
    name: str                  # Display name
    status: Optional[str] = UserStatus.ENABLED.value
    hrType: Optional[HrType] = None
    hris_attributes: Optional[CustomAppUserHRISAttributes] = None
```

**Example:**

```python
user = CustomAppUser(
    id="john.doe@company.com",
    username="john.doe@company.com",
    name="John Doe",
    status=UserStatus.ENABLED.name,
    hrType=HrType.EMPLOYEE
)
```

#### CustomAppNhi

Represents a non-human identity (service account, API key, etc.).

```python
@dataclass
class CustomAppNhi:
    id: str
    username: str
    name: str
    type: Optional[str] = NhiType.CUSTOM_APP_NHI.name
    is_external_client: Optional[bool] = False
    ownerId: Optional[str] = None
    custodianId: Optional[str] = None
    status: Optional[str] = None
```

#### CustomAppGroup

Represents a group of users.

```python
@dataclass
class CustomAppGroup:
    id: str
    name: str
    memberUserIds: List[str] = field(default_factory=list)
    memberSubgroupIds: List[str] = field(default_factory=list)
```

**Example:**

```python
group = CustomAppGroup(
    id="admins",
    name="Administrators",
    memberUserIds=["john.doe@company.com", "jane.smith@company.com"]
)
```

#### CustomAppScope

Represents a permission scope (folder, account, resource group).

```python
@dataclass
class CustomAppScope:
    id: str
    name: str
    type: str                  # ScopeType enum value
    parentScopeId: Optional[str] = None
```

**Example - Hierarchical Scopes:**

```python
# Parent scope
server_scope = CustomAppScope(
    id="FileServer01",
    name="FileServer01",
    type=ScopeType.FOLDER.name
)

# Child scope
folder_scope = CustomAppScope(
    id="FileServer01/Finance",
    name="Finance",
    type=ScopeType.ACCOUNT.name,
    parentScopeId="FileServer01"
)
```

#### CustomAppRole

Represents a role with associated permissions.

```python
@dataclass
class CustomAppRole:
    id: str
    name: str
    type: Optional[str] = RoleType.CUSTOM_APP_ROLE.name
    permissions: List[str] = field(default_factory=list)
```

**Example:**

```python
role = CustomAppRole(
    id="data_analyst",
    name="Data Analyst",
    type=RoleType.CUSTOM_APP_ROLE.name,
    permissions=["read_data", "create_reports", "export_data"]
)
```

#### CustomAppRoleAssignment

Represents a role assignment to a principal (user, group, or NHI).

```python
@dataclass
class CustomAppRoleAssignment:
    id: str
    principalId: str           # User/Group/NHI ID
    principalType: str         # PrincipalType enum value
    roleId: str
    scopeId: Optional[str] = None
```

**Example:**

```python
assignment = CustomAppRoleAssignment(
    id="john.doe@company.com_data_analyst_folder123",
    principalId="john.doe@company.com",
    principalType=PrincipalType.HUMAN.name,
    roleId="data_analyst",
    scopeId="folder123"
)
```

#### CustomAppPermission

Represents a permission in the application.

```python
@dataclass
class CustomAppPermission:
    name: str
    accessLevel: Optional[str] = None
    serviceName: Optional[str] = None
```

#### CustomAppInventory

Container for all inventory data.

```python
@dataclass
class CustomAppInventory:
    users: Dict[str, CustomAppUser] = field(default_factory=dict)
    nhis: Dict[str, CustomAppNhi] = field(default_factory=dict)
    roles: Dict[str, CustomAppRole] = field(default_factory=dict)
    assignments: Dict[str, CustomAppRoleAssignment] = field(default_factory=dict)
    permissions: Dict[str, CustomAppPermission] = field(default_factory=dict)
    groups: Dict[str, CustomAppGroup] = field(default_factory=dict)
    scopes: Dict[str, CustomAppScope] = field(default_factory=dict)
```

---

## Utility Functions

`sdk/customapp/custom_app_utils.py`

### convert_to_andromeda_dict()

Converts inventory dictionaries from snake_case to camelCase and removes empty values.

```python
def convert_to_andromeda_dict(obj: Any) -> Any:
    """
    Recursively convert dictionary keys from snake_case to camelCase.
    Removes empty values.
    """
```

**Example:**

```python
from sdk.customapp.custom_app_utils import convert_to_andromeda_dict

inventory_dict = asdict(inventory)
andromeda_format = convert_to_andromeda_dict(inventory_dict)
```

### parse_arguments()

Standard argument parser for custom app transformers.

```python
def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for custom app transformers.

    Arguments:
        --app_name, -n: Application name
        --inventory_file, -i: Path to CSV inventory file
        --output_dir, -o: Output directory for JSON (default: /tmp/customapp_export)
    """
```

**Example:**

```python
from sdk.customapp.custom_app_utils import parse_arguments

args = parse_arguments()
print(f"App: {args.app_name}, File: {args.inventory_file}")
```

---

## Base Transformer Class

`sdk/customapp/csv_transformer.py`

### CustomAppCsvTransformer

Abstract base class that provides common CSV transformation functionality.

#### Constructor

```python
def __init__(self,
             app_name: str,
             inventory_file: str,
             output_dir: str,
             has_extra_header_rows: bool = False,
             field_names: Optional[List[str]] = None)
```

**Parameters:**

- `app_name`: Name of the custom application
- `inventory_file`: Path to CSV file to transform
- `output_dir`: Directory for JSON output
- `has_extra_header_rows`: Set to `True` if CSV has extra header rows to skip
- `field_names`: Custom field names if CSV headers are non-standard

#### Key Methods

##### transform_and_export()

Main entry point for transformation.

```python
def transform_and_export(self) -> Tuple[dict, str]:
    """
    Transform CSV inventory to JSON and export to file.

    Returns:
        Tuple of (inventory_dict, output_file_path)
    """
```

##### process_csv_row() (Abstract)

Must be implemented by subclasses.

```python
def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]):
    """
    Process a single CSV row and update inventory.

    Args:
        row: Dictionary of CSV row data
        errors: List to append errors to
    """
    raise NotImplementedError("Subclass must implement this method")
```

##### csv_batch_reader()

Reads CSV files in batches (100 rows by default).

```python
def csv_batch_reader(self, csv_file: str, batch_size: int = 100) -> Generator[list, None, None]:
    """Read CSV file in batches for memory efficiency."""
```

##### summarize()

Generates summary statistics.

```python
def summarize(self) -> Dict[str, int]:
    """
    Generate summary statistics for inventory.

    Returns:
        Dictionary with counts: users, roles, assignments, permissions, groups, scopes
    """
```

#### Validation Methods

The base class provides built-in validation:

- `inventory_validation()`: Validates entire inventory
- `_validate_users()`: Validates user status
- `_validate_roles()`: Validates role types and permissions
- `_validate_assignments()`: Validates assignment references

---

## Creating a New Custom App Transformer

### Step-by-Step Guide

#### Step 1: Create Transformer Class

Create a new file: `lib/python/sdk/custom_app_type1_sample/custom_app_myapp.py`

```python
"""
Custom App Inventory Transformer for MyApp

Transforms MyApp CSV exports into Andromeda inventory format.
"""

import logging
import traceback
from typing import Dict, List, Optional

from sdk.customapp.csv_transformer import CustomAppCsvTransformer
from sdk.customapp.custom_app_models import (
    CustomAppUser, UserStatus, PrincipalType, RoleType,
    CustomAppRole, CustomAppRoleAssignment, CustomAppGroup
)
from sdk.customapp.custom_app_utils import parse_arguments

logger = logging.getLogger(__name__)

class CustomAppMyAppTransformer(CustomAppCsvTransformer):
    """Transforms MyApp CSV inventory into standardized JSON format."""

    def process_csv_row(self, row: Dict[str, str],
                       errors: List[Dict[str, str]]) -> None:
        """Process a single CSV row and update inventory."""
        # Your transformation logic here
        pass
```

#### Step 2: Implement Helper Methods

Add methods to create users, roles, and assignments:

```python
def create_user(self, row: Dict[str, str]) -> Optional[CustomAppUser]:
    """Create a user from CSV row."""
    email = row.get('email', '').strip()
    if not email:
        logger.error("Skipping row: email not set")
        return None

    # Check if user already exists
    if email in self.inventory.users:
        return self.inventory.users[email]

    user = CustomAppUser(
        id=email,
        username=email,
        name=row.get('name', email),
        status=UserStatus.ENABLED.name
    )

    self.inventory.users[email] = user
    return user

def create_role(self, row: Dict[str, str]) -> Optional[CustomAppRole]:
    """Create a role from CSV row."""
    role_name = row.get('role', '').strip()
    if not role_name:
        return None

    if role_name in self.inventory.roles:
        return self.inventory.roles[role_name]

    role = CustomAppRole(
        id=role_name,
        name=role_name,
        type=RoleType.CUSTOM_APP_ROLE.name
    )

    self.inventory.roles[role_name] = role
    return role

def create_role_assignment(self, user: CustomAppUser,
                          role: CustomAppRole) -> CustomAppRoleAssignment:
    """Create a role assignment."""
    assignment_id = f"{user.id}_{role.id}"

    if assignment_id in self.inventory.assignments:
        return self.inventory.assignments[assignment_id]

    assignment = CustomAppRoleAssignment(
        id=assignment_id,
        principalId=user.id,
        principalType=PrincipalType.HUMAN.name,
        roleId=role.id
    )

    self.inventory.assignments[assignment_id] = assignment
    return assignment
```

#### Step 3: Implement process_csv_row()

```python
def process_csv_row(self, row: Dict[str, str],
                   errors: List[Dict[str, str]]) -> None:
    """Process a single CSV row and update inventory."""
    try:
        # Create user
        user = self.create_user(row)
        if not user:
            errors.append(row)
            return

        # Create role
        role = self.create_role(row)
        if not role:
            errors.append(row)
            return

        # Create assignment
        self.create_role_assignment(user, role)

    except Exception as e:
        logger.error("Error processing row %s: %s", row, e)
        errors.append(row)
```

#### Step 4: Add Main Function

```python
def setup_logging() -> None:
    """Setup logging configuration."""
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    setup_logging()

    try:
        transformer = CustomAppMyAppTransformer(
            app_name=args.app_name.strip(),
            inventory_file=args.inventory_file.strip(),
            output_dir=args.output_dir.strip()
        )

        _, output_file = transformer.transform_and_export()
        logger.info("Transformation completed successfully: %s", output_file)

    except Exception as e:
        logger.error("Transformation failed: %s", e)
        logger.error("Stack trace: %s", traceback.format_exc())
        raise

if __name__ == '__main__':
    main()
```

#### Step 5: Test Locally

```bash
cd lib/python/sdk/custom_app_type1_sample

python3 custom_app_myapp.py \
    --app_name=myapp \
    --inventory_file=sample_inventory.csv \
    --output_dir=/tmp/customapp_export
```

#### Step 6: Validate Output

Check the generated JSON:

```bash
cat /tmp/customapp_export/myapp-*.json | jq .
```

Verify the structure:

```json
{
  "users": { ... },
  "roles": { ... },
  "assignments": { ... },
  "groups": { ... },
  "scopes": { ... }
}
```

#### Step 7: Upload to Andromeda

1. Create a Custom App Provider in Andromeda UI
2. Upload your transformer script
3. Upload your CSV inventory file
4. Trigger the transformation job
5. Validate the ingested data in Andromeda

---

## Examples

### Example 1: Simple User-Role Mapping

**CSV Format:**

```csv
email,name,role
john.doe@company.com,John Doe,admin
jane.smith@company.com,Jane Smith,viewer
```

**Transformer:**

```python
class SimpleTransformer(CustomAppCsvTransformer):
    def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]) -> None:
        user = self.create_user(row)
        role = self.create_role(row)
        if user and role:
            self.create_role_assignment(user, role)
```

### Example 2: Group-Based Assignments

**CSV Format:**

```csv
email,name,group,role
john.doe@company.com,John Doe,engineering,developer
jane.smith@company.com,Jane Smith,engineering,developer
```

**Transformer:**

```python
class GroupBasedTransformer(CustomAppCsvTransformer):
    def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]) -> None:
        # Create user
        user = self.create_user(row)

        # Create group
        group = self.create_group(row)

        # Add user to group
        if user and group and user.id not in group.memberUserIds:
            group.memberUserIds.append(user.id)

        # Create role assignment for group
        role = self.create_role(row)
        if group and role:
            self.create_group_role_assignment(group, role)
```

### Example 3: Scoped Permissions

**CSV Format:**

```csv
email,name,file_server,folder_path,permission
john.doe@company.com,John Doe,FileServer01,/finance,Read
jane.smith@company.com,Jane Smith,FileServer01,/finance,Modify
```

**Transformer:**

```python
class ScopedTransformer(CustomAppCsvTransformer):
    def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]) -> None:
        # Create scope hierarchy
        scope = self.create_scope(row)

        # Create user
        user = self.create_user(row)

        # Create role
        role = self.create_role(row)

        # Create scoped assignment
        if user and role and scope:
            assignment = CustomAppRoleAssignment(
                id=f"{user.id}_{role.id}_{scope.id}",
                principalId=user.id,
                principalType=PrincipalType.HUMAN.name,
                roleId=role.id,
                scopeId=scope.id
            )
            self.inventory.assignments[assignment.id] = assignment
```

---

## Testing

### Unit Tests

Create tests in `tests/lib/python/sdk/customapp/`:

```python
import unittest
from sdk.customapp.custom_app_models import CustomAppUser, UserStatus

class TestCustomAppModels(unittest.TestCase):
    def test_create_user(self):
        user = CustomAppUser(
            id="test@example.com",
            username="test@example.com",
            name="Test User",
            status=UserStatus.ENABLED.name
        )
        self.assertEqual(user.username, "test@example.com")
        self.assertEqual(user.status, "ENABLED")
```

### Integration Tests

Test full transformation with sample CSV:

```python
def test_transformation():
    transformer = CustomAppMyAppTransformer(
        app_name="test_app",
        inventory_file="test_data.csv",
        output_dir="/tmp/test"
    )

    inventory_dict, output_file = transformer.transform_and_export()

    # Validate output
    assert len(inventory_dict["users"]) > 0
    assert len(inventory_dict["roles"]) > 0
    assert os.path.exists(output_file)
```

---

## Best Practices

1. **Always validate input data** - Check for required fields before creating objects
2. **Handle duplicates gracefully** - Check if entity already exists before creating
3. **Log errors clearly** - Include row data in error messages for debugging
4. **Use type hints** - Makes code self-documenting and catches errors early
5. **Follow naming conventions** - Use consistent ID formats (e.g., `{app_name}|{principal}|{role}|{scope}`)
6. **Test with real data** - Use production-like CSV exports during development
7. **Document CSV format** - Include expected columns in transformer docstring

---

## Troubleshooting

### Common Issues

**Issue: "Module sdk.customapp not found"**

- Solution: Ensure you're running from the correct directory or add SDK path to sys.path

**Issue: "No users found in inventory"**

- Solution: Check CSV field names match your `process_csv_row()` logic

**Issue: "Assignment validation failed"**

- Solution: Ensure all referenced users/roles exist in inventory before creating assignments

**Issue: "Permission denied writing output file"**

- Solution: Check output directory exists and has write permissions

---

## Reference

- **Models**: `sdk/customapp/custom_app_models.py`
- **Utils**: `sdk/customapp/custom_app_utils.py`
- **Base Class**: `sdk/customapp/csv_transformer.py`
- **Examples**: `lib/python/sdk/custom_app_type1_sample/`
- **Mock Data**: `sdk/customapp/mock_data.json`
