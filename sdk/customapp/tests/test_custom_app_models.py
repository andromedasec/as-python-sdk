"""
Unit tests for custom_app_models.py

Tests cover:
- Snake_case constructor parameters (preferred Pythonic style)
- CamelCase constructor parameters (deprecated but backward compatible)
- Mixed constructor parameters (snake_case takes precedence)
- Property access with both naming styles
- Property setters with both naming styles
- Invalid attributes that should raise errors
"""

import pytest
from sdk.customapp.custom_app_models import (
    CustomAppUser,
    CustomAppUserHRISAttributes,
    CustomAppNhi,
    CustomAppGroup,
    CustomAppScope,
    CustomAppRoleAssignment,
    CustomAppPermission,
    HrType,
)


class TestCustomAppUser:
    """Test CustomAppUser with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters (preferred)."""
        user = CustomAppUser(
            id="user1",
            username="user@example.com",
            name="Test User",
            status="ENABLED",
            hr_type=HrType.EMPLOYEE
        )

        assert user.id == "user1"
        assert user.username == "user@example.com"
        assert user.name == "Test User"
        assert user.status == "ENABLED"
        assert user.hr_type == HrType.EMPLOYEE

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        user = CustomAppUser(
            id="user2",
            username="user2@example.com",
            name="Test User 2",
            status="ENABLED",
            hrType=HrType.CONTINGENT_WORKER
        )

        # Should work via backward compatibility
        assert user.id == "user2"
        assert user.hr_type == HrType.CONTINGENT_WORKER
        assert user.hrType == HrType.CONTINGENT_WORKER  # Property alias works

    def test_mixed_constructor_snake_case_wins(self):
        """Test constructor with both snake_case and camelCase (snake_case wins)."""
        user = CustomAppUser(
            id="user3",
            username="user3@example.com",
            name="Test User 3",
            hr_type=HrType.EMPLOYEE,
            hrType=HrType.CONTINGENT_WORKER  # Should be ignored
        )

        # snake_case should take precedence
        assert user.hr_type == HrType.EMPLOYEE
        assert user.hrType == HrType.EMPLOYEE

    def test_property_access_both_styles(self):
        """Test property access with both snake_case and camelCase."""
        user = CustomAppUser(
            id="user4",
            username="user4@example.com",
            name="Test User 4",
            hr_type=HrType.THIRD_PARTY
        )

        # Both should work
        assert user.hr_type == HrType.THIRD_PARTY
        assert user.hrType == HrType.THIRD_PARTY

    def test_property_setter_snake_case(self):
        """Test property setter with snake_case."""
        user = CustomAppUser(
            id="user5",
            username="user5@example.com",
            name="Test User 5"
        )

        user.hr_type = HrType.EMPLOYEE
        assert user.hr_type == HrType.EMPLOYEE
        assert user.hrType == HrType.EMPLOYEE

    def test_property_setter_camel_case(self):
        """Test property setter with deprecated camelCase."""
        user = CustomAppUser(
            id="user6",
            username="user6@example.com",
            name="Test User 6"
        )

        user.hrType = HrType.CONTINGENT_WORKER
        assert user.hr_type == HrType.CONTINGENT_WORKER
        assert user.hrType == HrType.CONTINGENT_WORKER

    def test_invalid_attribute_raises_error(self):
        """Test that accessing invalid attributes raises AttributeError."""
        user = CustomAppUser(
            id="user7",
            username="user7@example.com",
            name="Test User 7"
        )

        with pytest.raises(AttributeError):
            _ = user.invalid_attribute

    def test_missing_required_field(self):
        """Test that missing required fields raises TypeError."""
        with pytest.raises(TypeError):
            CustomAppUser(username="user@example.com", name="Test")


class TestCustomAppUserHRISAttributes:
    """Test CustomAppUserHRISAttributes dataclass."""

    def test_hris_attributes_full_constructor(self):
        """Test creating HRIS attributes with all fields."""
        hris_attrs = CustomAppUserHRISAttributes(
            email="john.doe@example.com",
            org_name="Engineering",
            business_title="Software Engineer",
            manager_id="mgr123",
            manager_name="Jane Manager",
            position_title="Senior Engineer",
            division="Product Development",
            city="San Francisco",
            state="CA",
            country="USA",
            hire_date="2020-01-15",
            termination_date=None
        )

        assert hris_attrs.email == "john.doe@example.com"
        assert hris_attrs.org_name == "Engineering"
        assert hris_attrs.business_title == "Software Engineer"
        assert hris_attrs.manager_id == "mgr123"
        assert hris_attrs.manager_name == "Jane Manager"
        assert hris_attrs.position_title == "Senior Engineer"
        assert hris_attrs.division == "Product Development"
        assert hris_attrs.city == "San Francisco"
        assert hris_attrs.state == "CA"
        assert hris_attrs.country == "USA"
        assert hris_attrs.hire_date == "2020-01-15"
        assert hris_attrs.termination_date is None

    def test_hris_attributes_optional_fields(self):
        """Test that all HRIS attributes fields are optional."""
        hris_attrs = CustomAppUserHRISAttributes()

        assert hris_attrs.email is None
        assert hris_attrs.org_name is None
        assert hris_attrs.business_title is None
        assert hris_attrs.manager_id is None
        assert hris_attrs.manager_name is None
        assert hris_attrs.position_title is None
        assert hris_attrs.division is None
        assert hris_attrs.city is None
        assert hris_attrs.state is None
        assert hris_attrs.country is None
        assert hris_attrs.hire_date is None
        assert hris_attrs.termination_date is None

    def test_hris_attributes_partial_fields(self):
        """Test creating HRIS attributes with partial fields."""
        hris_attrs = CustomAppUserHRISAttributes(
            email="user@example.com",
            manager_id="mgr456",
            city="New York"
        )

        assert hris_attrs.email == "user@example.com"
        assert hris_attrs.manager_id == "mgr456"
        assert hris_attrs.city == "New York"
        assert hris_attrs.org_name is None
        assert hris_attrs.business_title is None

    def test_user_with_hris_attributes_object(self):
        """Test creating CustomAppUser with HRIS attributes object."""
        hris_attrs = CustomAppUserHRISAttributes(
            email="john.doe@example.com",
            org_name="Engineering",
            business_title="Software Engineer",
            manager_id="mgr123"
        )

        user = CustomAppUser(
            id="user1",
            username="jdoe",
            name="John Doe",
            status="ENABLED",
            hr_type=HrType.EMPLOYEE,
            hris_attributes=hris_attrs
        )

        assert user.id == "user1"
        assert user.username == "jdoe"
        assert user.name == "John Doe"
        assert user.hris_attributes is not None
        assert isinstance(user.hris_attributes, CustomAppUserHRISAttributes)
        assert user.hris_attributes.email == "john.doe@example.com"
        assert user.hris_attributes.org_name == "Engineering"
        assert user.hris_attributes.business_title == "Software Engineer"
        assert user.hris_attributes.manager_id == "mgr123"

    def test_user_without_hris_attributes(self):
        """Test creating CustomAppUser without HRIS attributes."""
        user = CustomAppUser(
            id="user2",
            username="jsmith",
            name="Jane Smith",
            status="ENABLED",
            hr_type=HrType.CONTINGENT_WORKER
        )

        assert user.hris_attributes is None

    def test_hris_attributes_dataclass_asdict(self):
        """Test that dataclasses.asdict() works with CustomAppUserHRISAttributes."""
        from dataclasses import asdict

        hris_attrs = CustomAppUserHRISAttributes(
            email="test@example.com",
            org_name="Sales",
            city="Boston"
        )

        hris_dict = asdict(hris_attrs)
        assert hris_dict["email"] == "test@example.com"
        assert hris_dict["org_name"] == "Sales"
        assert hris_dict["city"] == "Boston"
        assert hris_dict["business_title"] is None


