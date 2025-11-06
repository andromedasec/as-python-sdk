f"""
Migrate PingIdentity provider from PingOne provider

It will migrate in the following steps:
1. Get all the PingOne Provider's list

2. For each PingOne Provider,
   - Get all the Eligibility Mappings for the Provider
   - Resolve the eligiblity mapping against the Provider ides
    - The Group ID should be the Ping Group ID
    - The user Id should be the Ping User ID or username
    - The role Id should be the Ping Role ID
    - The Provisioning Group ID should be the Ping Group ID
    - SSO Application ID should be the Ping {Application ID, Environment ID}

3. For each eligibility Mapping at the Application level.
-  resolve the andromeda UUID corresponding to the Provisioning Group ID, User ID and Group ID
-  For each environment, create an eligibility mapping.
"""

import argparse
from enum import StrEnum
import logging
import time
import os
import csv
from typing import Optional, Dict, Any, List
from sdk.api_utils import APIUtils, InvalidInputException
from sdk.as_inventory import AndromedaInventory
import requests

logger = logging.getLogger(__name__)

def _setup_args() -> argparse.Namespace:
    help_str = """
    This script updates the resource policies used for resource set JIT.

    Step1:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:
        # update resource policies for resource set JIT
        python3 sdk/samples/as_create_eligibilities.py --eligibility_file=/tmp/eligibilities.csv
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(help_str)
    )
    parser.add_argument('--as_api_token', '-t',
                        help='API token for Andromeda')
    parser.add_argument('--as_session_token', '-s',
                        help='Session token for Andromeda')
    parser.add_argument('--as_api_endpoint',
                        default="https://api.live.andromedasecurity.com",
                        help='GQL endpoint for the inventory')
    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')
    parser.add_argument('--dry_run',
                        action='store_true',
                        help='Dry run the script')
    parser.add_argument('--providers',
                        help='Providers to migrate. If not provided, all providers of type PingOne will be migrated')
    return parser.parse_args()

def _setup_logging():
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(lineno)s: %(message)s')
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

if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    api_session = _get_api_session(args.as_api_endpoint, args.as_session_token, args.as_api_token)
    if not api_session:
        raise ValueError("API session not found")
    as_inventory = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=args.as_api_endpoint, gql_endpoint=args.as_gql_endpoint)
    api_utils = APIUtils(api_endpoint=args.as_api_endpoint)

    migrate_pingidentity(api_session, api_utils, args.providers)


def migrate_pingidentity_provider(api_session: requests.Session, api_utils: APIUtils,
    as_inventory: AndromedaInventory, provider_data: Dict[str, Any]) -> None:
    """
    Migrate PingIdentity provider from PingOne provider
    """
    logger.info("Migrating PingIdentity provider: %s: %s",
        provider_data['name'], provider_data['id'])
    provider_id = provider_data['id']

    for eligibility in as_inventory.provider_eligibilities_itr(provider_id, provider_data):


def migrate_pingidentity(api_session: requests.Session, api_utils: APIUtils,
    as_inventory: AndromedaInventory, provider_ids: Optional[List[str]] = None) -> None:
    """
    Migrate PingIdentity provider from PingOne provider
    """
    if not provider_ids:
        provider_ids = [p['id'] for p in as_inventory.provider_itr(filters={'type': 'PROVIDER_TYPE_PINGONE'})]

    for provider in provider_ids:
        provider_data = next(as_inventory.provider_itr(filters={'id': provider}))
        logger.info("Migrating PingIdentity provider: %s: %s",
            provider_data['name'], provider_data['id'])
        migrate_pingidentity_provider(api_session, api_utils, as_inventory, provider_data)
