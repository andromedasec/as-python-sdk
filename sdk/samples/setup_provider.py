import argparse
from ipaddress import ip_address
import os
import requests
import logging
import yaml
from sdk import api_utils
import traceback


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def _get_setup_config(as_settings: str = "andromeda_settings.yaml") -> dict:
    """ Load the setup config from the yaml file """
    cwd = os.path.dirname(os.path.abspath(__file__))
    data = None
    try:
        with open(os.path.join(cwd, as_settings), "r",
                  encoding='utf-8') as yaml_file:
            data = yaml.safe_load(yaml_file)
    except Exception as exc:
        logger.error('Failed to load setup config')
        logger.error('exception %s\n %s', exc, traceback.format_exc())
        raise exc
    return data


def _get_base_provider(provider_name: str, provider_type: str = "PROVIDER_TYPE_AWS") -> dict:
    """
    This function returns a dictionary with the provider config
    """
    provider_config = {
        "name": provider_name,
        "type": provider_type,
    }
    return provider_config

def _get_aws_config_object(
        profile_name: str, config: dict, idp_provider_obj: dict = None) -> dict:
    """ Create provider config object """
    aws_provider = config['settings']['cloud_provider']['awsConfiguration']

    if aws_provider.get('enable_resource_inventory', False):
        aws_provider['enableResourceInventory'] = True

    if aws_provider['authConfig']['authMode'] == "AWS_AUTHMODE_ASSUME_ROLE_WITH_CREDENTIALS":
        aws_provider['authConfig']['assumeRoleWithCredentials']['accessKeyId'] = os.environ['AWS_MGMT_ACCESS_KEY_ID']
        aws_provider['authConfig']['assumeRoleWithCredentials']['secretAccessKey'] = os.environ['AWS_MGMT_SECRET_ACCESS_KEY']
    return aws_provider

def create_or_update_idp_provider(api_session: requests.Session, au: api_utils.APIUtils, config: dict, dry_run: bool = False) -> tuple[int, dict, dict]:
    """
    This function creates or updates an IDP provider
    """
    idp_provider = config['settings'].get('idp_provider', None)
    if not idp_provider:
        return 200, None, None
    idp_provider_config = _get_base_provider(idp_provider['name'], idp_provider['provider_type'])
    idp_provider_config['mode'] = idp_provider.get('mode', "OBSERVATION")
    if idp_provider_config['mode'] == "ENFORCEMENT":
        idp_provider_config['provisioningConfig'] = idp_provider.get('provisioningConfig', None)
    else:
        idp_provider_config['provisioningConfig'] = {
            "provisioningPolicy": "PRINCIPAL_DIRECT_BINDING"
        }

    if dry_run:
        logger.debug("Skipping idp provider creation %s", idp_provider_config)
        return 200, None, None
    status_code, idp_provider_obj = au.create_or_update_base_provider(
        api_session, idp_provider_config)
    logger.debug("idp provider obj %s", idp_provider_obj)
    if status_code != 200 or not idp_provider_obj:
        raise Exception(
            f'Failed to create idp provider {idp_provider["name"]} status_code {status_code} response {idp_provider_obj}')
    provider_id = idp_provider_obj['id']
    idp_config_obj = None
    if idp_provider['provider_type'] == "PROVIDER_TYPE_OKTA":
        okta_config_obj = config['settings']['idp_provider']['oktaConfiguration']
        if not okta_config_obj.get('accessToken', None):
            okta_config_obj['accessToken'] = os.environ['OKTA_ACCESS_TOKEN']
        status_code, idp_config_obj = au.create_or_update_okta_provider_config(
            api_session, provider_id, okta_provider_obj=okta_config_obj)
    return status_code, idp_provider_obj, idp_config_obj


def create_or_update_cloud_provider(api_session: requests.Session, au: api_utils.APIUtils, config: dict, idp_provider_obj: dict, dry_run: bool = False) -> tuple[int, dict]:
    cloud_provider = config['settings'].get('cloud_provider', None)
    if not cloud_provider:
        return None, None
    if cloud_provider['provider_type'] == "PROVIDER_TYPE_AWS":
        status_code, cloud_provider_obj, _ = create_or_update_aws_provider(
            api_session, au, config, idp_provider_obj, dry_run)
    return status_code, cloud_provider_obj