class TestCustomAppNhi:
    """Test CustomAppNhi with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters."""
        nhi = CustomAppNhi(
            id="nhi1",
            username="app-service",
            name="Application Service",
            owner_id="owner1",
            custodian_id="custodian1"
        )

        assert nhi.id == "nhi1"
        assert nhi.owner_id == "owner1"
        assert nhi.custodian_id == "custodian1"

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        nhi = CustomAppNhi(
            id="nhi2",
            username="app-service-2",
            name="Application Service 2",
            ownerId="owner2",
            custodianId="custodian2"
        )

        assert nhi.owner_id == "owner2"
        assert nhi.custodian_id == "custodian2"
        assert nhi.ownerId == "owner2"
        assert nhi.custodianId == "custodian2"

    def test_mixed_constructor_snake_case_wins(self):
        """Test constructor with both naming styles (snake_case wins)."""
        nhi = CustomAppNhi(
            id="nhi3",
            username="app-service-3",
            name="Application Service 3",
            owner_id="owner_snake",
            ownerId="owner_camel",
            custodian_id="custodian_snake",
            custodianId="custodian_camel"
        )

        assert nhi.owner_id == "owner_snake"
        assert nhi.custodian_id == "custodian_snake"

    def test_property_setters(self):
        """Test property setters with both naming styles."""
        nhi = CustomAppNhi(
            id="nhi4",
            username="app-service-4",
            name="Application Service 4"
        )

        # Snake_case setter
        nhi.owner_id = "new_owner"
        assert nhi.owner_id == "new_owner"
        assert nhi.ownerId == "new_owner"

        # CamelCase setter
        nhi.custodianId = "new_custodian"
        assert nhi.custodian_id == "new_custodian"
        assert nhi.custodianId == "new_custodian"


class TestCustomAppGroup:
    """Test CustomAppGroup with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters."""
        group = CustomAppGroup(
            id="group1",
            name="Engineering Team",
            member_user_ids=["user1", "user2"],
            member_subgroup_ids=["subgroup1"]
        )

        assert group.id == "group1"
        assert group.member_user_ids == ["user1", "user2"]
        assert group.member_subgroup_ids == ["subgroup1"]

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        group = CustomAppGroup(
            id="group2",
            name="Finance Team",
            memberUserIds=["user3", "user4"],
            memberSubgroupIds=["subgroup2"]
        )

        assert group.member_user_ids == ["user3", "user4"]
        assert group.member_subgroup_ids == ["subgroup2"]
        assert group.memberUserIds == ["user3", "user4"]
        assert group.memberSubgroupIds == ["subgroup2"]

    def test_default_empty_lists(self):
        """Test that default values work correctly."""
        group = CustomAppGroup(id="group3", name="Empty Group")

        assert group.member_user_ids == []
        assert group.member_subgroup_ids == []
        assert group.memberUserIds == []
        assert group.memberSubgroupIds == []

    def test_property_setters(self):
        """Test property setters with both naming styles."""
        group = CustomAppGroup(id="group4", name="Test Group")

        # Snake_case setter
        group.member_user_ids = ["user5", "user6"]
        assert group.member_user_ids == ["user5", "user6"]
        assert group.memberUserIds == ["user5", "user6"]

        # CamelCase setter
        group.memberSubgroupIds = ["sub1", "sub2"]
        assert group.member_subgroup_ids == ["sub1", "sub2"]
        assert group.memberSubgroupIds == ["sub1", "sub2"]


class TestCustomAppScope:
    """Test CustomAppScope with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters."""
        scope = CustomAppScope(
            id="scope1",
            name="Root Scope",
            type="FOLDER",
            parent_scope_id="parent1"
        )

        assert scope.id == "scope1"
        assert scope.parent_scope_id == "parent1"

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        scope = CustomAppScope(
            id="scope2",
            name="Child Scope",
            type="ACCOUNT",
            parentScopeId="parent2"
        )

        assert scope.parent_scope_id == "parent2"
        assert scope.parentScopeId == "parent2"

    def test_optional_parent_scope_id(self):
        """Test that parent_scope_id is optional."""
        scope = CustomAppScope(
            id="scope3",
            name="Top Level Scope",
            type="PROVIDER"
        )

        assert scope.parent_scope_id is None
        assert scope.parentScopeId is None

    def test_property_setter(self):
        """Test property setter with both naming styles."""
        scope = CustomAppScope(id="scope4", name="Test Scope", type="FOLDER")

        # Snake_case setter
        scope.parent_scope_id = "new_parent"
        assert scope.parent_scope_id == "new_parent"
        assert scope.parentScopeId == "new_parent"

        # CamelCase setter
        scope.parentScopeId = "another_parent"
        assert scope.parent_scope_id == "another_parent"


