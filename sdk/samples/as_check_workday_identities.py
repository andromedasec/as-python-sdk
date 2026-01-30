"""
This script checks the workday identities against the inventory

Step1:
    fetch the api token from the Andromeda UI and run the script with the api token
Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
"""

import argparse
import logging
import os
import csv

import requests

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from sdk.api_utils import APIUtils, InvalidInputException
from sdk.as_inventory import AndromedaInventory


logger = logging.getLogger(__name__)

def _setup_args() -> argparse.Namespace:
    help_str = """
    This script checks the workday identities against the inventory

    Step1:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:

    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(help_str)
    )
    parser.add_argument('--workday_file', help='workday validation file', required=True)
    return parser.parse_args()

def _setup_logging():
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _get_api_session(api_endpoint: str, as_session_token: str,
    as_api_token: str | None = None) -> requests.Session:
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


def _get_gql_client(api_session: requests.Session, graphql_url: str):
    """ Create GraphQL client and schema from the API session """
    logger.debug("Creating GraphQL client %s", graphql_url)
    transport = RequestsHTTPTransport(url=graphql_url,
                                headers=api_session.headers,
                                cookies=api_session.cookies,
                                timeout=240)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    introspection = "{__schema{queryType{name}}}"
    client.execute(gql(introspection))
    return client

if __name__ == '__main__':
    g_args = _setup_args()
    _setup_logging()
    as_gql_endpoint = os.getenv("AS_GQL_ENDPOINT", "https://api.live.andromedasecurity.com/graphql")
    as_api_endpoint = os.getenv("AS_API_ENDPOINT", "https://api.live.andromedasecurity.com")
    as_session_token = os.getenv("AS_SESSION_COOKIE", "")
    as_api_token = os.getenv("AS_API_TOKEN", "")

    g_api_session = _get_api_session(
        as_api_endpoint, as_session_token, as_api_token)
    if not g_api_session:
        raise ValueError("API session not found")

    g_gql_client = _get_gql_client(g_api_session, as_gql_endpoint)
    g_as_inventory = AndromedaInventory(
        g_gql_client, api_session=g_api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=as_api_endpoint, gql_endpoint=as_gql_endpoint)
    g_api_utils = APIUtils(api_endpoint=as_api_endpoint)

    # Read the workday csv file and load the users into dictionary keyed by the email which
    #
    with open(g_args.workday_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        workday_users_map = {row['email']: row for row in csv_reader}
    logger.info("Workday users: %s", len(workday_users_map))

    # filter only the users who are active in the workday file
    active_users = {email: user for email, user in workday_users_map.items() if user['active'] == 'TRUE'}
    logger.info("Active users: %s", len(active_users))

    # filter only the users who don't match configured domains in the inventory
    tenant_data = g_as_inventory.as_tenant_data()
    configured_domains = tenant_data['configuredDomains']
    unmatched_domains_users = {email: user for email, user in active_users.items() if user['email'].split('@')[1] not in configured_domains}
    logger.info("No configured domains users: %s", len(unmatched_domains_users))

    # filter only the users who are present in the inventory
    not_found_users = set(unmatched_domains_users.keys())
    logger.info("Not found users: %s", not_found_users)
    for user in g_as_inventory.as_humans_itr(filters={"email": {"in": not_found_users}}):
        logger.info("User %s found in the inventory", user['email'])
        not_found_users.remove(user['email'])

    logger.info("Not found users: %s", not_found_users)

    # check if all the active users are found in the inventory
    found_users = set()
    for user in g_as_inventory.as_humans_itr(filters={"email": {"in": active_users.keys()}}):
        logger.info("User %s found in the inventory", user['email'])
        found_users.add(user['email'])

    logger.info("Found users: %s", found_users)
    logger.info("Not found users: %s", not_found_users)
    missing_users = active_users.keys() - found_users
    logger.info("Missing users: %s", missing_users)