def create_or_update_providers(api_session: requests.Session, au: api_utils.APIUtils, config: dict, dry_run: bool = False) -> tuple[int, dict]:
    """
    1. Check and setup IDP provider
    2. Check and setup cloud provider
    """
    _, idp_provider_obj, _ = create_or_update_idp_provider(api_session, au, config, dry_run)
    # check if cloud provider is present
    _, cloud_provider_obj = create_or_update_cloud_provider(api_session, au, config, idp_provider_obj, dry_run)
    return idp_provider_obj, cloud_provider_obj

def create_or_update_aws_provider(api_session: requests.Session, au: api_utils.APIUtils, config: dict,
                                  idp_provider_obj: dict, dry_run: bool = False) -> None:
    """
    This function creates or updates an AWS provider
    """
    provider_name = config['settings']['cloud_provider']['name']
    provider_config = _get_base_provider(provider_name)
    if idp_provider_obj:
        provider_config['idpProviderId'] = idp_provider_obj['id']
    if provider_config.get('mode', "ACCOUNT_MODE_OBSERVATION") == "ACCOUNT_MODE_ENFORCEMENT":
        provider_config['provisioningConfig'] = config['settings']['cloud_provider']['provisioningConfig']
    else:
        provider_config['provisioningConfig'] = {
            "provisioningPolicy": "PRINCIPAL_DIRECT_BINDING"
        }

    if dry_run:
        logger.debug("Skipping aws provider creation %s", provider_config)
        return 200, None, None

    status_code, provider_obj = au.create_or_update_base_provider(
        api_session, provider_config)
    logger.debug("provider obj %s", provider_obj)
    if status_code != 200 or not provider_obj:
        raise Exception(
            f'Failed to create provider {provider_name} status_code {status_code} provider_obj {provider_obj}')
    provider_id = provider_obj['id']
    aws_provider_config = _get_aws_config_object(provider_name, config, idp_provider_obj)
    if idp_provider_obj:
        aws_provider_config['iamSsoIntegration'] = {
            "providerId": idp_provider_obj['id'],
        }
    status_code, aws_config = au.create_or_update_aws_provider_config(
        api_session, provider_id, aws_provider_config)
    if status_code != 200 or not aws_config:
        raise Exception(
            f'Failed to create aws config for provider {provider_name} status_code {status_code} aws_config {aws_config}')
    logger.info("Successfully created provider and aws config %s", provider_name)
    return status_code, provider_obj, aws_config


def create_or_update_environments(api_session: requests.Session, au: api_utils.APIUtils, config: dict, dry_run: bool = False) -> None:
    """
    This function creates or updates environments with criticality
    """
    envs = config['settings'].get('environments', [])
    logger.info("Create or update %d environments", len(envs))
    for env in envs:
        if dry_run:
            logger.debug("Skipping environment setting %s", env)
            continue
        au.create_or_update_environment(api_session, env)


def patch_environment_mappings(api_session: requests.Session, au: api_utils.APIUtils, config: dict, dry_run: bool = False) -> None:
    patches = config['settings'].get('environment_mapping_policies_patches', [])
    logger.info("applying %d patches to the environment mapping", len(patches))
    for p in patches:
        logger.info("applying patch to provider %s", p['provider_name'])
        status_code, provider_obj = au.get_resource_by_name(
            api_session, "providers", p['provider_name'])
        if status_code != 200:
            logger.error("Did not find provider %s", p['provider_name'])
            return
        # fetch the existing provider mapping
        provider_id = provider_obj['id']
        url = au.get_resource_url(f"providers/{provider_id}/environmentmappingpolicies")
        response = api_session.get(url)
        if response.status_code != 200 or not response.json()['results']:
            return
        env_policy = response.json()['results'][0]
        au.patch_policy_rules(p, env_policy)
        for rule in env_policy['rules']:
            env = rule.get('environment_name', "")
            if not env:
                # needs no fixing
                continue
            status_code, e = au.get_resource_by_name(api_session, 'environments', env)
            if not e:
                logger.error("did not find environment %s", env)
                raise api_utils.InvalidInputException("Environment %s not found" % env)
            rule.pop('environment_name')
            rule['environmentId'] = e['id']
        # find if rule exists
        url = au.get_resource_url(
            f"providers/{provider_id}/environmentmappingpolicies",
            resource_id=env_policy["id"])
        response = api_session.put(url, json=env_policy)
        logger.info("updated policy %s status_code %s", url, response.status_code)


