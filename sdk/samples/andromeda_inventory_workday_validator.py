# Copyright 2025 Andromeda Security, Inc.
#
"""
This script get list of identities matching a significance / insight
"""
import argparse
import logging
import json
import os
import csv
from sdk.api_utils import APIUtils
from sdk.as_inventory import AndromedaInventory

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
        python3 sdk/samples/andromeda_inventory_sample.py --as_ops_insights=ADMIN_ACCOUNT --as_risk_factors=RISK_FACTOR_STALE
        python3 sdk/samples/andromeda_inventory_sample.py --operation_type=dashboard_summary
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(help_str)
    )

    parser.add_argument('--as_api_token', '-t',
                        help='API token for Andromeda')

    parser.add_argument('--as_session_token', '-s',
                        help='Session token for Andromeda')

    parser.add_argument('--as_output_dir',
                        help='Output directory for the inventory',
                        default="/tmp/andromeda-inventory/andromeda_inventory_sample")

    parser.add_argument('--as_api_endpoint', default="https://api.live.andromedasecurity.com",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--workday_file', '-w',
                        help='Workday file to validate',
                        required=True)

    return parser.parse_args()

def _setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _get_api_session(as_api_endpoint: str, as_session_token: str, as_api_token: str) -> APIUtils:
    """
    Get the API session from the arguments or environment variables
    Args:
        args: argparse.ArgumentParser
    Returns:
        APIUtils
    """
    au = APIUtils(api_endpoint=as_api_endpoint)
    as_session_token = as_session_token or os.getenv("AS_SESSION_COOKIE")
    if as_session_token:
        return au.get_api_session_w_cookie(as_session_token)
    as_api_token = as_api_token or os.getenv("AS_API_TOKEN")
    if as_api_token:
        return au.get_api_session_w_api_token(as_api_token)
    raise api_utils.InvalidInputException(
        "Either as_api_token or as_session_token must be provided")


def _validate_workday_file(
        as_inventory: AndromedaInventory, workday_file: str, as_output_dir: str) -> None:
    """
    Validate the workday file
    """
    missing_users = []
    missing_users_in_provider = []
    processed_users = set()
    num_users = 0
    provider_data = next(as_inventory.app_provider_itr( filters={"id": {"equals": "84f8ee5e-b1c1-4351-91c4-c7387aea10d8"}}))
    workday_users_map = {}
    with open(workday_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        workday_users_map = {row['email']: row for row in csv_reader}
        workday_users = sorted(workday_users_map.keys())
        logger.info("Workday users: %s, unique: %s", len(workday_users), len(set(workday_users)))
        check_users = set()
        duplicate_users = []
        for user in workday_users:
            if user in check_users:
                logger.error("Duplicate user found in the workday file: %s", user)
                duplicate_users.append(user)
            check_users.add(user)
        if duplicate_users:
            logger.info("Duplicate users: %s", duplicate_users)
            assert False, "Duplicate users found in the workday file"
        # in batches of 50 check if the user is present
        batch_size = 50
        for i in range(0, len(workday_users), batch_size):
            batch = set(workday_users[i: i+ batch_size])
            logger.info("Checking batch: %s", sorted(batch))
            processed_users = set()
            #check using as_inventory if the user is present
            for hi in as_inventory.as_humans_itr(filters={"username": {"in": batch}}):
                if hi['email'] in batch:
                    #logger.debug("User %s found status %s", hi['email'], hi['state'])
                    batch.remove(hi['email'])
            missing_users.extend(list(batch))
            # find missing users in the provider
            batch = set(workday_users[i: i+ batch_size])
            # check if the set matches
            processed_users = set()
            for hi in as_inventory.provider_humans_itr(
                provider_id="84f8ee5e-b1c1-4351-91c4-c7387aea10d8",
                provider_data=provider_data, filters={"username": {"in": batch}}):
                if hi['email'] in batch:
                    batch.remove(hi['email'])
            missing_users_in_provider.extend(list(batch))
        logger.info("Missing users in the provider: %s", missing_users_in_provider)
        logger.info("Missing users: %s %s processed: %s", missing_users, num_users, len(processed_users))
    missing_users_map = {user: workday_users_map[user] for user in missing_users}
    logger.info("Missing users found in the inventory %s: %s", missing_users, missing_users_map)
    missing_users_map = {user: workday_users_map[user] for user in missing_users_in_provider}
    logger.info("Missing users found in the inventory %s: %s", missing_users_in_provider, missing_users_map)
    with open(f"{as_output_dir}/missing_users.txt", 'w', encoding='utf-8') as f:
        f.write(json.dumps(missing_users_map, indent=2) + '\n')

if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    as_api_endpoint = args.as_api_endpoint
    api_session = _get_api_session(args.as_api_endpoint, args.as_session_token, args.as_api_token)
    ai = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=as_api_endpoint, gql_endpoint=args.as_gql_endpoint)
    _validate_workday_file(ai, args.workday_file, args.as_output_dir)