class TestCustomAppRoleAssignment:
    """Test CustomAppRoleAssignment with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters."""
        assignment = CustomAppRoleAssignment(
            id="assign1",
            principal_id="user1",
            principal_type="HUMAN",
            role_id="role1",
            scope_id="scope1"
        )

        assert assignment.id == "assign1"
        assert assignment.principal_id == "user1"
        assert assignment.principal_type == "HUMAN"
        assert assignment.role_id == "role1"
        assert assignment.scope_id == "scope1"

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        assignment = CustomAppRoleAssignment(
            id="assign2",
            principalId="user2",
            principalType="GROUP",
            roleId="role2",
            scopeId="scope2"
        )

        assert assignment.principal_id == "user2"
        assert assignment.principal_type == "GROUP"
        assert assignment.role_id == "role2"
        assert assignment.scope_id == "scope2"
        assert assignment.principalId == "user2"
        assert assignment.principalType == "GROUP"
        assert assignment.roleId == "role2"
        assert assignment.scopeId == "scope2"

    def test_optional_scope_id(self):
        """Test that scope_id is optional."""
        assignment = CustomAppRoleAssignment(
            id="assign3",
            principal_id="user3",
            principal_type="HUMAN",
            role_id="role3"
        )

        assert assignment.scope_id is None
        assert assignment.scopeId is None

    def test_mixed_constructor_all_fields(self):
        """Test constructor with mixed naming (all 4 deprecated fields)."""
        assignment = CustomAppRoleAssignment(
            id="assign4",
            principal_id="user_snake",
            principalId="user_camel",
            principal_type="HUMAN_snake",
            principalType="HUMAN_camel",
            role_id="role_snake",
            roleId="role_camel",
            scope_id="scope_snake",
            scopeId="scope_camel"
        )

        # Snake_case should win for all fields
        assert assignment.principal_id == "user_snake"
        assert assignment.principal_type == "HUMAN_snake"
        assert assignment.role_id == "role_snake"
        assert assignment.scope_id == "scope_snake"

    def test_property_setters(self):
        """Test property setters with both naming styles."""
        assignment = CustomAppRoleAssignment(
            id="assign5",
            principal_id="initial",
            principal_type="HUMAN",
            role_id="role1"
        )

        # Snake_case setters
        assignment.principal_id = "new_principal"
        assignment.role_id = "new_role"
        assert assignment.principal_id == "new_principal"
        assert assignment.role_id == "new_role"

        # CamelCase setters
        assignment.principalType = "GROUP"
        assignment.scopeId = "new_scope"
        assert assignment.principal_type == "GROUP"
        assert assignment.scope_id == "new_scope"


class TestCustomAppPermission:
    """Test CustomAppPermission with snake_case and deprecated camelCase parameters."""

    def test_snake_case_constructor(self):
        """Test constructor with snake_case parameters."""
        permission = CustomAppPermission(
            name="pViewData",
            access_level="ACCESS_LEVEL_READ_DATA",
            service_name="Application"
        )

        assert permission.name == "pViewData"
        assert permission.access_level == "ACCESS_LEVEL_READ_DATA"
        assert permission.service_name == "Application"

    def test_camel_case_constructor_deprecated(self):
        """Test constructor with deprecated camelCase parameters."""
        permission = CustomAppPermission(
            name="pModifyData",
            accessLevel="ACCESS_LEVEL_WRITE_DATA",
            serviceName="Billing"
        )

        assert permission.access_level == "ACCESS_LEVEL_WRITE_DATA"
        assert permission.service_name == "Billing"
        assert permission.accessLevel == "ACCESS_LEVEL_WRITE_DATA"
        assert permission.serviceName == "Billing"

    def test_optional_fields(self):
        """Test that access_level and service_name are optional."""
        permission = CustomAppPermission(name="pBasicPermission")

        assert permission.name == "pBasicPermission"
        assert permission.access_level is None
        assert permission.service_name is None
        assert permission.accessLevel is None
        assert permission.serviceName is None

    def test_mixed_constructor(self):
        """Test constructor with mixed naming styles."""
        permission = CustomAppPermission(
            name="pTestPermission",
            access_level="ACCESS_LEVEL_SNAKE",
            accessLevel="ACCESS_LEVEL_CAMEL",
            service_name="Service_Snake",
            serviceName="Service_Camel"
        )

        # Snake_case should win
        assert permission.access_level == "ACCESS_LEVEL_SNAKE"
        assert permission.service_name == "Service_Snake"

    def test_property_setters(self):
        """Test property setters with both naming styles."""
        permission = CustomAppPermission(name="pTestPermission2")

        # Snake_case setter
        permission.access_level = "ACCESS_LEVEL_READ"
        assert permission.access_level == "ACCESS_LEVEL_READ"
        assert permission.accessLevel == "ACCESS_LEVEL_READ"

        # CamelCase setter
        permission.serviceName = "Infrastructure"
        assert permission.service_name == "Infrastructure"
        assert permission.serviceName == "Infrastructure"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_values_allowed_for_optional_fields(self):
        """Test that None values work for optional fields."""
        user = CustomAppUser(
            id="user1",
            username="user@example.com",
            name="Test User",
            hr_type=None
        )
        assert user.hr_type is None

        nhi = CustomAppNhi(
            id="nhi1",
            username="service",
            name="Service Account",
            owner_id=None,
            custodian_id=None
        )
        assert nhi.owner_id is None
        assert nhi.custodian_id is None

    def test_empty_strings_allowed(self):
        """Test that empty strings are allowed where strings are expected."""
        permission = CustomAppPermission(
            name="",
            access_level="",
            service_name=""
        )
        assert permission.name == ""
        assert permission.access_level == ""
        assert permission.service_name == ""

    def test_special_characters_in_ids(self):
        """Test that special characters work in ID fields."""
        scope = CustomAppScope(
            id="Server A/Drive:\\location\\finance",
            name="Finance Drive",
            type="ACCOUNT",
            parent_scope_id="Server A"
        )
        assert scope.id == "Server A/Drive:\\location\\finance"
        assert scope.parent_scope_id == "Server A"

    def test_unicode_characters(self):
        """Test that Unicode characters work in name fields."""
        user = CustomAppUser(
            id="user_unicode",
            username="user@例え.com",
            name="测试用户 Тест"
        )
        assert user.name == "测试用户 Тест"
        assert user.username == "user@例え.com"

    def test_dataclass_asdict_compatibility(self):
        """Test that dataclasses.asdict() works with the models."""
        from dataclasses import asdict

        user = CustomAppUser(
            id="user1",
            username="user@example.com",
            name="Test User",
            hr_type=HrType.EMPLOYEE
        )

        user_dict = asdict(user)
        assert user_dict["id"] == "user1"
        assert user_dict["hr_type"] == HrType.EMPLOYEE
        # Note: camelCase properties are not included in asdict()
        assert "hrType" not in user_dict


