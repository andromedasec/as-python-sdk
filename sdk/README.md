# Introduction

Python SDK for Andromeda Security

## Installation

```shell
virtualenv as-customapp
source as-customapp/bin/activate
tar -xzvf as-python-sdk.tgz
pip install -r sdk/requirements.txt
export PYTHONPATH=$PYTHONPATH:`pwd`
```

## Authentication

You can authenticate using either an API token or session token:

### API Token Authentication

Create API token using the Andromeda UI and export it:

```shell
export AS_API_TOKEN=<from UI>
```

### Session Token Authentication

Alternatively, use a session token:

```shell
export AS_SESSION_COOKIE=<session token>
```

## Run the Samples

### Andromeda Inventory Report

The `andromeda_inventory_report.py` script provides two main operations:

#### 1. Identity Insights (Default)

Export identities matching specific criteria:

```shell
# See the help
python3 samples/andromeda_inventory_report.py -h

# Get identities with ADMIN level privileges
python3 samples/andromeda_inventory_report.py --as_ops_insights=ADMIN_ACCOUNT

# Get identities with risk factor STALE
python3 samples/andromeda_inventory_report.py --as_risk_factors=RISK_FACTOR_STALE

# Combine multiple filters
python3 samples/andromeda_inventory_report.py --as_ops_insights=ADMIN_ACCOUNT --as_risk_factors=RISK_FACTOR_STALE

# Use API token directly
python3 samples/andromeda_inventory_report.py -t <api_token> --as_ops_insights=ADMIN_ACCOUNT

# Use session token directly
python3 samples/andromeda_inventory_report.py -s <session_token> --as_ops_insights=ADMIN_ACCOUNT

# Explicitly specify identity_insights operation (same as default)
python3 samples/andromeda_inventory_report.py --operation_type=identity_insights --as_ops_insights=ADMIN_ACCOUNT

# Explicitly specify dashboard summary. as_ops_insights arguments are ignored
python3 samples/andromeda_inventory_report.py --operation_type=dashboard_summary
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

# Dashboard summary with API token
python3 samples/andromeda_inventory_report.py --operation_type=dashboard_summary -t <api_token>

# Dashboard summary with session token
python3 samples/andromeda_inventory_report.py --operation_type=dashboard_summary -s <session_token>
```

### Output

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
