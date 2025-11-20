# Introduction

Python SDK for Andromeda Security

## Linxux / Mac Installation

### Create Virtual Environment

```shell
setopt interactive_comments

# Create Virtual Environment
python -m venv as-python-sdk

# Activate Virtual Environment
source as-python-sdk/bin/activate

# Untar python sdk in linux/mac
tar -xzvf as-python-sdk.tgz
# Export pythonpath in linux/mac
export PYTHONPATH=$PYTHONPATH:`pwd`
```

### Install python dependencies

```shell
pip install -r sdk/requirements.txt
```

### API Token Authentication or Session Token

```shell
# API Token from
export AS_API_TOKEN=<from UI>
# Alternatively Session Token Authentication
export AS_SESSION_COOKIE=<session token>
```

## Windows Installation

### Create virtual environment

```shell
python -m venv as-python-sdk`
```

### Activate virtual environment

```shell
as-python-sdk\Scripts\activate`
```

### Untar python sdk in windows

```shell
tar -xzvf as-python-sdk.tgz
```

### Export pythonpath in windows

```shell
set PYTHONPATH="%PYTHONPATH%;%CD%"
```

### Install python dependencies in windows

```shell
pip install -r sdk/requirements.txt
```

### API Token Authentication in Windows

Create API token using the Andromeda UI and export it:

```shell
set AS_API_TOKEN="<API token from Andromeda dashboard>"
```

### Session Token Authentication in Windows

Alternatively, use a session token:

```shell
set AS_SESSION_COOKIE="<session token>"
```

## Run samples programs

### Andromeda Inventory Report

The `andromeda_inventory_report.py` script provides two main operations:

#### 1. Identity Insights (Default)

Export identities matching specific criteria:

```shell
# See the help
python3 samples/andromeda_inventory_report.py -h

# Explicitly specify identity_insights operation (same as default)
python3 samples/andromeda_inventory_report.py --operation_type=identity_insights --as_ops_insights=ADMIN_ACCOUNT

# Get identities with risk factor STALE
python3 samples/andromeda_inventory_report.py --as_risk_factors=RISK_FACTOR_STALE

# Combine multiple filters
python3 samples/andromeda_inventory_report.py --as_ops_insights=ADMIN_ACCOUNT --as_risk_factors=RISK_FACTOR_STALE

# Use API token directly
python3 samples/andromeda_inventory_report.py -t <api_token> --as_ops_insights=ADMIN_ACCOUNT

# Use session token directly
python3 samples/andromeda_inventory_report.py -s <session_token> --as_ops_insights=ADMIN_ACCOUNT

```

#### 2. Dashboard Summary

Export comprehensive dashboard summaries including:

- Human identities summary
- Non-human identities summary
- Providers summary
- Cloud providers details
- Application providers details

```shell
# Basic dashboard summary
python3 samples/andromeda_inventory_report.py --operation_type=dashboard_summary

# Dashboard summary with custom output directory
python3 samples/andromeda_inventory_report.py --operation_type=dashboard_summary --as_output_dir=/custom/path


```

#### Output

The script generates output files in the specified directory (default: `/tmp/andromeda-inventory/andromeda_inventory_sample`):

- **Identity Insights**:
  - `andromeda_inventory_sample_identities.json` - Full identity data in JSON format
  - `andromeda_inventory_sample_identities.csv` - Identity data in CSV format

- **Dashboard Summary**:
  - `andromeda_inventory_sample_dashboard_summaries.json` - Complete dashboard summary data

### Available Arguments

- `--as_api_token, -t`: API token for Andromeda
- `--as_session_token, -s`: Session token for Andromeda
- `--as_ops_insights`: Comma-separated ops identity insights (e.g., ADMIN_ACCOUNT)
- `--as_risk_factors`: Comma-separated risk factors (e.g., STALE)
- `--as_output_dir`: Output directory for inventory files
- `--as_api_endpoint`: API endpoint (default: <https://api.live.andromedasecurity.com>)
- `--as_gql_endpoint`: GraphQL endpoint (default: <https://api.live.andromedasecurity.com/graphql>)
- `--operation_type`: Operation type - "identity_insights" or "dashboard_summary" (default: identity_insights)

#### 3. Access Requests (JIT)

Perform Access Requests for all requests that have been marked as favorites.

```shell
# Trigger Jit Request for all the favorites. The user is determined by the access token
python3 sdk/samples/as_jit_request.py --duration=3600 --request_favorites
```

Perform Access Request for a Role

```shell
# Trigger Jit Request for a given role.
python3 sdk/samples/as_jit_request.py --provider=<AWS> --account=<Prod> --role_names=<role1,role2> --duration=3600
```

Perform Access Request for a group

```shell
# Trigger Jit Request for a given group.
python3 sdk/samples/as_jit_request.py --provider=<Entra> --group_names=<g1,g2> --duration=3600

```
