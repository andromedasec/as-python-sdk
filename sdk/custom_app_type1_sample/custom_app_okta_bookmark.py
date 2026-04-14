"""
Custom App Inventory Transformer

This module provides functionality to transform CSV inventory files into
a standardized JSON format for custom applications.

The single app is set up to be used for multiple custom apps to make it easy
to share common code and maintainability. It is not a requirement to share the
transformer code between app but framework allows for that.

The transformer is based on three important parts

1. Base Class `CustomAppInventoryType1Transformer` that implements most common
utilities for the custom app. It implements utilities like csv readers, writers
validators etc. Important functions to be overriden are:
1.1 process_csv_row: This is callback invoked on every row.
1.2 constructor: for any set up for that app

2. Per Application Transformer Classes: These implement the logic for processing
every csv row and extract, user, role, assignments from it.

3. main function: It has the mapper for application name to Application Transformer class
Everytime a new application is created it needs to be updated.

4. tests: these are unit tests that can be used to validate application
transforming logic.

## Checklist for adding new Application

1. Take sample export of the application from real production data
2. Create a test data from the production data removing any PII
3. Add an Application Transformer class with following items
3.1 process_csv_row, create_user, create_role, create_role_assignment, create_permission
3.2 Add validators for the data specially assignment.
4. Add unit test for the Application
4.1 test the transform with sample data
5. Register the appplication in the `app_to_transformer_map`
6. Create Custom App Provider in Andromeda
7. Check custom app transfomer via `python3 custom_app_okta_bookmark_transformer.py --app_name=billing --inventory_file=billing_inventory.csv`
8. Upload the application and CSV to the UI
9. Optionally, use the sample app upload script to update the scripts
10. Validate the data in the Andromeda UI

"""

import logging
import traceback
from typing import Dict, List, Optional
from sdk.customapp.csv_transformer import CustomAppCsvTransformer
from sdk.customapp.custom_app_models import (
    CustomAppUser, UserStatus, PrincipalType, RoleType,
    CustomAppRole, CustomAppRoleAssignment, CustomAppGroup,
    HrType
)
from sdk.customapp.custom_app_utils import parse_arguments

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 100
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME = "custom_app_sample"
ID_SEPARATOR = "|"

