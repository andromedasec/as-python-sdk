
import os
import logging
import json
import pytest
from as_inventory import AndromedaInventory, AndromedaProvider
from api_utils import APIUtils
from api.graphql import graphql_query_snippets as gql_snippets

logger = logging.getLogger(__name__)

@pytest.fixture(name="ai", scope="module")
def ai_fixture():
    au = APIUtils()
    session_cookie = os.getenv("AS_SESSION_COOKIE")
    api_session = au.get_api_session_w_cookie(session_cookie)
    gql_endpoint = os.getenv("AS_GQL_ENDPOINT", "http://localhost:8088/graphql")
    ai = AndromedaInventory(None, api_session, output_dir="/tmp/andromeda-inventory/test_as_inventory/", gql_endpoint=gql_endpoint)
    return ai


def test_provider_summmary(ai: AndromedaInventory):
    provider_summary = ai=ai._fetch_providers_summary()
    logger.info("Provider summary: %s", provider_summary)
    assert provider_summary

def test_provider_data(ai: AndromedaInventory):
    providers = ai._fetch_cloud_providers()
    assert providers, "No providers found"
    for provider in providers["Providers"]["edges"]:
        assert provider["node"]["id"]
        logger.debug("Provider data: %s", provider)
        assert provider["node"]

def test_idp_applications_data(ai: AndromedaInventory):
    providers = ai._fetch_idp_applications_providers()
    assert providers, "No IDP applications providers found"
    for provider in providers["Providers"]["edges"]:
        assert provider["node"]["id"]
        provider_id, provider_data = provider["node"]["id"], provider["node"]
        logger.debug("IDP Applications provider data: %s", provider)
        assert provider["node"]
        assert provider['node']['idpApplicationData']

def test_idp_applications_assignments_data(ai: AndromedaInventory):
    providers = ai._fetch_idp_applications_providers()
    assert providers, "No IDP applications providers found"
    for provider in providers["Providers"]["edges"]:
        provider_id, provider_data = provider["node"]["id"], provider["node"]
        if provider_id not in ai.provider_map:
            ai.provider_map[provider_id] = AndromedaProvider()
        ai.provider_map[provider_id].update(provider_data)
        provider_data = ai.provider_map[provider_id]
        assert provider["node"]["id"]
        logger.debug("IDP Applications provider data: %s", provider)
        assert provider["node"]
        assert provider['node']['idpApplicationData']
        #assert provider['node']['idpApplicationData']['logo']['url']
        assignments = ai._fetch_application_assignments(provider_id, provider_data)
        logger.debug("IDP Applications provider assignments: %s", assignments)
        # assert assignments, f"No assignments found for {provider_data}"

        assignableUsers = ai._fetch_assignable_users(provider_id, provider_data)
        logger.debug("IDP Applications provider assignable users: %s", assignableUsers)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

def test_idp_applications_assignable_data(ai: AndromedaInventory):
    providers = ai._fetch_idp_applications_providers()
    assert providers, "No IDP applications providers found"
    for provider in providers["Providers"]["edges"]:
        provider_id, provider_data = provider["node"]["id"], provider["node"]
        if provider_id not in ai.provider_map:
            ai.provider_map[provider_id] = AndromedaProvider()
        ai.provider_map[provider_id].update(provider_data)
        provider_data = ai.provider_map[provider_id]
        assert provider["node"]["id"]
        logger.debug("IDP Applications provider data: %s", provider)
        assert provider["node"]
        assert provider['node']['idpApplicationData']

        assignableUsers = ai._fetch_assignable_users(provider_id, provider_data)
        logger.debug("IDP Applications provider assignable users: %s", assignableUsers)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

        assignableGroups = ai._fetch_assignable_groups(provider_id, provider_data)
        logger.debug("IDP Applications provider assignable users: %s", assignableGroups)
        #assert assignableUsers, f"No assignable users found for {provider_data}"

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



def test_full_inventory(ai: AndromedaInventory):
    data_file = ai.download_inventory()
    assert os.path.exists(data_file)
