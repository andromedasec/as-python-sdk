"""
# Copyright 2025 Andromeda Security, Inc.

This script Creates eligibilities based on a csv file of format:
Application, Eligibility Group,	provisioning_group_name

Validations:
- It will check if the application, eligibility group and provisioning group name are valid

Step1:
    fetch the api token from the Andromeda UI and run the script with the api token

Step2:
    export AS_SESSION_COOKIE=<session token> or
    export AS_API_TOKEN=<api token>

Step3:
    check if the mapping for the csv file matches CsvHeaderMap

Example:
    # create eligibilities
    python3 sdk/samples/as_create_eligibilities.py --eligibility_file=/tmp/eligibilities.csv
    # dry run the script
    python3 sdk/samples/as_create_eligibilities.py --eligibility_file=/tmp/eligibilities.csv --dry_run

"""

import argparse
from enum import StrEnum
import logging
import time
import os
import csv
from typing import Optional, Dict, Any
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
    parser.add_argument('--eligibility_file',
                        help='location of the csv eligibility file to be updated.',
                        required=True)
    parser.add_argument('--dry_run',
                        action='store_true',
                        help='Dry run the script')
    parser.add_argument('--cleanup',
                        action='store_true',
                        help='Cleanup mismatched eligibilities')

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


def create_app_eligibility(
        as_inventory: AndromedaInventory,
        api_session: requests.Session,
        as_api_endpoint: str,
        application: str,
        eligibility_group: str,
        provisioning_group: str,
        role_name: Optional[str] = None,
        dry_run: bool = False, cleanup: bool = False) -> Dict[str, Any]:
    """
    Create an eligibility for an application
    """
    logger.debug("Creating eligibility for %s, %s, %s, %s",
                 application, eligibility_group, provisioning_group, dry_run)
    # first check if the groups are valid
    try:
        provider_obj = next(as_inventory.app_provider_itr(
            filters={"name": {"equals": application}}))
        provider_id = provider_obj['id']
    except StopIteration as e:
        logger.error("Application %s not found", application)
        raise InvalidInputException(f"Application {application} not found") from e
    try:
        eligibility_group_obj = next(as_inventory.provider_assignable_groups_itr(
            provider_id, provider_obj, filters={"name": {"equals": eligibility_group}}))
        eligibility_group_id = eligibility_group_obj['groupDetails']['id']
    except StopIteration as e:
        logger.error("Application %s: Eligibility group %s not found", application, eligibility_group)
        raise InvalidInputException(f"Application {application}: Eligibility group {eligibility_group} not found") from e
    try:
        provisioning_group_obj = next(as_inventory.as_provider_groups_itr(
            provider_id, provider_obj, filters={"name": {"equals": provisioning_group}}))
        provisioning_group_id = provisioning_group_obj['id']
    except StopIteration as e:
        logger.error("Application %s: Provisioning group %s not found", application, provisioning_group)
        raise InvalidInputException(f"Application {application}: Provisioning group {provisioning_group} not found") from e

    eligibility_type = "PROVIDER_ELIGIBILITY" if not role_name else "ROLE_ELIGIBILITY"
    # check if the eligibility already exists
    eligibility_filters = {
        "applicationId": {"equals": provider_id},
        "principalName": {"equals": eligibility_group},
        "eligibilityType": {"equals": eligibility_type}
    }
    eligibility_obj = next(as_inventory.provider_eligibilities_itr(
        provider_id, provider_obj, filters=eligibility_filters), None)
    if eligibility_obj:
        logger.debug("Eligibility already exists for %s, %s, %s: %s",
                    application, eligibility_group, provisioning_group, eligibility_obj)
        eligibility_id = eligibility_obj['eligibilityId']
        if cleanup and eligibility_obj[
                'provisioningGroupConfiguration']['id'] != provisioning_group_id:
            logger.error("Eligibility %s is mismatched with the provisioning group %s, deleting",
                        eligibility_id,
                        eligibility_obj['provisioningGroupConfiguration']['id'])
            if dry_run:
                logger.info(
                    "Dry run: eligibility %s provisioning group mismatched %s, deleting",
                    eligibility_id,
                    eligibility_obj['provisioningGroupConfiguration']['id'])
            else:
                resp = api_session.delete(
                    f"{as_api_endpoint}/providers/{provider_id}/eligibilities/{eligibility_id}")
                #resp.raise_for_status()
                logger.info("Eligibility deleted for %s, %s, %s, %s, response: %s",
                            application, eligibility_group, provisioning_group, eligibility_id, resp.status_code)
                time.sleep(2)
        else:
            return eligibility_obj
    else:
        logger.debug("no eligibility found for %s, %s, %s",
                    application, eligibility_group, eligibility_filters)
    eligibility_data = {
        "providerId": provider_id,
        "eligibilityType": "PROVIDER_ELIGIBILITY",
        "provisioningGroupId": provisioning_group_id,
        "eligibleGroupIds": [eligibility_group_id],
        "eligibilityConstraint":{"scopeType":"PROVIDER"},
        "provisioningGroupConfiguration":{
            "name": provisioning_group,
            "id": provisioning_group_id
        }
    }
    if dry_run:
        logger.info("Dry run: Eligibility data: %s", application)
        return eligibility_data

    resp = api_session.post(f"{as_api_endpoint}/providers/{provider_id}/eligibilities",
                            json=eligibility_data)
    resp.raise_for_status()
    eligibility_obj = resp.json()
    logger.info("Eligibility created for %s, %s, %s, %s",
                application, eligibility_group, provisioning_group, eligibility_obj)
    return eligibility_obj

