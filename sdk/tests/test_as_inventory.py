
import os
import logging
import json
import pytest
from sdk.as_inventory import AndromedaInventory, AndromedaProvider
from sdk.api_utils import APIUtils
from api.graphql import graphql_query_snippets as gql_snippets

logger = logging.getLogger(__name__)
logging.getLogger("gql").setLevel(logging.ERROR)



@pytest.fixture(name="ai", scope="module")
def ai_fixture():
    au = APIUtils(api_endpoint="http://localhost:8080")
    session_cookie = os.getenv("AS_SESSION_COOKIE")
    api_token = os.getenv("AS_API_TOKEN")
    if api_token:
        api_session = au.get_api_session_w_api_token(api_token)
    elif session_cookie:
        api_session = au.get_api_session_w_cookie(session_cookie)
    else:
        raise ValueError("No API token or session cookie provided")
    gql_endpoint = os.getenv("AS_GQL_ENDPOINT", "http://localhost:8088/graphql")
    ai = AndromedaInventory(None, api_session, output_dir="/tmp/andromeda-inventory/test_as_inventory/", gql_endpoint=gql_endpoint)
    return ai

def test_provider_summmary(ai: AndromedaInventory):
    provider_summary = ai=ai.fetch_providers_summary()
    logger.info("Provider summary: %s", provider_summary)
    assert provider_summary

def test_idp_applications_data(ai: AndromedaInventory):
    filters = {"type": {"equals": "PROVIDER_TYPE_IDP_APPLICATION"}}

    for provider in ai.app_provider_itr(filters=filters, page_size=10):
        assert provider["id"]
        logger.debug("IDP Applications provider data: %s", provider["name"])
        assert provider['idpApplicationData']

def test_provider_human_eligible_data(ai: AndromedaInventory):
    filters = {"type": {"equals": "PROVIDER_TYPE_IDP_APPLICATION"}}
    for provider in ai.app_provider_itr(filters=filters, page_size=10):
        provider_id = provider["id"]
        for human in ai.provider_humans_itr(provider_id, provider):
            assert human
            logger.debug("IDP Applications provider human data: %s", human)
            assert human["identityProviderData"]

def test_idp_applications_assignments_data(ai: AndromedaInventory):
    filters = {"type": {"equals": "PROVIDER_TYPE_IDP_APPLICATION"}}
    for provider in ai.app_provider_itr(filters=filters, page_size=10):
        provider_id = provider["id"]
        if provider_id not in ai.provider_map:
            ai.provider_map[provider_id] = AndromedaProvider()
        ai.provider_map[provider_id].update(provider)
        provider = ai.provider_map[provider_id]
        assert provider["id"]
        logger.debug("IDP Applications provider data: %s", provider)
        assert provider['idpApplicationData']
        #assert provider['node']['idpApplicationData']['logo']['url']
        assignments = ai._fetch_application_assignments(provider_id, provider)
        logger.debug("IDP Applications provider assignments: %s", assignments)
        # assert assignments, f"No assignments found for {provider_data}"

        assignableUsers = ai._fetch_assignable_users(provider_id, provider)
        logger.debug("IDP Applications provider assignable users: %s", assignableUsers)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

def test_idp_applications_assignable_data(ai: AndromedaInventory):
    filters = {"type": {"equals": "PROVIDER_TYPE_IDP_APPLICATION"}}
    for provider in ai.app_provider_itr(filters=filters, page_size=10):
        provider_id = provider["id"]
        if provider_id not in ai.provider_map:
            ai.provider_map[provider_id] = AndromedaProvider()
        ai.provider_map[provider_id].update(provider)
        provider = ai.provider_map[provider_id]
        assert provider["id"]
        logger.debug("IDP Applications provider data: %s", provider)
        assert provider['idpApplicationData']

        assignableUsers = ai._fetch_assignable_users(provider_id, provider)
        logger.debug("IDP Applications provider assignable users: %s", assignableUsers)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

        assignableGroups = ai._fetch_assignable_groups(provider_id, provider)
        logger.debug("IDP Applications provider assignable users: %s", assignableGroups)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

def test_full_inventory(ai: AndromedaInventory):
    data_file = ai.download_inventory()
    assert os.path.exists(data_file)
    with open(data_file, "r") as f:
        data = json.load(f)
        assert data
    data_file_cached = ai.download_inventory(use_cached=True)
    assert os.path.exists(data_file_cached)
    assert data_file == data_file_cached, f"{data_file} != {data_file_cached}"
    with open(data_file_cached, "r") as f:
        data2 = json.load(f)
        assert data2
    assert data == data2

def test_provider_inventory(ai: AndromedaInventory, e2e_provider: dict):
    provider_id = e2e_provider["id"]
    data_file = ai.download_inventory(provider_id=provider_id)
    assert os.path.exists(data_file)
    with open(data_file, "r") as f:
        data = json.load(f)
        assert data
    #logger.debug("Provider data: %s", json.dumps(data, indent=2))
    data_file_cached = ai.download_inventory(provider_id=provider_id, use_cached=True)
    assert os.path.exists(data_file_cached)
    assert data_file == data_file_cached, f"{data_file} != {data_file_cached}"
    with open(data_file_cached, "r") as f:
        data2 = json.load(f)
        assert data2
    assert data == data2

def test_access_requests(ai: AndromedaInventory, e2e_provider: dict):
    for request in ai.as_provider_access_requests_itr(e2e_provider["id"]):
        logger.debug("Access request: %s reviews %s",
                     request['requestId'], len(request.get('reviews', [])))

def test_as_access_keys(ai: AndromedaInventory, e2e_provider: dict):
    for key in ai.as_access_keys_itr(e2e_provider["id"]):
        logger.debug("Access keys: %s",  key)


def test_as_groups(ai: AndromedaInventory, e2e_provider: dict):
    for group in ai.as_provider_groups_itr(e2e_provider["id"], e2e_provider):
        logger.debug("group keys: %s",  group)

def test_user_provider_resolved_assignments(ai: AndromedaInventory):
    """
    Test the user provider resolved assignments
    This test is to ensure that the user provider resolved assignments are fetched correctly
    for all the users in the inventory.
    This test is to ensure that the user provider resolved assignments are fetched correctly
    """

    human = next(ai.as_humans_itr())

    # for this human get the origins
    logger.debug("Human origins: %s origins %s", human['username'], len(human["origins"]))
    for origin_node in human["origins"]['edges']:
        origin = origin_node['node']
        user_id = origin["originUserId"]
        # get user providers
        user_providers = ai.as_user_providers_with_assignments_itr(user_id)
        for user_provider in user_providers:
            provider_id = user_provider["id"]
            for assignment in ai.as_user_provider_resolved_assignments_itr(user_id, provider_id):
                logger.debug("User provider resolved assignments: %s", assignment)
                logger.debug("user %s provider %s Assignment: %s",
                             user_id, provider_id, assignment)
                assert assignment["principalUsername"]
                assert assignment["providerName"]
                assert assignment["roleName"]
