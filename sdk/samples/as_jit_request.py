"""
This script creates a JIT request for a given provider and account.

Step1:
    fetch the api token from the Andromeda UI and run the script with the api token
Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
"""

import argparse
import logging
import os
from collections import namedtuple
from typing import Generator, Optional

import requests

from gql import Client, gql
from gql.dsl import DSLQuery, DSLSchema, dsl_gql
from gql.transport.requests import RequestsHTTPTransport

from sdk.api_utils import APIUtils, InvalidInputException
from sdk.as_inventory import AndromedaInventory
from api.graphql import graphql_query_snippets as gql_snippets


logger = logging.getLogger(__name__)

JIT_ACTIVE_STATUSES = ['REVIEW_IN_PROGRESS', 'PROVISIONED', 'PROVISIONING_IN_PROGRESS']

ArTuple = namedtuple('ArTuple', ['requesterUserId', 'providerId', 'scopeId', 'assignmentType',
    'policyId', 'groupId', 'resourceSetDataName'])

def _setup_args() -> argparse.Namespace:
    help_str = """
    This script updates the resource policies used for resource set JIT.

    Step1:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:
        # Trigger Jit Request for all the favorites. The user is determined by the access token
        python3 sdk/samples/as_jit_request.py --duration=3600 --request_favorites

        # Trigger Jit Request for a given role.
        python3 sdk/samples/as_jit_request.py --provider=<AWS> --account=<Prod> --role_names=<role1,role2> --duration=3600

        # Trigger Jit Request for a given group.
        python3 sdk/samples/as_jit_request.py --provider=<Entra> --group_names=<g1,g2> --duration=3600

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
    parser.add_argument('--provider_name',
                        help='provider for which the JIT request is to be created')
    parser.add_argument('--account_name',
                        help='account for which the JIT request is to be created')
    parser.add_argument('--role_names',
                        help='comma separated role names for which the JIT request is to be created',
                        default="")
    parser.add_argument('--group_names',
                        help='comma separated group names for which the JIT request is to be created',
                        default="")
    parser.add_argument('--duration',
                        help='duration for which the JIT request is to be created',
                        type=int,
                        default=3600)
    parser.add_argument('--request_favorites',
                        help='request favorites for which the JIT request is to be created',
                        action='store_true')
    parser.add_argument('--request_tags',
                        help='request tags for which the JIT request is to be created')
    parser.add_argument('--request_description',
                        help='request description for which the JIT request is to be created')
    parser.add_argument('--access_request_user_id',
                        help='access request user id for which the JIT request is to be created. If not provided, the user id will be fetched from the identity details.')
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


def access_request_favs_base_fn(
    api_session: requests.Session, gql_client: Client,
    page_size: int, skip: int, filters: dict) -> list[dict]:
    """
    Base function for access request
    """
    ds = DSLSchema(gql_client.schema) if gql_client.schema else None
    if not ds:
        raise ValueError("GQL client schema not found")
    query = dsl_gql(DSLQuery(
        ds.Query.Favorites.select(
            ds.Favorites.favoriteAccessRequestTemplates(
                pageArgs={"pageSize": page_size, "skip": skip},
                filters=filters
            ).select(
                ds.FavoriteAccessRequestTemplateConnection.edges.select(
                    ds.FavoriteAccessRequestTemplateEdge.node.select(
                        *gql_snippets.list_trivial_fields_FavoriteAccessRequestTemplate(ds),
                        ds.FavoriteAccessRequestTemplate.roleAccessData.select(
                            ds.RoleAccessData.roleIds
                        ),
                        ds.FavoriteAccessRequestTemplate.groupAccessData.select(
                            ds.GroupAccessData.groupIds
                        ),
                        ds.FavoriteAccessRequestTemplate.resourceSetAccessData.select(
                            ds.AccessRequestResourceSetData.name
                        )
                    )
                )
            )
        )
    ))
    response = gql_client.execute(query, get_execution_result=True).formatted
    try:
        favs = response["data"]['Favorites']['favoriteAccessRequestTemplates']['edges']
        favs = [node['node'] for node in favs]
        logger.debug("num resource groups returned %s", len(favs))
        return favs
    except (KeyError, TypeError):
        logger.error("Error getting favorites: %s", response)
        return []


def favorites_itr(api_session: requests.Session, gql_client: Client,
    filters: dict, page_size: int) -> Generator[dict, None, None]:
    """
    Iterate through favorites
    """
    favs = []
    max_items = 10000
    skip = 0
    for skip in range(0, max_items, page_size):
        favs = access_request_favs_base_fn(api_session, gql_client, page_size, skip, filters)
        for favorite in favs:
            yield favorite

def request_favorite_access_request(
    api_session: requests.Session, gql_client: Client,
    duration: int, description: str, api_utils: APIUtils,
    as_inventory: AndromedaInventory, provider_id: str,
    account_id: str, role_ids: list[str], group_ids: list[str]) -> None:
    """
    Request a favorite access request
    1. Fetch favorites for the user
    2. Check if any of the favorites already have a jit request.
    3. If not, create a new jit request for the favorite.

    """

    response = api_session.get(f"{api_utils.api_endpoint}/identity-details")
    response.raise_for_status()
    identity_id = response.json()['identityId']

    active_ars = as_inventory.as_identity_access_requests_itr(
        identity_id, filters={'status': {'in': JIT_ACTIVE_STATUSES}}, page_size=100)
    # create a dictionary of the active ARs using ArTuple as the key
    active_ars_dict = {
        ArTuple(ar['requesterUser']['id'], ar['providerDetailsData']['id'],
            ar['requestScope']['scopeId'], ar['assignmentType'], ar['policyId'],
            ar['accessGroupId'], ar.get('resourceSetDataName', '')):
            ar for ar in active_ars}
    logger.debug("Active ARs %s", active_ars_dict)
    for fav in favorites_itr(api_session, gql_client, filters={}, page_size=100):
        logger.debug("Favorite %s", fav)
        role_id = ""
        group_id = ""
        resource_set_name = ""
        if fav['assignmentType'] == "ROLE_ASSIGNMENT":
            role_id = fav['roleAccessData']['roleIds'][0]
        elif fav['assignmentType'] == "GROUP_ASSIGNMENT":
            group_id = fav['groupAccessData']['groupIds'][0]
        elif fav['assignmentType'] == "RESOURCE_SET_ASSIGNMENT":
            resource_set_name = fav['resourceSetAccessData']['name']
        else:
            raise ValueError(f"Invalid assignment type: {fav['assignmentType']}")

        # check if filters are provided for the favorite.
        if provider_id and fav['providerId'] != provider_id:
            continue
        if account_id and fav['accountId'] != account_id:
            continue
        if role_ids and fav['roleAccessData']['roleIds'][0] not in role_ids:
            continue
        if group_ids in fav['groupAccessData']['groupIds'][0] not in group_ids:
            continue
        # make jit request for the favorite
        # check if there are active jit requests for the identity.
        # if yes then skip those JIT requests.
        ar_tuple = ArTuple(fav['requesterUserId'], fav['providerId'],
            fav['scopeId'], fav['assignmentType'], role_id, group_id, resource_set_name)
        if ar_tuple in active_ars_dict:
            logger.info("Active JIT request %s found for the identity. Skipping JIT request.",
            ar_tuple)
            continue
        logger.info("No active JIT request found for the identity. Creating JIT request %s",
            ar_tuple)
        # check if there are active jit requests for the identity.
        make_jit_request_from_favorite(api_session, fav, api_utils, duration, description)


def jit_payload_from_fav_gql(fav: dict, duration: int, description: str) -> dict:
    """
    Convert a favorite to a JIT request payload
    {
        "id": "371e125e-684b-405b-bb4e-b6881ecc632d",
        "name": "",
        "description": "",
        "requesterUserId": "9c7eefa3-477a-4ac5-a7f6-0bd4fdd79c7a",
        "eligibilityId": "",
        "accessRequestType": "JIT",
        "tags": [],
        "providerId": "c91dbb43-7a9d-4099-8d15-58981b1339d0",
        "requestScope": {
            "scopeType": "ACCOUNT",
            "scopeId": "128ddb12-e53d-44d4-8412-b410fd136067",
            "scopeName": "Beatles-Development"
        },
        "accountId": "",
        "assignmentType": "ROLE_ASSIGNMENT",
        "roleAccessData": {
            "roleIds": [
                "0016d729-3084-4e74-b66d-9c4265226d59"
            ]
        },
        "accessRequestDuration": 3600,
        "accessRequestDescription": ""
    }

    """
    jit_request = {
        "name": fav["name"],
        "duration": duration,
        "description": description,
        "tags": fav.get("tags", []),
        "requesterUserId": fav["requesterUserId"],
        "accessRequestType": fav["accessRequestType"],
        "assignmentType": fav["assignmentType"],
        "accountId": fav.get("accountId", "")
    }
    if fav["assignmentType"] == "ROLE_ASSIGNMENT":
        jit_request["policyId"] = fav['roleAccessData']['roleIds'][0]
    elif fav["assignmentType"] == "GROUP_ASSIGNMENT":
        jit_request["groupId"] = fav['groupAccessData']['groupIds'][0]
    elif fav["assignmentType"] == "RESOURCE_SET_ASSIGNMENT":
        jit_request["resourceSetData"] = fav['resourceSetAccessData']
    else:
        raise ValueError(f"Invalid assignment type: {fav['assignmentType']}")
    jit_request["providerId"] = fav["providerId"]
    jit_request["requestScope"] = {
        "scopeType": fav["scopeType"],
        "scopeId": fav["scopeId"],
    }
    return jit_request

def make_jit_request_from_favorite(
    api_session: requests.Session, fav: dict, api_utils: APIUtils,
    duration: int, description: str) -> tuple[int, dict]:
    """
    Make a JIT request from a favorite template
    """
    jit_request = jit_payload_from_fav_gql(fav, duration, description)
    logger.debug("Making JIT request for favorite %s", fav)
    jit_url = f"{api_utils.api_endpoint}/providers/{fav['providerId']}/accessrequests"
    resp = api_session.post(jit_url, json=jit_request)
    assert resp.status_code == 200, (
        f"Failed to make JIT request: for favorite {fav} {resp.json()}"
    )
    logger.info("JIT request for fav %s with id %s created.",
        fav, resp.json()['id'])
    return resp.status_code, resp.json()

def get_identity_id_from_user_id(as_inventory: AndromedaInventory, access_request_user_id: str) -> str:
    """
    Get the identity id from the user id
    """
    user = next(as_inventory.as_users_itr(filters={'id': {'equals': access_request_user_id}}))
    return user['identity']['id']

def make_role_based_jit_request(api_session: requests.Session, duration: int, description: str,
    api_utils: APIUtils, provider_id: str, account_id: str, role_id: str,
    access_request_user_id: str = "", eligibility_data: Optional[list[dict]] = None) -> None:
    """
    Make a role based JIT request
    If user id is not provided then need to fetch the user id from the eligibility
    """
    if not access_request_user_id and eligibility_data:
        # find the user_id from the eligibility data.
        for e in eligibility_data:
            if e['eligibleAccessType'] != 'ROLE_ACCESS':
                continue
            if e['eligibilityData']['policyId'] == role_id:
                access_request_user_id = e['eligibleUser']['originUserId']
                break
    assert access_request_user_id, (
        f"User id not found for role id: {role_id} and provider id: {provider_id}"
    )
    jit_request = {
        "duration": duration,
        "description": description,
        "requesterUserId": access_request_user_id,
        "accessRequestType": 'JIT',
        "assignmentType": 'ROLE_ASSIGNMENT',
        "providerId": provider_id,
        "policyId": role_id
    }

    if account_id:
        jit_request["accountId"] = account_id
        jit_request["requestScope"] = {
            "scopeType": "ACCOUNT",
            "scopeId": account_id
        }
    else:
        jit_request["requestScope"] = {
            "scopeType": "PROVIDER",
            "scopeId": provider_id
        }
    logger.debug("JIT request payload %s", jit_request)
    jit_url = f"{api_utils.api_endpoint}/providers/{provider_id}/accessrequests"
    logger.debug("JIT request URL %s", jit_url)
    resp = api_session.post(jit_url, json=jit_request)
    assert resp.status_code == 200, f"Failed to make JIT request: {resp.json()}"
    logger.info("JIT request id %s created", resp.json()['id'])
    return resp.json()

def make_group_based_jit_request(api_session: requests.Session,
    duration: int, description: str, api_utils: APIUtils,
    provider_id: str, account_id: str, group_id: str,
    access_request_user_id: str = "", eligibility_data: Optional[list[dict]] = None) -> None:
    """
    Make a role based JIT request
    If user id is not provided then need to fetch the user id from the eligibility
    """
    if not access_request_user_id and eligibility_data:
        # find the user_id from the eligibility data.
        for e in eligibility_data:
            if e['eligibleAccessType'] != 'GROUP_ACCESS':
                continue
            #logger.debug("Eligibility data %s for group id %s", e, group_id)
            if e['eligibilityData']['id'] == group_id:
                access_request_user_id = e['eligibleUser']['originUserId']
                break
    assert access_request_user_id, (
        f"User id not found for group id: {group_id} and provider id: {provider_id}"
    )
    jit_request = {
        "duration": duration,
        "description": description,
        "requesterUserId": access_request_user_id,
        "accessRequestType": 'JIT',
        "assignmentType": 'GROUP_ASSIGNMENT',
        "providerId": provider_id,
        "groupId": group_id
    }

    if account_id:
        jit_request["accountId"] = account_id
        jit_request["requestScope"] = {
            "scopeType": "ACCOUNT",
            "scopeId": account_id
        }
    else:
        jit_request["requestScope"] = {
            "scopeType": "PROVIDER",
            "scopeId": provider_id
        }
    logger.debug("JIT request payload %s", jit_request)
    jit_url = f"{api_utils.api_endpoint}/providers/{provider_id}/accessrequests"
    logger.debug("JIT request URL %s", jit_url)
    resp = api_session.post(jit_url, json=jit_request)
    assert resp.status_code == 200, f"Failed to make JIT request: {resp.json()}"
    logger.info("JIT request id %s created", resp.json()['id'])
    return resp.json()

def make_jit_request(
    api_session: requests.Session, gql_client: Client,
    duration: int, description: str,
    api_utils: APIUtils, as_inventory: AndromedaInventory,
    provider_id: str, account_id: str, role_ids: list[str], group_ids: list[str],
    access_request_user_id: str = "") -> None:
    """
    Make a JIT request for a given role.

    """
    # fetch the identity id for the user. if the identity id is not provided
    # fetch the eligibilities for the role.
    # if there are multiple user based eligibilities, require that user_id is provided in the request.
    # if there is only one user based eligibility, make a JIT request for the role.
    # if there is no eligibility for the role, raise an error.
    # fetch eligibility data for the identity

    if not access_request_user_id:
        response = api_session.get(f"{api_utils.api_endpoint}/identity-details")
        response.raise_for_status()
        identity_id = response.json()['identityId']
    else:
        # user the access request user id to fetch the identity id.
        try:
            identity_id = get_identity_id_from_user_id(as_inventory, access_request_user_id)
        except StopIteration as exc:
            raise ValueError(
                f"Identity id not found for user id: {access_request_user_id}") from exc

    eligibility_data = []
    try:
        eligibility_data = list(as_inventory.as_identity_eligibility_details_itr(identity_id))
    except StopIteration as exc:
        logger.error("Error getting eligibility data for identity id: %s", identity_id)
        raise ValueError(f"Eligibility data not found for identity id: {identity_id}") from exc

    for role_id in role_ids:
        # make role based JIT request for the role.
        make_role_based_jit_request(api_session, duration, description,
            api_utils, provider_id, account_id, role_id,
            access_request_user_id, eligibility_data=eligibility_data)
    for group_id in group_ids:
        # make group based JIT request for the group.
        make_group_based_jit_request(api_session, duration, description,
            api_utils, provider_id, account_id, group_id,
            access_request_user_id, eligibility_data=eligibility_data)


def _resolve_args_to_uuids(args: argparse.Namespace,
    as_inventory: AndromedaInventory) -> tuple[str, str, list, list]:

    provider_id = ""
    provider_data = {}
    if args.provider_name:
        try:
            provider = next(as_inventory.as_provider_itr(
                filters={'name': {'equals': args.provider_name}}))
            provider_id = provider['id']
        except StopIteration as exc:
            raise ValueError(f"Provider not found: {args.provider_name}") from exc
    account_id = ""
    if args.account_name:
        try:
            account = next(as_inventory.provider_accounts_itr(provider_id,
            filters={'name': {'equals': args.account_name}}))
            account_id = account['id']
        except StopIteration as exc:
            raise ValueError(f"Account not found: {args.account_name}") from exc
    role_ids = []
    if args.role_names:
        role_names = args.role_names.split(',')
        role_names = [role_name.strip() for role_name in role_names]
        assert provider_id, "Provider id is required when account name is provided"
        try:
            role_filters = {'policyName': {'in': role_names}}
            if account_id:
                role_filters['accountId'] = {'equals': account_id}
            for role in as_inventory.provider_assignable_policies_itr(
                provider_id, provider_data, filters=role_filters):
                role_ids.append(role['policyId'])
        except StopIteration as exc:
            raise ValueError(f"Roles not found: {role_names}") from exc

    group_ids = []
    if args.group_names:
        group_names = args.group_names.split(',')
        group_names = [group_name.strip() for group_name in group_names]
        try:
            group_ids = [group['id'] for group in g_as_inventory.as_groups_itr(
                filters={'name': {'in': group_names}})]
        except StopIteration as exc:
            raise ValueError(f"Groups not found: {args.group_names}") from exc

    if role_ids and group_ids:
        raise ValueError("Role ids and group ids cannot be provided together")
    return provider_id, account_id, role_ids, group_ids


if __name__ == '__main__':
    g_args = _setup_args()
    _setup_logging()
    g_api_session = _get_api_session(
        g_args.as_api_endpoint, g_args.as_session_token, g_args.as_api_token)
    if not g_api_session:
        raise ValueError("API session not found")

    g_gql_client = _get_gql_client(g_api_session, g_args.as_gql_endpoint)
    g_as_inventory = AndromedaInventory(
        g_gql_client, api_session=g_api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=g_args.as_api_endpoint, gql_endpoint=g_args.as_gql_endpoint)
    g_api_utils = APIUtils(api_endpoint=g_args.as_api_endpoint)

    g_provider_id, g_account_id, g_role_ids, g_group_ids = \
        _resolve_args_to_uuids(g_args, g_as_inventory)
    if g_args.request_favorites:
        request_favorite_access_request(
            g_api_session, g_gql_client, g_args.duration, g_args.request_description,
            g_api_utils, g_as_inventory, g_provider_id, g_account_id, g_role_ids, g_group_ids)
    else:
        make_jit_request(
            g_api_session, g_gql_client, g_args.duration, g_args.request_description,
            g_api_utils, g_as_inventory, g_provider_id, g_account_id, g_role_ids, g_group_ids,
            g_args.access_request_user_id)