class CsvHeaderMap(StrEnum):
    """Represents a permission access level in the custom application inventory."""
    PROVIDER = "Application"
    ELIGIBILITY_GROUP = "Eligibility Group"
    PROVISIONING_GROUP = "provisioning_group_name"
    ROLE_NAME = "role_name"


def check_n_update_app_enforcement_mode(
        as_inventory: AndromedaInventory,
        api_session: requests.Session,
        as_api_endpoint: str,
        application: str,
        dry_run: bool = False) -> None:
    """
    Check if the application is in enforcement mode and if not then change it to enforcement mode
    """
    try:
        application_obj = next(as_inventory.app_provider_itr(
            page_size=25,
            filters={"name": {"equals": application}}))
    except StopIteration as e:
        logger.error("Application %s not found", application)
        raise InvalidInputException(f"Application {application} not found") from e
    if application_obj["mode"] == "ENFORCEMENT":
        logger.debug("Application %s is already in enforcement mode", application)
    else:
        logger.debug("Application %s is not in enforcement mode, changing to enforcement mode",
                    application)
    resp = api_session.get(f"{as_api_endpoint}/providers/{application_obj['id']}/idpapplication/config")
    resp.raise_for_status()
    provider_config = resp.json()
    provider_config["mode"] = "ENFORCEMENT"
    provider_config["accessRequestProvisioningConfig"] = {
        "provisioningPolicy": "IDENTITY_ACCESS_VIA_GROUP_BINDING",
        "managedProvisioningGroupConfig": {
            "matchType": "CUSTOM_GROUP"
        }
    }
    if dry_run:
        logger.info("Dry run: provider enforcement mode config: %s: %s", application, provider_config['id'])
        return
    resp = api_session.put(f"{as_api_endpoint}/providers/{application_obj['id']}/idpapplication/config", json=provider_config)
    resp.raise_for_status()
    logger.info("Application:%s is now in enforcement mode", application)

def create_eligibilities(
        as_api_endpoint: str,
        as_inventory: AndromedaInventory,
        api_session: requests.Session,
        eligibility_file: str,
        dry_run: bool = False, cleanup: bool = False) -> None:
    """
    Create eligibilities based on a csv file of format:
    Application, Eligibility Group,	provisioning_group_name

    Validations:
    - It will check if the application, eligibility group and provisioning group name are valid
    - Check if application is in enforcement mode and if not then change it to enforcement mode

    Args:
        as_inventory: AndromedaInventory
        api_session: requests.Session
        as_api_endpoint: str
        eligibility_file: str
    """
    with open(eligibility_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        eligibilities_map = {}
        for row in reader:
            try:
                application = row[CsvHeaderMap.PROVIDER.value]
                eligibility_group = row[CsvHeaderMap.ELIGIBILITY_GROUP.value]
                provisioning_group = row[CsvHeaderMap.PROVISIONING_GROUP.value]
                role_name = row.get('role_name', None)
            except KeyError as e:
                logger.error("Invalid row: %s error: %s skipping", row, e)
                continue
            if not application or not eligibility_group or not provisioning_group:
                raise InvalidInputException(f"Invalid row: {row}")

            if application not in eligibilities_map:
                eligibilities_map[application] = []
            eligibilities_map[application].append({
                "eligibility_group": eligibility_group,
                "provisioning_group": provisioning_group,
                "role_name": role_name
            })
        for application, eligibility in eligibilities_map.items():
            # check if the application is in enforcement mode
            try:
                check_n_update_app_enforcement_mode(
                    as_inventory, api_session, as_api_endpoint, application, dry_run)
            except InvalidInputException as e:
                logger.error("Invalid application: %s, error: %s", application, e)
                continue
            for e in eligibility:
                try:
                    eligibility_group = e["eligibility_group"]
                    provisioning_group = e["provisioning_group"]
                    role_name = e["role_name"]
                    create_app_eligibility(
                        as_inventory, api_session, as_api_endpoint,
                        application, eligibility_group, provisioning_group, role_name, dry_run, cleanup)
                except InvalidInputException as e:
                    logger.error("Invalid input: %s", e)
                    continue

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
    create_eligibilities(
        args.as_api_endpoint, as_inventory, api_session,
        args.eligibility_file, args.dry_run, args.cleanup)
