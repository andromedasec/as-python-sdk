# Copyright 2025 Andromeda Security, Inc.
#
"""
This script downloads all users from the Andromeda inventory and exports them to JSON.
"""
import argparse
import logging
import json
import os
import requests
from sdk.api_utils import APIUtils
from sdk.as_inventory import AndromedaInventory

logger = logging.getLogger(__name__)


def _setup_args() -> argparse.Namespace:
    help_str = """
    This script downloads all users from the Andromeda inventory and exports them to JSON.

    Step1:
        Fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:
        python3 sdk/samples/andromeda_users_export.py
        python3 sdk/samples/andromeda_users_export.py --as_output_dir /tmp/my-export
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(help_str)
    )
    parser.add_argument('--as_output_dir',
                        help='Output directory for the exported JSON',
                        default="/tmp/andromeda-inventory/andromeda_users_export")

    parser.add_argument('--as_api_endpoint', default="https://api.live.andromedasecurity.com",
                        help='API endpoint for Andromeda')

    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')

    return parser.parse_args()


def _setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _get_api_session(as_api_endpoint: str) -> requests.Session:
    au = APIUtils(api_endpoint=as_api_endpoint)
    as_session_token = os.getenv("AS_SESSION_COOKIE")
    if as_session_token:
        return au.get_api_session_w_cookie(as_session_token)
    as_api_token = os.getenv("AS_API_TOKEN")
    if as_api_token:
        return au.get_api_session_w_api_token(as_api_token)
    raise ValueError("Either AS_SESSION_COOKIE or AS_API_TOKEN environment variable must be set")


def _export_users(as_inventory: AndromedaInventory, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    json_output_f = f"{output_dir}/andromeda_users.json"
    users = {}
    for user in as_inventory.as_users_itr():
        if user["id"] not in users:
            users[user["id"]] = user
    with open(json_output_f, 'w', encoding='utf-8') as f:
        json.dump(list(users.values()), f, indent=2)
    logger.info("%s users exported to %s", len(users), json_output_f)


if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    api_session = _get_api_session(args.as_api_endpoint)
    ai = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=args.as_api_endpoint, gql_endpoint=args.as_gql_endpoint)
    _export_users(ai, args.as_output_dir)
