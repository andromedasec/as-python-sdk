from gql.dsl import DSLSchema
# File: andromeda/nonpublic/kuiper.proto
def list_trivial_fields_Permission(ds: DSLSchema):
    """ List all trivial fields of the Permission type """
    return (
        ds.Permission.name,
        ds.Permission.accessLevel,
        ds.Permission.sensitiveInformationExposure,
        ds.Permission.resourceExposure,
        ds.Permission.privilegeEscalationExposure,
        ds.Permission.score,
        ds.Permission.service,
        ds.Permission.serviceCriticality,
        ds.Permission.riskLevel,
        ds.Permission.usageLevel,
    )

# End of file: andromeda/nonpublic/kuiper.proto

# File: andromeda/nonpublic/graph/explorer_view_service.proto
def list_trivial_fields_ExplorerViewConnection(ds: DSLSchema):
    """ List all trivial fields of the ExplorerViewConnection type """
    return (
    )
def list_trivial_fields_ExplorerViewEdge(ds: DSLSchema):
    """ List all trivial fields of the ExplorerViewEdge type """
    return (
    )
def list_trivial_fields_MatchingEntitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the MatchingEntitiesSummary type """
    return (
        ds.MatchingEntitiesSummary.updatedAt,
        ds.MatchingEntitiesSummary.entitiesCount,
    )
def list_trivial_fields_ExplorerView(ds: DSLSchema):
    """ List all trivial fields of the ExplorerView type """
    return (
        ds.ExplorerView.id,
        ds.ExplorerView.name,
        ds.ExplorerView.type,
        ds.ExplorerView.category,
        ds.ExplorerView.ownerId,
        ds.ExplorerView.gqlFiltersJson,
        ds.ExplorerView.createdAt,
        ds.ExplorerView.updatedAt,
        ds.ExplorerView.description,
    )

# End of file: andromeda/nonpublic/graph/explorer_view_service.proto

# File: andromeda/nonpublic/graph/tenant_service.proto
def list_trivial_fields_TenantFeatureData(ds: DSLSchema):
    """ List all trivial fields of the TenantFeatureData type """
    return (
        ds.TenantFeatureData.type,
        ds.TenantFeatureData.status,
    )
def list_trivial_fields_PrimaryIdentityProviderEdge(ds: DSLSchema):
    """ List all trivial fields of the PrimaryIdentityProviderEdge type """
    return (
    )
def list_trivial_fields_PrimaryIdentityProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the PrimaryIdentityProvidersConnection type """
    return (
    )
def list_trivial_fields_TenantSettings(ds: DSLSchema):
    """ List all trivial fields of the TenantSettings type """
    return (
    )
def list_trivial_fields_TenantData(ds: DSLSchema):
    """ List all trivial fields of the TenantData type """
    return (
        ds.TenantData.tenantId,
        ds.TenantData.status,
    )
def list_trivial_fields_PartitionSummary(ds: DSLSchema):
    """ List all trivial fields of the PartitionSummary type """
    return (
        ds.PartitionSummary.hiCount,
        ds.PartitionSummary.nhiCount,
        ds.PartitionSummary.providersCount,
    )
def list_trivial_fields_PartitionData(ds: DSLSchema):
    """ List all trivial fields of the PartitionData type """
    return (
        ds.PartitionData.id,
        ds.PartitionData.name,
    )
def list_trivial_fields_PartitionEdge(ds: DSLSchema):
    """ List all trivial fields of the PartitionEdge type """
    return (
    )
def list_trivial_fields_PartitionsConnection(ds: DSLSchema):
    """ List all trivial fields of the PartitionsConnection type """
    return (
    )
def list_trivial_fields_DepartmentDataConnection(ds: DSLSchema):
    """ List all trivial fields of the DepartmentDataConnection type """
    return (
    )
def list_trivial_fields_DepartmentDataEdge(ds: DSLSchema):
    """ List all trivial fields of the DepartmentDataEdge type """
    return (
    )
def list_trivial_fields_DepartmentData(ds: DSLSchema):
    """ List all trivial fields of the DepartmentData type """
    return (
        ds.DepartmentData.department,
    )

# End of file: andromeda/nonpublic/graph/tenant_service.proto

# File: andromeda/nonpublic/graph/metrics_service.proto
def list_trivial_fields_MetricsCollection(ds: DSLSchema):
    """ List all trivial fields of the MetricsCollection type """
    return (
    )
def list_trivial_fields_MetricsConnection(ds: DSLSchema):
    """ List all trivial fields of the MetricsConnection type """
    return (
    )
def list_trivial_fields_MetricsEdge(ds: DSLSchema):
    """ List all trivial fields of the MetricsEdge type """
    return (
    )
def list_trivial_fields_MetricNode(ds: DSLSchema):
    """ List all trivial fields of the MetricNode type """
    return (
        ds.MetricNode.timestamp,
        ds.MetricNode.avgValue,
        ds.MetricNode.maxValue,
        ds.MetricNode.minValue,
        ds.MetricNode.sumValue,
    )
def list_trivial_fields_MetricHeader(ds: DSLSchema):
    """ List all trivial fields of the MetricHeader type """
    return (
        ds.MetricHeader.metric,
        ds.MetricHeader.step,
        ds.MetricHeader.providerId,
        ds.MetricHeader.accountId,
        ds.MetricHeader.policyId,
        ds.MetricHeader.identityId,
    )

# End of file: andromeda/nonpublic/graph/metrics_service.proto

# File: andromeda/nonpublic/graph/account_service.proto
def list_trivial_fields_PolicyEligibilityMapping(ds: DSLSchema):
    """ List all trivial fields of the PolicyEligibilityMapping type """
    return (
        ds.PolicyEligibilityMapping.eligibilityId,
        ds.PolicyEligibilityMapping.accountId,
        ds.PolicyEligibilityMapping.accountName,
        ds.PolicyEligibilityMapping.accountMode,
        ds.PolicyEligibilityMapping.principalType,
        ds.PolicyEligibilityMapping.principalId,
        ds.PolicyEligibilityMapping.principalName,
        ds.PolicyEligibilityMapping.policyId,
        ds.PolicyEligibilityMapping.policyName,
        ds.PolicyEligibilityMapping.policyType,
        ds.PolicyEligibilityMapping.policyBlastRisk,
        ds.PolicyEligibilityMapping.isPolicyBlastRiskComputed,
        ds.PolicyEligibilityMapping.status,
        ds.PolicyEligibilityMapping.eligibilityType,
        ds.PolicyEligibilityMapping.eligibilityName,
    )
def list_trivial_fields_AccessRequestProfileData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProfileData type """
    return (
        ds.AccessRequestProfileData.id,
        ds.AccessRequestProfileData.name,
    )
def list_trivial_fields_PolicyEligibilityMappingEdge(ds: DSLSchema):
    """ List all trivial fields of the PolicyEligibilityMappingEdge type """
    return (
    )
def list_trivial_fields_PolicyEligibilityMappingsConnection(ds: DSLSchema):
    """ List all trivial fields of the PolicyEligibilityMappingsConnection type """
    return (
    )
def list_trivial_fields_Account(ds: DSLSchema):
    """ List all trivial fields of the Account type """
    return (
        ds.Account.id,
        ds.Account.name,
        ds.Account.mode,
        ds.Account.lspEnabled,
        ds.Account.accountType,
        ds.Account.accountCategory,
        ds.Account.risk,
        ds.Account.riskLevel,
        ds.Account.isRiskComputed,
        ds.Account.sensitive,
        ds.Account.environment,
        ds.Account.contactEmails,
        ds.Account.criticality,
        ds.Account.createDate,
        ds.Account.tags,
        ds.Account.isManagementAccount,
        ds.Account.providerId,
        ds.Account.ownerIds,
        ds.Account.providerAccountId,
        ds.Account.providerType,
    )
def list_trivial_fields_ResourceConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceConnection type """
    return (
    )
def list_trivial_fields_ResourceEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceEdge type """
    return (
    )
def list_trivial_fields_Resource(ds: DSLSchema):
    """ List all trivial fields of the Resource type """
    return (
        ds.Resource.id,
        ds.Resource.externalId,
        ds.Resource.name,
        ds.Resource.serviceType,
        ds.Resource.type,
        ds.Resource.region,
        ds.Resource.createdTimestamp,
        ds.Resource.accessibility,
    )
def list_trivial_fields_ResourceRoleAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleAssignmentsConnection type """
    return (
    )
def list_trivial_fields_ResourceRoleAssignmentEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleAssignmentEdge type """
    return (
    )
def list_trivial_fields_ResourceRoleAssignment(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleAssignment type """
    return (
        ds.ResourceRoleAssignment.roleId,
        ds.ResourceRoleAssignment.roleName,
        ds.ResourceRoleAssignment.roleType,
        ds.ResourceRoleAssignment.roleAssignmentType,
        ds.ResourceRoleAssignment.matchTypes,
    )
def list_trivial_fields_AccountIdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesConnection type """
    return (
    )
def list_trivial_fields_AccountIdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentityEdge type """
    return (
    )
def list_trivial_fields_AccountServiceIdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountServiceIdentitiesConnection type """
    return (
        ds.AccountServiceIdentitiesConnection.serviceIdentityIds,
    )
def list_trivial_fields_AccountServiceIdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountServiceIdentityEdge type """
    return (
    )
def list_trivial_fields_ResourceGroupConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroupConnection type """
    return (
    )
def list_trivial_fields_ResourceGroupEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroupEdge type """
    return (
    )
