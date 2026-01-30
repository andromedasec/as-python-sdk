# Custom App Inventory Downloader

This module provides functionality to download and transform custom application inventory data into a standardized JSON format for ingestion into Andromeda.

## Overview

The Custom App Inventory Downloader transforms custom application inventory data (users, groups, roles, scopes, and assignments) into Andromeda's canonical inventory format. It supports various inventory types and can be extended to handle different custom application sources.

## Features

- **Multiple Entity Types**: Supports users, NHIs (non-human identities), groups, roles, scopes, permissions, and role assignments
- **Authentication Support**: Handles custom app authentication via environment variables
- **Mock Data Support**: Includes built-in mock data for testing and development

## Data Model

The module defines the following entity types:

### Users (`CustomAppUser`)

- `username`: User's unique username
- `name`: Display name
- `id`: Unique identifier
- `status`: User status (ENABLED, DEACTIVATED, SUSPENDED, etc.)
- `hrType`: HR type (EMPLOYEE, CONTINGENT_WORKER, THIRD_PARTY)

### NHIs (`CustomAppNhi`)

- `username`: Service identity username
- `name`: Display name
- `id`: Unique identifier
- `type`: NHI type (CUSTOM_APP_NHI)
- `is_external_client`: External client flag
- `ownerId`: Owner user ID
- `custodianId`: Custodian user ID
- `status`: Status

### Groups (`CustomAppGroup`)

- `name`: Group name
- `id`: Unique identifier
- `memberUserIds`: List of member user IDs
- `memberSubgroupIds`: List of nested subgroup IDs

### Scopes (`CustomAppScope`)

- `id`: Unique identifier
- `name`: Scope name
- `type`: Scope type (PROVIDER, FOLDER, ACCOUNT, RESOURCE_GROUP)
- `parentScopeId`: Parent scope for hierarchical structures

### Roles (`CustomAppRole`)

- `name`: Role name
- `id`: Unique identifier
- `type`: Role type (CUSTOM_APP_ROLE, CUSTOM_APP_USER_ROLE)
- `permissions`: List of permission identifiers

### Role Assignments (`CustomAppRoleAssignment`)

- `id`: Unique identifier
- `principalId`: Principal ID (user/group/NHI)
- `principalType`: Principal type (HUMAN, NHI, GROUP)
- `roleId`: Assigned role ID
- `scopeId`: Optional scope for scoped assignments

## Usage

### Command Line

```bash
python3 custom_app_inventory_downloader.py \
  --app_name="my_custom_app" \
  --output_dir="/tmp/customapp_export"
```

### Environment Variables

The module supports the following environment variables:

- `AS_CUSTOM_APP_AUTH_JSON`: JSON string containing authentication credentials for the custom app
- `AS_CUSTOM_APP_METADATA`: JSON string containing metadata about the custom app

Example usage:

```bash
export AS_CUSTOM_APP_AUTH_JSON='{"api_key": "xxx", "api_secret": "yyy"}'
export AS_CUSTOM_APP_METADATA='{"region": "us-west-2", "instance": "prod"}'
```

### Arguments

- `--app_name`: Application name prefix for output files (default: "test")
- `--output_dir`: Directory for output JSON files (default: "/tmp/customapp_export")

## Output Format

The module generates timestamped JSON files with the following structure:

```json
{
  "users": {
    "user@example.com": {
      "username": "user@example.com",
      "name": "User Name",
      "id": "user@example.com",
      "status": "ENABLED",
      "hrType": "EMPLOYEE"
    }
  },
  "nhis": {
    "service-account-1": {
      "username": "service-account-1",
      "name": "Service Account 1",
      "id": "app-uuid-001",
      "type": "CUSTOM_APP_NHI",
      "ownerId": "owner@example.com",
      "custodianId": "custodian@example.com",
      "status": "ENABLED"
    }
  },
  "groups": {
    "Group A": {
      "id": "Group A",
      "name": "Group A",
      "memberUserIds": ["user1@example.com", "user2@example.com"]
    }
  },
  "scopes": {
    "Server A": {
      "id": "Server A",
      "name": "Server A",
      "type": "FOLDER"
    }
  },
  "roles": {
    "admin_role": {
      "id": "admin_role",
      "name": "admin_role",
      "type": "CUSTOM_APP_ROLE",
      "permissions": ["pViewOrg", "pModifyData"]
    }
  },
  "assignments": {
    "user@example.com_admin_role": {
      "id": "user@example.com_admin_role",
      "principalId": "user@example.com",
      "principalType": "HUMAN",
      "roleId": "admin_role",
      "scopeId": "Server A"
    }
  }
}
```

### Output File Naming

Output files are named using the pattern: `{app_name}-{timestamp}.json`

Example: `my_custom_app-2026-01-24T10:30:00.json`

## Integration with Andromeda

This module is designed to work with the Custom App integration system:

1. **Setup Custom App Provider**: Setup Custom App Provider with the Secrets
2. **Upload Inventory Script**: Either use UI or the `customapp_transformer_uploader.py` module uploads the inventory downloader. Andromeda will periodically invoke this downloader to fetch inventory
3. **Ingestion Phase**: Andromeda ingests the inventory via the custom app provider

## Development

### Adding Custom Inventory Sources

To add support for a new custom app inventory source:

1. Extend the `CustomAppInventoryTransformer` class
2. Implement source-specific data fetching logic
3. Map source data to the standard data classes
4. Use the existing `transform_and_export()` method for output

### Mock Data

The module includes comprehensive mock data for testing. The mock data demonstrates:

- Human users with HR types
- Service identities (NHIs) with owners and custodians
- Hierarchical groups
- Nested scopes (folders and accounts)
- Role definitions with permissions
- User and group role assignments with scopes

## Enums and Constants

### UserStatus

- `ENABLED`: Active user
- `DEACTIVATED`: Deactivated user
- `IDENTITY_STATUS_UNRESOLVED`: Status pending resolution
- `SUSPENDED`: Suspended user

### PrincipalType

- `HUMAN`: Human user
- `NHI`: Non-human identity (service account, app, etc.)
- `GROUP`: Group of users

### RoleType

- `CUSTOM_APP_ROLE`: Standard custom app role
- `CUSTOM_APP_USER_ROLE`: User-specific custom app role

### ScopeType

- `PROVIDER`: Provider-level scope
- `FOLDER`: Folder/organizational unit
- `ACCOUNT`: Account-level scope
- `RESOURCE_GROUP`: Resource group scope

### HrType

- `EMPLOYEE`: Full-time employee
- `CONTINGENT_WORKER`: Contractor or temporary worker
- `THIRD_PARTY`: External third party

## Logging

The module uses Python's standard logging framework with INFO level by default. Logs include:

- Authentication status
- File operations
- Transformation progress
- Error details

### Log Format

`timestamp:level:module:function:line: message`

## Error Handling

The module includes comprehensive error handling for:

- Missing environment variables
- File I/O errors
- JSON parsing errors
- Authentication failures

All errors are logged with detailed context before raising exceptions.
