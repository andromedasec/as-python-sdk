# PIM Eligibility Migration

Fetches PIM (Privileged Identity Management) eligible assignments from Microsoft Entra and creates corresponding eligibilities in Andromeda.

## About the Tool

The script performs three steps:

1. **Fetch** -- Connects to Microsoft Graph API and collects PIM eligible assignments:
   - Entra directory role eligibilities
   - Group membership eligibilities (per-group pagination)
   - Azure resource role eligibilities (per subscription)
2. **Transform** -- Resolves Azure external IDs (users, groups, roles) to Andromeda UUIDs via `POST /inventory/find`, then builds Andromeda eligibility payloads. Unresolved IDs appear as `NOT_FOUND` in the output.
3. **Apply** (when `dryRun: false`) -- Upserts eligibilities: rows whose **stable identity** matches `output/<run_name>_eligibilities.json` are refreshed with `GET` + `PUT` (only `eligibleUserIds` / `eligibleGroupIds` are taken from the new transform output); others are created with `POST`. The state file is merged so previously tracked rows that are absent from the current PIM snapshot remain listed until you run **cleanup**. `cleanup: true` still deletes every eligibility referenced in that file.

Output files are written to `output/<run_name>_input.json` (raw PIM assignments) and `output/<run_name>_output.json` (transformed eligibilities).

## How to Use

### Prerequisites

```bash
pip install -r requirements.txt
```

### Configuration

Copy `config.sample.json` to `config.json` and fill in the values:

```bash
cp config.sample.json config.json
```

### Environment variables

| Variable | Used for |
|----------|----------|
| `ANDROMEDA_ACCESS_KEY` | Andromeda access key for `POST /login/access-key` (ID resolution, eligibility create/delete). Takes precedence over `andromeda.accessKey` in config if both are set. |
| `ENTRA_APP_ID` | App registration client ID for **Microsoft Graph** (Entra directory roles + group PIM) |
| `ENTRA_SECRET` | Client secret for that app |
| `AZURE_APP_ID` | App registration client ID for **Azure Resource Manager** (subscription resource PIM) |
| `AZURE_SECRET` | Client secret for that app |

The two Microsoft apps may be the same registration or different; each needs the appropriate API permissions (see below).

### config.json Fields

| Section | Field | Description |
|---|---|---|
| `andromeda.apiEndpoint` | Andromeda API base URL (e.g. `https://api.live.andromedasecurity.com`) | |
| `andromeda.accessKey` | Optional. Andromeda access key if not using `ANDROMEDA_ACCESS_KEY`. | |
| `entraConfig.azureTenantId` | Azure AD / Entra tenant ID for Graph token (directory roles + groups) | |
| `entraConfig.andromedaProviderId` | Andromeda provider UUID for the Entra provider (role + group eligibilities) | |
| `entraConfig.groupIds` | Group object IDs for group PIM eligibilities. If empty, groups are listed page by page from Graph. | |
| `entraConfig.entraRoleAssignmentsDiscoveryEnabled` | When `true` (default), fetches Entra directory role eligibilities. | |
| `entraConfig.groupAssignmentsDiscoveryEnabled` | When `true` (default), fetches group membership eligibilities. | |
| `azureConfig.azureTenantId` | Tenant ID for ARM token (resource PIM) | |
| `azureConfig.andromedaProviderId` | Andromeda provider UUID for the Azure provider (resource role eligibilities) | |
| `azureConfig.subscriptionIds` | Subscription IDs for resource PIM. If empty, enabled subscriptions visible to the ARM app are auto-discovered. | |
| `azureConfig.azureResourceAssignmentsDiscoveryEnabled` | When `true` (default), fetches Azure resource role eligibilities. | |
| `migration.dryRun` | When `true`, only writes output JSON (no POST to Andromeda). When `false`, creates eligibilities via API. | |
| `migration.cleanup` | When `true`, deletes eligibilities previously created by the script from `output/<run_name>_eligibilities.json` and exits without fetching, transforming, or creating. Use for cleanup-only runs. Requires `andromeda.apiEndpoint` and `ANDROMEDA_ACCESS_KEY` (or `andromeda.accessKey`). | |
| `migration.skipIngestion` | When `true`, loads assignments from `output/<run_name>_input.json` instead of fetching from Azure. Skips Azure env validation. Use for re-runs after editing the input. | |

### Run

```bash
python3 main.py <run_name>
```

For example:

```bash
python3 main.py migration-2026-03-16
```

This produces:
- `output/migration-2026-03-16_input.json` -- raw PIM assignments from Entra
- `output/migration-2026-03-16_output.json` -- transformed Andromeda eligibility payloads

When `dryRun` is `false`, eligibilities are upserted in Andromeda (create or update-by-identity as above).

## Andromeda Client

Authentication uses the same pattern as `lib/python/sdk/api_utils.py`. The script calls `POST /login/access-key` with `{"code": "<accessKey>"}` using the value from `ANDROMEDA_ACCESS_KEY` or `andromeda.accessKey`. The response sets session cookies via `Set-Cookie` headers, which are stored in a `requests.Session`. All subsequent API calls (ID resolution, eligibility creation) use this session -- no `Authorization` header is needed.

The client is initialized once in `main.py` before transform and apply steps via `init_client_and_login(api_endpoint, access_key)`. All functions in `andromeda.py` use the global singleton client.

## Permissions Required in Entra for App Registration

The Azure app registration used by this script needs the following Microsoft Graph API **application** permissions:

| Permission | Type | Purpose |
|---|---|---|
| `Group.Read.All` | Application | Read groups to fetch Entra Group assignments |
| `RoleEligibilitySchedule.Read.Directory` | Application | Read role eligibility schedule instances |
| `PrivilegedEligibilitySchedule.Read.AzureADGroup` | Application | Read group membership eligibility schedules |

For Azure resource role eligibilities (subscription-scoped), the app also needs:

| Permission | Type | Purpose |
|---|---|---|
| `Reader` role on target subscriptions | Azure RBAC | List resource role eligibility schedule instances via Azure Resource Manager |

Grant admin consent for all Graph permissions in the Azure portal under **App registrations > API permissions**.