def list_trivial_fields_ResourceGroup(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroup type """
    return (
        ds.ResourceGroup.id,
        ds.ResourceGroup.name,
        ds.ResourceGroup.externalId,
        ds.ResourceGroup.connectionString,
    )
def list_trivial_fields_ResourceGroupTag(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroupTag type """
    return (
        ds.ResourceGroupTag.key,
        ds.ResourceGroupTag.values,
    )
def list_trivial_fields_PoliciesSignificanceData(ds: DSLSchema):
    """ List all trivial fields of the PoliciesSignificanceData type """
    return (
        ds.PoliciesSignificanceData.policyUsedByMultipleNonHumanIdentitiesCount,
        ds.PoliciesSignificanceData.policyUnused30To90DaysCount,
        ds.PoliciesSignificanceData.policyUnused90To180DaysCount,
        ds.PoliciesSignificanceData.policyUnused180To365DaysCount,
        ds.PoliciesSignificanceData.policyUnused365DaysPlusCount,
        ds.PoliciesSignificanceData.notAllPolicyAssignmentsUsed365DaysPlusCount,
        ds.PoliciesSignificanceData.policyOverProvisionedCount,
        ds.PoliciesSignificanceData.policiesWithAdminPrivilegeCount,
    )
def list_trivial_fields_AccountPolicyDataEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyDataEdge type """
    return (
    )
def list_trivial_fields_PrincipalTrustData(ds: DSLSchema):
    """ List all trivial fields of the PrincipalTrustData type """
    return (
        ds.PrincipalTrustData.type,
        ds.PrincipalTrustData.sourceAccountCount,
        ds.PrincipalTrustData.crossAccountCount,
    )
def list_trivial_fields_PolicyIncomingTrustsSummary(ds: DSLSchema):
    """ List all trivial fields of the PolicyIncomingTrustsSummary type """
    return (
    )
def list_trivial_fields_PolicyOutgoingTrustsSummary(ds: DSLSchema):
    """ List all trivial fields of the PolicyOutgoingTrustsSummary type """
    return (
        ds.PolicyOutgoingTrustsSummary.sourceAccountCount,
        ds.PolicyOutgoingTrustsSummary.crossAccountCount,
    )
def list_trivial_fields_AccountPolicyData(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyData type """
    return (
        ds.AccountPolicyData.policyId,
        ds.AccountPolicyData.policyName,
        ds.AccountPolicyData.policyAssignmentType,
        ds.AccountPolicyData.policyType,
        ds.AccountPolicyData.blastRisk,
        ds.AccountPolicyData.blastRiskLevel,
        ds.AccountPolicyData.isBlastRiskComputed,
        ds.AccountPolicyData.isActive,
        ds.AccountPolicyData.hasAdminPermissions,
        ds.AccountPolicyData.policyLastUsedAt,
        ds.AccountPolicyData.policyLastUsedAtDataSource,
        ds.AccountPolicyData.isLsp,
        ds.AccountPolicyData.accountId,
        ds.AccountPolicyData.accountName,
        ds.AccountPolicyData.accountMode,
        ds.AccountPolicyData.isAdminPolicy,
        ds.AccountPolicyData.numberOfIdentitiesWithPolicyAccess,
        ds.AccountPolicyData.roleTrustDocument,
        ds.AccountPolicyData.externalId,
    )
def list_trivial_fields_RoleServiceDataConnection(ds: DSLSchema):
    """ List all trivial fields of the RoleServiceDataConnection type """
    return (
    )
def list_trivial_fields_RoleServiceDataEdge(ds: DSLSchema):
    """ List all trivial fields of the RoleServiceDataEdge type """
    return (
    )
def list_trivial_fields_RoleServiceData(ds: DSLSchema):
    """ List all trivial fields of the RoleServiceData type """
    return (
        ds.RoleServiceData.serviceType,
    )
def list_trivial_fields_AccountPoliciesDataConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountPoliciesDataConnection type """
    return (
        ds.AccountPoliciesDataConnection.policyIds,
    )
def list_trivial_fields_AccountPolicyIdentityBinding(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyIdentityBinding type """
    return (
        ds.AccountPolicyIdentityBinding.accountId,
        ds.AccountPolicyIdentityBinding.accountName,
        ds.AccountPolicyIdentityBinding.accountMode,
        ds.AccountPolicyIdentityBinding.externalBindingId,
    )
def list_trivial_fields_AccountPolicyIdentityBindingEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyIdentityBindingEdge type """
    return (
    )
def list_trivial_fields_AccountPolicyUserResolvedAssignmentEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyUserResolvedAssignmentEdge type """
    return (
    )
def list_trivial_fields_AccountPolicyUserResolvedAssignment(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyUserResolvedAssignment type """
    return (
        ds.AccountPolicyUserResolvedAssignment.providerName,
        ds.AccountPolicyUserResolvedAssignment.accountId,
        ds.AccountPolicyUserResolvedAssignment.accountName,
        ds.AccountPolicyUserResolvedAssignment.accountMode,
        ds.AccountPolicyUserResolvedAssignment.policyId,
        ds.AccountPolicyUserResolvedAssignment.roleName,
        ds.AccountPolicyUserResolvedAssignment.policyBindingLastUsedAt,
        ds.AccountPolicyUserResolvedAssignment.userId,
        ds.AccountPolicyUserResolvedAssignment.identityId,
        ds.AccountPolicyUserResolvedAssignment.principalUsername,
        ds.AccountPolicyUserResolvedAssignment.principalType,
        ds.AccountPolicyUserResolvedAssignment.policyType,
    )
def list_trivial_fields_ResourcesDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourcesDataConnection type """
    return (
    )
def list_trivial_fields_ResourceDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceDataEdge type """
    return (
    )
def list_trivial_fields_ResourceData(ds: DSLSchema):
    """ List all trivial fields of the ResourceData type """
    return (
        ds.ResourceData.serviceType,
        ds.ResourceData.allResources,
        ds.ResourceData.andromedaSupportEnabled,
        ds.ResourceData.discoveredFrom,
    )
def list_trivial_fields_ResourcePermissionsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourcePermissionsDataConnection type """
    return (
    )
def list_trivial_fields_ResourcePermissionsDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourcePermissionsDataEdge type """
    return (
    )
def list_trivial_fields_ResourcesData(ds: DSLSchema):
    """ List all trivial fields of the ResourcesData type """
    return (
        ds.ResourcesData.allResources,
    )
def list_trivial_fields_ResourcePermissionsData(ds: DSLSchema):
    """ List all trivial fields of the ResourcePermissionsData type """
    return (
        ds.ResourcePermissionsData.allPermissions,
        ds.ResourcePermissionsData.blastRisk,
        ds.ResourcePermissionsData.blastRiskLevel,
    )
def list_trivial_fields_ResourceInstancesConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceInstancesConnection type """
    return (
    )
def list_trivial_fields_ResourceInstanceEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceInstanceEdge type """
    return (
    )
def list_trivial_fields_ResourceInstance(ds: DSLSchema):
    """ List all trivial fields of the ResourceInstance type """
    return (
        ds.ResourceInstance.externalId,
        ds.ResourceInstance.region,
        ds.ResourceInstance.resourceFound,
        ds.ResourceInstance.name,
        ds.ResourceInstance.id,
        ds.ResourceInstance.accessibility,
    )
def list_trivial_fields_AccountPolicyUserResolvedAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyUserResolvedAssignmentsConnection type """
    return (
    )
def list_trivial_fields_AccountPolicyIdentityBindingsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyIdentityBindingsConnection type """
    return (
    )
def list_trivial_fields_AccountsGroupedByRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedByRiskLevel type """
    return (
        ds.AccountsGroupedByRiskLevel.riskLevel,
        ds.AccountsGroupedByRiskLevel.count,
    )
def list_trivial_fields_AccountsGroupedByMode(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedByMode type """
    return (
        ds.AccountsGroupedByMode.mode,
        ds.AccountsGroupedByMode.count,
    )
def list_trivial_fields_AccountsGroupedByEnvironment(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedByEnvironment type """
    return (
        ds.AccountsGroupedByEnvironment.environment,
        ds.AccountsGroupedByEnvironment.count,
    )
def list_trivial_fields_AccountsGroupedBySensitivity(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedBySensitivity type """
    return (
        ds.AccountsGroupedBySensitivity.sensitive,
        ds.AccountsGroupedBySensitivity.count,
    )
def list_trivial_fields_AccountsGroupedByCriticality(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedByCriticality type """
    return (
        ds.AccountsGroupedByCriticality.criticality,
        ds.AccountsGroupedByCriticality.count,
    )
def list_trivial_fields_AccountsGroupedByCriticalitySensitivityRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the AccountsGroupedByCriticalitySensitivityRiskLevel type """
    return (
        ds.AccountsGroupedByCriticalitySensitivityRiskLevel.riskLevel,
        ds.AccountsGroupedByCriticalitySensitivityRiskLevel.criticality,
        ds.AccountsGroupedByCriticalitySensitivityRiskLevel.sensitive,
        ds.AccountsGroupedByCriticalitySensitivityRiskLevel.count,
    )
def list_trivial_fields_AccountsSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountsSummary type """
    return (
    )
def list_trivial_fields_AccountIdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesSummary type """
    return (
    )
def list_trivial_fields_AccountServiceIdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountServiceIdentitiesSummary type """
    return (
    )
def list_trivial_fields_AccountIdentitiesOriginSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesOriginSummary type """
    return (
        ds.AccountIdentitiesOriginSummary.originType,
        ds.AccountIdentitiesOriginSummary.count,
    )
def list_trivial_fields_AccountPoliciesSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountPoliciesSummary type """
    return (
    )
def list_trivial_fields_AccountPolicyUsageSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyUsageSummary type """
    return (
        ds.AccountPolicyUsageSummary.interval,
        ds.AccountPolicyUsageSummary.count,
    )
def list_trivial_fields_AccountPolicyUsage(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyUsage type """
    return (
        ds.AccountPolicyUsage.unused,
        ds.AccountPolicyUsage.used,
        ds.AccountPolicyUsage.untracked,
    )
def list_trivial_fields_AccountIdentitiesGroupedByBlastRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedByBlastRiskLevel type """
    return (
        ds.AccountIdentitiesGroupedByBlastRiskLevel.blastRiskLevel,
        ds.AccountIdentitiesGroupedByBlastRiskLevel.count,
    )
def list_trivial_fields_AccountIdentitiesGroupedByBlastRiskLevelAndHrType(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedByBlastRiskLevelAndHrType type """
    return (
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndHrType.hrType,
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndHrType.blastRiskLevel,
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndHrType.count,
    )
def list_trivial_fields_AccountIdentitiesGroupedByHighBlastRiskIdentitiesChanges(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedByHighBlastRiskIdentitiesChanges type """
    return (
        ds.AccountIdentitiesGroupedByHighBlastRiskIdentitiesChanges.changeType,
        ds.AccountIdentitiesGroupedByHighBlastRiskIdentitiesChanges.count,
    )
def list_trivial_fields_PoliciesGroupedByRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the PoliciesGroupedByRiskLevel type """
    return (
        ds.PoliciesGroupedByRiskLevel.riskLevel,
        ds.PoliciesGroupedByRiskLevel.count,
    )
def list_trivial_fields_AccountIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType type """
    return (
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.serviceIdentityType,
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.blastRiskLevel,
        ds.AccountIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.count,
    )
def list_trivial_fields_AccountServiceIdentitiesGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the AccountServiceIdentitiesGroupedBySignificance type """
    return (
        ds.AccountServiceIdentitiesGroupedBySignificance.significance,
        ds.AccountServiceIdentitiesGroupedBySignificance.count,
    )
def list_trivial_fields_AccountIdentitiesGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedBySignificance type """
    return (
        ds.AccountIdentitiesGroupedBySignificance.significance,
        ds.AccountIdentitiesGroupedBySignificance.count,
    )
def list_trivial_fields_IdentitiesOriginTypeSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentitiesOriginTypeSummary type """
    return (
        ds.IdentitiesOriginTypeSummary.identityOriginType,
        ds.IdentitiesOriginTypeSummary.count,
    )
def list_trivial_fields_PoliciesGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the PoliciesGroupedBySignificance type """
    return (
        ds.PoliciesGroupedBySignificance.significance,
        ds.PoliciesGroupedBySignificance.count,
    )
def list_trivial_fields_AccountIdentitiesGroupedByAccessKeysCount(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentitiesGroupedByAccessKeysCount type """
    return (
        ds.AccountIdentitiesGroupedByAccessKeysCount.singleAccessKeyCount,
        ds.AccountIdentitiesGroupedByAccessKeysCount.multipleAccessKeysCount,
    )
def list_trivial_fields_ActivitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the ActivitiesSummary type """
    return (
    )
def list_trivial_fields_ActivitiesGroupedByPolicy(ds: DSLSchema):
    """ List all trivial fields of the ActivitiesGroupedByPolicy type """
    return (
        ds.ActivitiesGroupedByPolicy.policyId,
        ds.ActivitiesGroupedByPolicy.policyName,
        ds.ActivitiesGroupedByPolicy.count,
    )
def list_trivial_fields_ActivitiesGroupedByIdentity(ds: DSLSchema):
    """ List all trivial fields of the ActivitiesGroupedByIdentity type """
    return (
        ds.ActivitiesGroupedByIdentity.identityId,
        ds.ActivitiesGroupedByIdentity.identityName,
        ds.ActivitiesGroupedByIdentity.identityType,
        ds.ActivitiesGroupedByIdentity.count,
    )
def list_trivial_fields_AccountIdentityGroupedByMetadata(ds: DSLSchema):
    """ List all trivial fields of the AccountIdentityGroupedByMetadata type """
    return (
    )
def list_trivial_fields_ResourceRoleEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleEligibilityData type """
    return (
        ds.ResourceRoleEligibilityData.serviceType,
        ds.ResourceRoleEligibilityData.allResources,
        ds.ResourceRoleEligibilityData.index,
    )
def list_trivial_fields_RoleEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the RoleEligibilityData type """
    return (
    )
def list_trivial_fields_GroupEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the GroupEligibilityData type """
    return (
    )
def list_trivial_fields_ResourceSetEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the ResourceSetEligibilityData type """
    return (
        ds.ResourceSetEligibilityData.name,
        ds.ResourceSetEligibilityData.eligibilityConstraint,
    )
def list_trivial_fields_ResourceRoleEligibilityConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleEligibilityConnection type """
    return (
    )
def list_trivial_fields_ResourceRoleEligibilityEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceRoleEligibilityEdge type """
    return (
    )

# End of file: andromeda/nonpublic/graph/account_service.proto

# File: andromeda/nonpublic/graph/service_identity.proto
def list_trivial_fields_UnifiedServiceIdentityPoliciesDataConnection(ds: DSLSchema):
    """ List all trivial fields of the UnifiedServiceIdentityPoliciesDataConnection type """
    return (
    )
def list_trivial_fields_UnifiedServiceIdentityPolicyDataEdge(ds: DSLSchema):
    """ List all trivial fields of the UnifiedServiceIdentityPolicyDataEdge type """
    return (
    )
def list_trivial_fields_UnifiedServiceIdentityPolicyData(ds: DSLSchema):
    """ List all trivial fields of the UnifiedServiceIdentityPolicyData type """
    return (
        ds.UnifiedServiceIdentityPolicyData.policyId,
        ds.UnifiedServiceIdentityPolicyData.policyName,
        ds.UnifiedServiceIdentityPolicyData.blastRisk,
        ds.UnifiedServiceIdentityPolicyData.blastRiskLevel,
        ds.UnifiedServiceIdentityPolicyData.isBlastRiskComputed,
        ds.UnifiedServiceIdentityPolicyData.hasAdminPermissions,
        ds.UnifiedServiceIdentityPolicyData.policyType,
        ds.UnifiedServiceIdentityPolicyData.excessivePrivilegeScore,
        ds.UnifiedServiceIdentityPolicyData.highRiskFrequentlyUsedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.highRiskInfrequentlyUsedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.highRiskUnusedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.lowRiskFrequentlyUsedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.lowRiskUnusedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.untrackedPermissionsCount,
        ds.UnifiedServiceIdentityPolicyData.unusedPermissionsPercentage,
        ds.UnifiedServiceIdentityPolicyData.accountId,
        ds.UnifiedServiceIdentityPolicyData.accountName,
        ds.UnifiedServiceIdentityPolicyData.accountMode,
        ds.UnifiedServiceIdentityPolicyData.roleTrustDocument,
    )
def list_trivial_fields_ServiceIdentityProviderDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityProviderDataEdge type """
    return (
    )
def list_trivial_fields_ServiceIdentityProvidersDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityProvidersDataConnection type """
    return (
    )
def list_trivial_fields_ServiceIdentityProviderData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityProviderData type """
    return (
        ds.ServiceIdentityProviderData.providerId,
        ds.ServiceIdentityProviderData.providerName,
        ds.ServiceIdentityProviderData.type,
        ds.ServiceIdentityProviderData.blastRisk,
        ds.ServiceIdentityProviderData.isBlastRiskComputed,
        ds.ServiceIdentityProviderData.providerCategory,
        ds.ServiceIdentityProviderData.providerTierId,
        ds.ServiceIdentityProviderData.providerTierName,
        ds.ServiceIdentityProviderData.providerBindingType,
        ds.ServiceIdentityProviderData.providerType,
        ds.ServiceIdentityProviderData.accountsCount,
        ds.ServiceIdentityProviderData.authType,
        ds.ServiceIdentityProviderData.activityCount,
        ds.ServiceIdentityProviderData.lastActivityAt,
    )
def list_trivial_fields_ServiceIdentityResolvedAssignmentsData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityResolvedAssignmentsData type """
    return (
    )
def list_trivial_fields_ServiceIdentityProviderAssignmentData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityProviderAssignmentData type """
    return (
        ds.ServiceIdentityProviderAssignmentData.assignmentType,
        ds.ServiceIdentityProviderAssignmentData.accessRequestId,
        ds.ServiceIdentityProviderAssignmentData.isAndromedaManaged,
        ds.ServiceIdentityProviderAssignmentData.status,
        ds.ServiceIdentityProviderAssignmentData.isDirectBinding,
    )
def list_trivial_fields_ServiceIdentityResolvedAssignmentsEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityResolvedAssignmentsEdge type """
    return (
    )
def list_trivial_fields_ServiceIdentityResolvedAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityResolvedAssignmentsConnection type """
    return (
    )
def list_trivial_fields_ServiceIdentityOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityOpsInsightData type """
    return (
        ds.ServiceIdentityOpsInsightData.type,
        ds.ServiceIdentityOpsInsightData.category,
    )
def list_trivial_fields_ServiceIdentitySignificanceData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitySignificanceData type """
    return (
        ds.ServiceIdentitySignificanceData.isRiskAccepted,
        ds.ServiceIdentitySignificanceData.hasAdminPrivileges,
        ds.ServiceIdentitySignificanceData.hasCrossAccountWithCriticalityEscalation,
        ds.ServiceIdentitySignificanceData.isInactive,
        ds.ServiceIdentitySignificanceData.isEksClusterNotFound,
        ds.ServiceIdentitySignificanceData.isOidcProviderNotFound,
        ds.ServiceIdentitySignificanceData.hasMultipleBindingsForEks,
        ds.ServiceIdentitySignificanceData.isSamlProviderNotFound,
        ds.ServiceIdentitySignificanceData.isEksServiceAccountWithoutConstraint,
        ds.ServiceIdentitySignificanceData.isEksServiceAccountWithInvalidTrust,
        ds.ServiceIdentitySignificanceData.multipleNhisShareSameAwsRole,
        ds.ServiceIdentitySignificanceData.hasNoPolicyBindings,
        ds.ServiceIdentitySignificanceData.hasOverPrivilegedRole,
        ds.ServiceIdentitySignificanceData.hasUnusedRole,
    )
def list_trivial_fields_ServiceIdentityAccountsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityAccountsDataConnection type """
    return (
    )
def list_trivial_fields_ServiceIdentityAccountDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityAccountDataEdge type """
    return (
    )
def list_trivial_fields_ServiceIdentityAccountData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityAccountData type """
    return (
        ds.ServiceIdentityAccountData.accountId,
        ds.ServiceIdentityAccountData.accountName,
        ds.ServiceIdentityAccountData.blastRisk,
        ds.ServiceIdentityAccountData.blastRiskLevel,
        ds.ServiceIdentityAccountData.isBlastRiskComputed,
        ds.ServiceIdentityAccountData.highRiskFrequentlyUsedPermissionsCount,
        ds.ServiceIdentityAccountData.highRiskInfrequentlyUsedPermissionsCount,
        ds.ServiceIdentityAccountData.highRiskUnusedPermissionsCount,
        ds.ServiceIdentityAccountData.lowRiskFrequentlyUsedPermissionsCount,
        ds.ServiceIdentityAccountData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.ServiceIdentityAccountData.lowRiskUnusedPermissionsCount,
        ds.ServiceIdentityAccountData.untrackedPermissionsCount,
        ds.ServiceIdentityAccountData.unusedPermissionsPercentage,
        ds.ServiceIdentityAccountData.totalPermissions,
        ds.ServiceIdentityAccountData.excessivePrivilegeScore,
        ds.ServiceIdentityAccountData.isRiskAccepted,
        ds.ServiceIdentityAccountData.servicesUsed,
        ds.ServiceIdentityAccountData.computedBlastRisk,
        ds.ServiceIdentityAccountData.computedBlastRiskLevel,
        ds.ServiceIdentityAccountData.activityCount,
        ds.ServiceIdentityAccountData.lastActivityAt,
        ds.ServiceIdentityAccountData.mode,
    )
def list_trivial_fields_ServiceIdentityPoliciesDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityPoliciesDataConnection type """
    return (
    )
def list_trivial_fields_ServiceIdentityPolicyDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityPolicyDataEdge type """
    return (
    )
def list_trivial_fields_ServiceIdentityPolicyData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityPolicyData type """
    return (
        ds.ServiceIdentityPolicyData.policyId,
        ds.ServiceIdentityPolicyData.policyName,
        ds.ServiceIdentityPolicyData.blastRisk,
        ds.ServiceIdentityPolicyData.blastRiskLevel,
        ds.ServiceIdentityPolicyData.isBlastRiskComputed,
        ds.ServiceIdentityPolicyData.hasAdminPermissions,
        ds.ServiceIdentityPolicyData.policyType,
        ds.ServiceIdentityPolicyData.excessivePrivilegeScore,
        ds.ServiceIdentityPolicyData.highRiskFrequentlyUsedPermissionsCount,
        ds.ServiceIdentityPolicyData.highRiskInfrequentlyUsedPermissionsCount,
        ds.ServiceIdentityPolicyData.highRiskUnusedPermissionsCount,
        ds.ServiceIdentityPolicyData.lowRiskFrequentlyUsedPermissionsCount,
        ds.ServiceIdentityPolicyData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.ServiceIdentityPolicyData.lowRiskUnusedPermissionsCount,
        ds.ServiceIdentityPolicyData.untrackedPermissionsCount,
        ds.ServiceIdentityPolicyData.unusedPermissionsPercentage,
        ds.ServiceIdentityPolicyData.roleTrustDocument,
    )
def list_trivial_fields_ServiceIdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesConnection type """
    return (
        ds.ServiceIdentitiesConnection.serviceIdentityIds,
    )
def list_trivial_fields_TrustedService(ds: DSLSchema):
    """ List all trivial fields of the TrustedService type """
    return (
        ds.TrustedService.name,
    )
def list_trivial_fields_EksClusterDetails(ds: DSLSchema):
    """ List all trivial fields of the EksClusterDetails type """
    return (
        ds.EksClusterDetails.name,
    )
def list_trivial_fields_AwsExternalServiceIdentity(ds: DSLSchema):
    """ List all trivial fields of the AwsExternalServiceIdentity type """
    return (
        ds.AwsExternalServiceIdentity.subType,
    )
def list_trivial_fields_AzureServiceIdentity(ds: DSLSchema):
    """ List all trivial fields of the AzureServiceIdentity type """
    return (
        ds.AzureServiceIdentity.subType,
    )
def list_trivial_fields_GcpServiceIdentity(ds: DSLSchema):
    """ List all trivial fields of the GcpServiceIdentity type """
    return (
        ds.GcpServiceIdentity.subType,
    )
def list_trivial_fields_KubernetesServiceIdentity(ds: DSLSchema):
    """ List all trivial fields of the KubernetesServiceIdentity type """
    return (
        ds.KubernetesServiceIdentity.subType,
    )
def list_trivial_fields_ServiceIdentity(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentity type """
    return (
        ds.ServiceIdentity.id,
        ds.ServiceIdentity.username,
        ds.ServiceIdentity.state,
        ds.ServiceIdentity.serviceIdentityType,
        ds.ServiceIdentity.createdAt,
        ds.ServiceIdentity.awsExternalServiceIdentitySubType,
        ds.ServiceIdentity.blastRisk,
        ds.ServiceIdentity.blastRiskLevel,
        ds.ServiceIdentity.isBlastRiskComputed,
        ds.ServiceIdentity.risk,
        ds.ServiceIdentity.riskLevel,
        ds.ServiceIdentity.trustedService,
        ds.ServiceIdentity.eksClusterName,
        ds.ServiceIdentity.originAccountId,
        ds.ServiceIdentity.originAccountName,
        ds.ServiceIdentity.roleTrustConditionType,
        ds.ServiceIdentity.activityCount,
        ds.ServiceIdentity.lastActivityAt,
    )
def list_trivial_fields_ServiceIdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityEdge type """
    return (
    )
def list_trivial_fields_OriginData(ds: DSLSchema):
    """ List all trivial fields of the OriginData type """
    return (
        ds.OriginData.providerId,
        ds.OriginData.providerName,
        ds.OriginData.folderId,
        ds.OriginData.folderName,
        ds.OriginData.accountId,
        ds.OriginData.accountName,
        ds.OriginData.resourceGroupId,
        ds.OriginData.resourceGroupName,
        ds.OriginData.defaultOriginId,
        ds.OriginData.defaultOriginName,
    )
def list_trivial_fields_ServiceIdentityRiskFactorData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityRiskFactorData type """
    return (
        ds.ServiceIdentityRiskFactorData.type,
        ds.ServiceIdentityRiskFactorData.category,
    )
def list_trivial_fields_ServiceIdentityRiskFactors(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityRiskFactors type """
    return (
        ds.ServiceIdentityRiskFactors.noHumanOwner,
        ds.ServiceIdentityRiskFactors.consoleAccess,
        ds.ServiceIdentityRiskFactors.sharedAcrossApps,
        ds.ServiceIdentityRiskFactors.accessedFromOutside,
        ds.ServiceIdentityRiskFactors.anamalousCloudActivities,
        ds.ServiceIdentityRiskFactors.highBlastRisk,
        ds.ServiceIdentityRiskFactors.passwordHygiene,
        ds.ServiceIdentityRiskFactors.keyHygiene,
        ds.ServiceIdentityRiskFactors.staleOwner,
        ds.ServiceIdentityRiskFactors.accessKeyRotationPastDueDate,
    )
def list_trivial_fields_ServiceIdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesSummary type """
    return (
    )
def list_trivial_fields_ServiceIdentitiesGroupedByType(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesGroupedByType type """
    return (
        ds.ServiceIdentitiesGroupedByType.serviceIdentityType,
        ds.ServiceIdentitiesGroupedByType.count,
    )
def list_trivial_fields_ServiceIdentitiesGroupedByAwsExternalSubType(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesGroupedByAwsExternalSubType type """
    return (
        ds.ServiceIdentitiesGroupedByAwsExternalSubType.awsExternalServiceIdentitySubType,
        ds.ServiceIdentitiesGroupedByAwsExternalSubType.count,
    )
def list_trivial_fields_ServiceIdentityGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityGroupedBySignificance type """
    return (
        ds.ServiceIdentityGroupedBySignificance.significance,
        ds.ServiceIdentityGroupedBySignificance.count,
    )
def list_trivial_fields_IdentityGroupedByTrustedService(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByTrustedService type """
    return (
        ds.IdentityGroupedByTrustedService.trustedService,
        ds.IdentityGroupedByTrustedService.count,
    )
def list_trivial_fields_ServiceInstancesConnection(ds: DSLSchema):
    """ List all trivial fields of the ServiceInstancesConnection type """
    return (
    )
def list_trivial_fields_ServiceInstanceEdge(ds: DSLSchema):
    """ List all trivial fields of the ServiceInstanceEdge type """
    return (
    )
def list_trivial_fields_ServiceInstance(ds: DSLSchema):
    """ List all trivial fields of the ServiceInstance type """
    return (
        ds.ServiceInstance.serviceType,
        ds.ServiceInstance.serviceInstanceName,
    )
def list_trivial_fields_IdentityGroupedByMetadata(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByMetadata type """
    return (
    )
def list_trivial_fields_ServiceIdentitiesGroupedByEksCluster(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesGroupedByEksCluster type """
    return (
        ds.ServiceIdentitiesGroupedByEksCluster.eksClusterName,
        ds.ServiceIdentitiesGroupedByEksCluster.count,
    )
def list_trivial_fields_ServiceIdentitiesGroupedByAzureServiceIdentitySubType(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesGroupedByAzureServiceIdentitySubType type """
    return (
        ds.ServiceIdentitiesGroupedByAzureServiceIdentitySubType.azureServiceIdentitySubType,
        ds.ServiceIdentitiesGroupedByAzureServiceIdentitySubType.count,
    )
def list_trivial_fields_ServiceIdentitiesGroupedByGcpServiceIdentitySubType(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentitiesGroupedByGcpServiceIdentitySubType type """
    return (
        ds.ServiceIdentitiesGroupedByGcpServiceIdentitySubType.gcpServiceIdentitySubType,
        ds.ServiceIdentitiesGroupedByGcpServiceIdentitySubType.count,
    )

# End of file: andromeda/nonpublic/graph/service_identity.proto

# File: andromeda/nonpublic/graph/campaign_service.proto
def list_trivial_fields_CampaignsConnection(ds: DSLSchema):
    """ List all trivial fields of the CampaignsConnection type """
    return (
        ds.CampaignsConnection.campaignIds,
    )
def list_trivial_fields_CampaignEdge(ds: DSLSchema):
    """ List all trivial fields of the CampaignEdge type """
    return (
    )
def list_trivial_fields_CampaignSummary(ds: DSLSchema):
    """ List all trivial fields of the CampaignSummary type """
    return (
        ds.CampaignSummary.reviewerCount,
        ds.CampaignSummary.reviewsCount,
    )
def list_trivial_fields_CampaignProviderEdge(ds: DSLSchema):
    """ List all trivial fields of the CampaignProviderEdge type """
    return (
    )
def list_trivial_fields_CampaignProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the CampaignProvidersConnection type """
    return (
    )
def list_trivial_fields_Campaign(ds: DSLSchema):
    """ List all trivial fields of the Campaign type """
    return (
        ds.Campaign.id,
        ds.Campaign.name,
        ds.Campaign.description,
        ds.Campaign.targetCompletionTime,
        ds.Campaign.snapshotCreationTime,
        ds.Campaign.stateTransitionedAt,
        ds.Campaign.nextCampaignScheduledDate,
        ds.Campaign.scheduledStart,
    )
def list_trivial_fields_CampaignEvent(ds: DSLSchema):
    """ List all trivial fields of the CampaignEvent type """
    return (
        ds.CampaignEvent.eventAt,
        ds.CampaignEvent.event,
        ds.CampaignEvent.prevState,
        ds.CampaignEvent.nextState,
        ds.CampaignEvent.triggeredByIdentityId,
        ds.CampaignEvent.triggeredByIdentityUsername,
        ds.CampaignEvent.reason,
    )
def list_trivial_fields_CampaignReviewersConnection(ds: DSLSchema):
    """ List all trivial fields of the CampaignReviewersConnection type """
    return (
    )
def list_trivial_fields_CampaignReviewerEdge(ds: DSLSchema):
    """ List all trivial fields of the CampaignReviewerEdge type """
    return (
    )
def list_trivial_fields_AccessReviewerCampaignSummary(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignSummary type """
    return (
    )
def list_trivial_fields_CampaignReviewersGroupedByStatus(ds: DSLSchema):
    """ List all trivial fields of the CampaignReviewersGroupedByStatus type """
    return (
        ds.CampaignReviewersGroupedByStatus.status,
        ds.CampaignReviewersGroupedByStatus.count,
    )
def list_trivial_fields_AccessReviewerCampaignData(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignData type """
    return (
        ds.AccessReviewerCampaignData.id,
        ds.AccessReviewerCampaignData.isReviewerReassigned,
        ds.AccessReviewerCampaignData.originalReviewerAssignmentReason,
    )
def list_trivial_fields_AccessReviewsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsConnection type """
    return (
    )
def list_trivial_fields_AccessReviewEdge(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewEdge type """
    return (
    )
def list_trivial_fields_AccessReviewPolicySnapshot(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewPolicySnapshot type """
    return (
        ds.AccessReviewPolicySnapshot.id,
        ds.AccessReviewPolicySnapshot.name,
        ds.AccessReviewPolicySnapshot.riskLevel,
        ds.AccessReviewPolicySnapshot.blastRisk,
        ds.AccessReviewPolicySnapshot.blastRiskLevel,
        ds.AccessReviewPolicySnapshot.isBlastRiskComputed,
        ds.AccessReviewPolicySnapshot.type,
    )
def list_trivial_fields_AssignmentConfigurationSnapshotData(ds: DSLSchema):
    """ List all trivial fields of the AssignmentConfigurationSnapshotData type """
    return (
        ds.AssignmentConfigurationSnapshotData.assignmentType,
        ds.AssignmentConfigurationSnapshotData.isDirectBinding,
    )
def list_trivial_fields_AccessAssignmentData(ds: DSLSchema):
    """ List all trivial fields of the AccessAssignmentData type """
    return (
        ds.AccessAssignmentData.principalId,
        ds.AccessAssignmentData.principalUsername,
        ds.AccessAssignmentData.identityId,
        ds.AccessAssignmentData.roleName,
    )
def list_trivial_fields_ActivitySnapshot(ds: DSLSchema):
    """ List all trivial fields of the ActivitySnapshot type """
    return (
        ds.ActivitySnapshot.providerId,
        ds.ActivitySnapshot.accountId,
        ds.ActivitySnapshot.timestamp,
        ds.ActivitySnapshot.action,
        ds.ActivitySnapshot.identityIncarnationId,
        ds.ActivitySnapshot.policyId,
        ds.ActivitySnapshot.policyName,
        ds.ActivitySnapshot.accessType,
    )
def list_trivial_fields_AssignmentConfigurationSnapshotConnection(ds: DSLSchema):
    """ List all trivial fields of the AssignmentConfigurationSnapshotConnection type """
    return (
    )
def list_trivial_fields_AssignmentConfigurationSnapshotEdge(ds: DSLSchema):
    """ List all trivial fields of the AssignmentConfigurationSnapshotEdge type """
    return (
    )
def list_trivial_fields_AccessReview(ds: DSLSchema):
    """ List all trivial fields of the AccessReview type """
    return (
        ds.AccessReview.id,
        ds.AccessReview.campaignId,
        ds.AccessReview.campaignName,
        ds.AccessReview.assignedReviewerId,
        ds.AccessReview.assignedReviewerName,
        ds.AccessReview.originalReviewerId,
        ds.AccessReview.originalReviewerName,
        ds.AccessReview.accessReviewerCampaignDataId,
        ds.AccessReview.originalReviewerAssignmentReason,
        ds.AccessReview.hrType,
        ds.AccessReview.department,
    )
def list_trivial_fields_AccessReviewReviewStatus(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewReviewStatus type """
    return (
        ds.AccessReviewReviewStatus.status,
        ds.AccessReviewReviewStatus.reason,
        ds.AccessReviewReviewStatus.updatedAt,
        ds.AccessReviewReviewStatus.updatedById,
        ds.AccessReviewReviewStatus.updatedByIdentityName,
        ds.AccessReviewReviewStatus.updatedByIdentityState,
        ds.AccessReviewReviewStatus.updatedByIdentityEmail,
    )
def list_trivial_fields_CampaignTemplatesConnection(ds: DSLSchema):
    """ List all trivial fields of the CampaignTemplatesConnection type """
    return (
    )
def list_trivial_fields_CampaignTemplateEdge(ds: DSLSchema):
    """ List all trivial fields of the CampaignTemplateEdge type """
    return (
    )
def list_trivial_fields_CampaignTemplate(ds: DSLSchema):
    """ List all trivial fields of the CampaignTemplate type """
    return (
        ds.CampaignTemplate.id,
        ds.CampaignTemplate.name,
        ds.CampaignTemplate.createdAt,
        ds.CampaignTemplate.entitlementType,
        ds.CampaignTemplate.description,
        ds.CampaignTemplate.scheduled,
        ds.CampaignTemplate.fallbackReviewerId,
        ds.CampaignTemplate.disableSelfReview,
    )
def list_trivial_fields_IdentityOpsInsightDataList(ds: DSLSchema):
    """ List all trivial fields of the IdentityOpsInsightDataList type """
    return (
    )
def list_trivial_fields_RiskFactorDataList(ds: DSLSchema):
    """ List all trivial fields of the RiskFactorDataList type """
    return (
    )
def list_trivial_fields_PolicyOpsInsightDataList(ds: DSLSchema):
    """ List all trivial fields of the PolicyOpsInsightDataList type """
    return (
    )
def list_trivial_fields_CampaignUserDataConnection(ds: DSLSchema):
    """ List all trivial fields of the CampaignUserDataConnection type """
    return (
    )
def list_trivial_fields_CampaignUserDataEdge(ds: DSLSchema):
    """ List all trivial fields of the CampaignUserDataEdge type """
    return (
    )
def list_trivial_fields_AccessReviewCampaignScope(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewCampaignScope type """
    return (
    )
def list_trivial_fields_AccessReviewScopeFilter(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewScopeFilter type """
    return (
    )

# End of file: andromeda/nonpublic/graph/campaign_service.proto

# File: andromeda/nonpublic/graph/integration_service.proto
def list_trivial_fields_IntegrationsConnection(ds: DSLSchema):
    """ List all trivial fields of the IntegrationsConnection type """
    return (
    )
def list_trivial_fields_IntegrationEdge(ds: DSLSchema):
    """ List all trivial fields of the IntegrationEdge type """
    return (
    )
def list_trivial_fields_Integration(ds: DSLSchema):
    """ List all trivial fields of the Integration type """
    return (
        ds.Integration.id,
        ds.Integration.name,
        ds.Integration.type,
    )

# End of file: andromeda/nonpublic/graph/integration_service.proto

# File: andromeda/nonpublic/graph/user_behavior_events_service.proto
def list_trivial_fields_UserBehaviorEventsConnection(ds: DSLSchema):
    """ List all trivial fields of the UserBehaviorEventsConnection type """
    return (
    )
def list_trivial_fields_UserBehaviorEventsEdge(ds: DSLSchema):
    """ List all trivial fields of the UserBehaviorEventsEdge type """
    return (
    )
def list_trivial_fields_UserBehaviorEventsNode(ds: DSLSchema):
    """ List all trivial fields of the UserBehaviorEventsNode type """
    return (
        ds.UserBehaviorEventsNode.id,
        ds.UserBehaviorEventsNode.type,
        ds.UserBehaviorEventsNode.subtype,
        ds.UserBehaviorEventsNode.severity,
        ds.UserBehaviorEventsNode.eventTime,
        ds.UserBehaviorEventsNode.summary,
    )
def list_trivial_fields_UserBehaviorEventsOrigin(ds: DSLSchema):
    """ List all trivial fields of the UserBehaviorEventsOrigin type """
    return (
        ds.UserBehaviorEventsOrigin.providerId,
        ds.UserBehaviorEventsOrigin.providerName,
        ds.UserBehaviorEventsOrigin.providerType,
        ds.UserBehaviorEventsOrigin.accountId,
        ds.UserBehaviorEventsOrigin.accountName,
        ds.UserBehaviorEventsOrigin.accountMode,
        ds.UserBehaviorEventsOrigin.identityId,
        ds.UserBehaviorEventsOrigin.policyId,
        ds.UserBehaviorEventsOrigin.location,
        ds.UserBehaviorEventsOrigin.device,
    )

# End of file: andromeda/nonpublic/graph/user_behavior_events_service.proto

# File: andromeda/nonpublic/graph/user_service.proto
def list_trivial_fields_UserOpsInsights(ds: DSLSchema):
    """ List all trivial fields of the UserOpsInsights type """
    return (
        ds.UserOpsInsights.type,
    )
def list_trivial_fields_ProviderUserOpsInsights(ds: DSLSchema):
    """ List all trivial fields of the ProviderUserOpsInsights type """
    return (
        ds.ProviderUserOpsInsights.type,
    )
def list_trivial_fields_AccountUserOpsInsights(ds: DSLSchema):
    """ List all trivial fields of the AccountUserOpsInsights type """
    return (
        ds.AccountUserOpsInsights.type,
    )
def list_trivial_fields_UserConnection(ds: DSLSchema):
    """ List all trivial fields of the UserConnection type """
    return (
    )
def list_trivial_fields_UserEdge(ds: DSLSchema):
    """ List all trivial fields of the UserEdge type """
    return (
    )
def list_trivial_fields_User(ds: DSLSchema):
    """ List all trivial fields of the User type """
    return (
        ds.User.id,
        ds.User.username,
    )
def list_trivial_fields_UserProviderAccessSummary(ds: DSLSchema):
    """ List all trivial fields of the UserProviderAccessSummary type """
    return (
        ds.UserProviderAccessSummary.count,
        ds.UserProviderAccessSummary.providerCategory,
    )
def list_trivial_fields_UserProviderDataConnection(ds: DSLSchema):
    """ List all trivial fields of the UserProviderDataConnection type """
    return (
    )
def list_trivial_fields_UserProviderDataEdge(ds: DSLSchema):
    """ List all trivial fields of the UserProviderDataEdge type """
    return (
    )
def list_trivial_fields_UserProviderData(ds: DSLSchema):
    """ List all trivial fields of the UserProviderData type """
    return (
    )
def list_trivial_fields_UserProviderAccountDataConnection(ds: DSLSchema):
    """ List all trivial fields of the UserProviderAccountDataConnection type """
    return (
    )
def list_trivial_fields_UserProviderAccountDataEdge(ds: DSLSchema):
    """ List all trivial fields of the UserProviderAccountDataEdge type """
    return (
    )
def list_trivial_fields_UserProviderAccountData(ds: DSLSchema):
    """ List all trivial fields of the UserProviderAccountData type """
    return (
    )
def list_trivial_fields_UsersSummary(ds: DSLSchema):
    """ List all trivial fields of the UsersSummary type """
    return (
    )
def list_trivial_fields_UserGroupedByDomain(ds: DSLSchema):
    """ List all trivial fields of the UserGroupedByDomain type """
    return (
        ds.UserGroupedByDomain.domain,
        ds.UserGroupedByDomain.count,
    )

# End of file: andromeda/nonpublic/graph/user_service.proto

# File: andromeda/nonpublic/graph/broker_service.proto
def list_trivial_fields_BrokerConnection(ds: DSLSchema):
    """ List all trivial fields of the BrokerConnection type """
    return (
    )
def list_trivial_fields_BrokersEdge(ds: DSLSchema):
    """ List all trivial fields of the BrokersEdge type """
    return (
    )
def list_trivial_fields_BrokerNode(ds: DSLSchema):
    """ List all trivial fields of the BrokerNode type """
    return (
        ds.BrokerNode.id,
        ds.BrokerNode.name,
        ds.BrokerNode.status,
        ds.BrokerNode.lastCheckedAt,
    )
def list_trivial_fields_BrokerProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the BrokerProvidersConnection type """
    return (
    )
def list_trivial_fields_BrokerProviderEdge(ds: DSLSchema):
    """ List all trivial fields of the BrokerProviderEdge type """
    return (
    )
def list_trivial_fields_BrokerProviderNode(ds: DSLSchema):
    """ List all trivial fields of the BrokerProviderNode type """
    return (
        ds.BrokerProviderNode.id,
        ds.BrokerProviderNode.name,
        ds.BrokerProviderNode.providerType,
        ds.BrokerProviderNode.isAccessible,
        ds.BrokerProviderNode.errorMessage,
        ds.BrokerProviderNode.lastCheckedAt,
    )

# End of file: andromeda/nonpublic/graph/broker_service.proto

# File: andromeda/nonpublic/graph/identity_service.proto
def list_trivial_fields_UnifiedIdentityPolicyDataEdge(ds: DSLSchema):
    """ List all trivial fields of the UnifiedIdentityPolicyDataEdge type """
    return (
    )
def list_trivial_fields_UnifiedIdentityPolicyDataConnection(ds: DSLSchema):
    """ List all trivial fields of the UnifiedIdentityPolicyDataConnection type """
    return (
    )
def list_trivial_fields_UnifiedIdentityPolicyData(ds: DSLSchema):
    """ List all trivial fields of the UnifiedIdentityPolicyData type """
    return (
        ds.UnifiedIdentityPolicyData.policyId,
        ds.UnifiedIdentityPolicyData.policyName,
        ds.UnifiedIdentityPolicyData.policyType,
        ds.UnifiedIdentityPolicyData.blastRisk,
        ds.UnifiedIdentityPolicyData.blastRiskLevel,
        ds.UnifiedIdentityPolicyData.isBlastRiskComputed,
        ds.UnifiedIdentityPolicyData.hasAdminPermissions,
        ds.UnifiedIdentityPolicyData.excessivePrivilegeScore,
        ds.UnifiedIdentityPolicyData.highRiskFrequentlyUsedPermissionsCount,
        ds.UnifiedIdentityPolicyData.highRiskInfrequentlyUsedPermissionsCount,
        ds.UnifiedIdentityPolicyData.highRiskUnusedPermissionsCount,
        ds.UnifiedIdentityPolicyData.lowRiskFrequentlyUsedPermissionsCount,
        ds.UnifiedIdentityPolicyData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.UnifiedIdentityPolicyData.lowRiskUnusedPermissionsCount,
        ds.UnifiedIdentityPolicyData.unusedPermissionsPercentage,
        ds.UnifiedIdentityPolicyData.untrackedPermissionsCount,
        ds.UnifiedIdentityPolicyData.accountId,
        ds.UnifiedIdentityPolicyData.accountName,
        ds.UnifiedIdentityPolicyData.accountMode,
        ds.UnifiedIdentityPolicyData.roleTrustDocument,
    )
def list_trivial_fields_RiskFactorData(ds: DSLSchema):
    """ List all trivial fields of the RiskFactorData type """
    return (
        ds.RiskFactorData.type,
        ds.RiskFactorData.category,
    )
def list_trivial_fields_RiskFactors(ds: DSLSchema):
    """ List all trivial fields of the RiskFactors type """
    return (
        ds.RiskFactors.noMfa,
        ds.RiskFactors.weakMfa,
        ds.RiskFactors.stale,
        ds.RiskFactors.unusualTravel,
        ds.RiskFactors.anomalousCloudActivity,
        ds.RiskFactors.anomalousAppActivity,
        ds.RiskFactors.anomalousLoginActivity,
        ds.RiskFactors.highBlastRisk,
        ds.RiskFactors.passwordHygiene,
        ds.RiskFactors.keyHygiene,
        ds.RiskFactors.accessKeyRotationPastDueDate,
    )
def list_trivial_fields_AccessKeySignificanceData(ds: DSLSchema):
    """ List all trivial fields of the AccessKeySignificanceData type """
    return (
        ds.AccessKeySignificanceData.accessKeyInactive365DaysPlus,
        ds.AccessKeySignificanceData.accessKeyInactive180365Days,
        ds.AccessKeySignificanceData.accessKeyInactive90180Days,
        ds.AccessKeySignificanceData.accessKeyInactive3090Days,
        ds.AccessKeySignificanceData.accessKeyActive,
    )
def list_trivial_fields_AccessData(ds: DSLSchema):
    """ List all trivial fields of the AccessData type """
    return (
    )
def list_trivial_fields_ConsoleAccessData(ds: DSLSchema):
    """ List all trivial fields of the ConsoleAccessData type """
    return (
        ds.ConsoleAccessData.lastUsed,
    )
def list_trivial_fields_ConsoleOpsInsight(ds: DSLSchema):
    """ List all trivial fields of the ConsoleOpsInsight type """
    return (
        ds.ConsoleOpsInsight.type,
        ds.ConsoleOpsInsight.category,
    )
def list_trivial_fields_IdentityOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the IdentityOpsInsightData type """
    return (
        ds.IdentityOpsInsightData.type,
        ds.IdentityOpsInsightData.category,
    )
def list_trivial_fields_IdentitySignificanceData(ds: DSLSchema):
    """ List all trivial fields of the IdentitySignificanceData type """
    return (
        ds.IdentitySignificanceData.isSuperAdmin,
        ds.IdentitySignificanceData.isAccountOwner,
        ds.IdentitySignificanceData.isAccountAdmin,
        ds.IdentitySignificanceData.isRiskAccepted,
        ds.IdentitySignificanceData.isInactive,
        ds.IdentitySignificanceData.isNonCompliant,
        ds.IdentitySignificanceData.isDataInconsistent,
        ds.IdentitySignificanceData.hasCrossAccountWithCriticalityEscalation,
        ds.IdentitySignificanceData.isDeactivatedUserWithPolicyBindings,
        ds.IdentitySignificanceData.isLocalIdentity,
        ds.IdentitySignificanceData.isInactive3090Days,
        ds.IdentitySignificanceData.isInactive90180Days,
        ds.IdentitySignificanceData.isInactive180365Days,
        ds.IdentitySignificanceData.isInactive365DaysPlus,
    )
def list_trivial_fields_Activity(ds: DSLSchema):
    """ List all trivial fields of the Activity type """
    return (
        ds.Activity.providerId,
        ds.Activity.providerName,
        ds.Activity.providerType,
        ds.Activity.providerLogoUrl,
        ds.Activity.providerCategory,
        ds.Activity.accountName,
        ds.Activity.accountId,
        ds.Activity.scopeId,
        ds.Activity.scopeType,
        ds.Activity.timestamp,
        ds.Activity.action,
        ds.Activity.identityIncarnationId,
        ds.Activity.policyId,
        ds.Activity.policyName,
        ds.Activity.accessType,
    )
def list_trivial_fields_KnownLocation(ds: DSLSchema):
    """ List all trivial fields of the KnownLocation type """
    return (
        ds.KnownLocation.timestamp,
    )
def list_trivial_fields_Device(ds: DSLSchema):
    """ List all trivial fields of the Device type """
    return (
        ds.Device.deviceInfo,
        ds.Device.ipAddress,
        ds.Device.os,
        ds.Device.engine,
        ds.Device.architecture,
    )
def list_trivial_fields_KnownDevice(ds: DSLSchema):
    """ List all trivial fields of the KnownDevice type """
    return (
        ds.KnownDevice.timestamp,
    )
def list_trivial_fields_ActivitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the ActivitiesConnection type """
    return (
    )
def list_trivial_fields_KnownLocationsConnection(ds: DSLSchema):
    """ List all trivial fields of the KnownLocationsConnection type """
    return (
    )
def list_trivial_fields_KnownDevicesConnection(ds: DSLSchema):
    """ List all trivial fields of the KnownDevicesConnection type """
    return (
    )
def list_trivial_fields_IdentityProviderDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderDataEdge type """
    return (
    )
def list_trivial_fields_IdentityProvidersDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityProvidersDataConnection type """
    return (
    )
def list_trivial_fields_IdentityProviderData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderData type """
    return (
        ds.IdentityProviderData.providerId,
        ds.IdentityProviderData.providerName,
        ds.IdentityProviderData.type,
        ds.IdentityProviderData.providerCategory,
        ds.IdentityProviderData.providerTierId,
        ds.IdentityProviderData.providerTierName,
        ds.IdentityProviderData.isOwner,
        ds.IdentityProviderData.accountsCount,
        ds.IdentityProviderData.applicationAuthType,
        ds.IdentityProviderData.blastRisk,
        ds.IdentityProviderData.isBlastRiskComputed,
        ds.IdentityProviderData.isSuperAdmin,
        ds.IdentityProviderData.serviceIdentitiesCount,
        ds.IdentityProviderData.accessRequestsCount,
        ds.IdentityProviderData.authType,
        ds.IdentityProviderData.providerState,
        ds.IdentityProviderData.activityCount,
        ds.IdentityProviderData.lastActivityAt,
        ds.IdentityProviderData.accessTypes,
    )
def list_trivial_fields_IdentityProviderMembersMetadata(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderMembersMetadata type """
    return (
        ds.IdentityProviderMembersMetadata.successfulLoginsByUsersCount,
        ds.IdentityProviderMembersMetadata.successfulLoginsCount,
        ds.IdentityProviderMembersMetadata.failedLoginsByUsersCount,
        ds.IdentityProviderMembersMetadata.failedLoginsCount,
        ds.IdentityProviderMembersMetadata.loginsCount,
        ds.IdentityProviderMembersMetadata.loginsByUsersCount,
    )
def list_trivial_fields_IdentityDataIssue(ds: DSLSchema):
    """ List all trivial fields of the IdentityDataIssue type """
    return (
        ds.IdentityDataIssue.type,
        ds.IdentityDataIssue.description,
    )
def list_trivial_fields_IdentityDataIssueEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityDataIssueEdge type """
    return (
    )
def list_trivial_fields_IdentityDataIssueConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityDataIssueConnection type """
    return (
    )
def list_trivial_fields_IdentityInsight(ds: DSLSchema):
    """ List all trivial fields of the IdentityInsight type """
    return (
        ds.IdentityInsight.summary,
    )
def list_trivial_fields_IdentityInsightLocation(ds: DSLSchema):
    """ List all trivial fields of the IdentityInsightLocation type """
    return (
        ds.IdentityInsightLocation.city,
        ds.IdentityInsightLocation.locationState,
        ds.IdentityInsightLocation.country,
        ds.IdentityInsightLocation.countryCode,
        ds.IdentityInsightLocation.zipCode,
        ds.IdentityInsightLocation.streetAddress,
    )
def list_trivial_fields_IdentityHrisData(ds: DSLSchema):
    """ List all trivial fields of the IdentityHrisData type """
    return (
        ds.IdentityHrisData.id,
        ds.IdentityHrisData.name,
        ds.IdentityHrisData.email,
        ds.IdentityHrisData.title,
        ds.IdentityHrisData.positionTitle,
        ds.IdentityHrisData.businessTitle,
        ds.IdentityHrisData.department,
        ds.IdentityHrisData.orgName,
        ds.IdentityHrisData.managerId,
        ds.IdentityHrisData.managerName,
        ds.IdentityHrisData.managerEmail,
        ds.IdentityHrisData.managerTitle,
        ds.IdentityHrisData.hrType,
        ds.IdentityHrisData.hireDate,
        ds.IdentityHrisData.terminationDate,
        ds.IdentityHrisData.category,
        ds.IdentityHrisData.state,
        ds.IdentityHrisData.username,
    )
def list_trivial_fields_IdentityIdpData(ds: DSLSchema):
    """ List all trivial fields of the IdentityIdpData type """
    return (
        ds.IdentityIdpData.id,
        ds.IdentityIdpData.username,
        ds.IdentityIdpData.name,
        ds.IdentityIdpData.email,
        ds.IdentityIdpData.mfaEnabled,
        ds.IdentityIdpData.title,
        ds.IdentityIdpData.managerId,
        ds.IdentityIdpData.managerName,
        ds.IdentityIdpData.managerEmail,
        ds.IdentityIdpData.managerUsername,
        ds.IdentityIdpData.managerTitle,
        ds.IdentityIdpData.department,
        ds.IdentityIdpData.hrType,
        ds.IdentityIdpData.state,
        ds.IdentityIdpData.isPrivilegedUser,
    )
def list_trivial_fields_IdpApplication(ds: DSLSchema):
    """ List all trivial fields of the IdpApplication type """
    return (
        ds.IdpApplication.applicationOriginId,
        ds.IdpApplication.applicationName,
    )
def list_trivial_fields_AwsExternalId(ds: DSLSchema):
    """ List all trivial fields of the AwsExternalId type """
    return (
        ds.AwsExternalId.id,
        ds.AwsExternalId.issuer,
    )
def list_trivial_fields_IdentityProviderIdpSsoData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderIdpSsoData type """
    return (
        ds.IdentityProviderIdpSsoData.username,
        ds.IdentityProviderIdpSsoData.idpProviderId,
        ds.IdentityProviderIdpSsoData.idpProviderName,
        ds.IdentityProviderIdpSsoData.state,
    )
def list_trivial_fields_IdentityAwsIdcData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAwsIdcData type """
    return (
        ds.IdentityAwsIdcData.username,
        ds.IdentityAwsIdcData.name,
        ds.IdentityAwsIdcData.id,
        ds.IdentityAwsIdcData.email,
        ds.IdentityAwsIdcData.title,
        ds.IdentityAwsIdcData.scimType,
        ds.IdentityAwsIdcData.userType,
        ds.IdentityAwsIdcData.state,
    )
def list_trivial_fields_IdentityAzureData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAzureData type """
    return (
        ds.IdentityAzureData.username,
        ds.IdentityAzureData.name,
        ds.IdentityAzureData.id,
        ds.IdentityAzureData.azureObjectId,
        ds.IdentityAzureData.email,
        ds.IdentityAzureData.title,
        ds.IdentityAzureData.state,
    )
def list_trivial_fields_IdentityApplicationData(ds: DSLSchema):
    """ List all trivial fields of the IdentityApplicationData type """
    return (
        ds.IdentityApplicationData.username,
        ds.IdentityApplicationData.name,
        ds.IdentityApplicationData.id,
        ds.IdentityApplicationData.applicationObjectId,
        ds.IdentityApplicationData.email,
        ds.IdentityApplicationData.state,
        ds.IdentityApplicationData.applicationType,
    )
def list_trivial_fields_OrganizationInfo(ds: DSLSchema):
    """ List all trivial fields of the OrganizationInfo type """
    return (
        ds.OrganizationInfo.employeeId,
        ds.OrganizationInfo.orgName,
        ds.OrganizationInfo.businessTitle,
        ds.OrganizationInfo.managerId,
        ds.OrganizationInfo.managerName,
        ds.OrganizationInfo.positionTitle,
        ds.OrganizationInfo.department,
        ds.OrganizationInfo.city,
        ds.OrganizationInfo.country,
        ds.OrganizationInfo.hrType,
    )
def list_trivial_fields_IdentityAwsIamData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAwsIamData type """
    return (
        ds.IdentityAwsIamData.id,
        ds.IdentityAwsIamData.username,
        ds.IdentityAwsIamData.arn,
        ds.IdentityAwsIamData.path,
        ds.IdentityAwsIamData.originProviderId,
        ds.IdentityAwsIamData.originProviderName,
        ds.IdentityAwsIamData.consoleAccess,
        ds.IdentityAwsIamData.state,
        ds.IdentityAwsIamData.name,
    )
def list_trivial_fields_AccessKeyData(ds: DSLSchema):
    """ List all trivial fields of the AccessKeyData type """
    return (
        ds.AccessKeyData.id,
        ds.AccessKeyData.keyId,
        ds.AccessKeyData.name,
        ds.AccessKeyData.createdAt,
        ds.AccessKeyData.lastUsed,
        ds.AccessKeyData.keyRotationPastDueDays,
        ds.AccessKeyData.status,
        ds.AccessKeyData.keyRotationDueAt,
        ds.AccessKeyData.identityOriginType,
        ds.AccessKeyData.keyType,
    )
def list_trivial_fields_KeyRiskData(ds: DSLSchema):
    """ List all trivial fields of the KeyRiskData type """
    return (
        ds.KeyRiskData.type,
        ds.KeyRiskData.category,
    )
def list_trivial_fields_KeyOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the KeyOpsInsightData type """
    return (
        ds.KeyOpsInsightData.type,
        ds.KeyOpsInsightData.category,
    )
def list_trivial_fields_MfaData(ds: DSLSchema):
    """ List all trivial fields of the MfaData type """
    return (
        ds.MfaData.mfaFactorId,
        ds.MfaData.factorType,
        ds.MfaData.mfaCreatedAt,
        ds.MfaData.mfaStrength,
    )
def list_trivial_fields_IdentityOrgInfo(ds: DSLSchema):
    """ List all trivial fields of the IdentityOrgInfo type """
    return (
        ds.IdentityOrgInfo.hrType,
        ds.IdentityOrgInfo.hireDate,
        ds.IdentityOrgInfo.terminationDate,
        ds.IdentityOrgInfo.orgName,
        ds.IdentityOrgInfo.managerName,
        ds.IdentityOrgInfo.managerId,
        ds.IdentityOrgInfo.department,
        ds.IdentityOrgInfo.title,
        ds.IdentityOrgInfo.managerUuid,
    )
def list_trivial_fields_IdentityOriginData(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginData type """
    return (
        ds.IdentityOriginData.identityOriginType,
        ds.IdentityOriginData.originId,
        ds.IdentityOriginData.originName,
        ds.IdentityOriginData.isReference,
        ds.IdentityOriginData.isSourceOfTruth,
        ds.IdentityOriginData.hasIncarnation,
        ds.IdentityOriginData.originUserId,
        ds.IdentityOriginData.originUserName,
        ds.IdentityOriginData.originUserUsername,
        ds.IdentityOriginData.userCreatedAt,
        ds.IdentityOriginData.lastUpdatedAt,
        ds.IdentityOriginData.lastLoginAt,
        ds.IdentityOriginData.passwordLastUsed,
        ds.IdentityOriginData.state,
        ds.IdentityOriginData.providerId,
        ds.IdentityOriginData.providerName,
        ds.IdentityOriginData.originUserExternalId,
        ds.IdentityOriginData.originUserEmail,
        ds.IdentityOriginData.isIncarnation,
        ds.IdentityOriginData.isPrivilegedUser,
        ds.IdentityOriginData.consoleAccess,
    )
def list_trivial_fields_IdentityOriginDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginDataEdge type """
    return (
    )
def list_trivial_fields_IdentityOriginDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginDataConnection type """
    return (
    )
def list_trivial_fields_ProviderOwnershipSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderOwnershipSummary type """
    return (
        ds.ProviderOwnershipSummary.id,
        ds.ProviderOwnershipSummary.name,
        ds.ProviderOwnershipSummary.type,
    )
def list_trivial_fields_IdentityProvidersSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentityProvidersSummary type """
    return (
    )
def list_trivial_fields_AccountOwnershipSummary(ds: DSLSchema):
    """ List all trivial fields of the AccountOwnershipSummary type """
    return (
        ds.AccountOwnershipSummary.accountId,
        ds.AccountOwnershipSummary.accountName,
        ds.AccountOwnershipSummary.providerId,
        ds.AccountOwnershipSummary.providerName,
        ds.AccountOwnershipSummary.providerType,
    )
def list_trivial_fields_IdentityAccountSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccountSummary type """
    return (
    )
def list_trivial_fields_IdentityAccountsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccountsDataConnection type """
    return (
    )
def list_trivial_fields_IdentityAccountDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccountDataEdge type """
    return (
    )
def list_trivial_fields_IdentityGroupData(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupData type """
    return (
        ds.IdentityGroupData.id,
        ds.IdentityGroupData.name,
        ds.IdentityGroupData.type,
        ds.IdentityGroupData.lastUpdatedAt,
        ds.IdentityGroupData.groupCreatedAt,
        ds.IdentityGroupData.membershipModifiedAt,
    )
def list_trivial_fields_IdentityGroupDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupDataEdge type """
    return (
    )
def list_trivial_fields_IdentityGroupsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupsDataConnection type """
    return (
    )
def list_trivial_fields_Group(ds: DSLSchema):
    """ List all trivial fields of the Group type """
    return (
        ds.Group.id,
        ds.Group.name,
        ds.Group.externalId,
        ds.Group.type,
        ds.Group.groupType,
        ds.Group.isReference,
        ds.Group.lastUpdatedAt,
        ds.Group.groupCreatedAt,
    )
def list_trivial_fields_GroupProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the GroupProvidersConnection type """
    return (
    )
def list_trivial_fields_GroupProviderEdge(ds: DSLSchema):
    """ List all trivial fields of the GroupProviderEdge type """
    return (
    )
def list_trivial_fields_GroupProviderData(ds: DSLSchema):
    """ List all trivial fields of the GroupProviderData type """
    return (
    )
def list_trivial_fields_GroupProviderAccountDataConnection(ds: DSLSchema):
    """ List all trivial fields of the GroupProviderAccountDataConnection type """
    return (
    )
def list_trivial_fields_GroupProviderAccountDataEdge(ds: DSLSchema):
    """ List all trivial fields of the GroupProviderAccountDataEdge type """
    return (
    )
def list_trivial_fields_GroupProviderAccountData(ds: DSLSchema):
    """ List all trivial fields of the GroupProviderAccountData type """
    return (
    )
def list_trivial_fields_GroupHumanMembersDataConnection(ds: DSLSchema):
    """ List all trivial fields of the GroupHumanMembersDataConnection type """
    return (
    )
def list_trivial_fields_GroupHumanMembersDataEdge(ds: DSLSchema):
    """ List all trivial fields of the GroupHumanMembersDataEdge type """
    return (
        ds.GroupHumanMembersDataEdge.bindingType,
    )
def list_trivial_fields_GroupHumanMembersData(ds: DSLSchema):
    """ List all trivial fields of the GroupHumanMembersData type """
    return (
    )
def list_trivial_fields_GroupNonHumanMembersDataConnection(ds: DSLSchema):
    """ List all trivial fields of the GroupNonHumanMembersDataConnection type """
    return (
    )
def list_trivial_fields_GroupNonHumanMembersDataEdge(ds: DSLSchema):
    """ List all trivial fields of the GroupNonHumanMembersDataEdge type """
    return (
        ds.GroupNonHumanMembersDataEdge.node,
    )
def list_trivial_fields_GroupNonHumanMembersData(ds: DSLSchema):
    """ List all trivial fields of the GroupNonHumanMembersData type """
    return (
    )
def list_trivial_fields_GroupMembers(ds: DSLSchema):
    """ List all trivial fields of the GroupMembers type """
    return (
    )
def list_trivial_fields_GroupDataEdge(ds: DSLSchema):
    """ List all trivial fields of the GroupDataEdge type """
    return (
    )
def list_trivial_fields_GroupsConnection(ds: DSLSchema):
    """ List all trivial fields of the GroupsConnection type """
    return (
    )
def list_trivial_fields_IdentityAccessRequestDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestDataConnection type """
    return (
    )
def list_trivial_fields_IdentityAccessRequestDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestDataEdge type """
    return (
    )
def list_trivial_fields_IdentityActiveAccessRequestDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityActiveAccessRequestDataConnection type """
    return (
    )
def list_trivial_fields_IdentityAccessRequestData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestData type """
    return (
        ds.IdentityAccessRequestData.requestId,
        ds.IdentityAccessRequestData.policyId,
        ds.IdentityAccessRequestData.policyName,
        ds.IdentityAccessRequestData.policyType,
        ds.IdentityAccessRequestData.accountId,
        ds.IdentityAccessRequestData.accountName,
        ds.IdentityAccessRequestData.startTime,
        ds.IdentityAccessRequestData.updatedAt,
        ds.IdentityAccessRequestData.createdAt,
        ds.IdentityAccessRequestData.duration,
        ds.IdentityAccessRequestData.tags,
        ds.IdentityAccessRequestData.description,
        ds.IdentityAccessRequestData.type,
        ds.IdentityAccessRequestData.expiresIn,
        ds.IdentityAccessRequestData.accountMode,
        ds.IdentityAccessRequestData.assignmentType,
        ds.IdentityAccessRequestData.accessGroupId,
    )
def list_trivial_fields_AccessRequestResourceData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestResourceData type """
    return (
        ds.AccessRequestResourceData.name,
    )
def list_trivial_fields_IdentityAccessRequestRequesterUserData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestRequesterUserData type """
    return (
        ds.IdentityAccessRequestRequesterUserData.id,
        ds.IdentityAccessRequestRequesterUserData.name,
        ds.IdentityAccessRequestRequesterUserData.userName,
        ds.IdentityAccessRequestRequesterUserData.identityOriginType,
    )
def list_trivial_fields_IdentityAccessRequestRequesterData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestRequesterData type """
    return (
        ds.IdentityAccessRequestRequesterData.id,
        ds.IdentityAccessRequestRequesterData.type,
        ds.IdentityAccessRequestRequesterData.name,
    )
def list_trivial_fields_IdentityAccessRequestReviewData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestReviewData type """
    return (
        ds.IdentityAccessRequestReviewData.email,
        ds.IdentityAccessRequestReviewData.name,
        ds.IdentityAccessRequestReviewData.status,
        ds.IdentityAccessRequestReviewData.reason,
        ds.IdentityAccessRequestReviewData.reviewerId,
        ds.IdentityAccessRequestReviewData.reviewerType,
        ds.IdentityAccessRequestReviewData.reviewLevel,
        ds.IdentityAccessRequestReviewData.updatedAt,
    )
def list_trivial_fields_ProviderDetailsData(ds: DSLSchema):
    """ List all trivial fields of the ProviderDetailsData type """
    return (
        ds.ProviderDetailsData.id,
        ds.ProviderDetailsData.name,
        ds.ProviderDetailsData.type,
    )
def list_trivial_fields_IdentityAccountData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccountData type """
    return (
        ds.IdentityAccountData.accountId,
        ds.IdentityAccountData.accountName,
        ds.IdentityAccountData.isOwner,
        ds.IdentityAccountData.blastRisk,
        ds.IdentityAccountData.blastRiskLevel,
        ds.IdentityAccountData.isBlastRiskComputed,
        ds.IdentityAccountData.highRiskFrequentlyUsedPermissionsCount,
        ds.IdentityAccountData.highRiskInfrequentlyUsedPermissionsCount,
        ds.IdentityAccountData.highRiskUnusedPermissionsCount,
        ds.IdentityAccountData.lowRiskFrequentlyUsedPermissionsCount,
        ds.IdentityAccountData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.IdentityAccountData.lowRiskUnusedPermissionsCount,
        ds.IdentityAccountData.untrackedPermissionsCount,
        ds.IdentityAccountData.totalPermissions,
        ds.IdentityAccountData.excessivePrivilegeScore,
        ds.IdentityAccountData.unusedPermissionsPercentage,
        ds.IdentityAccountData.isAdmin,
        ds.IdentityAccountData.isRiskAccepted,
        ds.IdentityAccountData.servicesUsed,
        ds.IdentityAccountData.mode,
        ds.IdentityAccountData.accountProviderId,
        ds.IdentityAccountData.identityAccountState,
        ds.IdentityAccountData.computedBlastRisk,
        ds.IdentityAccountData.computedBlastRiskLevel,
        ds.IdentityAccountData.activityCount,
        ds.IdentityAccountData.lastActivityAt,
        ds.IdentityAccountData.accessTypes,
    )
def list_trivial_fields_IdentityOriginAccountsSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginAccountsSummary type """
    return (
        ds.IdentityOriginAccountsSummary.isGlobal,
        ds.IdentityOriginAccountsSummary.localCount,
        ds.IdentityOriginAccountsSummary.crossAccountCount,
    )
def list_trivial_fields_CrossAccountInfo(ds: DSLSchema):
    """ List all trivial fields of the CrossAccountInfo type """
    return (
        ds.CrossAccountInfo.id,
        ds.CrossAccountInfo.name,
    )
def list_trivial_fields_IdentityOriginAccountData(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginAccountData type """
    return (
        ds.IdentityOriginAccountData.identityOriginType,
        ds.IdentityOriginAccountData.username,
        ds.IdentityOriginAccountData.arn,
        ds.IdentityOriginAccountData.isCrossAccount,
    )
def list_trivial_fields_IdentityOriginAccountDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginAccountDataEdge type """
    return (
    )
def list_trivial_fields_IdentityOriginAccountDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityOriginAccountDataConnection type """
    return (
    )
def list_trivial_fields_IdentityReviewRequestDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityReviewRequestDataConnection type """
    return (
    )
def list_trivial_fields_IdentityReviewRequestDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityReviewRequestDataEdge type """
    return (
    )
def list_trivial_fields_IdentityReviewRequestData(ds: DSLSchema):
    """ List all trivial fields of the IdentityReviewRequestData type """
    return (
        ds.IdentityReviewRequestData.reviewId,
        ds.IdentityReviewRequestData.status,
        ds.IdentityReviewRequestData.reason,
        ds.IdentityReviewRequestData.updatedAt,
    )
def list_trivial_fields_IdentityAccountsSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccountsSummary type """
    return (
    )
def list_trivial_fields_IdentityPolicyEligibilityDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyEligibilityDataConnection type """
    return (
    )
def list_trivial_fields_IdentityPolicyEligibilityDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyEligibilityDataEdge type """
    return (
    )
def list_trivial_fields_IdentityPolicyEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyEligibilityData type """
    return (
        ds.IdentityPolicyEligibilityData.policyId,
        ds.IdentityPolicyEligibilityData.policyName,
        ds.IdentityPolicyEligibilityData.policyType,
        ds.IdentityPolicyEligibilityData.accountId,
        ds.IdentityPolicyEligibilityData.accountName,
        ds.IdentityPolicyEligibilityData.identityId,
        ds.IdentityPolicyEligibilityData.providerId,
        ds.IdentityPolicyEligibilityData.eligibilityIds,
        ds.IdentityPolicyEligibilityData.bindingType,
        ds.IdentityPolicyEligibilityData.blastRisk,
    )
def list_trivial_fields_EligibleResourceGroupEdge(ds: DSLSchema):
    """ List all trivial fields of the EligibleResourceGroupEdge type """
    return (
    )
def list_trivial_fields_EligibleResourceGroupsConnection(ds: DSLSchema):
    """ List all trivial fields of the EligibleResourceGroupsConnection type """
    return (
    )
def list_trivial_fields_EligibleResourceGroup(ds: DSLSchema):
    """ List all trivial fields of the EligibleResourceGroup type """
    return (
        ds.EligibleResourceGroup.id,
        ds.EligibleResourceGroup.name,
        ds.EligibleResourceGroup.eligibilityId,
    )
def list_trivial_fields_EligibleUserIncarnationsConnection(ds: DSLSchema):
    """ List all trivial fields of the EligibleUserIncarnationsConnection type """
    return (
    )
def list_trivial_fields_EligibleUserIncarnationEdge(ds: DSLSchema):
    """ List all trivial fields of the EligibleUserIncarnationEdge type """
    return (
    )
def list_trivial_fields_EligibleUserIncarnation(ds: DSLSchema):
    """ List all trivial fields of the EligibleUserIncarnation type """
    return (
        ds.EligibleUserIncarnation.userId,
        ds.EligibleUserIncarnation.name,
        ds.EligibleUserIncarnation.username,
        ds.EligibleUserIncarnation.identityOriginType,
    )
def list_trivial_fields_IdentityPolicyEligibilityConstraints(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyEligibilityConstraints type """
    return (
        ds.IdentityPolicyEligibilityConstraints.scopeType,
    )
def list_trivial_fields_PolicyAccessRequestProfile(ds: DSLSchema):
    """ List all trivial fields of the PolicyAccessRequestProfile type """
    return (
        ds.PolicyAccessRequestProfile.policyRequestReviewers,
    )
def list_trivial_fields_PolicyRequestReviewer(ds: DSLSchema):
    """ List all trivial fields of the PolicyRequestReviewer type """
    return (
        ds.PolicyRequestReviewer.level,
        ds.PolicyRequestReviewer.minimumRequiredApprovals,
    )
def list_trivial_fields_ReviewerDetails(ds: DSLSchema):
    """ List all trivial fields of the ReviewerDetails type """
    return (
        ds.ReviewerDetails.name,
        ds.ReviewerDetails.email,
    )
def list_trivial_fields_IdentityAccessRequestSummaryData(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestSummaryData type """
    return (
    )
def list_trivial_fields_IdentityActiveAccessRequestSummaryData(ds: DSLSchema):
    """ List all trivial fields of the IdentityActiveAccessRequestSummaryData type """
    return (
        ds.IdentityActiveAccessRequestSummaryData.requestId,
        ds.IdentityActiveAccessRequestSummaryData.startTime,
        ds.IdentityActiveAccessRequestSummaryData.duration,
        ds.IdentityActiveAccessRequestSummaryData.type,
        ds.IdentityActiveAccessRequestSummaryData.accountName,
        ds.IdentityActiveAccessRequestSummaryData.requesterName,
    )
def list_trivial_fields_IdentityAccessRequestSummaryByType(ds: DSLSchema):
    """ List all trivial fields of the IdentityAccessRequestSummaryByType type """
    return (
        ds.IdentityAccessRequestSummaryByType.type,
        ds.IdentityAccessRequestSummaryByType.completedCount,
    )
def list_trivial_fields_IdentityPoliciesDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityPoliciesDataConnection type """
    return (
    )
def list_trivial_fields_IdentityPolicyDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyDataEdge type """
    return (
    )
def list_trivial_fields_IdentityPolicyData(ds: DSLSchema):
    """ List all trivial fields of the IdentityPolicyData type """
    return (
        ds.IdentityPolicyData.policyId,
        ds.IdentityPolicyData.policyName,
        ds.IdentityPolicyData.policyType,
        ds.IdentityPolicyData.blastRisk,
        ds.IdentityPolicyData.blastRiskLevel,
        ds.IdentityPolicyData.isBlastRiskComputed,
        ds.IdentityPolicyData.policyLastUsedAt,
        ds.IdentityPolicyData.policyLastUsedAtDataSource,
        ds.IdentityPolicyData.hasAdminPermissions,
        ds.IdentityPolicyData.excessivePrivilegeScore,
        ds.IdentityPolicyData.highRiskFrequentlyUsedPermissionsCount,
        ds.IdentityPolicyData.highRiskInfrequentlyUsedPermissionsCount,
        ds.IdentityPolicyData.highRiskUnusedPermissionsCount,
        ds.IdentityPolicyData.lowRiskFrequentlyUsedPermissionsCount,
        ds.IdentityPolicyData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.IdentityPolicyData.lowRiskUnusedPermissionsCount,
        ds.IdentityPolicyData.unusedPermissionsPercentage,
        ds.IdentityPolicyData.untrackedPermissionsCount,
        ds.IdentityPolicyData.roleTrustDocument,
    )
def list_trivial_fields_PermissionsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the PermissionsDataConnection type """
    return (
    )
def list_trivial_fields_PermissionsDataEdge(ds: DSLSchema):
    """ List all trivial fields of the PermissionsDataEdge type """
    return (
    )
def list_trivial_fields_PermissionsData(ds: DSLSchema):
    """ List all trivial fields of the PermissionsData type """
    return (
        ds.PermissionsData.permissionName,
        ds.PermissionsData.riskLevel,
        ds.PermissionsData.accessLevel,
        ds.PermissionsData.serviceName,
        ds.PermissionsData.used,
        ds.PermissionsData.usageLevel,
    )
def list_trivial_fields_UnifiedIdentityAccountPolicyRecommendation(ds: DSLSchema):
    """ List all trivial fields of the UnifiedIdentityAccountPolicyRecommendation type """
    return (
        ds.UnifiedIdentityAccountPolicyRecommendation.jsonData,
        ds.UnifiedIdentityAccountPolicyRecommendation.blastRisk,
        ds.UnifiedIdentityAccountPolicyRecommendation.blastRiskLevel,
        ds.UnifiedIdentityAccountPolicyRecommendation.recommendedPolicyName,
        ds.UnifiedIdentityAccountPolicyRecommendation.providerPolicyType,
        ds.UnifiedIdentityAccountPolicyRecommendation.responseType,
    )
def list_trivial_fields_AccountPolicyDetailsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyDetailsConnection type """
    return (
    )
def list_trivial_fields_AccountPolicyDetailsEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyDetailsEdge type """
    return (
    )
def list_trivial_fields_AccountPolicyDetails(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyDetails type """
    return (
        ds.AccountPolicyDetails.externalId,
        ds.AccountPolicyDetails.name,
        ds.AccountPolicyDetails.type,
        ds.AccountPolicyDetails.jsonData,
    )
def list_trivial_fields_PermissionsSummary(ds: DSLSchema):
    """ List all trivial fields of the PermissionsSummary type """
    return (
        ds.PermissionsSummary.totalPermissionsCount,
        ds.PermissionsSummary.usedPermissionsCount,
        ds.PermissionsSummary.unusedPermissionsCount,
        ds.PermissionsSummary.highRiskPermissionsCount,
        ds.PermissionsSummary.lowRiskPermissionsCount,
        ds.PermissionsSummary.unusedPermissionsPercentage,
        ds.PermissionsSummary.untrackedPermissionsCount,
    )
def list_trivial_fields_PermissionsAccessLevelSummary(ds: DSLSchema):
    """ List all trivial fields of the PermissionsAccessLevelSummary type """
    return (
        ds.PermissionsAccessLevelSummary.accessLevel,
        ds.PermissionsAccessLevelSummary.totalPermissionsCount,
        ds.PermissionsAccessLevelSummary.usedPermissionsCount,
        ds.PermissionsAccessLevelSummary.unusedPermissionsCount,
        ds.PermissionsAccessLevelSummary.highRiskPermissionsCount,
        ds.PermissionsAccessLevelSummary.lowRiskPermissionsCount,
        ds.PermissionsAccessLevelSummary.untrackedPermissionsCount,
    )
def list_trivial_fields_IdentityPermissionsDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityPermissionsDataConnection type """
    return (
    )
def list_trivial_fields_IdentityPermissionsDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityPermissionsDataEdge type """
    return (
    )
def list_trivial_fields_IdentityPermissionsData(ds: DSLSchema):
    """ List all trivial fields of the IdentityPermissionsData type """
    return (
        ds.IdentityPermissionsData.permissionName,
        ds.IdentityPermissionsData.riskLevel,
        ds.IdentityPermissionsData.accessLevel,
        ds.IdentityPermissionsData.serviceName,
        ds.IdentityPermissionsData.used,
        ds.IdentityPermissionsData.usageLevel,
    )
def list_trivial_fields_RiskAccessLevels(ds: DSLSchema):
    """ List all trivial fields of the RiskAccessLevels type """
    return (
        ds.RiskAccessLevels.accessLevelUnspecifiedCount,
        ds.RiskAccessLevels.accessLevelListCount,
        ds.RiskAccessLevels.accessLevelWriteTagCount,
        ds.RiskAccessLevels.accessLevelDeleteTagCount,
        ds.RiskAccessLevels.accessLevelReadMetadataCount,
        ds.RiskAccessLevels.accessLevelReadDataCount,
        ds.RiskAccessLevels.accessLevelWriteMetadataCount,
        ds.RiskAccessLevels.accessLevelCreateCount,
        ds.RiskAccessLevels.accessLevelWriteDataCount,
        ds.RiskAccessLevels.accessLevelDeleteDataCount,
        ds.RiskAccessLevels.accessLevelDeleteCount,
        ds.RiskAccessLevels.accessLevelPermissionsManagementCount,
    )
def list_trivial_fields_IdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentitiesConnection type """
    return (
        ds.IdentitiesConnection.identityIds,
    )
def list_trivial_fields_IdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the IdentitiesSummary type """
    return (
    )
def list_trivial_fields_Identity(ds: DSLSchema):
    """ List all trivial fields of the Identity type """
    return (
        ds.Identity.id,
        ds.Identity.name,
        ds.Identity.username,
        ds.Identity.email,
        ds.Identity.state,
        ds.Identity.type,
        ds.Identity.blastRisk,
        ds.Identity.blastRiskLevel,
        ds.Identity.isBlastRiskComputed,
        ds.Identity.risk,
        ds.Identity.riskLevel,
        ds.Identity.isSuperAdmin,
        ds.Identity.activityCount,
        ds.Identity.lastActivityAt,
        ds.Identity.createdAt,
        ds.Identity.lastUpdatedAt,
    )
def list_trivial_fields_AccessKeysDataEdge(ds: DSLSchema):
    """ List all trivial fields of the AccessKeysDataEdge type """
    return (
    )
def list_trivial_fields_AccessKeyDataConnection(ds: DSLSchema):
    """ List all trivial fields of the AccessKeyDataConnection type """
    return (
        ds.AccessKeyDataConnection.accessKeyIds,
    )
def list_trivial_fields_AccessKeysSummary(ds: DSLSchema):
    """ List all trivial fields of the AccessKeysSummary type """
    return (
        ds.AccessKeysSummary.rotationPastDueCount,
        ds.AccessKeysSummary.accessKeysCount,
        ds.AccessKeysSummary.accessKeyInactive365DaysPlus,
        ds.AccessKeysSummary.accessKeyInactive180365Days,
        ds.AccessKeysSummary.accessKeyInactive90180Days,
        ds.AccessKeysSummary.accessKeyInactive3090Days,
    )
def list_trivial_fields_PoliciesSummary(ds: DSLSchema):
    """ List all trivial fields of the PoliciesSummary type """
    return (
    )
def list_trivial_fields_IdentityGroupedByRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByRiskLevel type """
    return (
        ds.IdentityGroupedByRiskLevel.riskLevel,
        ds.IdentityGroupedByRiskLevel.count,
    )
def list_trivial_fields_IdentityGroupedByBlastRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByBlastRiskLevel type """
    return (
        ds.IdentityGroupedByBlastRiskLevel.blastRiskLevel,
        ds.IdentityGroupedByBlastRiskLevel.count,
    )
def list_trivial_fields_IdentityGroupedByHrType(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByHrType type """
    return (
        ds.IdentityGroupedByHrType.hrType,
        ds.IdentityGroupedByHrType.count,
    )
def list_trivial_fields_IdentityGroupedByRiskLevelAndHrType(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByRiskLevelAndHrType type """
    return (
        ds.IdentityGroupedByRiskLevelAndHrType.hrType,
        ds.IdentityGroupedByRiskLevelAndHrType.riskLevel,
        ds.IdentityGroupedByRiskLevelAndHrType.count,
    )
def list_trivial_fields_IdentityGroupedByGeo(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByGeo type """
    return (
        ds.IdentityGroupedByGeo.count,
    )
def list_trivial_fields_IdentityGroupedByJml(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByJml type """
    return (
        ds.IdentityGroupedByJml.jml,
        ds.IdentityGroupedByJml.count,
    )
def list_trivial_fields_IdentityGroupedByRiskFactor(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByRiskFactor type """
    return (
        ds.IdentityGroupedByRiskFactor.factor,
        ds.IdentityGroupedByRiskFactor.type,
        ds.IdentityGroupedByRiskFactor.count,
    )
def list_trivial_fields_IdentityGroupedByRiskCategory(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByRiskCategory type """
    return (
        ds.IdentityGroupedByRiskCategory.category,
        ds.IdentityGroupedByRiskCategory.count,
    )
def list_trivial_fields_IdentityGroupedByRiskCategorySummary(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByRiskCategorySummary type """
    return (
        ds.IdentityGroupedByRiskCategorySummary.count,
    )
def list_trivial_fields_IdentityGroupedByState(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByState type """
    return (
        ds.IdentityGroupedByState.state,
        ds.IdentityGroupedByState.count,
    )
def list_trivial_fields_HighRiskIdentityGroupedByChanges(ds: DSLSchema):
    """ List all trivial fields of the HighRiskIdentityGroupedByChanges type """
    return (
        ds.HighRiskIdentityGroupedByChanges.changeType,
        ds.HighRiskIdentityGroupedByChanges.count,
    )
def list_trivial_fields_IdentityGroupedByAccessKeysCount(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByAccessKeysCount type """
    return (
        ds.IdentityGroupedByAccessKeysCount.singleAccessKeyCount,
        ds.IdentityGroupedByAccessKeysCount.multipleAccessKeysCount,
    )
def list_trivial_fields_IdentityGroupedByMfaStrength(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByMfaStrength type """
    return (
        ds.IdentityGroupedByMfaStrength.mfaStrength,
        ds.IdentityGroupedByMfaStrength.count,
    )
def list_trivial_fields_IdentityGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedBySignificance type """
    return (
        ds.IdentityGroupedBySignificance.significance,
        ds.IdentityGroupedBySignificance.count,
    )
def list_trivial_fields_IdentityGroupedByEnvironment(ds: DSLSchema):
    """ List all trivial fields of the IdentityGroupedByEnvironment type """
    return (
        ds.IdentityGroupedByEnvironment.environment,
        ds.IdentityGroupedByEnvironment.count,
    )
def list_trivial_fields_IdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityEdge type """
    return (
    )
def list_trivial_fields_ActivityEdge(ds: DSLSchema):
    """ List all trivial fields of the ActivityEdge type """
    return (
    )
def list_trivial_fields_PrincipalData(ds: DSLSchema):
    """ List all trivial fields of the PrincipalData type """
    return (
        ds.PrincipalData.type,
        ds.PrincipalData.id,
        ds.PrincipalData.name,
        ds.PrincipalData.providerId,
        ds.PrincipalData.integrationId,
        ds.PrincipalData.accountId,
        ds.PrincipalData.accountName,
        ds.PrincipalData.principalOriginType,
        ds.PrincipalData.idInOrigin,
        ds.PrincipalData.identityId,
    )
def list_trivial_fields_TrustEdges(ds: DSLSchema):
    """ List all trivial fields of the TrustEdges type """
    return (
        ds.TrustEdges.type,
        ds.TrustEdges.policyBindingType,
        ds.TrustEdges.isAndromedaManaged,
        ds.TrustEdges.status,
    )
def list_trivial_fields_IncomingTrustEdge(ds: DSLSchema):
    """ List all trivial fields of the IncomingTrustEdge type """
    return (
    )
def list_trivial_fields_IncomingTrustsConnection(ds: DSLSchema):
    """ List all trivial fields of the IncomingTrustsConnection type """
    return (
    )
def list_trivial_fields_OutgoingTrust(ds: DSLSchema):
    """ List all trivial fields of the OutgoingTrust type """
    return (
        ds.OutgoingTrust.principalAccountId,
        ds.OutgoingTrust.principalAccountName,
        ds.OutgoingTrust.principalAccountMode,
        ds.OutgoingTrust.principalId,
        ds.OutgoingTrust.principalName,
    )
def list_trivial_fields_OutgoingTrustEdge(ds: DSLSchema):
    """ List all trivial fields of the OutgoingTrustEdge type """
    return (
    )
def list_trivial_fields_OutgoingTrustsConnection(ds: DSLSchema):
    """ List all trivial fields of the OutgoingTrustsConnection type """
    return (
    )
def list_trivial_fields_KnownLocationEdge(ds: DSLSchema):
    """ List all trivial fields of the KnownLocationEdge type """
    return (
    )
def list_trivial_fields_KnownDeviceEdge(ds: DSLSchema):
    """ List all trivial fields of the KnownDeviceEdge type """
    return (
    )
def list_trivial_fields_StandingPoliciesInfo(ds: DSLSchema):
    """ List all trivial fields of the StandingPoliciesInfo type """
    return (
        ds.StandingPoliciesInfo.totalStandingPolicies,
        ds.StandingPoliciesInfo.totalStandingPoliciesViaLateralMovement,
        ds.StandingPoliciesInfo.totalUnusedPolicies,
    )
def list_trivial_fields_PoliciesGroupedByBlastRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the PoliciesGroupedByBlastRiskLevel type """
    return (
        ds.PoliciesGroupedByBlastRiskLevel.blastRiskLevel,
        ds.PoliciesGroupedByBlastRiskLevel.count,
    )
def list_trivial_fields_IdentityProviderEligibilityDataConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderEligibilityDataConnection type """
    return (
    )
def list_trivial_fields_IdentityProviderEligibilityDataEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderEligibilityDataEdge type """
    return (
    )
def list_trivial_fields_IdentityProviderEligibilityPolicyData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderEligibilityPolicyData type """
    return (
        ds.IdentityProviderEligibilityPolicyData.policyId,
        ds.IdentityProviderEligibilityPolicyData.policyName,
        ds.IdentityProviderEligibilityPolicyData.policyType,
        ds.IdentityProviderEligibilityPolicyData.blastRisk,
        ds.IdentityProviderEligibilityPolicyData.blastRiskLevel,
        ds.IdentityProviderEligibilityPolicyData.externalId,
    )
def list_trivial_fields_IdentityProviderEligibilityAccountData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderEligibilityAccountData type """
    return (
        ds.IdentityProviderEligibilityAccountData.accountId,
        ds.IdentityProviderEligibilityAccountData.accountName,
        ds.IdentityProviderEligibilityAccountData.accountMode,
    )
def list_trivial_fields_IdentityProviderEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderEligibilityData type """
    return (
        ds.IdentityProviderEligibilityData.providerId,
        ds.IdentityProviderEligibilityData.providerName,
        ds.IdentityProviderEligibilityData.providerType,
        ds.IdentityProviderEligibilityData.providerCategory,
        ds.IdentityProviderEligibilityData.eligibilityIds,
        ds.IdentityProviderEligibilityData.eligibleAccessType,
        ds.IdentityProviderEligibilityData.scopeType,
    )
def list_trivial_fields_EligibleUsersConnection(ds: DSLSchema):
    """ List all trivial fields of the EligibleUsersConnection type """
    return (
    )
def list_trivial_fields_EligibleUsersEdge(ds: DSLSchema):
    """ List all trivial fields of the EligibleUsersEdge type """
    return (
    )
def list_trivial_fields_IdentityResourceEligibilityData(ds: DSLSchema):
    """ List all trivial fields of the IdentityResourceEligibilityData type """
    return (
    )
def list_trivial_fields_IdentityResourceEligibilityConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityResourceEligibilityConnection type """
    return (
    )
def list_trivial_fields_IdentityResourceEligibilityEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityResourceEligibilityEdge type """
    return (
    )
def list_trivial_fields_IdentityResourceEligibilityNode(ds: DSLSchema):
    """ List all trivial fields of the IdentityResourceEligibilityNode type """
    return (
        ds.IdentityResourceEligibilityNode.serviceType,
        ds.IdentityResourceEligibilityNode.allResources,
        ds.IdentityResourceEligibilityNode.eligibilityIds,
    )
def list_trivial_fields_IdentityEligibleProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityEligibleProvidersConnection type """
    return (
    )
def list_trivial_fields_IdentityEligibleProvidersEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityEligibleProvidersEdge type """
    return (
    )
def list_trivial_fields_IdentityProviderAssignmentData(ds: DSLSchema):
    """ List all trivial fields of the IdentityProviderAssignmentData type """
    return (
        ds.IdentityProviderAssignmentData.assignmentType,
        ds.IdentityProviderAssignmentData.accessRequestId,
        ds.IdentityProviderAssignmentData.isAndromedaManaged,
        ds.IdentityProviderAssignmentData.status,
        ds.IdentityProviderAssignmentData.isDirectBinding,
    )
def list_trivial_fields_IdentityResolvedAssignmentsData(ds: DSLSchema):
    """ List all trivial fields of the IdentityResolvedAssignmentsData type """
    return (
    )
def list_trivial_fields_IdentityResolvedAssignmentsEdge(ds: DSLSchema):
    """ List all trivial fields of the IdentityResolvedAssignmentsEdge type """
    return (
    )
def list_trivial_fields_IdentityResolvedAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the IdentityResolvedAssignmentsConnection type """
    return (
    )
def list_trivial_fields_FolderConnection(ds: DSLSchema):
    """ List all trivial fields of the FolderConnection type """
    return (
    )
def list_trivial_fields_FolderEdge(ds: DSLSchema):
    """ List all trivial fields of the FolderEdge type """
    return (
    )
def list_trivial_fields_Folder(ds: DSLSchema):
    """ List all trivial fields of the Folder type """
    return (
        ds.Folder.id,
        ds.Folder.name,
        ds.Folder.externalId,
    )
def list_trivial_fields_AccessReviewerCampaignsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignsConnection type """
    return (
    )
def list_trivial_fields_AccessReviewerCampaignEdge(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignEdge type """
    return (
        ds.AccessReviewerCampaignEdge.node,
        ds.AccessReviewerCampaignEdge.reviewerCampaignData,
    )
def list_trivial_fields_AccessReviewerData(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerData type """
    return (
    )
def list_trivial_fields_AccessReviewerReviewsSummary(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerReviewsSummary type """
    return (
    )
def list_trivial_fields_ProviderAssignmentData(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentData type """
    return (
        ds.ProviderAssignmentData.assignmentType,
        ds.ProviderAssignmentData.accessRequestId,
        ds.ProviderAssignmentData.isAndromedaManaged,
        ds.ProviderAssignmentData.policyAssignmentType,
        ds.ProviderAssignmentData.isDirectBinding,
        ds.ProviderAssignmentData.isCrossScope,
        ds.ProviderAssignmentData.configuredPrincipalAccountId,
    )
def list_trivial_fields_ProviderAssignmentDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentDataEdge type """
    return (
        ds.ProviderAssignmentDataEdge.cursor,
    )
def list_trivial_fields_ProviderAssignmentDataConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentDataConnection type """
    return (
    )
def list_trivial_fields_CampaignOwnersData(ds: DSLSchema):
    """ List all trivial fields of the CampaignOwnersData type """
    return (
    )
def list_trivial_fields_LogoData(ds: DSLSchema):
    """ List all trivial fields of the LogoData type """
    return (
        ds.LogoData.url,
        ds.LogoData.httpContentType,
    )
def list_trivial_fields_GroupedByAccessLevelType(ds: DSLSchema):
    """ List all trivial fields of the GroupedByAccessLevelType type """
    return (
        ds.GroupedByAccessLevelType.accessType,
        ds.GroupedByAccessLevelType.count,
    )
def list_trivial_fields_EligibilityDetailsSummary(ds: DSLSchema):
    """ List all trivial fields of the EligibilityDetailsSummary type """
    return (
    )
def list_trivial_fields_UserScopeRoleData(ds: DSLSchema):
    """ List all trivial fields of the UserScopeRoleData type """
    return (
        ds.UserScopeRoleData.userId,
        ds.UserScopeRoleData.scopeId,
        ds.UserScopeRoleData.roleId,
        ds.UserScopeRoleData.roleName,
        ds.UserScopeRoleData.roleType,
        ds.UserScopeRoleData.blastRisk,
        ds.UserScopeRoleData.blastRiskLevel,
        ds.UserScopeRoleData.roleTrustDocument,
        ds.UserScopeRoleData.hasAdminPrivileges,
        ds.UserScopeRoleData.highRiskFrequentlyUsedPermissionsCount,
        ds.UserScopeRoleData.highRiskInfrequentlyUsedPermissionsCount,
        ds.UserScopeRoleData.highRiskUnusedPermissionsCount,
        ds.UserScopeRoleData.lowRiskFrequentlyUsedPermissionsCount,
        ds.UserScopeRoleData.lowRiskInfrequentlyUsedPermissionsCount,
        ds.UserScopeRoleData.lowRiskUnusedPermissionsCount,
        ds.UserScopeRoleData.untrackedPermissionsCount,
        ds.UserScopeRoleData.excessivePrivilegeScore,
        ds.UserScopeRoleData.unusedPermissionsPercentage,
    )
def list_trivial_fields_ProviderGroupsSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsSummary type """
    return (
    )
def list_trivial_fields_ProviderGroupsGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsGroupedBySignificance type """
    return (
        ds.ProviderGroupsGroupedBySignificance.significance,
        ds.ProviderGroupsGroupedBySignificance.count,
    )
def list_trivial_fields_GroupInsights(ds: DSLSchema):
    """ List all trivial fields of the GroupInsights type """
    return (
        ds.GroupInsights.type,
        ds.GroupInsights.category,
    )
def list_trivial_fields_AccountPolicyRecommendation(ds: DSLSchema):
    """ List all trivial fields of the AccountPolicyRecommendation type """
    return (
        ds.AccountPolicyRecommendation.jsonData,
        ds.AccountPolicyRecommendation.blastRisk,
        ds.AccountPolicyRecommendation.blastRiskLevel,
        ds.AccountPolicyRecommendation.recommendedPolicyName,
        ds.AccountPolicyRecommendation.providerPolicyType,
        ds.AccountPolicyRecommendation.responseType,
    )

# End of file: andromeda/nonpublic/graph/identity_service.proto

# File: andromeda/nonpublic/graph/distribution.proto
def list_trivial_fields_Linear(ds: DSLSchema):
    """ List all trivial fields of the Linear type """
    return (
        ds.Linear.numFiniteBuckets,
        ds.Linear.width,
        ds.Linear.offset,
    )
def list_trivial_fields_Exponential(ds: DSLSchema):
    """ List all trivial fields of the Exponential type """
    return (
        ds.Exponential.numFiniteBuckets,
        ds.Exponential.growthFactor,
        ds.Exponential.scale,
    )
def list_trivial_fields_Explicit(ds: DSLSchema):
    """ List all trivial fields of the Explicit type """
    return (
        ds.Explicit.bounds,
    )
def list_trivial_fields_BucketOptions(ds: DSLSchema):
    """ List all trivial fields of the BucketOptions type """
    return (
    )
def list_trivial_fields_Distribution(ds: DSLSchema):
    """ List all trivial fields of the Distribution type """
    return (
        ds.Distribution.count,
        ds.Distribution.bucketCounts,
    )

# End of file: andromeda/nonpublic/graph/distribution.proto

# File: andromeda/nonpublic/graph/provider_service.proto
def list_trivial_fields_ApplicationLicensing(ds: DSLSchema):
    """ List all trivial fields of the ApplicationLicensing type """
    return (
        ds.ApplicationLicensing.licensesCount,
    )
def list_trivial_fields_AppOktaData(ds: DSLSchema):
    """ List all trivial fields of the AppOktaData type """
    return (
        ds.AppOktaData.appCatalogLabel,
        ds.AppOktaData.features,
        ds.AppOktaData.samlMetadata,
        ds.AppOktaData.accessPolicyJson,
        ds.AppOktaData.isPushGroupEnabled,
    )
def list_trivial_fields_AppEntraData(ds: DSLSchema):
    """ List all trivial fields of the AppEntraData type """
    return (
        ds.AppEntraData.displayName,
    )
def list_trivial_fields_IdpApplicationData(ds: DSLSchema):
    """ List all trivial fields of the IdpApplicationData type """
    return (
        ds.IdpApplicationData.signOnMode,
        ds.IdpApplicationData.externalId,
        ds.IdpApplicationData.lastUpdatedAt,
        ds.IdpApplicationData.createdAt,
    )
def list_trivial_fields_ProviderTierData(ds: DSLSchema):
    """ List all trivial fields of the ProviderTierData type """
    return (
        ds.ProviderTierData.id,
        ds.ProviderTierData.name,
        ds.ProviderTierData.description,
    )
def list_trivial_fields_ProviderLogIngestionSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderLogIngestionSummary type """
    return (
        ds.ProviderLogIngestionSummary.historicalLogIngestionStatus,
        ds.ProviderLogIngestionSummary.historicalLogEarliestLogTime,
        ds.ProviderLogIngestionSummary.historicalLogLatestLogTime,
    )
def list_trivial_fields_Provider(ds: DSLSchema):
    """ List all trivial fields of the Provider type """
    return (
        ds.Provider.id,
        ds.Provider.name,
        ds.Provider.type,
        ds.Provider.category,
        ds.Provider.isPrimaryIdentityProvider,
        ds.Provider.applicationAuthType,
        ds.Provider.defaultMode,
        ds.Provider.contactEmails,
        ds.Provider.risk,
        ds.Provider.riskLevel,
        ds.Provider.isRiskComputed,
        ds.Provider.createDate,
        ds.Provider.scimEnabled,
        ds.Provider.ssoEnabled,
        ds.Provider.mode,
        ds.Provider.numHighRiskHis,
    )
def list_trivial_fields_CustomAppData(ds: DSLSchema):
    """ List all trivial fields of the CustomAppData type """
    return (
        ds.CustomAppData.inventoryFileId,
        ds.CustomAppData.inventoryFileType,
        ds.CustomAppData.inventoryFileLastUpdated,
        ds.CustomAppData.inventoryFileName,
        ds.CustomAppData.inventoryFileSize,
        ds.CustomAppData.inventoryFileUploadedByIdentityId,
        ds.CustomAppData.translatorFileId,
        ds.CustomAppData.translatorFileType,
        ds.CustomAppData.translatorFileLastUpdated,
        ds.CustomAppData.translatorFileName,
        ds.CustomAppData.translatorFileSize,
        ds.CustomAppData.translatorFileUploadedByIdentityId,
    )
def list_trivial_fields_IdpAppProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the IdpAppProvidersConnection type """
    return (
    )
def list_trivial_fields_IdpAppProvidersEdge(ds: DSLSchema):
    """ List all trivial fields of the IdpAppProvidersEdge type """
    return (
    )
def list_trivial_fields_IdpAppProvidersSummary(ds: DSLSchema):
    """ List all trivial fields of the IdpAppProvidersSummary type """
    return (
    )
def list_trivial_fields_ProviderObjMapping(ds: DSLSchema):
    """ List all trivial fields of the ProviderObjMapping type """
    return (
        ds.ProviderObjMapping.andromedaObjType,
        ds.ProviderObjMapping.supported,
        ds.ProviderObjMapping.label,
        ds.ProviderObjMapping.optional,
    )
def list_trivial_fields_Options(ds: DSLSchema):
    """ List all trivial fields of the Options type """
    return (
        ds.Options.enabled,
        ds.Options.label,
        ds.Options.option,
    )
def list_trivial_fields_ProviderFeatures(ds: DSLSchema):
    """ List all trivial fields of the ProviderFeatures type """
    return (
        ds.ProviderFeatures.integrationLevel,
        ds.ProviderFeatures.riskSupported,
        ds.ProviderFeatures.userMappingRulesSupported,
        ds.ProviderFeatures.nhiSupported,
        ds.ProviderFeatures.nhiTypes,
        ds.ProviderFeatures.activityLogsSupported,
        ds.ProviderFeatures.supportedRecommendationTypes,
    )
def list_trivial_fields_ScopeFeatures(ds: DSLSchema):
    """ List all trivial fields of the ScopeFeatures type """
    return (
        ds.ScopeFeatures.scopeType,
        ds.ScopeFeatures.crossScopeAssignmentsSupported,
        ds.ScopeFeatures.riskSupported,
        ds.ScopeFeatures.assignmentsInheritedFromParentScope,
    )
def list_trivial_fields_IdpProviderCapabilities(ds: DSLSchema):
    """ List all trivial fields of the IdpProviderCapabilities type """
    return (
        ds.IdpProviderCapabilities.idpApplicationSupported,
        ds.IdpProviderCapabilities.pushGroupSupported,
    )
def list_trivial_fields_AccessRequestGroupProvisioningPolicyData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestGroupProvisioningPolicyData type """
    return (
        ds.AccessRequestGroupProvisioningPolicyData.matchType,
        ds.AccessRequestGroupProvisioningPolicyData.groupCreationSupported,
        ds.AccessRequestGroupProvisioningPolicyData.groupDeletionSupported,
    )
def list_trivial_fields_AccessRequestProvisioningPolicySupportData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProvisioningPolicySupportData type """
    return (
        ds.AccessRequestProvisioningPolicySupportData.policy,
    )
def list_trivial_fields_AccessManagementCapabilities(ds: DSLSchema):
    """ List all trivial fields of the AccessManagementCapabilities type """
    return (
        ds.AccessManagementCapabilities.accessManagementSupported,
        ds.AccessManagementCapabilities.accessManagementEnabled,
        ds.AccessManagementCapabilities.suportedEligibilityTypes,
        ds.AccessManagementCapabilities.supportedResourceSetEligibilityConstraints,
        ds.AccessManagementCapabilities.sessionSummarySupported,
        ds.AccessManagementCapabilities.allowAllResourcesInResourcesetSupported,
        ds.AccessManagementCapabilities.andromedaResourcePoliciesSupported,
    )
def list_trivial_fields_ParentProviderData(ds: DSLSchema):
    """ List all trivial fields of the ParentProviderData type """
    return (
        ds.ParentProviderData.providerId,
        ds.ParentProviderData.providerName,
        ds.ParentProviderData.accountId,
        ds.ParentProviderData.accountName,
    )
def list_trivial_fields_AssignableServicesConnection(ds: DSLSchema):
    """ List all trivial fields of the AssignableServicesConnection type """
    return (
    )
def list_trivial_fields_AssignableServicesEdge(ds: DSLSchema):
    """ List all trivial fields of the AssignableServicesEdge type """
    return (
    )
def list_trivial_fields_AssignableServiceData(ds: DSLSchema):
    """ List all trivial fields of the AssignableServiceData type """
    return (
        ds.AssignableServiceData.name,
        ds.AssignableServiceData.type,
    )
def list_trivial_fields_LogInventoryRuntimeStatus(ds: DSLSchema):
    """ List all trivial fields of the LogInventoryRuntimeStatus type """
    return (
        ds.LogInventoryRuntimeStatus.statusCode,
        ds.LogInventoryRuntimeStatus.errorMessages,
    )
def list_trivial_fields_HistoricalLogIngestionSummary(ds: DSLSchema):
    """ List all trivial fields of the HistoricalLogIngestionSummary type """
    return (
        ds.HistoricalLogIngestionSummary.lastSuccessfulRunTime,
    )
def list_trivial_fields_RealtimeLogIngestionSummary(ds: DSLSchema):
    """ List all trivial fields of the RealtimeLogIngestionSummary type """
    return (
        ds.RealtimeLogIngestionSummary.lastSuccessfulRunTime,
    )
def list_trivial_fields_LogIngestionSummary(ds: DSLSchema):
    """ List all trivial fields of the LogIngestionSummary type """
    return (
        ds.LogIngestionSummary.earliestLogIngestionTime,
    )
def list_trivial_fields_LogProcessingRuntimeSummary(ds: DSLSchema):
    """ List all trivial fields of the LogProcessingRuntimeSummary type """
    return (
        ds.LogProcessingRuntimeSummary.statusCode,
        ds.LogProcessingRuntimeSummary.errorMessages,
    )
def list_trivial_fields_LogProcessingSummary(ds: DSLSchema):
    """ List all trivial fields of the LogProcessingSummary type """
    return (
        ds.LogProcessingSummary.lastSuccessfulProcessingTime,
    )
def list_trivial_fields_ProviderStatus(ds: DSLSchema):
    """ List all trivial fields of the ProviderStatus type """
    return (
        ds.ProviderStatus.providerId,
        ds.ProviderStatus.lastUpdatedAt,
    )
def list_trivial_fields_SupportedEligibilityConfiguration(ds: DSLSchema):
    """ List all trivial fields of the SupportedEligibilityConfiguration type """
    return (
        ds.SupportedEligibilityConfiguration.eligibilityTypes,
    )
def list_trivial_fields_ResourceSetEligibilityConfiguration(ds: DSLSchema):
    """ List all trivial fields of the ResourceSetEligibilityConfiguration type """
    return (
        ds.ResourceSetEligibilityConfiguration.eligibilityConstraintSelectionAllowed,
    )
def list_trivial_fields_SupportedProvisioningGroupInputConfiguration(ds: DSLSchema):
    """ List all trivial fields of the SupportedProvisioningGroupInputConfiguration type """
    return (
        ds.SupportedProvisioningGroupInputConfiguration.isSupported,
        ds.SupportedProvisioningGroupInputConfiguration.isRequired,
    )
def list_trivial_fields_ConfigurableEligibilityScope(ds: DSLSchema):
    """ List all trivial fields of the ConfigurableEligibilityScope type """
    return (
        ds.ConfigurableEligibilityScope.isOptional,
        ds.ConfigurableEligibilityScope.scopeType,
    )
def list_trivial_fields_InventoryMetadataConnection(ds: DSLSchema):
    """ List all trivial fields of the InventoryMetadataConnection type """
    return (
    )
def list_trivial_fields_InventoryMetadataEdge(ds: DSLSchema):
    """ List all trivial fields of the InventoryMetadataEdge type """
    return (
    )
def list_trivial_fields_InventoryMetadataRecord(ds: DSLSchema):
    """ List all trivial fields of the InventoryMetadataRecord type """
    return (
        ds.InventoryMetadataRecord.id,
        ds.InventoryMetadataRecord.correlationId,
        ds.InventoryMetadataRecord.syncStartTime,
        ds.InventoryMetadataRecord.syncEndTime,
        ds.InventoryMetadataRecord.ingestionStatus,
        ds.InventoryMetadataRecord.processingStatus,
        ds.InventoryMetadataRecord.inventorySyncMode,
        ds.InventoryMetadataRecord.fetchedResourceCount,
        ds.InventoryMetadataRecord.lastUpdatedAt,
    )
def list_trivial_fields_InventoryStatisticsConnection(ds: DSLSchema):
    """ List all trivial fields of the InventoryStatisticsConnection type """
    return (
    )
def list_trivial_fields_InventoryStatisticsEdge(ds: DSLSchema):
    """ List all trivial fields of the InventoryStatisticsEdge type """
    return (
    )
def list_trivial_fields_InventoryStatistics(ds: DSLSchema):
    """ List all trivial fields of the InventoryStatistics type """
    return (
        ds.InventoryStatistics.tenantId,
        ds.InventoryStatistics.providerId,
        ds.InventoryStatistics.correlationId,
        ds.InventoryStatistics.resourceCount,
        ds.InventoryStatistics.resourceType,
        ds.InventoryStatistics.batchId,
        ds.InventoryStatistics.syncStartTime,
        ds.InventoryStatistics.syncEndTime,
        ds.InventoryStatistics.inventorySyncMessageType,
        ds.InventoryStatistics.operationType,
    )
def list_trivial_fields_ProviderMembersMetadata(ds: DSLSchema):
    """ List all trivial fields of the ProviderMembersMetadata type """
    return (
        ds.ProviderMembersMetadata.configuredUsersCount,
        ds.ProviderMembersMetadata.configuredIdentitiesCount,
        ds.ProviderMembersMetadata.configuredServiceIdentitiesCount,
        ds.ProviderMembersMetadata.activeUsersCount,
        ds.ProviderMembersMetadata.activeIdentitiesCount,
        ds.ProviderMembersMetadata.activeServiceIdentitiesCount,
        ds.ProviderMembersMetadata.inactiveUsersCount,
        ds.ProviderMembersMetadata.inactiveIdentitiesCount,
        ds.ProviderMembersMetadata.inactiveServiceIdentitiesCount,
        ds.ProviderMembersMetadata.loginsByUsersCount,
        ds.ProviderMembersMetadata.loginsByIdentitiesCount,
        ds.ProviderMembersMetadata.loginsByServiceIdentitiesCount,
        ds.ProviderMembersMetadata.successfulLoginsByUsersCount,
        ds.ProviderMembersMetadata.successfulLoginsByIdentitiesCount,
        ds.ProviderMembersMetadata.successfulLoginsByServiceIdentitiesCount,
        ds.ProviderMembersMetadata.failedLoginsByUsersCount,
        ds.ProviderMembersMetadata.failedLoginsByIdentitiesCount,
        ds.ProviderMembersMetadata.failedLoginsByServiceIdentitiesCount,
    )
def list_trivial_fields_ProviderAssignmentsData(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentsData type """
    return (
    )
def list_trivial_fields_ProviderAssignmentsEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentsEdge type """
    return (
    )
def list_trivial_fields_ProviderAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderAssignmentsConnection type """
    return (
    )
def list_trivial_fields_ProviderResolvedAssignmentsData(ds: DSLSchema):
    """ List all trivial fields of the ProviderResolvedAssignmentsData type """
    return (
    )
def list_trivial_fields_ProviderResolvedAssignmentsEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderResolvedAssignmentsEdge type """
    return (
    )
def list_trivial_fields_ProviderResolvedAssignmentsConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderResolvedAssignmentsConnection type """
    return (
    )
def list_trivial_fields_ProviderGroupsConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsConnection type """
    return (
    )
def list_trivial_fields_ProviderGroupDataEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupDataEdge type """
    return (
    )
def list_trivial_fields_ProviderGroupsData(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsData type """
    return (
        ds.ProviderGroupsData.providerName,
    )
def list_trivial_fields_ProviderGroupMetadata(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupMetadata type """
    return (
        ds.ProviderGroupMetadata.parentGroupsCount,
        ds.ProviderGroupMetadata.childGroupsCount,
        ds.ProviderGroupMetadata.maxDepth,
    )
def list_trivial_fields_ProviderGroupMembers(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupMembers type """
    return (
    )
def list_trivial_fields_ProviderOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the ProviderOpsInsightData type """
    return (
        ds.ProviderOpsInsightData.type,
        ds.ProviderOpsInsightData.category,
    )
def list_trivial_fields_ProvidersGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ProvidersGroupedBySignificance type """
    return (
        ds.ProvidersGroupedBySignificance.type,
        ds.ProvidersGroupedBySignificance.category,
        ds.ProvidersGroupedBySignificance.count,
    )
def list_trivial_fields_ProvidersGroupedByTier(ds: DSLSchema):
    """ List all trivial fields of the ProvidersGroupedByTier type """
    return (
        ds.ProvidersGroupedByTier.tierId,
        ds.ProvidersGroupedByTier.tierName,
        ds.ProvidersGroupedByTier.count,
    )
def list_trivial_fields_ProvidersGroupedByAuthType(ds: DSLSchema):
    """ List all trivial fields of the ProvidersGroupedByAuthType type """
    return (
        ds.ProvidersGroupedByAuthType.authType,
        ds.ProvidersGroupedByAuthType.count,
    )
def list_trivial_fields_ProvidersSummary(ds: DSLSchema):
    """ List all trivial fields of the ProvidersSummary type """
    return (
    )
def list_trivial_fields_InventorySummary(ds: DSLSchema):
    """ List all trivial fields of the InventorySummary type """
    return (
    )
def list_trivial_fields_ProcessingDetails(ds: DSLSchema):
    """ List all trivial fields of the ProcessingDetails type """
    return (
        ds.ProcessingDetails.lastSuccessfulRun,
    )
def list_trivial_fields_OperationRuntimeStatusData(ds: DSLSchema):
    """ List all trivial fields of the OperationRuntimeStatusData type """
    return (
        ds.OperationRuntimeStatusData.runtimeStatus,
        ds.OperationRuntimeStatusData.errorMessages,
    )
def list_trivial_fields_IngestionDetails(ds: DSLSchema):
    """ List all trivial fields of the IngestionDetails type """
    return (
        ds.IngestionDetails.lastSuccessfulRun,
        ds.IngestionDetails.syncStartTime,
    )
def list_trivial_fields_AccountsConnection(ds: DSLSchema):
    """ List all trivial fields of the AccountsConnection type """
    return (
    )
def list_trivial_fields_AccountEdge(ds: DSLSchema):
    """ List all trivial fields of the AccountEdge type """
    return (
    )
def list_trivial_fields_ProviderPoliciesSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderPoliciesSummary type """
    return (
    )
def list_trivial_fields_ProviderIdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesSummary type """
    return (
    )
def list_trivial_fields_ProviderServiceIdentitiesSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderServiceIdentitiesSummary type """
    return (
    )
def list_trivial_fields_ProviderIdentitiesGroupedByBlastRiskLevel(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedByBlastRiskLevel type """
    return (
        ds.ProviderIdentitiesGroupedByBlastRiskLevel.blastRiskLevel,
        ds.ProviderIdentitiesGroupedByBlastRiskLevel.count,
    )
def list_trivial_fields_ProviderIdentitiesGroupedByAccessKeysCount(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedByAccessKeysCount type """
    return (
        ds.ProviderIdentitiesGroupedByAccessKeysCount.singleAccessKeyCount,
        ds.ProviderIdentitiesGroupedByAccessKeysCount.multipleAccessKeysCount,
    )
def list_trivial_fields_ProviderIdentitiesGroupedByBlastRiskLevelAndHrType(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedByBlastRiskLevelAndHrType type """
    return (
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndHrType.hrType,
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndHrType.blastRiskLevel,
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndHrType.count,
    )
def list_trivial_fields_ProviderIdentitiesGroupedByHighBlastRiskIdentitiesChanges(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedByHighBlastRiskIdentitiesChanges type """
    return (
        ds.ProviderIdentitiesGroupedByHighBlastRiskIdentitiesChanges.changeType,
        ds.ProviderIdentitiesGroupedByHighBlastRiskIdentitiesChanges.count,
    )
def list_trivial_fields_ProviderIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType type """
    return (
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.serviceIdentityType,
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.blastRiskLevel,
        ds.ProviderIdentitiesGroupedByBlastRiskLevelAndServiceIdentityType.count,
    )
def list_trivial_fields_ProviderIdentitiesGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesGroupedBySignificance type """
    return (
        ds.ProviderIdentitiesGroupedBySignificance.significance,
        ds.ProviderIdentitiesGroupedBySignificance.count,
    )
def list_trivial_fields_ProviderServiceIdentitiesGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ProviderServiceIdentitiesGroupedBySignificance type """
    return (
        ds.ProviderServiceIdentitiesGroupedBySignificance.significance,
        ds.ProviderServiceIdentitiesGroupedBySignificance.count,
    )
def list_trivial_fields_ScimPushGroupRoleData(ds: DSLSchema):
    """ List all trivial fields of the ScimPushGroupRoleData type """
    return (
    )
def list_trivial_fields_Policy(ds: DSLSchema):
    """ List all trivial fields of the Policy type """
    return (
        ds.Policy.id,
        ds.Policy.name,
        ds.Policy.providerId,
        ds.Policy.data,
        ds.Policy.isLsp,
        ds.Policy.policyData,
        ds.Policy.accountId,
        ds.Policy.policyType,
        ds.Policy.hasAdminPermissions,
        ds.Policy.accountName,
        ds.Policy.externalId,
        ds.Policy.accountMode,
    )
def list_trivial_fields_License(ds: DSLSchema):
    """ List all trivial fields of the License type """
    return (
        ds.License.licenseId,
        ds.License.licenseName,
        ds.License.licenseType,
    )
def list_trivial_fields_PoliciesConnection(ds: DSLSchema):
    """ List all trivial fields of the PoliciesConnection type """
    return (
    )
def list_trivial_fields_PolicyEdge(ds: DSLSchema):
    """ List all trivial fields of the PolicyEdge type """
    return (
    )
def list_trivial_fields_ProviderIdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentitiesConnection type """
    return (
    )
def list_trivial_fields_ProviderIdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentityEdge type """
    return (
    )
def list_trivial_fields_ProviderServiceIdentitiesConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderServiceIdentitiesConnection type """
    return (
        ds.ProviderServiceIdentitiesConnection.serviceIdentityIds,
    )
def list_trivial_fields_ProviderServiceIdentityEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderServiceIdentityEdge type """
    return (
    )
def list_trivial_fields_AssignableGroupsConnection(ds: DSLSchema):
    """ List all trivial fields of the AssignableGroupsConnection type """
    return (
    )
def list_trivial_fields_AssignableGroupDataEdge(ds: DSLSchema):
    """ List all trivial fields of the AssignableGroupDataEdge type """
    return (
    )
def list_trivial_fields_AssignableGroup(ds: DSLSchema):
    """ List all trivial fields of the AssignableGroup type """
    return (
    )
def list_trivial_fields_AssignableUserDataConnection(ds: DSLSchema):
    """ List all trivial fields of the AssignableUserDataConnection type """
    return (
    )
def list_trivial_fields_AssignableUserDataEdge(ds: DSLSchema):
    """ List all trivial fields of the AssignableUserDataEdge type """
    return (
    )
def list_trivial_fields_AssignableUserData(ds: DSLSchema):
    """ List all trivial fields of the AssignableUserData type """
    return (
    )
def list_trivial_fields_ProviderAccessKeyData(ds: DSLSchema):
    """ List all trivial fields of the ProviderAccessKeyData type """
    return (
        ds.ProviderAccessKeyData.id,
        ds.ProviderAccessKeyData.keyId,
        ds.ProviderAccessKeyData.name,
        ds.ProviderAccessKeyData.createdAt,
        ds.ProviderAccessKeyData.lastUsed,
        ds.ProviderAccessKeyData.keyRotationPastDueDays,
        ds.ProviderAccessKeyData.keyRotationDueAt,
        ds.ProviderAccessKeyData.status,
        ds.ProviderAccessKeyData.userId,
        ds.ProviderAccessKeyData.userType,
        ds.ProviderAccessKeyData.principalId,
        ds.ProviderAccessKeyData.providerId,
        ds.ProviderAccessKeyData.accountId,
    )
def list_trivial_fields_ProviderAccessKeysConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderAccessKeysConnection type """
    return (
    )
def list_trivial_fields_ProviderAccessKeyEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderAccessKeyEdge type """
    return (
    )
def list_trivial_fields_ProviderIdentityGroupedByMetadata(ds: DSLSchema):
    """ List all trivial fields of the ProviderIdentityGroupedByMetadata type """
    return (
    )
def list_trivial_fields_ProvidersGroupedByCategoryAndType(ds: DSLSchema):
    """ List all trivial fields of the ProvidersGroupedByCategoryAndType type """
    return (
        ds.ProvidersGroupedByCategoryAndType.type,
        ds.ProvidersGroupedByCategoryAndType.category,
        ds.ProvidersGroupedByCategoryAndType.count,
    )
def list_trivial_fields_ProvidersGroupedByCategory(ds: DSLSchema):
    """ List all trivial fields of the ProvidersGroupedByCategory type """
    return (
        ds.ProvidersGroupedByCategory.category,
        ds.ProvidersGroupedByCategory.count,
    )
def list_trivial_fields_ProviderTiersConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderTiersConnection type """
    return (
    )
def list_trivial_fields_ProviderTiersEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderTiersEdge type """
    return (
    )
def list_trivial_fields_ProviderTierNode(ds: DSLSchema):
    """ List all trivial fields of the ProviderTierNode type """
    return (
        ds.ProviderTierNode.id,
        ds.ProviderTierNode.name,
        ds.ProviderTierNode.description,
        ds.ProviderTierNode.priority,
    )
def list_trivial_fields_ProviderConfiguredAssignment(ds: DSLSchema):
    """ List all trivial fields of the ProviderConfiguredAssignment type """
    return (
        ds.ProviderConfiguredAssignment.principalType,
        ds.ProviderConfiguredAssignment.principalId,
        ds.ProviderConfiguredAssignment.principalName,
        ds.ProviderConfiguredAssignment.principalIdentityId,
        ds.ProviderConfiguredAssignment.accountId,
        ds.ProviderConfiguredAssignment.accountName,
        ds.ProviderConfiguredAssignment.accountMode,
        ds.ProviderConfiguredAssignment.roleId,
        ds.ProviderConfiguredAssignment.roleName,
        ds.ProviderConfiguredAssignment.roleType,
        ds.ProviderConfiguredAssignment.assignmentType,
        ds.ProviderConfiguredAssignment.isAndromedaManaged,
        ds.ProviderConfiguredAssignment.isCrossAccount,
        ds.ProviderConfiguredAssignment.scopeId,
        ds.ProviderConfiguredAssignment.scopeType,
    )
def list_trivial_fields_ProviderConfiguredAssignmentConnection(ds: DSLSchema):
    """ List all trivial fields of the ProviderConfiguredAssignmentConnection type """
    return (
    )
def list_trivial_fields_ProviderConfiguredAssignmentEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderConfiguredAssignmentEdge type """
    return (
    )
def list_trivial_fields_Bucket(ds: DSLSchema):
    """ List all trivial fields of the Bucket type """
    return (
        ds.Bucket.rangeLabel,
        ds.Bucket.lowerBound,
        ds.Bucket.upperBound,
        ds.Bucket.groupCount,
        ds.Bucket.percentage,
    )
def list_trivial_fields_ProviderGroupsMetadataBucketSummaryData(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsMetadataBucketSummaryData type """
    return (
        ds.ProviderGroupsMetadataBucketSummaryData.metadata,
    )
def list_trivial_fields_ProviderGroupsMetadataBucketSummary(ds: DSLSchema):
    """ List all trivial fields of the ProviderGroupsMetadataBucketSummary type """
    return (
        ds.ProviderGroupsMetadataBucketSummary.totalGroups,
    )
def list_trivial_fields_ConfiguredAssignmentsGroupedBySignificance(ds: DSLSchema):
    """ List all trivial fields of the ConfiguredAssignmentsGroupedBySignificance type """
    return (
        ds.ConfiguredAssignmentsGroupedBySignificance.significance,
        ds.ConfiguredAssignmentsGroupedBySignificance.count,
    )
def list_trivial_fields_ConfiguredAssignmentsGroupedByPrincipalType(ds: DSLSchema):
    """ List all trivial fields of the ConfiguredAssignmentsGroupedByPrincipalType type """
    return (
        ds.ConfiguredAssignmentsGroupedByPrincipalType.principalType,
        ds.ConfiguredAssignmentsGroupedByPrincipalType.count,
    )
def list_trivial_fields_ConfiguredAssignmentsGroupedByScopeAndPrincipal(ds: DSLSchema):
    """ List all trivial fields of the ConfiguredAssignmentsGroupedByScopeAndPrincipal type """
    return (
        ds.ConfiguredAssignmentsGroupedByScopeAndPrincipal.scopeType,
        ds.ConfiguredAssignmentsGroupedByScopeAndPrincipal.totalCount,
    )
def list_trivial_fields_ConfiguredAssignmentsSummary(ds: DSLSchema):
    """ List all trivial fields of the ConfiguredAssignmentsSummary type """
    return (
        ds.ConfiguredAssignmentsSummary.totalAssignments,
    )

# End of file: andromeda/nonpublic/graph/provider_service.proto

# File: andromeda/nonpublic/graph/as_gql_common.proto
def list_trivial_fields_ProviderScopeData(ds: DSLSchema):
    """ List all trivial fields of the ProviderScopeData type """
    return (
        ds.ProviderScopeData.name,
        ds.ProviderScopeData.id,
        ds.ProviderScopeData.type,
        ds.ProviderScopeData.isInherited,
    )
def list_trivial_fields_FolderScopeData(ds: DSLSchema):
    """ List all trivial fields of the FolderScopeData type """
    return (
        ds.FolderScopeData.name,
        ds.FolderScopeData.id,
        ds.FolderScopeData.isInherited,
        ds.FolderScopeData.type,
    )
def list_trivial_fields_AccountScopeData(ds: DSLSchema):
    """ List all trivial fields of the AccountScopeData type """
    return (
        ds.AccountScopeData.name,
        ds.AccountScopeData.id,
        ds.AccountScopeData.isInherited,
        ds.AccountScopeData.type,
    )
def list_trivial_fields_ResourceGroupScopeData(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroupScopeData type """
    return (
        ds.ResourceGroupScopeData.name,
        ds.ResourceGroupScopeData.id,
        ds.ResourceGroupScopeData.isInherited,
        ds.ResourceGroupScopeData.type,
    )
def list_trivial_fields_GroupScopeData(ds: DSLSchema):
    """ List all trivial fields of the GroupScopeData type """
    return (
        ds.GroupScopeData.name,
        ds.GroupScopeData.id,
        ds.GroupScopeData.isInherited,
        ds.GroupScopeData.type,
    )
def list_trivial_fields_ResourceScopeData(ds: DSLSchema):
    """ List all trivial fields of the ResourceScopeData type """
    return (
        ds.ResourceScopeData.name,
        ds.ResourceScopeData.id,
        ds.ResourceScopeData.externalId,
        ds.ResourceScopeData.isInherited,
        ds.ResourceScopeData.resourceType,
        ds.ResourceScopeData.type,
    )
def list_trivial_fields_ScopeEdge(ds: DSLSchema):
    """ List all trivial fields of the ScopeEdge type """
    return (
        ds.ScopeEdge.cursor,
    )
def list_trivial_fields_ScopeConnection(ds: DSLSchema):
    """ List all trivial fields of the ScopeConnection type """
    return (
    )
def list_trivial_fields_AccessReviewsGroupedByRevocationStatus(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsGroupedByRevocationStatus type """
    return (
        ds.AccessReviewsGroupedByRevocationStatus.status,
        ds.AccessReviewsGroupedByRevocationStatus.count,
    )
def list_trivial_fields_AccessReviewsGroupedByStatusAndAiRecommendation(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsGroupedByStatusAndAiRecommendation type """
    return (
        ds.AccessReviewsGroupedByStatusAndAiRecommendation.reviewStatus,
        ds.AccessReviewsGroupedByStatusAndAiRecommendation.aiRecommendation,
        ds.AccessReviewsGroupedByStatusAndAiRecommendation.count,
    )
def list_trivial_fields_AccessReviewsGroupedByStatus(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsGroupedByStatus type """
    return (
        ds.AccessReviewsGroupedByStatus.reviewStatus,
        ds.AccessReviewsGroupedByStatus.count,
    )
def list_trivial_fields_AccessReviewsGroupedByAiRecommendation(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsGroupedByAiRecommendation type """
    return (
        ds.AccessReviewsGroupedByAiRecommendation.recommendation,
        ds.AccessReviewsGroupedByAiRecommendation.count,
    )
def list_trivial_fields_AccessReviewsGroupedByScope(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewsGroupedByScope type """
    return (
        ds.AccessReviewsGroupedByScope.providerId,
        ds.AccessReviewsGroupedByScope.reviewStatus,
        ds.AccessReviewsGroupedByScope.count,
        ds.AccessReviewsGroupedByScope.accountId,
    )
def list_trivial_fields_AccessReviewerCampaignsGroupedByStatus(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignsGroupedByStatus type """
    return (
        ds.AccessReviewerCampaignsGroupedByStatus.status,
        ds.AccessReviewerCampaignsGroupedByStatus.count,
    )
def list_trivial_fields_AccessReviewerCampaignsGroupedByEntitlementType(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerCampaignsGroupedByEntitlementType type """
    return (
        ds.AccessReviewerCampaignsGroupedByEntitlementType.type,
        ds.AccessReviewerCampaignsGroupedByEntitlementType.count,
    )
def list_trivial_fields_PolicyBindingOpsInsightsData(ds: DSLSchema):
    """ List all trivial fields of the PolicyBindingOpsInsightsData type """
    return (
        ds.PolicyBindingOpsInsightsData.type,
        ds.PolicyBindingOpsInsightsData.category,
    )
def list_trivial_fields_ResourceMutationEventsConnection(ds: DSLSchema):
    """ List all trivial fields of the ResourceMutationEventsConnection type """
    return (
    )
def list_trivial_fields_ResourceMutationEventsEdge(ds: DSLSchema):
    """ List all trivial fields of the ResourceMutationEventsEdge type """
    return (
    )
def list_trivial_fields_ResourceMutationEventNode(ds: DSLSchema):
    """ List all trivial fields of the ResourceMutationEventNode type """
    return (
        ds.ResourceMutationEventNode.scopeExternalId,
        ds.ResourceMutationEventNode.scopeExternalType,
        ds.ResourceMutationEventNode.eventId,
        ds.ResourceMutationEventNode.eventType,
        ds.ResourceMutationEventNode.eventTime,
        ds.ResourceMutationEventNode.eventData,
        ds.ResourceMutationEventNode.eventProcessingStartTime,
        ds.ResourceMutationEventNode.correlationId,
    )
def list_trivial_fields_GroupAccessData(ds: DSLSchema):
    """ List all trivial fields of the GroupAccessData type """
    return (
        ds.GroupAccessData.groupIds,
    )
def list_trivial_fields_RoleAccessData(ds: DSLSchema):
    """ List all trivial fields of the RoleAccessData type """
    return (
        ds.RoleAccessData.roleIds,
    )
def list_trivial_fields_PolicyOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the PolicyOpsInsightData type """
    return (
        ds.PolicyOpsInsightData.type,
        ds.PolicyOpsInsightData.category,
    )
def list_trivial_fields_ServiceIdentityAccountPolicyOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the ServiceIdentityAccountPolicyOpsInsightData type """
    return (
        ds.ServiceIdentityAccountPolicyOpsInsightData.type,
        ds.ServiceIdentityAccountPolicyOpsInsightData.category,
    )
def list_trivial_fields_ConfiguredAssignmentOpsInsightData(ds: DSLSchema):
    """ List all trivial fields of the ConfiguredAssignmentOpsInsightData type """
    return (
        ds.ConfiguredAssignmentOpsInsightData.type,
        ds.ConfiguredAssignmentOpsInsightData.category,
    )

# End of file: andromeda/nonpublic/graph/as_gql_common.proto

# File: andromeda/nonpublic/graph/inventory_resources_trigger_service.proto
def list_trivial_fields_InventoryResourceStatusResponse(ds: DSLSchema):
    """ List all trivial fields of the InventoryResourceStatusResponse type """
    return (
    )
def list_trivial_fields_InventoryResourceStatus(ds: DSLSchema):
    """ List all trivial fields of the InventoryResourceStatus type """
    return (
        ds.InventoryResourceStatus.id,
        ds.InventoryResourceStatus.name,
        ds.InventoryResourceStatus.type,
        ds.InventoryResourceStatus.scope,
        ds.InventoryResourceStatus.tenantId,
        ds.InventoryResourceStatus.providerId,
        ds.InventoryResourceStatus.providerAccountId,
        ds.InventoryResourceStatus.state,
        ds.InventoryResourceStatus.startTime,
        ds.InventoryResourceStatus.endTime,
        ds.InventoryResourceStatus.metadata,
    )

# End of file: andromeda/nonpublic/graph/inventory_resources_trigger_service.proto

# File: andromeda/nonpublic/graph/recommendation_type_config_service.proto
def list_trivial_fields_RecommendationTypeConfigConnection(ds: DSLSchema):
    """ List all trivial fields of the RecommendationTypeConfigConnection type """
    return (
    )
def list_trivial_fields_RecommendationTypeConfigEdge(ds: DSLSchema):
    """ List all trivial fields of the RecommendationTypeConfigEdge type """
    return (
    )
def list_trivial_fields_RecommendationTypeConfigNode(ds: DSLSchema):
    """ List all trivial fields of the RecommendationTypeConfigNode type """
    return (
        ds.RecommendationTypeConfigNode.id,
        ds.RecommendationTypeConfigNode.providerId,
        ds.RecommendationTypeConfigNode.type,
        ds.RecommendationTypeConfigNode.state,
        ds.RecommendationTypeConfigNode.createdAt,
        ds.RecommendationTypeConfigNode.canBeEnabled,
    )

# End of file: andromeda/nonpublic/graph/recommendation_type_config_service.proto

# File: andromeda/nonpublic/graph/favorites_service.proto
def list_trivial_fields_FavoriteAccessRequestTemplateConnection(ds: DSLSchema):
    """ List all trivial fields of the FavoriteAccessRequestTemplateConnection type """
    return (
    )
def list_trivial_fields_FavoriteAccessRequestTemplateEdge(ds: DSLSchema):
    """ List all trivial fields of the FavoriteAccessRequestTemplateEdge type """
    return (
    )
def list_trivial_fields_FavoriteAccessRequestTemplate(ds: DSLSchema):
    """ List all trivial fields of the FavoriteAccessRequestTemplate type """
    return (
        ds.FavoriteAccessRequestTemplate.id,
        ds.FavoriteAccessRequestTemplate.name,
        ds.FavoriteAccessRequestTemplate.description,
        ds.FavoriteAccessRequestTemplate.ownerId,
        ds.FavoriteAccessRequestTemplate.requesterUserId,
        ds.FavoriteAccessRequestTemplate.eligibilityId,
        ds.FavoriteAccessRequestTemplate.accessRequestType,
        ds.FavoriteAccessRequestTemplate.tags,
        ds.FavoriteAccessRequestTemplate.providerId,
        ds.FavoriteAccessRequestTemplate.scopeName,
        ds.FavoriteAccessRequestTemplate.scopeType,
        ds.FavoriteAccessRequestTemplate.scopeId,
        ds.FavoriteAccessRequestTemplate.accountId,
        ds.FavoriteAccessRequestTemplate.assignmentType,
        ds.FavoriteAccessRequestTemplate.accessRequestDuration,
        ds.FavoriteAccessRequestTemplate.accessRequestDescription,
    )
def list_trivial_fields_Favorites(ds: DSLSchema):
    """ List all trivial fields of the Favorites type """
    return (
    )

# End of file: andromeda/nonpublic/graph/favorites_service.proto

# File: andromeda/nonpublic/graph/graph_hr_service.proto
def list_trivial_fields_HrIdentityInfo(ds: DSLSchema):
    """ List all trivial fields of the HrIdentityInfo type """
    return (
        ds.HrIdentityInfo.userId,
        ds.HrIdentityInfo.hrType,
        ds.HrIdentityInfo.hireDate,
        ds.HrIdentityInfo.terminationDate,
        ds.HrIdentityInfo.orgName,
        ds.HrIdentityInfo.managerName,
        ds.HrIdentityInfo.managerId,
        ds.HrIdentityInfo.city,
        ds.HrIdentityInfo.locationState,
        ds.HrIdentityInfo.country,
        ds.HrIdentityInfo.lastMoved,
        ds.HrIdentityInfo.positionTitle,
        ds.HrIdentityInfo.businessTitle,
        ds.HrIdentityInfo.department,
        ds.HrIdentityInfo.managerUuid,
    )

# End of file: andromeda/nonpublic/graph/graph_hr_service.proto

# File: andromeda/nonpublic/graph/events_service.proto
def list_trivial_fields_AndromedaEventsConnection(ds: DSLSchema):
    """ List all trivial fields of the AndromedaEventsConnection type """
    return (
    )
def list_trivial_fields_AndromedaEventsEdge(ds: DSLSchema):
    """ List all trivial fields of the AndromedaEventsEdge type """
    return (
    )
def list_trivial_fields_AndromedaEventsNode(ds: DSLSchema):
    """ List all trivial fields of the AndromedaEventsNode type """
    return (
        ds.AndromedaEventsNode.id,
        ds.AndromedaEventsNode.type,
        ds.AndromedaEventsNode.name,
        ds.AndromedaEventsNode.time,
        ds.AndromedaEventsNode.actor,
        ds.AndromedaEventsNode.level,
        ds.AndromedaEventsNode.subtype,
        ds.AndromedaEventsNode.data,
        ds.AndromedaEventsNode.eventPrimaryKey,
    )

# End of file: andromeda/nonpublic/graph/events_service.proto

# File: andromeda/nonpublic/graph/recommendation_service.proto
def list_trivial_fields_RecommendationConnection(ds: DSLSchema):
    """ List all trivial fields of the RecommendationConnection type """
    return (
    )
def list_trivial_fields_RecommendationEdge(ds: DSLSchema):
    """ List all trivial fields of the RecommendationEdge type """
    return (
    )
def list_trivial_fields_RecommendationNode(ds: DSLSchema):
    """ List all trivial fields of the RecommendationNode type """
    return (
        ds.RecommendationNode.id,
        ds.RecommendationNode.recommendation,
        ds.RecommendationNode.createdAt,
        ds.RecommendationNode.internalType,
        ds.RecommendationNode.state,
        ds.RecommendationNode.severity,
        ds.RecommendationNode.category,
        ds.RecommendationNode.type,
        ds.RecommendationNode.context,
        ds.RecommendationNode.count,
        ds.RecommendationNode.recommendationText,
        ds.RecommendationNode.snoozedUntil,
    )
def list_trivial_fields_RecommendationOrigin(ds: DSLSchema):
    """ List all trivial fields of the RecommendationOrigin type """
    return (
        ds.RecommendationOrigin.providerId,
        ds.RecommendationOrigin.providerName,
        ds.RecommendationOrigin.providerType,
        ds.RecommendationOrigin.accountId,
        ds.RecommendationOrigin.accountName,
        ds.RecommendationOrigin.accountMode,
    )
def list_trivial_fields_RecommendationsGroupedBySeverity(ds: DSLSchema):
    """ List all trivial fields of the RecommendationsGroupedBySeverity type """
    return (
        ds.RecommendationsGroupedBySeverity.severity,
        ds.RecommendationsGroupedBySeverity.count,
    )

# End of file: andromeda/nonpublic/graph/recommendation_service.proto

# File: andromeda/utils/graphql.proto
def list_trivial_fields_PageInfo(ds: DSLSchema):
    """ List all trivial fields of the PageInfo type """
    return (
        ds.PageInfo.count,
    )

# End of file: andromeda/utils/graphql.proto

# File: andromeda/utils/common.proto
def list_trivial_fields_Location(ds: DSLSchema):
    """ List all trivial fields of the Location type """
    return (
        ds.Location.city,
        ds.Location.state,
        ds.Location.country,
        ds.Location.latitude,
        ds.Location.longitude,
        ds.Location.accuracyRadius,
    )
def list_trivial_fields_GeoLocation(ds: DSLSchema):
    """ List all trivial fields of the GeoLocation type """
    return (
        ds.GeoLocation.city,
        ds.GeoLocation.state,
        ds.GeoLocation.country,
    )
def list_trivial_fields_Tag(ds: DSLSchema):
    """ List all trivial fields of the Tag type """
    return (
        ds.Tag.key,
        ds.Tag.value,
    )

# End of file: andromeda/utils/common.proto

# File: andromeda/api/models/meta.proto
def list_trivial_fields_ProviderEdge(ds: DSLSchema):
    """ List all trivial fields of the ProviderEdge type """
    return (
    )
def list_trivial_fields_ProvidersConnection(ds: DSLSchema):
    """ List all trivial fields of the ProvidersConnection type """
    return (
    )

# End of file: andromeda/api/models/meta.proto

# File: andromeda/api/models/campaigns/campaign_instance.proto
def list_trivial_fields_CampaignTransactionStatus(ds: DSLSchema):
    """ List all trivial fields of the CampaignTransactionStatus type """
    return (
        ds.CampaignTransactionStatus.status,
        ds.CampaignTransactionStatus.reason,
        ds.CampaignTransactionStatus.transitionedAt,
        ds.CampaignTransactionStatus.lastStatus,
    )

# End of file: andromeda/api/models/campaigns/campaign_instance.proto

# File: andromeda/api/models/campaigns/campaign_snapshot.proto
def list_trivial_fields_CampaignSnapshotReviewReviewerTrail(ds: DSLSchema):
    """ List all trivial fields of the CampaignSnapshotReviewReviewerTrail type """
    return (
        ds.CampaignSnapshotReviewReviewerTrail.action,
        ds.CampaignSnapshotReviewReviewerTrail.reason,
        ds.CampaignSnapshotReviewReviewerTrail.triggeredAt,
        ds.CampaignSnapshotReviewReviewerTrail.triggeredById,
        ds.CampaignSnapshotReviewReviewerTrail.processedAt,
    )
def list_trivial_fields_RevocationStatus(ds: DSLSchema):
    """ List all trivial fields of the RevocationStatus type """
    return (
        ds.RevocationStatus.status,
        ds.RevocationStatus.updatedAt,
        ds.RevocationStatus.reason,
        ds.RevocationStatus.revocationAttempts,
    )
def list_trivial_fields_CampaignSnapshotReviewReviewerStatus(ds: DSLSchema):
    """ List all trivial fields of the CampaignSnapshotReviewReviewerStatus type """
    return (
        ds.CampaignSnapshotReviewReviewerStatus.reviewerStatus,
        ds.CampaignSnapshotReviewReviewerStatus.reason,
        ds.CampaignSnapshotReviewReviewerStatus.updatedAt,
        ds.CampaignSnapshotReviewReviewerStatus.updatedById,
    )
def list_trivial_fields_CampaignSnapshotReviewAction(ds: DSLSchema):
    """ List all trivial fields of the CampaignSnapshotReviewAction type """
    return (
        ds.CampaignSnapshotReviewAction.action,
        ds.CampaignSnapshotReviewAction.reason,
        ds.CampaignSnapshotReviewAction.triggeredAt,
        ds.CampaignSnapshotReviewAction.triggeredById,
        ds.CampaignSnapshotReviewAction.processedAt,
        ds.CampaignSnapshotReviewAction.triggeredByEmail,
    )
def list_trivial_fields_ReassignReviewActionData(ds: DSLSchema):
    """ List all trivial fields of the ReassignReviewActionData type """
    return (
        ds.ReassignReviewActionData.reassignedReviewerId,
    )
def list_trivial_fields_AccessReviewAiAnalysisCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewAiAnalysisCheck type """
    return (
        ds.AccessReviewAiAnalysisCheck.analysisName,
        ds.AccessReviewAiAnalysisCheck.summary,
        ds.AccessReviewAiAnalysisCheck.status,
        ds.AccessReviewAiAnalysisCheck.category,
        ds.AccessReviewAiAnalysisCheck.checkType,
    )
def list_trivial_fields_AccessReviewAiAnalysis(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewAiAnalysis type """
    return (
        ds.AccessReviewAiAnalysis.aiReviewRecommendation,
        ds.AccessReviewAiAnalysis.accessReviewSummary,
    )

# End of file: andromeda/api/models/campaigns/campaign_snapshot.proto

# File: andromeda/api/models/config/campaign_template.proto
def list_trivial_fields_CampaignAccessRevocationPolicy(ds: DSLSchema):
    """ List all trivial fields of the CampaignAccessRevocationPolicy type """
    return (
        ds.CampaignAccessRevocationPolicy.accessRevocationCheckEnabled,
        ds.CampaignAccessRevocationPolicy.automatedAccessRevocationEnabled,
        ds.CampaignAccessRevocationPolicy.groupMembershipRevocationEnabled,
    )
def list_trivial_fields_CampaignOwnersTemplate(ds: DSLSchema):
    """ List all trivial fields of the CampaignOwnersTemplate type """
    return (
    )
def list_trivial_fields_IdentityPersonaCampaignOwnersTemplate(ds: DSLSchema):
    """ List all trivial fields of the IdentityPersonaCampaignOwnersTemplate type """
    return (
        ds.IdentityPersonaCampaignOwnersTemplate.identityIds,
    )
def list_trivial_fields_AccessReviewerIdentityTemplate(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewerIdentityTemplate type """
    return (
        ds.AccessReviewerIdentityTemplate.identityId,
    )
def list_trivial_fields_CampaignReviewerAssignmentScheme(ds: DSLSchema):
    """ List all trivial fields of the CampaignReviewerAssignmentScheme type """
    return (
        ds.CampaignReviewerAssignmentScheme.personaType,
    )
def list_trivial_fields_ProviderTypeMatch(ds: DSLSchema):
    """ List all trivial fields of the ProviderTypeMatch type """
    return (
        ds.ProviderTypeMatch.providerTypes,
    )
def list_trivial_fields_AccessReviewRuleCondition(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewRuleCondition type """
    return (
    )
def list_trivial_fields_AccessReviewRoleBlastRiskCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewRoleBlastRiskCheck type """
    return (
        ds.AccessReviewRoleBlastRiskCheck.matchCriteria,
        ds.AccessReviewRoleBlastRiskCheck.blastRiskThreshold,
    )
def list_trivial_fields_AccessReviewRecentlyApprovedCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewRecentlyApprovedCheck type """
    return (
        ds.AccessReviewRecentlyApprovedCheck.lastApprovalThresholdSeconds,
    )
def list_trivial_fields_AccessReviewIdentityStatusCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewIdentityStatusCheck type """
    return (
        ds.AccessReviewIdentityStatusCheck.matchCriteria,
        ds.AccessReviewIdentityStatusCheck.identityStatus,
    )
def list_trivial_fields_AccessReviewPolicyLastUsageCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewPolicyLastUsageCheck type """
    return (
        ds.AccessReviewPolicyLastUsageCheck.policyLastUsageThresholdSecs,
    )
def list_trivial_fields_AccessReviewLastIdentityActivityCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewLastIdentityActivityCheck type """
    return (
        ds.AccessReviewLastIdentityActivityCheck.lastIdentityActivityThresholdSecs,
    )
def list_trivial_fields_AccessReviewAnalysisCheck(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewAnalysisCheck type """
    return (
        ds.AccessReviewAnalysisCheck.enabled,
        ds.AccessReviewAnalysisCheck.name,
        ds.AccessReviewAnalysisCheck.action,
        ds.AccessReviewAnalysisCheck.checkType,
    )
def list_trivial_fields_AccessReviewAnalysisPolicy(ds: DSLSchema):
    """ List all trivial fields of the AccessReviewAnalysisPolicy type """
    return (
    )
def list_trivial_fields_CampaignNotificationsConfig(ds: DSLSchema):
    """ List all trivial fields of the CampaignNotificationsConfig type """
    return (
        ds.CampaignNotificationsConfig.reviewReminderIntervalDays,
        ds.CampaignNotificationsConfig.dailyReminderThresholdDays,
    )
def list_trivial_fields_CampaignScheduleConfig(ds: DSLSchema):
    """ List all trivial fields of the CampaignScheduleConfig type """
    return (
        ds.CampaignScheduleConfig.startDate,
        ds.CampaignScheduleConfig.autoActivateCampaign,
        ds.CampaignScheduleConfig.campaignDuration,
    )

# End of file: andromeda/api/models/config/campaign_template.proto

# File: andromeda/api/models/config/schedule.proto
def list_trivial_fields_ReccurenceSettings(ds: DSLSchema):
    """ List all trivial fields of the ReccurenceSettings type """
    return (
        ds.ReccurenceSettings.frequency,
        ds.ReccurenceSettings.interval,
        ds.ReccurenceSettings.until,
    )

# End of file: andromeda/api/models/config/schedule.proto

# File: andromeda/api/models/config/tenant_settings.proto
def list_trivial_fields_AccessRequestNotificationSettings(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestNotificationSettings type """
    return (
    )
def list_trivial_fields_SlackChannelNotifications(ds: DSLSchema):
    """ List all trivial fields of the SlackChannelNotifications type """
    return (
        ds.SlackChannelNotifications.enabled,
        ds.SlackChannelNotifications.notificationChannels,
    )
def list_trivial_fields_TeamsChannelNotifications(ds: DSLSchema):
    """ List all trivial fields of the TeamsChannelNotifications type """
    return (
        ds.TeamsChannelNotifications.enabled,
        ds.TeamsChannelNotifications.notificationChannels,
    )
def list_trivial_fields_NotificationSettingSlack(ds: DSLSchema):
    """ List all trivial fields of the NotificationSettingSlack type """
    return (
        ds.NotificationSettingSlack.enabled,
    )
def list_trivial_fields_NotificationSettingMicrosoftTeams(ds: DSLSchema):
    """ List all trivial fields of the NotificationSettingMicrosoftTeams type """
    return (
        ds.NotificationSettingMicrosoftTeams.enabled,
    )
def list_trivial_fields_NotificationSettingEmail(ds: DSLSchema):
    """ List all trivial fields of the NotificationSettingEmail type """
    return (
        ds.NotificationSettingEmail.enabled,
    )

# End of file: andromeda/api/models/config/tenant_settings.proto

# File: andromeda/api/models/config/jit_profile.proto
def list_trivial_fields_AccessRequestItsmSettings(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestItsmSettings type """
    return (
        ds.AccessRequestItsmSettings.validItsmTicketCheckEnabled,
        ds.AccessRequestItsmSettings.accessRequesterItsmTicketCheckEnabled,
        ds.AccessRequestItsmSettings.itsmResolutionStatusBasedDeprovisioningEnabled,
        ds.AccessRequestItsmSettings.validItsmTicketStatusCheckEnabled,
    )
def list_trivial_fields_AccessRequestExtensionConfig(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestExtensionConfig type """
    return (
        ds.AccessRequestExtensionConfig.maxExtensionRequestCount,
        ds.AccessRequestExtensionConfig.maxExtensionDuration,
        ds.AccessRequestExtensionConfig.enabled,
        ds.AccessRequestExtensionConfig.defaultExtensionDuration,
    )
def list_trivial_fields_AccessRequestValidationConfig(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestValidationConfig type """
    return (
        ds.AccessRequestValidationConfig.minDuration,
        ds.AccessRequestValidationConfig.maxDuration,
        ds.AccessRequestValidationConfig.allowedRequestTypes,
        ds.AccessRequestValidationConfig.maxScheduledRequestsCount,
        ds.AccessRequestValidationConfig.eligibilityBasedRevocationStrategy,
        ds.AccessRequestValidationConfig.requestExpirationDays,
    )

# End of file: andromeda/api/models/config/jit_profile.proto

# File: andromeda/api/models/config/jit_transaction.proto
def list_trivial_fields_AccessRequestReviewLevelDetails(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestReviewLevelDetails type """
    return (
        ds.AccessRequestReviewLevelDetails.currentReviewLevel,
        ds.AccessRequestReviewLevelDetails.totalReviewLevels,
    )
def list_trivial_fields_RequiredApprovalsDetails(ds: DSLSchema):
    """ List all trivial fields of the RequiredApprovalsDetails type """
    return (
        ds.RequiredApprovalsDetails.level,
        ds.RequiredApprovalsDetails.minimumRequiredApprovals,
    )
def list_trivial_fields_AccessRequestProvisioningDetails(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProvisioningDetails type """
    return (
        ds.AccessRequestProvisioningDetails.provisioningPolicy,
        ds.AccessRequestProvisioningDetails.externalBindingId,
        ds.AccessRequestProvisioningDetails.provisionedAt,
        ds.AccessRequestProvisioningDetails.deprovisionedAt,
    )
def list_trivial_fields_AccessRequestProvisioningCredentials(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProvisioningCredentials type """
    return (
        ds.AccessRequestProvisioningCredentials.authType,
    )
def list_trivial_fields_BasicAccessAuthCredentials(ds: DSLSchema):
    """ List all trivial fields of the BasicAccessAuthCredentials type """
    return (
        ds.BasicAccessAuthCredentials.username,
    )
def list_trivial_fields_AccessRequestProvisioningRole(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProvisioningRole type """
    return (
        ds.AccessRequestProvisioningRole.roleExternalId,
    )
def list_trivial_fields_AwsPolicyStatement(ds: DSLSchema):
    """ List all trivial fields of the AwsPolicyStatement type """
    return (
        ds.AwsPolicyStatement.sid,
        ds.AwsPolicyStatement.effect,
        ds.AwsPolicyStatement.actions,
        ds.AwsPolicyStatement.resources,
        ds.AwsPolicyStatement.conditionJson,
    )
def list_trivial_fields_AwsResourcePermissionSetData(ds: DSLSchema):
    """ List all trivial fields of the AwsResourcePermissionSetData type """
    return (
        ds.AwsResourcePermissionSetData.id,
        ds.AwsResourcePermissionSetData.name,
    )
def list_trivial_fields_AccessRequestProvisioningGroup(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestProvisioningGroup type """
    return (
        ds.AccessRequestProvisioningGroup.andromedaId,
        ds.AccessRequestProvisioningGroup.externalId,
        ds.AccessRequestProvisioningGroup.externalResourceType,
        ds.AccessRequestProvisioningGroup.name,
    )
def list_trivial_fields_JitPolicyTransactionStatus(ds: DSLSchema):
    """ List all trivial fields of the JitPolicyTransactionStatus type """
    return (
        ds.JitPolicyTransactionStatus.status,
        ds.JitPolicyTransactionStatus.reason,
        ds.JitPolicyTransactionStatus.transitionedAt,
        ds.JitPolicyTransactionStatus.lastStatus,
    )
def list_trivial_fields_JitPolicyRequestAnalysis(ds: DSLSchema):
    """ List all trivial fields of the JitPolicyRequestAnalysis type """
    return (
        ds.JitPolicyRequestAnalysis.aiReviewRecommendation,
        ds.JitPolicyRequestAnalysis.policyRiskScore,
    )
def list_trivial_fields_JitPolicyRequestAnalysisCheck(ds: DSLSchema):
    """ List all trivial fields of the JitPolicyRequestAnalysisCheck type """
    return (
        ds.JitPolicyRequestAnalysisCheck.category,
        ds.JitPolicyRequestAnalysisCheck.summary,
        ds.JitPolicyRequestAnalysisCheck.status,
    )
def list_trivial_fields_JitSessionAnalysis(ds: DSLSchema):
    """ List all trivial fields of the JitSessionAnalysis type """
    return (
        ds.JitSessionAnalysis.duration,
        ds.JitSessionAnalysis.summary,
        ds.JitSessionAnalysis.reason,
        ds.JitSessionAnalysis.sessionLogsFileLocation,
    )

# End of file: andromeda/api/models/config/jit_transaction.proto

# File: andromeda/api/models/config/policy_eligibility_mapping.proto
def list_trivial_fields_ProvisioningGroupConfiguration(ds: DSLSchema):
    """ List all trivial fields of the ProvisioningGroupConfiguration type """
    return (
        ds.ProvisioningGroupConfiguration.name,
        ds.ProvisioningGroupConfiguration.id,
    )
def list_trivial_fields_PolicyProvisioningConditionsData(ds: DSLSchema):
    """ List all trivial fields of the PolicyProvisioningConditionsData type """
    return (
    )
def list_trivial_fields_AzureConditions(ds: DSLSchema):
    """ List all trivial fields of the AzureConditions type """
    return (
        ds.AzureConditions.resolvedRawCode,
        ds.AzureConditions.rawCode,
    )
def list_trivial_fields_AzureRoleAssignmentConditionsRules(ds: DSLSchema):
    """ List all trivial fields of the AzureRoleAssignmentConditionsRules type """
    return (
    )
def list_trivial_fields_AzureRoleAssignmentCondition(ds: DSLSchema):
    """ List all trivial fields of the AzureRoleAssignmentCondition type """
    return (
    )
def list_trivial_fields_AzureRoleAssignmentMatchTarget(ds: DSLSchema):
    """ List all trivial fields of the AzureRoleAssignmentMatchTarget type """
    return (
    )
def list_trivial_fields_AzureResourceMatch(ds: DSLSchema):
    """ List all trivial fields of the AzureResourceMatch type """
    return (
    )
def list_trivial_fields_EligibilityConstraint(ds: DSLSchema):
    """ List all trivial fields of the EligibilityConstraint type """
    return (
        ds.EligibilityConstraint.scopeType,
    )
def list_trivial_fields_ScopeTagConstraint(ds: DSLSchema):
    """ List all trivial fields of the ScopeTagConstraint type """
    return (
    )
def list_trivial_fields_EligibilityConstraintTagMatch(ds: DSLSchema):
    """ List all trivial fields of the EligibilityConstraintTagMatch type """
    return (
        ds.EligibilityConstraintTagMatch.tagKey,
        ds.EligibilityConstraintTagMatch.matchCriteria,
        ds.EligibilityConstraintTagMatch.tagValue,
    )
def list_trivial_fields_ResourceGroupIdConstraints(ds: DSLSchema):
    """ List all trivial fields of the ResourceGroupIdConstraints type """
    return (
        ds.ResourceGroupIdConstraints.resourceGroupIds,
    )

# End of file: andromeda/api/models/config/policy_eligibility_mapping.proto

# File: andromeda/api/models/config/match.proto
def list_trivial_fields_TagMatch(ds: DSLSchema):
    """ List all trivial fields of the TagMatch type """
    return (
        ds.TagMatch.matchKeyCriteria,
        ds.TagMatch.matchKeyStr,
        ds.TagMatch.matchValueCriteria,
        ds.TagMatch.matchValueStr,
    )
def list_trivial_fields_HrTypeMatch(ds: DSLSchema):
    """ List all trivial fields of the HrTypeMatch type """
    return (
        ds.HrTypeMatch.matchCriteria,
        ds.HrTypeMatch.values,
    )
def list_trivial_fields_ExternalUserStatusMatch(ds: DSLSchema):
    """ List all trivial fields of the ExternalUserStatusMatch type """
    return (
        ds.ExternalUserStatusMatch.matchCriteria,
        ds.ExternalUserStatusMatch.values,
    )
def list_trivial_fields_DepartmentMatch(ds: DSLSchema):
    """ List all trivial fields of the DepartmentMatch type """
    return (
        ds.DepartmentMatch.matchCriteria,
        ds.DepartmentMatch.values,
    )
def list_trivial_fields_ProviderCategoryMatch(ds: DSLSchema):
    """ List all trivial fields of the ProviderCategoryMatch type """
    return (
        ds.ProviderCategoryMatch.categories,
    )
def list_trivial_fields_ProviderMatch(ds: DSLSchema):
    """ List all trivial fields of the ProviderMatch type """
    return (
        ds.ProviderMatch.matchCriteria,
        ds.ProviderMatch.providerIds,
    )
def list_trivial_fields_GroupMatch(ds: DSLSchema):
    """ List all trivial fields of the GroupMatch type """
    return (
        ds.GroupMatch.matchCriteria,
        ds.GroupMatch.groupIds,
    )
def list_trivial_fields_IdentityMatch(ds: DSLSchema):
    """ List all trivial fields of the IdentityMatch type """
    return (
        ds.IdentityMatch.matchCriteria,
        ds.IdentityMatch.identityIds,
    )
def list_trivial_fields_ScopeMatch(ds: DSLSchema):
    """ List all trivial fields of the ScopeMatch type """
    return (
        ds.ScopeMatch.matchCriteria,
        ds.ScopeMatch.scopeIds,
    )
def list_trivial_fields_RolesMatch(ds: DSLSchema):
    """ List all trivial fields of the RolesMatch type """
    return (
        ds.RolesMatch.matchCriteria,
        ds.RolesMatch.roleIds,
    )
def list_trivial_fields_ProviderAccountMatch(ds: DSLSchema):
    """ List all trivial fields of the ProviderAccountMatch type """
    return (
        ds.ProviderAccountMatch.matchCriteria,
        ds.ProviderAccountMatch.accountIds,
    )
def list_trivial_fields_IdentityUsernameMatch(ds: DSLSchema):
    """ List all trivial fields of the IdentityUsernameMatch type """
    return (
        ds.IdentityUsernameMatch.matchCriteria,
        ds.IdentityUsernameMatch.usernames,
    )
def list_trivial_fields_KvTagMatch(ds: DSLSchema):
    """ List all trivial fields of the KvTagMatch type """
    return (
        ds.KvTagMatch.keyMatchCriteria,
        ds.KvTagMatch.key,
        ds.KvTagMatch.valueMatchCriteria,
        ds.KvTagMatch.values,
    )

# End of file: andromeda/api/models/config/match.proto

# File: andromeda/api/models/config/jit_request.proto
def list_trivial_fields_AccessRequestResourceSetData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestResourceSetData type """
    return (
        ds.AccessRequestResourceSetData.name,
    )
def list_trivial_fields_AccessRequestResourceRoleData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestResourceRoleData type """
    return (
        ds.AccessRequestResourceRoleData.serviceType,
        ds.AccessRequestResourceRoleData.allResources,
        ds.AccessRequestResourceRoleData.resourceIds,
        ds.AccessRequestResourceRoleData.externalRoleIds,
        ds.AccessRequestResourceRoleData.roleIds,
    )
def list_trivial_fields_AccessRequestItsmData(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestItsmData type """
    return (
        ds.AccessRequestItsmData.ticketId,
        ds.AccessRequestItsmData.url,
    )
def list_trivial_fields_JitPolicyRequestUserAction(ds: DSLSchema):
    """ List all trivial fields of the JitPolicyRequestUserAction type """
    return (
        ds.JitPolicyRequestUserAction.action,
        ds.JitPolicyRequestUserAction.triggeredById,
        ds.JitPolicyRequestUserAction.triggeredByEmail,
        ds.JitPolicyRequestUserAction.triggeredAt,
    )
def list_trivial_fields_RequestExtensionUserActionData(ds: DSLSchema):
    """ List all trivial fields of the RequestExtensionUserActionData type """
    return (
        ds.RequestExtensionUserActionData.extendedDuration,
        ds.RequestExtensionUserActionData.comment,
    )
def list_trivial_fields_AccessRequestScope(ds: DSLSchema):
    """ List all trivial fields of the AccessRequestScope type """
    return (
        ds.AccessRequestScope.scopeType,
        ds.AccessRequestScope.scopeId,
        ds.AccessRequestScope.scopeName,
    )

# End of file: andromeda/api/models/config/jit_request.proto

# File: andromeda/api/models/config/enums.proto
def list_trivial_fields_AccessKeySignificanceMessage(ds: DSLSchema):
    """ List all trivial fields of the AccessKeySignificanceMessage type """
    return (
        ds.AccessKeySignificanceMessage.accessKeySignificance,
    )
def list_trivial_fields_KeyTypeMessage(ds: DSLSchema):
    """ List all trivial fields of the KeyTypeMessage type """
    return (
        ds.KeyTypeMessage.test,
    )
def list_trivial_fields_ConsoleAccessSignificanceMessage(ds: DSLSchema):
    """ List all trivial fields of the ConsoleAccessSignificanceMessage type """
    return (
        ds.ConsoleAccessSignificanceMessage.consoleAccessSignificance,
    )

# End of file: andromeda/api/models/config/enums.proto

# File: andromeda/nonpublic/job_status.proto

# End of file: andromeda/nonpublic/job_status.proto

# File: andromeda/nonpublic/enums.proto

# End of file: andromeda/nonpublic/enums.proto

# File: andromeda/nonpublic/inventory/inventory_sync.proto

# End of file: andromeda/nonpublic/inventory/inventory_sync.proto

# File: andromeda/nonpublic/graph/models/graph_enums.proto

# End of file: andromeda/nonpublic/graph/models/graph_enums.proto

# File: andromeda/utils/options.proto

# End of file: andromeda/utils/options.proto

# File: andromeda/api/models/config/jit_review.proto

# End of file: andromeda/api/models/config/jit_review.proto

# File: andromeda/api/models/config/inventory_resource_mapping.proto

# End of file: andromeda/api/models/config/inventory_resource_mapping.proto

# File: andromeda/api/models/config/andromeda_broker.proto

# End of file: andromeda/api/models/config/andromeda_broker.proto

# File: andromeda/api/models/recommendation/enum/recommendation_enum.proto

# End of file: andromeda/api/models/recommendation/enum/recommendation_enum.proto