def patch_sensitivity_mappings(api_session: requests.Session, au: api_utils.APIUtils, config: dict, dry_run: bool = False) -> None:
    patches = config['settings'].get('sensitivity_mapping_policies_patches', [])
    logger.info("applying %d patches to the sensitivity mapping", len(patches))
    for p in patches:
        logger.info("applying patch to provider %s", p['provider_name'])
        status_code, provider_obj = au.get_resource_by_name(
            api_session, "providers", p['provider_name'])
        if status_code != 200:
            logger.error("Did not find provider %s", p['provider_name'])
            return
        # fetch the existing provider mapping
        provider_id = provider_obj['id']
        url = au.get_resource_url(f"providers/{provider_id}/sensitivitymappingpolicies")
        response = api_session.get(url)
        if response.status_code != 200 or not response.json()['results']:
            return
        policy = response.json()['results'][0]
        au.patch_policy_rules(p, policy)
        url = au.get_resource_url(
            f"providers/{provider_id}/sensitivitymappingpolicies",
            resource_id=policy["id"])
        response = api_session.put(url, json=policy)
        logger.info("updated policy %s status_code %s result %s",
                    url, response.status_code, response.json())


if __name__ == '__main__':
    HELP_STR = """
    This script creates or updates an Andromeda Provider. It takes the parameters from the andromeda_settings.yaml file.

    Step1:
       export OKTA_ACCESS_TOKEN=<okta token>
    Step2:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step3:
        create upate settings file like andromeda_settings_iam_sso.yaml

    Example:
        python3 lib/python/sdk/samples/setup_provider.py --setup_tenant --as_settings=andromeda_settings_iam_sso.yaml --api_token <api_token>

    Note:
        When using AWS_AUTHMODE_ASSUME_ROLE_WITH_CREDENTIALS the script looks for following env variables
        AWS_MGMT_ACCESS_KEY_ID, AWS_MGMT_SECRET_ACCESS_KEY, AWS_LOGS_ACCESS_KEY_ID, AWS_LOGS_SECRET_ACCESS_KEY
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(HELP_STR)
    )

    parser.add_argument('--api_token', '-t',
                        help='API token for Andromeda')

    parser.add_argument('--setup_provider',
                        help='Create a new provider', action='store_true')

    parser.add_argument('--setup_tenant',
                        help='Setup all as configurations from the config file', action='store_true')

    parser.add_argument('--as_settings',
                        help='YAML file with andromeda settings')

    parser.add_argument('--dry_run',
                        help='Prints the configuration without making the change', action='store_true')


    config = _get_setup_config(parser.parse_args().as_settings)

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    api_endpoint = config['settings'].get(
        'api_endpoint', "https://api.staging.andromedasecurity.com")
    au = api_utils.APIUtils(api_endpoint=api_endpoint)

    api_session = None
    session_cookie = config['settings'].get('cookie', "")

    if session_cookie:
        logger.debug("Using cookie for session")
        api_session = au.get_api_session_w_cookie(session_cookie)
    elif parser.parse_args().api_token:
        api_session = au.get_api_session_w_api_token(
            parser.parse_args().api_token)

    dry_run = parser.parse_args().dry_run
    if not api_session:
        raise api_utils.APISessionException()

    if parser.parse_args().setup_tenant:
        create_or_update_environments(api_session, au, config, dry_run)

    if parser.parse_args().setup_provider or parser.parse_args().setup_tenant:
        create_or_update_providers(api_session, au, config, dry_run)

    # if parser.parse_args().setup_provider or parser.parse_args().setup_as_tenant:
    #     create_or_update_aws_provider(api_session, au, config, dry_run)

    if parser.parse_args().setup_tenant:
        patch_environment_mappings(api_session, au, config, dry_run)

    if parser.parse_args().setup_tenant:
        patch_sensitivity_mappings(api_session, au, config, dry_run)
