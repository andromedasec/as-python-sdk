# Copyright 2025 Andromeda Security, Inc.
#
"""
This script get list of identities matching a significance / insight
"""
import argparse
import logging
import json
import os
from datetime import datetime, timedelta
from sdk.api_utils import APIUtils, InvalidInputException
from sdk.as_inventory import AndromedaInventory
import requests

logger = logging.getLogger(__name__)


def _setup_args() -> argparse.Namespace:
    help_str = """
    This script get list of identities matching a significance / insight

    Step1:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:
        # export access events for last 7 days
        python3 sdk/samples/andromeda_events_export.py --as_event_subtype=ACCESS_REQUEST
        # export user events for last 7 days
        python3 sdk/samples/andromeda_events_export.py --as_event_type=USER_EVENT
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(help_str)
    )
    parser.add_argument('--as_api_token', '-t',
                        help='API token for Andromeda')

    parser.add_argument('--as_session_token', '-s',
                        help='Session token for Andromeda')

    parser.add_argument('--as_ops_insights',
                        help='Comma Separated Opts Identity OpsInsights Eg. ADMIN_ACCOUNT')

    parser.add_argument('--as_event_type',
                        help='Comma Separated Risk Factors Eg. STALE',
                        choices=["USER_EVENT", "ACCESS_EVENT", "SYSTEM_EVENT"])

    parser.add_argument('--as_event_subtype',
                        help='Comma Separated Risk Factors Eg. STALE',
                        choices=["AUTHENTICATION", "ACCESS_REQUEST", "CONFIGURATION"])

    parser.add_argument('--start_time',
                        help='Start time for the events, datetime.now() - timedelta(days=7)',
                        default=(datetime.now() - timedelta(days=7)).isoformat())

    parser.add_argument('--as_output_dir',
                        help='Output directory for the inventory',
                        default="/tmp/andromeda-inventory/andromeda_inventory_sample")

    parser.add_argument('--as_api_endpoint', default="https://api.live.andromedasecurity.com",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--as_event_name',
                        help='Comma Separated event names',
                        choices=sorted(["USER_AUTH_LOGIN", "USER_REQUEST_ACCESS_KEY", "PROVIDER_CONFIG_CREATE", "PROVIDER_CONFIG_MODIFY", "PROVIDER_CONFIG_DELETE", "AWS_PROVIDER_CONFIG_CREATE", "AWS_PROVIDER_CONFIG_UPDATE", "AWS_PROVIDER_CONFIG_DELETE", "TENANT_INTERNAL_CONFIG_CREATE", "TENANT_INTERNAL_CONFIG_UPDATE", "TENANT_INTERNAL_CONFIG_DELETE", "AZURE_PROVIDER_CONFIG_CREATE", "AZURE_PROVIDER_CONFIG_UPDATE", "ENTRA_PROVIDER_CONFIG_CREATE", "ENTRA_PROVIDER_CONFIG_UPDATE", "OKTA_PROVIDER_CONFIG_CREATE", "OKTA_PROVIDER_CONFIG_UPDATE", "TENANT_SETTINGS_UPDATE", "ACCEPTED_IDENTITY_RISK_CONFIG_CREATE", "ACCEPTED_IDENTITY_RISK_CONFIG_DELETE", "ELIGIBILITY_MAPPING_CREATE", "ELIGIBILITY_MAPPING_DELETE", "ACCESS_REQUEST_CREATE", "ACCESS_REQUEST_REVIEW", "ACCESS_REQUEST_ADMIN_OVERRIDE_REVIEW", "ACCESS_REQUEST_USER_ACTION", "ACCESS_REQUEST_USER_ACTION_CLOSE", "ACCESS_REQUEST_USER_ACTION_EXTEND", "ACCESS_REQUEST_ADMIN_OVERRIDE_REVIEW_APPROVE", "ACCESS_REQUEST_ADMIN_OVERRIDE_REVIEW_REJECT", "ACCESS_REQUEST_REVIEW_APPROVE", "ACCESS_REQUEST_REVIEW_REJECT", "ACCESS_REQUEST_ANALYZED", "ACCESS_REQUEST_APPROVED", "ACCESS_REQUEST_PROVISIONED", "ACCESS_REQUEST_DEPROVISIONED", "ACCESS_REQUEST_REJECTED", "ACCESS_REQUEST_FAILED", "ACCESS_REQUEST_TIMED_OUT"]))

    return parser.parse_args()

def _setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _get_api_session(api_endpoint: str, as_session_token: str, as_api_token: str) -> requests.Session:
    """
    Get the API session from the arguments or environment variables
    Args:
        args: argparse.ArgumentParser
    Returns:
        APIUtils
    """
    au = APIUtils(api_endpoint=api_endpoint)
    as_session_token = as_session_token or os.getenv("AS_SESSION_COOKIE", "")
    if as_session_token:
        return au.get_api_session_w_cookie(as_session_token)
    as_api_token = as_api_token or os.getenv("AS_API_TOKEN", "")
    if as_api_token:
        return au.get_api_session_w_api_token(as_api_token)
    raise InvalidInputException(
        "Either as_api_token or as_session_token must be provided")

def _export_events(
        as_inventory: AndromedaInventory, output_dir: str,
        event_type: str, event_subtype: str, start_time: str, event_name: str) -> None:
    """
    Export identities with ops insights to a file
    """
    json_output_f = f"{output_dir}/andromeda_events_export.json"

    filters = {}
    if event_type:
        filters["eventType"] = {"equals": event_type.strip()}
    if event_subtype:
        filters['eventSubtype'] = {"equals": event_subtype.strip()}
    if start_time:
        filters["eventTime"] = {"greaterThanOrEquals": start_time}
    if event_name:
        filters["name"] = {"equals": event_name.strip()}

    events = []
    with open(f"{json_output_f}", 'w', encoding='utf-8') as f:
        for event in as_inventory.as_events_itr(filters=filters):
            events.append(event)
        json.dump(events, f, indent=2)
    logger.info("Events exported to \n json: %s", json_output_f)

if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    as_api_endpoint = args.as_api_endpoint
    api_session = _get_api_session(args.as_api_endpoint, args.as_session_token, args.as_api_token)
    if not api_session:
        raise ValueError("API session not found")
    ai = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=as_api_endpoint, gql_endpoint=args.as_gql_endpoint)

    _export_events(
        ai, args.as_output_dir, args.as_event_type, args.as_event_subtype, args.start_time, args.as_event_name)