class TestTransformDeprecatedKwargs:
    """Test the _transform_deprecated_kwargs helper function."""

    def test_helper_function_transforms_correctly(self):
        """Test that the helper function correctly transforms kwargs."""
        from sdk.customapp.custom_app_models import _transform_deprecated_kwargs

        kwargs = {
            'id': 'test',
            'hrType': 'EMPLOYEE',
            'other_field': 'value'
        }

        deprecated_attrs = {'hrType': 'hr_type'}
        result = _transform_deprecated_kwargs(kwargs, deprecated_attrs)

        assert 'hrType' not in result
        assert result['hr_type'] == 'EMPLOYEE'
        assert result['id'] == 'test'
        assert result['other_field'] == 'value'

    def test_helper_snake_case_precedence(self):
        """Test that snake_case takes precedence when both are present."""
        from sdk.customapp.custom_app_models import _transform_deprecated_kwargs

        kwargs = {
            'hr_type': 'EMPLOYEE',
            'hrType': 'CONTINGENT_WORKER'
        }

        deprecated_attrs = {'hrType': 'hr_type'}
        result = _transform_deprecated_kwargs(kwargs, deprecated_attrs)

        assert result['hr_type'] == 'EMPLOYEE'
        assert 'hrType' not in result


class TestInventoryConsistencyChecker:
    """Test inventory consistency checker functions."""

    def test_validate_mock_data_json(self):
        """Test validation of mock_data.json file."""
        import json
        from pathlib import Path
        from sdk.customapp.custom_app_models import validate_inventory_from_json

        # Load mock_data.json
        test_dir = Path(__file__).parent.parent
        mock_data_path = test_dir / "mock_data.json"

        with open(mock_data_path, 'r') as f:
            data = json.load(f)

        # Validate inventory (should pass without errors)
        inventory = validate_inventory_from_json(data, strict_enums=True)

        # Verify inventory loaded correctly
        assert inventory is not None
        assert len(inventory.users) > 0
        assert len(inventory.roles) > 0
        assert len(inventory.assignments) > 0
        assert len(inventory.permissions) > 0

    def test_load_inventory_from_json_camel_case(self):
        """Test loading inventory from JSON with camelCase keys."""
        from sdk.customapp.custom_app_models import load_inventory_from_json

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "hrType": "EMPLOYEE"  # camelCase
                }
            },
            "roles": {
                "role1": {
                    "id": "role1",
                    "name": "Admin",
                    "type": "CUSTOM_APP_ROLE",
                    "permissions": []
                }
            },
            "assignments": {
                "assign1": {
                    "id": "assign1",
                    "principalId": "user1",  # camelCase
                    "principalType": "HUMAN",  # camelCase
                    "roleId": "role1"  # camelCase
                }
            },
            "permissions": {}
        }

        inventory = load_inventory_from_json(data)

        # Verify camelCase was properly handled
        assert inventory.users["user1"].hr_type == "EMPLOYEE"
        assert inventory.assignments["assign1"].principal_id == "user1"
        assert inventory.assignments["assign1"].principal_type == "HUMAN"
        assert inventory.assignments["assign1"].role_id == "role1"

    def test_load_inventory_from_json_snake_case(self):
        """Test loading inventory from JSON with snake_case keys."""
        from sdk.customapp.custom_app_models import load_inventory_from_json

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "hr_type": "EMPLOYEE"  # snake_case
                }
            },
            "roles": {
                "role1": {
                    "id": "role1",
                    "name": "Admin",
                    "type": "CUSTOM_APP_ROLE",
                    "permissions": []
                }
            },
            "assignments": {
                "assign1": {
                    "id": "assign1",
                    "principal_id": "user1",  # snake_case
                    "principal_type": "HUMAN",  # snake_case
                    "role_id": "role1"  # snake_case
                }
            },
            "permissions": {}
        }

        inventory = load_inventory_from_json(data)

        # Verify snake_case was properly handled
        assert inventory.users["user1"].hr_type == "EMPLOYEE"
        assert inventory.assignments["assign1"].principal_id == "user1"
        assert inventory.assignments["assign1"].principal_type == "HUMAN"
        assert inventory.assignments["assign1"].role_id == "role1"

    def test_load_inventory_with_nested_hris_attributes(self):
        """Test loading inventory with nested hris_attributes dict converts to object."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, CustomAppUserHRISAttributes

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "john.doe@example.com",
                    "name": "John Doe",
                    "status": "ENABLED",
                    "hr_type": "EMPLOYEE",
                    "hris_attributes": {
                        "email": "john.doe@example.com",
                        "org_name": "Engineering",
                        "business_title": "Software Engineer",
                        "manager_id": "mgr123",
                        "manager_name": "Jane Manager",
                        "position_title": "Senior Engineer",
                        "division": "Product Development",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "USA",
                        "hire_date": "2020-01-15"
                    }
                }
            }
        }

        inventory = load_inventory_from_json(data)
        user = inventory.users["user1"]

        # Verify hris_attributes is converted to CustomAppUserHRISAttributes object
        assert user.hris_attributes is not None
        assert isinstance(user.hris_attributes, CustomAppUserHRISAttributes)
        assert not isinstance(user.hris_attributes, dict)

        # Verify all fields are properly populated
        assert user.hris_attributes.email == "john.doe@example.com"
        assert user.hris_attributes.org_name == "Engineering"
        assert user.hris_attributes.business_title == "Software Engineer"
        assert user.hris_attributes.manager_id == "mgr123"
        assert user.hris_attributes.manager_name == "Jane Manager"
        assert user.hris_attributes.position_title == "Senior Engineer"
        assert user.hris_attributes.division == "Product Development"
        assert user.hris_attributes.city == "San Francisco"
        assert user.hris_attributes.state == "CA"
        assert user.hris_attributes.country == "USA"
        assert user.hris_attributes.hire_date == "2020-01-15"
        assert user.hris_attributes.termination_date is None

    def test_load_inventory_with_partial_hris_attributes(self):
        """Test loading inventory with partial hris_attributes fields."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, CustomAppUserHRISAttributes

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "jane.smith@example.com",
                    "name": "Jane Smith",
                    "hris_attributes": {
                        "email": "jane.smith@example.com",
                        "city": "New York",
                        "manager_id": "mgr456"
                    }
                }
            }
        }

        inventory = load_inventory_from_json(data)
        user = inventory.users["user1"]

        assert isinstance(user.hris_attributes, CustomAppUserHRISAttributes)
        assert user.hris_attributes.email == "jane.smith@example.com"
        assert user.hris_attributes.city == "New York"
        assert user.hris_attributes.manager_id == "mgr456"
        # Other fields should be None (defaults)
        assert user.hris_attributes.org_name is None
        assert user.hris_attributes.business_title is None
        assert user.hris_attributes.state is None

    def test_load_inventory_user_without_hris_attributes(self):
        """Test loading user without hris_attributes field."""
        from sdk.customapp.custom_app_models import load_inventory_from_json

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "status": "ENABLED"
                }
            }
        }

        inventory = load_inventory_from_json(data)
        user = inventory.users["user1"]

        # hris_attributes should be None if not provided
        assert user.hris_attributes is None

    def test_load_inventory_hris_attributes_snake_case_fields(self):
        """Test that hris_attributes with snake_case field names work correctly."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, CustomAppUserHRISAttributes

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "hris_attributes": {
                        "org_name": "Sales",  # snake_case
                        "business_title": "Account Executive",  # snake_case
                        "manager_id": "mgr789",  # snake_case
                        "position_title": "Senior AE"  # snake_case
                    }
                }
            }
        }

        inventory = load_inventory_from_json(data)
        user = inventory.users["user1"]

        assert isinstance(user.hris_attributes, CustomAppUserHRISAttributes)
        assert user.hris_attributes.org_name == "Sales"
        assert user.hris_attributes.business_title == "Account Executive"
        assert user.hris_attributes.manager_id == "mgr789"
        assert user.hris_attributes.position_title == "Senior AE"

    def test_load_inventory_multiple_users_with_hris_attributes(self):
        """Test loading multiple users with different hris_attributes."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, CustomAppUserHRISAttributes

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "user1@example.com",
                    "name": "User One",
                    "hris_attributes": {
                        "email": "user1@example.com",
                        "org_name": "Engineering"
                    }
                },
                "user2": {
                    "id": "user2",
                    "username": "user2@example.com",
                    "name": "User Two",
                    "hris_attributes": {
                        "email": "user2@example.com",
                        "org_name": "Sales",
                        "city": "Boston"
                    }
                },
                "user3": {
                    "id": "user3",
                    "username": "user3@example.com",
                    "name": "User Three"
                    # No hris_attributes
                }
            }
        }

        inventory = load_inventory_from_json(data)

        # user1 - has hris_attributes
        assert isinstance(inventory.users["user1"].hris_attributes, CustomAppUserHRISAttributes)
        assert inventory.users["user1"].hris_attributes.org_name == "Engineering"

        # user2 - has hris_attributes with more fields
        assert isinstance(inventory.users["user2"].hris_attributes, CustomAppUserHRISAttributes)
        assert inventory.users["user2"].hris_attributes.org_name == "Sales"
        assert inventory.users["user2"].hris_attributes.city == "Boston"

        # user3 - no hris_attributes
        assert inventory.users["user3"].hris_attributes is None

    def test_validate_inventory_with_invalid_enum(self):
        """Test validation catches invalid enum values."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "status": "INVALID_STATUS"  # Invalid enum
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have validation error for invalid status
        assert len(errors) > 0
        assert any("invalid status" in err.lower() for err in errors)

    def test_validate_inventory_with_missing_reference(self):
        """Test validation catches missing references."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User"
                }
            },
            "nhis": {
                "nhi1": {
                    "id": "nhi1",
                    "username": "service",
                    "name": "Service Account",
                    "owner_id": "non_existent_user"  # Reference to non-existent user
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have validation error for missing owner_id
        assert len(errors) > 0
        assert any("owner_id" in err and "not found" in err for err in errors)

    def test_validate_inventory_with_invalid_assignment(self):
        """Test validation catches invalid assignment references."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User"
                }
            },
            "roles": {
                "role1": {
                    "id": "role1",
                    "name": "Admin",
                    "type": "CUSTOM_APP_ROLE",
                    "permissions": []
                }
            },
            "assignments": {
                "assign1": {
                    "id": "assign1",
                    "principal_id": "user1",
                    "principal_type": "HUMAN",
                    "role_id": "non_existent_role"  # Reference to non-existent role
                }
            },
            "permissions": {}
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have validation error for missing role_id
        assert len(errors) > 0
        assert any("role_id" in err and "not found" in err for err in errors)

    def test_validate_inventory_from_json_raises_on_error(self):
        """Test that validate_inventory_from_json raises ValueError on validation errors."""
        from sdk.customapp.custom_app_models import validate_inventory_from_json

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "status": "INVALID_STATUS"
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            validate_inventory_from_json(data, strict_enums=True)

        # Verify error message contains useful information
        error_msg = str(exc_info.value)
        assert "validation failed" in error_msg.lower()
        assert "error" in error_msg.lower()

    def test_validate_inventory_strict_enums_false(self):
        """Test that strict_enums=False skips enum validation."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User",
                    "status": "CUSTOM_STATUS"  # Invalid enum but should be skipped
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=False)

        # Should have no errors since enum validation is disabled
        assert len(errors) == 0

    def test_validate_group_references(self):
        """Test validation of group member references."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "users": {
                "user1": {
                    "id": "user1",
                    "username": "test@example.com",
                    "name": "Test User"
                }
            },
            "groups": {
                "group1": {
                    "id": "group1",
                    "name": "Test Group",
                    "member_user_ids": ["user1", "non_existent_user"],
                    "member_subgroup_ids": ["non_existent_group"]
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have 2 errors (1 for missing user, 1 for missing subgroup)
        assert len(errors) == 2
        assert any("member_user_id" in err and "non_existent_user" in err for err in errors)
        assert any("member_subgroup_id" in err and "non_existent_group" in err for err in errors)

    def test_validate_scope_parent_reference(self):
        """Test validation of scope parent_scope_id references."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "scopes": {
                "scope1": {
                    "id": "scope1",
                    "name": "Child Scope",
                    "type": "FOLDER",
                    "parent_scope_id": "non_existent_parent"
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have error for missing parent scope
        assert len(errors) > 0
        assert any("parent_scope_id" in err and "not found" in err for err in errors)

    def test_validate_role_permission_reference(self):
        """Test validation of role permission references."""
        from sdk.customapp.custom_app_models import load_inventory_from_json, validate_inventory_consistency

        data = {
            "roles": {
                "role1": {
                    "id": "role1",
                    "name": "Admin",
                    "type": "CUSTOM_APP_ROLE",
                    "permissions": ["pViewData", "non_existent_permission"]
                }
            },
            "permissions": {
                "pViewData": {
                    "name": "pViewData"
                }
            }
        }

        inventory = load_inventory_from_json(data)
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have error for missing permission
        assert len(errors) > 0
        assert any("permission" in err and "non_existent_permission" in err for err in errors)


class TestValidateInventoryConsistencyNegative:
    """Negative tests for validate_inventory_consistency function."""

    def test_invalid_user_status_enum(self):
        """Test that invalid user status enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User",
            status="INVALID_STATUS_NOT_IN_ENUM"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "User 'user1'" in errors[0]
        assert "invalid status" in errors[0].lower()
        assert "INVALID_STATUS_NOT_IN_ENUM" in errors[0]

    def test_invalid_user_hr_type_enum(self):
        """Test that invalid user hr_type enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, HrType, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        # Create user with invalid hr_type by bypassing enum validation
        user = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        user.hr_type = "INVALID_HR_TYPE"  # Set invalid value directly
        inventory.users["user1"] = user

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "User 'user1'" in errors[0]
        assert "invalid hr_type" in errors[0].lower()

    def test_nhi_missing_owner_id(self):
        """Test that NHI with missing owner_id reference is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppNhi, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.nhis["nhi1"] = CustomAppNhi(
            id="nhi1",
            username="service",
            name="Service Account",
            owner_id="non_existent_owner"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "NHI 'nhi1'" in errors[0]
        assert "owner_id" in errors[0]
        assert "non_existent_owner" in errors[0]
        assert "not found in users" in errors[0]

    def test_nhi_missing_custodian_id(self):
        """Test that NHI with missing custodian_id reference is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppNhi, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        inventory.nhis["nhi1"] = CustomAppNhi(
            id="nhi1",
            username="service",
            name="Service Account",
            owner_id="user1",  # Valid
            custodian_id="non_existent_custodian"  # Invalid
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "NHI 'nhi1'" in errors[0]
        assert "custodian_id" in errors[0]
        assert "non_existent_custodian" in errors[0]

    def test_group_missing_member_user(self):
        """Test that group with missing member_user_id is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppGroup, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        inventory.groups["group1"] = CustomAppGroup(
            id="group1",
            name="Test Group",
            member_user_ids=["user1", "missing_user1", "missing_user2"]
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should have 2 errors for the 2 missing users
        assert len(errors) == 2
        assert all("Group 'group1'" in err for err in errors)
        assert any("missing_user1" in err for err in errors)
        assert any("missing_user2" in err for err in errors)

    def test_group_missing_member_subgroup(self):
        """Test that group with missing member_subgroup_id is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppGroup, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.groups["parent_group"] = CustomAppGroup(
            id="parent_group",
            name="Parent Group",
            member_subgroup_ids=["missing_subgroup"]
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Group 'parent_group'" in errors[0]
        assert "member_subgroup_id" in errors[0]
        assert "missing_subgroup" in errors[0]

    def test_scope_missing_parent(self):
        """Test that scope with missing parent_scope_id is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppScope, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.scopes["child_scope"] = CustomAppScope(
            id="child_scope",
            name="Child Scope",
            type="FOLDER",
            parent_scope_id="missing_parent"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Scope 'child_scope'" in errors[0]
        assert "parent_scope_id" in errors[0]
        assert "missing_parent" in errors[0]

    def test_scope_invalid_type_enum(self):
        """Test that scope with invalid type enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppScope, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        scope = CustomAppScope(
            id="scope1",
            name="Test Scope",
            type="INVALID_SCOPE_TYPE"
        )
        inventory.scopes["scope1"] = scope

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Scope 'scope1'" in errors[0]
        assert "invalid type" in errors[0].lower()
        assert "INVALID_SCOPE_TYPE" in errors[0]

    def test_role_missing_permission(self):
        """Test that role with missing permission is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppRole, CustomAppPermission, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.permissions["pViewData"] = CustomAppPermission(name="pViewData")
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=["pViewData", "pMissingPermission"]
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Role 'role1'" in errors[0]
        assert "permission" in errors[0]
        assert "pMissingPermission" in errors[0]
        assert "not found in permissions" in errors[0]

    def test_role_invalid_type_enum(self):
        """Test that role with invalid type enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppRole, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        role = CustomAppRole(
            id="role1",
            name="Test Role",
            type="INVALID_ROLE_TYPE",
            permissions=[]
        )
        inventory.roles["role1"] = role

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Role 'role1'" in errors[0]
        assert "invalid type" in errors[0].lower()
        assert "INVALID_ROLE_TYPE" in errors[0]

    def test_permission_invalid_access_level_enum(self):
        """Test that permission with invalid access_level enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppPermission, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        perm = CustomAppPermission(
            name="pTestPermission",
            access_level="INVALID_ACCESS_LEVEL"
        )
        inventory.permissions["pTestPermission"] = perm

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Permission 'pTestPermission'" in errors[0]
        assert "invalid access_level" in errors[0].lower()
        assert "INVALID_ACCESS_LEVEL" in errors[0]

    def test_assignment_missing_role(self):
        """Test that assignment with missing role_id is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="user1",
            principal_type="HUMAN",
            role_id="missing_role"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Assignment 'assign1'" in errors[0]
        assert "role_id" in errors[0]
        assert "missing_role" in errors[0]
        assert "not found in roles" in errors[0]

    def test_assignment_missing_scope(self):
        """Test that assignment with missing scope_id is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppRole, CustomAppRoleAssignment,
            validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=[]
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="user1",
            principal_type="HUMAN",
            role_id="role1",
            scope_id="missing_scope"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Assignment 'assign1'" in errors[0]
        assert "scope_id" in errors[0]
        assert "missing_scope" in errors[0]

    def test_assignment_invalid_principal_type_enum(self):
        """Test that assignment with invalid principal_type enum is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppRole, CustomAppRoleAssignment,
            validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User"
        )
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=[]
        )
        assignment = CustomAppRoleAssignment(
            id="assign1",
            principal_id="user1",
            principal_type="INVALID_TYPE",
            role_id="role1"
        )
        inventory.assignments["assign1"] = assignment

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) >= 1
        assert any("Assignment 'assign1'" in err and "invalid principal_type" in err.lower() for err in errors)

    def test_assignment_human_principal_not_found(self):
        """Test that assignment with HUMAN type but missing user is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppRole, CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=[]
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="missing_user",
            principal_type="HUMAN",
            role_id="role1"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Assignment 'assign1'" in errors[0]
        assert "principal_id" in errors[0]
        assert "missing_user" in errors[0]
        assert "not found in users" in errors[0]
        assert "(type=HUMAN)" in errors[0]

    def test_assignment_nhi_principal_not_found(self):
        """Test that assignment with NHI type but missing nhi is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppRole, CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=[]
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="missing_nhi",
            principal_type="NHI",
            role_id="role1"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Assignment 'assign1'" in errors[0]
        assert "principal_id" in errors[0]
        assert "missing_nhi" in errors[0]
        assert "not found in nhis" in errors[0]
        assert "(type=NHI)" in errors[0]

    def test_assignment_group_principal_not_found(self):
        """Test that assignment with GROUP type but missing group is caught."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppRole, CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Admin",
            type="CUSTOM_APP_ROLE",
            permissions=[]
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="missing_group",
            principal_type="GROUP",
            role_id="role1"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 1
        assert "Assignment 'assign1'" in errors[0]
        assert "principal_id" in errors[0]
        assert "missing_group" in errors[0]
        assert "not found in groups" in errors[0]
        assert "(type=GROUP)" in errors[0]

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors across different checks are all collected."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppNhi, CustomAppGroup,
            CustomAppRole, CustomAppPermission, CustomAppRoleAssignment,
            validate_inventory_consistency
        )

        inventory = CustomAppInventory()

        # Error 1: Invalid user status
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User",
            status="INVALID_STATUS"
        )

        # Error 2: NHI with missing owner
        inventory.nhis["nhi1"] = CustomAppNhi(
            id="nhi1",
            username="service",
            name="Service",
            owner_id="missing_owner"
        )

        # Error 3: Group with missing member
        inventory.groups["group1"] = CustomAppGroup(
            id="group1",
            name="Group",
            member_user_ids=["missing_member"]
        )

        # Error 4: Role with missing permission
        inventory.permissions["pValid"] = CustomAppPermission(name="pValid")
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Role",
            type="CUSTOM_APP_ROLE",
            permissions=["pValid", "pMissing"]
        )

        # Error 5: Assignment with missing principal
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="missing_principal",
            principal_type="HUMAN",
            role_id="role1"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        # Should collect all 5 errors
        assert len(errors) == 5
        assert any("User 'user1'" in err and "invalid status" in err.lower() for err in errors)
        assert any("NHI 'nhi1'" in err and "owner_id" in err for err in errors)
        assert any("Group 'group1'" in err and "member_user_id" in err for err in errors)
        assert any("Role 'role1'" in err and "permission" in err for err in errors)
        assert any("Assignment 'assign1'" in err and "principal_id" in err for err in errors)

    def test_strict_enums_false_skips_enum_validation(self):
        """Test that strict_enums=False skips all enum validations but keeps reference checks."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppRole, CustomAppPermission,
            CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()

        # Invalid enum values that should be skipped
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User",
            status="CUSTOM_STATUS"  # Invalid but should be skipped
        )

        # Invalid permission reference that should still be caught
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Role",
            type="CUSTOM_ROLE_TYPE",  # Invalid but should be skipped
            permissions=["missing_permission"]  # Should still be caught
        )

        errors = validate_inventory_consistency(inventory, strict_enums=False)

        # Should only have 1 error for missing permission, not for invalid enums
        assert len(errors) == 1
        assert "Role 'role1'" in errors[0]
        assert "permission" in errors[0]
        assert "missing_permission" in errors[0]

    def test_empty_inventory_passes_validation(self):
        """Test that an empty inventory passes validation."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 0

    def test_minimal_valid_inventory_passes(self):
        """Test that a minimal valid inventory passes all checks."""
        from sdk.customapp.custom_app_models import (
            CustomAppInventory, CustomAppUser, CustomAppRole, CustomAppPermission,
            CustomAppRoleAssignment, validate_inventory_consistency
        )

        inventory = CustomAppInventory()
        inventory.users["user1"] = CustomAppUser(
            id="user1",
            username="test@example.com",
            name="Test User",
            status="ENABLED"
        )
        inventory.permissions["pView"] = CustomAppPermission(name="pView")
        inventory.roles["role1"] = CustomAppRole(
            id="role1",
            name="Viewer",
            type="CUSTOM_APP_ROLE",
            permissions=["pView"]
        )
        inventory.assignments["assign1"] = CustomAppRoleAssignment(
            id="assign1",
            principal_id="user1",
            principal_type="HUMAN",
            role_id="role1"
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert len(errors) == 0


class TestNormalizeDeprecatedAccessLevels:
    """Test legacy access-level remapping before enum validation."""

    @pytest.mark.parametrize(
        "old_level,expected",
        [
            ("ACCESS_LEVEL_LIST", "ACCESS_LEVEL_METADATA_READ"),
            ("LIST", "ACCESS_LEVEL_METADATA_READ"),
            ("ACCESS_LEVEL_WRITE_TAG", "ACCESS_LEVEL_METADATA_CREATE"),
            ("WRITE_TAG", "ACCESS_LEVEL_METADATA_CREATE"),
            ("ACCESS_LEVEL_DELETE_TAG", "ACCESS_LEVEL_METADATA_DELETE"),
            ("DELETE_TAG", "ACCESS_LEVEL_METADATA_DELETE"),
            ("ACCESS_LEVEL_READ_METADATA", "ACCESS_LEVEL_METADATA_READ"),
            ("READ_METADATA", "ACCESS_LEVEL_METADATA_READ"),
            ("ACCESS_LEVEL_READ_DATA", "ACCESS_LEVEL_DATA_READ"),
            ("READ_DATA", "ACCESS_LEVEL_DATA_READ"),
            ("ACCESS_LEVEL_WRITE_METADATA", "ACCESS_LEVEL_METADATA_UPDATE"),
            ("WRITE_METADATA", "ACCESS_LEVEL_METADATA_UPDATE"),
            ("ACCESS_LEVEL_CREATE", "ACCESS_LEVEL_DATA_CREATE"),
            ("CREATE", "ACCESS_LEVEL_DATA_CREATE"),
            ("ACCESS_LEVEL_WRITE_DATA", "ACCESS_LEVEL_DATA_UPDATE"),
            ("WRITE_DATA", "ACCESS_LEVEL_DATA_UPDATE"),
            ("ACCESS_LEVEL_DELETE_DATA", "ACCESS_LEVEL_DATA_DELETE"),
            ("DELETE_DATA", "ACCESS_LEVEL_DATA_DELETE"),
            ("ACCESS_LEVEL_DELETE", "ACCESS_LEVEL_DATA_DELETE"),
            ("DELETE", "ACCESS_LEVEL_DATA_DELETE"),
            ("ACCESS_LEVEL_PERMISSIONS_MANAGEMENT", "ACCESS_LEVEL_AUTH_MANAGEMENT"),
            ("PERMISSIONS_MANAGEMENT", "ACCESS_LEVEL_AUTH_MANAGEMENT"),
        ],
    )
    def test_normalize_deprecated_access_levels(self, old_level, expected):
        from sdk.customapp.custom_app_models import (
            CustomAppInventory,
            CustomAppPermission,
            normalize_deprecated_access_levels,
        )

        inventory = CustomAppInventory()
        inventory.permissions["pLegacy"] = CustomAppPermission(
            name="pLegacy",
            access_level=old_level,
        )

        normalize_deprecated_access_levels(inventory)

        assert inventory.permissions["pLegacy"].access_level == expected

    def test_new_taxonomy_unchanged(self):
        from sdk.customapp.custom_app_models import (
            CustomAppInventory,
            CustomAppPermission,
            normalize_deprecated_access_levels,
        )

        inventory = CustomAppInventory()
        inventory.permissions["pRead"] = CustomAppPermission(
            name="pRead",
            access_level="ACCESS_LEVEL_DATA_READ",
        )

        normalize_deprecated_access_levels(inventory)

        assert inventory.permissions["pRead"].access_level == "ACCESS_LEVEL_DATA_READ"

    def test_validate_accepts_legacy_levels_and_mutates_in_place(self):
        from sdk.customapp.custom_app_models import (
            CustomAppInventory,
            CustomAppPermission,
            validate_inventory_consistency,
        )

        inventory = CustomAppInventory()
        inventory.permissions["pWrite"] = CustomAppPermission(
            name="pWrite",
            access_level="ACCESS_LEVEL_WRITE_DATA",
        )

        errors = validate_inventory_consistency(inventory, strict_enums=True)

        assert errors == []
        assert inventory.permissions["pWrite"].access_level == "ACCESS_LEVEL_DATA_UPDATE"

    def test_validate_inventory_from_json_legacy_access_level(self):
        from sdk.customapp.custom_app_models import validate_inventory_from_json

        data = {
            "permissions": {
                "pWrite": {
                    "name": "pWrite",
                    "accessLevel": "WRITE_DATA",
                }
            }
        }

        inventory = validate_inventory_from_json(data, strict_enums=True)

        assert inventory.permissions["pWrite"].access_level == "ACCESS_LEVEL_DATA_UPDATE"


def test_agent_auth_metadata_defaults_and_roundtrip():
    from sdk.customapp.custom_app_models import CustomAppAgent

    agent = CustomAppAgent(id="a1", name="Test Agent")
    assert agent.auth_metadata == {}   # default: empty dict, same convention as license_data

    agent2 = CustomAppAgent(
        id="a2",
        name="Test Agent 2",
        auth_metadata={"mcp_servers": [{"name": "brave-search", "env_var_names": ["BRAVE_API_KEY"]}]},
    )
    assert agent2.auth_metadata["mcp_servers"][0]["name"] == "brave-search"


def test_agent_mcp_servers_roundtrip_and_validation():
    from sdk.customapp.custom_app_models import (
        CustomAppAgent,
        CustomAppMcpServer,
        validate_inventory_from_json,
    )

    agent = CustomAppAgent(id="a1", name="Test Agent")
    assert agent.mcp_servers == []  # default: empty list, same convention as license_profiles

    # JSON loading rehydrates mcp_servers dicts into dataclasses.
    data = {
        "agents": {
            "a2": {
                "id": "a2",
                "name": "Agent With MCP",
                "mcp_servers": [
                    {"name": "brave-search", "transport": "STDIO", "command_present": True,
                     "env_var_names": ["BRAVE_API_KEY"]},
                    {"name": "github-remote", "transport": "HTTP", "url_host": "api.githubcopilot.com"},
                ],
            }
        }
    }
    inventory = validate_inventory_from_json(data, strict_enums=True)
    servers = inventory.agents["a2"].mcp_servers
    assert isinstance(servers[0], CustomAppMcpServer)
    assert servers[0].env_var_names == ["BRAVE_API_KEY"]
    assert servers[1].url_host == "api.githubcopilot.com"

    # strict_enums rejects transports outside the McpTransport enum.
    data["agents"]["a2"]["mcp_servers"] = [{"name": "x", "transport": "carrier-pigeon"}]
    try:
        validate_inventory_from_json(data, strict_enums=True)
        raised = False
    except ValueError as e:
        raised = True
        assert "invalid transport" in str(e)
    assert raised
