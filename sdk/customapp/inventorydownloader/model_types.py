"""Model type registry metadata for the custom app inventory downloader."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sdk.customapp.custom_app_models import (
    CustomAppAgent,
    CustomAppAgentLicenseProfile,
    CustomAppAgentModel,
    CustomAppGroupV2,
    CustomAppMcpServer,
    CustomAppNhiV2,
    CustomAppPermissionV2,
    CustomAppResource,
    CustomAppRole,
    CustomAppRoleAssignmentV2,
    CustomAppScopeV2,
    CustomAppUserHRISAttributes,
    CustomAppUserV2,
    Tag,
)


class ModelType(str, Enum):
    """Inventory model types supported by the downloader framework."""
    USERS = "users"
    NHIS = "nhis"
    GROUPS = "groups"
    SCOPES = "scopes"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    ASSIGNMENTS = "assignments"
    RESOURCES = "resources"
    AGENTS = "agents"


@dataclass(frozen=True)
class ModelTypeInfo:
    """Metadata for one model type: where it lives in CustomAppInventory and how it is keyed."""
    inventory_attr: str
    key_fn: Callable[[Any], str]
    model_cls: type


def _construct_user(data: dict) -> CustomAppUserV2:
    data = data.copy()
    if isinstance(data.get("hris_attributes"), dict):
        data["hris_attributes"] = CustomAppUserHRISAttributes(**data["hris_attributes"])
    return CustomAppUserV2(**data)


def _construct_resource(data: dict) -> CustomAppResource:
    data = data.copy()
    if isinstance(data.get("tags"), list):
        data["tags"] = [Tag(**t) if isinstance(t, dict) else t for t in data["tags"]]
    return CustomAppResource(**data)


def _construct_agent(data: dict) -> CustomAppAgent:
    data = data.copy()
    if isinstance(data.get("agent_model"), dict):
        data["agent_model"] = CustomAppAgentModel(**data["agent_model"])
    if isinstance(data.get("license_profiles"), list):
        data["license_profiles"] = [
            CustomAppAgentLicenseProfile(**p) if isinstance(p, dict) else p
            for p in data["license_profiles"]
        ]
    if isinstance(data.get("mcp_servers"), list):
        data["mcp_servers"] = [
            CustomAppMcpServer(**s) if isinstance(s, dict) else s
            for s in data["mcp_servers"]
        ]
    return CustomAppAgent(**data)


# Keying matches load_inventory_from_json conventions: users/nhis by username,
# permissions by name, everything else by id.
MODEL_TYPE_INFO: dict[ModelType, ModelTypeInfo] = {
    ModelType.USERS: ModelTypeInfo("users", lambda m: m.username, CustomAppUserV2),
    ModelType.NHIS: ModelTypeInfo("nhis", lambda m: m.username, CustomAppNhiV2),
    ModelType.GROUPS: ModelTypeInfo("groups", lambda m: m.id, CustomAppGroupV2),
    ModelType.SCOPES: ModelTypeInfo("scopes", lambda m: m.id, CustomAppScopeV2),
    ModelType.ROLES: ModelTypeInfo("roles", lambda m: m.id, CustomAppRole),
    ModelType.PERMISSIONS: ModelTypeInfo("permissions", lambda m: m.name, CustomAppPermissionV2),
    ModelType.ASSIGNMENTS: ModelTypeInfo("assignments", lambda m: m.id, CustomAppRoleAssignmentV2),
    ModelType.RESOURCES: ModelTypeInfo("resources", lambda m: m.id, CustomAppResource),
    ModelType.AGENTS: ModelTypeInfo("agents", lambda m: m.id, CustomAppAgent),
}

_CONSTRUCTORS: dict[ModelType, Callable[[dict], Any]] = {
    ModelType.USERS: _construct_user,
    ModelType.RESOURCES: _construct_resource,
    ModelType.AGENTS: _construct_agent,
}


def construct_model(model_type: ModelType, data: dict) -> Any:
    """Build a V2 model instance from a plain dict (used to reload checkpointed items)."""
    constructor = _CONSTRUCTORS.get(model_type)
    if constructor is not None:
        return constructor(data)
    return MODEL_TYPE_INFO[model_type].model_cls(**data)