class CustomAppOktaBookmarkTransformer(CustomAppCsvTransformer):
    """
    Transforms Okta Bookmark CSV export files into standardized JSON format.

    Expected CSV columns:
      field_names
    """
    # Map user status based on user status
    last_user = None

    field_names = ['id', 'userName', 'scope', "externalId", "firstName", "lastName",
                   "syncState", "salesforceGroups", "samlRoles", "groupName"]

    WORKLOAD_DOMAINS_HR_TYPE_MAP = {
            'beatles.ai': HrType.HR_TYPE_UNSPECIFIED,
    }

    def __init__(self, app_name: str, inventory_file: str, output_dir: str):
        super().__init__(app_name, inventory_file, output_dir,
                         has_extra_header_rows=True, field_names=self.field_names)
        self.group_membership_map = {}

    def create_user(self, row: Dict[str, str], last_user: Optional[CustomAppUser] = None) -> Optional[CustomAppUser]:
        """Create a user object from CSV row data."""
        if not row.get('userName'):
            logger.error("Skipping row: userName not set in %s", row)
            raise ValueError(f"Skipping row: userName not set in {row}")

        username = row['userName'].strip()
        user_id = username
        first_name = row.get('firstName', '').strip()
        last_name = row.get('lastName', '').strip()
        name = f"{first_name} {last_name}".strip() if first_name or last_name else username
        status = UserStatus.ENABLED.name
        # Check if user is already present in the inventory
        if username in self.inventory.users:
            return self.inventory.users[username]

        user = CustomAppUser(
            id=user_id,
            username=username,
            name=name,
            status=status,
            #hrType=self.get_hr_type_from_username(username).value
        )
        logger.debug("Added user %s to inventory", user)
        self.inventory.users[username] = user
        return user


    def create_group(self, row: Dict[str, str]) -> Optional[CustomAppGroup]:
        """Create a group object from CSV row data."""
        scope = row.get('scope', '').strip()
        group_name = row.get('groupName', '').strip()

        if scope != "GROUP" or not group_name:
            logger.error("Skipping row: scope and group name are set in %s", row)
            return None
        group_id = group_name
        # Check if group is already present in the inventory
        if group_id in self.inventory.groups:
            return self.inventory.groups[group_id]

        group = CustomAppGroup(id=group_id, name=group_name)
        self.inventory.groups[group_id] = group
        logger.debug("Added group %s to inventory", group)
        return group

    def _create_role(self, role_name: str, user: Optional[CustomAppUser]) -> Optional[CustomAppRole]:
        role_name = role_name.strip()
        if role_name.lower() == 'none':
            return None
        if role_name:
            role_type = RoleType.CUSTOM_APP_ROLE.name
        elif user:
            role_type = RoleType.CUSTOM_APP_USER_ROLE.name
            role_name = f"{self.app_name}-{user.name}-role"
        else:
            raise ValueError(
                f"{self.app_name} user required when role name is null")
        # Check if role is already present in the inventory
        if role_name in self.inventory.roles:
            return self.inventory.roles[role_name]
        role = CustomAppRole(
            id=role_name,
            name=role_name,
            type=role_type,
        )
        logger.debug("Added role %s to inventory", role_name)
        self.inventory.roles[role_name] = role
        return role

    def create_roles(self, row: Dict[str, str],
        user: Optional[CustomAppUser]) -> List[CustomAppRole]:
        """Create a role object from CSV row data.
        Uses the Group name as the role name.
        """
        roles = []
        role_name = f"{self.app_name}-default-role"
        role = self._create_role(role_name, user)
        if role:
            roles.append(role)
        return roles

    def create_role_assignments(self, user: Optional[CustomAppUser],
            group: Optional[CustomAppGroup], roles: List[CustomAppRole],
            row: Dict[str, str]) -> List[CustomAppRoleAssignment]:
        """Create a role assignment object."""
        principal_id = group.id if group else user.id if user else ""
        principal_type = (PrincipalType.GROUP.name
                          if group else PrincipalType.HUMAN.name if user else "")
        assignments = []
        assert roles, f"Roles are not set for {self.app_name}"
        for role in roles:
            assignment_id = f"{self.app_name}{ID_SEPARATOR}{principal_type}{ID_SEPARATOR}{principal_id}{ID_SEPARATOR}{role.id}"
            # Check for assignment conflicts
            if assignment_id in self.inventory.assignments:
                if principal_type == PrincipalType.GROUP.name:
                    logger.warning("App: %s, Assignment already exists: %s %s", self.app_name,
                        assignment_id, self.inventory.assignments[assignment_id])
                assignments.append(self.inventory.assignments[assignment_id])
            else:
                assignment = CustomAppRoleAssignment(
                    id=assignment_id,
                    principalId=principal_id,
                    principalType=principal_type,
                    roleId=role.id,
                )
                logger.debug("Creating assignment %s for principal %s role %s", assignment.id,
                            principal_id, role.name)
                self.inventory.assignments[assignment.id] = assignment
                assignments.append(assignment)
        return assignments

    def _is_row_valid(self, row: Dict[str, str]) -> bool:
        """Check if the row needs to be processed."""
        # Row is valid if it has an email and group name
        user_name = row.get('userName', '').strip()
        group_name = row.get('groupName', '').strip()
        scope = row.get('scope', '').strip()
        return bool(user_name and (group_name or scope))

    def process_csv_row(self, row: Dict[str, str],
                         errors: List[Dict[str, str]]) -> None:
        """Process a single CSV row and update inventory.
        Returns:
            CustomAppUser: The last processed user object if the row is valid, otherwise None
        """
        #logger.debug("Processing row %s", row)
        if not self._is_row_valid(row):
            return
        try:
            # Create or update role
            roles = self.create_roles(row, None)
            if not roles:
                logger.debug("No roles found for app %s row %s", self.app_name, row)
                return
            # Create or update user
            user = self.create_user(row, self.last_user)
            # Create or update group
            group = self.create_group(row)
            # Create group binding
            if group and user:
                group_members = self.group_membership_map.get(group.id, set())
                if user.id not in group_members:
                    group_members.add(user.id)
                    self.group_membership_map[group.id] = group_members
                    group.memberUserIds.append(user.id)
            if (user or group) and roles:
                self.create_role_assignments(user, group, roles, row)
            self.last_user = user
            return
        except ValueError as e:
            logger.error("Error Processing row %s: %s", row, e)
            errors.append(row)
        except Exception as e:
            logger.error("Error processing row %s: %s", row, e)
            errors.append(row)
        return



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


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    setup_logging()

    app_to_transformer_map = {
        'OpsGenie': CustomAppOktaBookmarkTransformer,
        'Torq': CustomAppOktaBookmarkTransformer,
        'ServiceNow': CustomAppOktaBookmarkTransformer,
        'Secure Access Cloud (Luminate)': CustomAppOktaBookmarkTransformer,
    }
    try:
        # Find the transformer class based on the app name
        # TODO: change this to actually fail if the transformer class is not found
        # need product change
        transformer_class = app_to_transformer_map.get(
            args.app_name.strip(), CustomAppOktaBookmarkTransformer)

        # Create the transformer instance
        transformer = transformer_class(
            app_name=args.app_name.strip(),
            inventory_file=args.inventory_file.strip(),
            output_dir=args.output_dir.strip())

        # Transform and export the inventory
        _, output_file = transformer.transform_and_export()
        logger.info("Transformation completed for app %s successfully, output file: %s", args.app_name, output_file)

    except Exception as e:
        logger.error("Transformation failed: {%s}", e)
        logger.error("Stack trace: %s", traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
