# Copyright 2025 Andromeda Security, Inc.
#
"""
This script get list of identities matching a significance / insight
"""
import argparse
import logging
import json
import os
import api_utils

from as_inventory import AndromedaInventory

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

    parser.add_argument('--as_ops_insights',
                        help='Comma Separated Opts Identity OpsInsights Eg. ADMIN_ACCOUNT')

    parser.add_argument('--as_risk_factors',
                        help='Comma Separated Risk Factors Eg. STALE')

    parser.add_argument('--as_output_dir',
                        help='Output directory for the inventory',
                        default="/tmp/andromeda-inventory/andromeda_inventory_sample")

    parser.add_argument('--as_api_endpoint', default="https://api.live.andromedasecurity.com",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--as_gql_endpoint',
                        default="https://api.live.andromedasecurity.com/graphql",
                        help='GQL endpoint for the inventory')

    parser.add_argument('--operation_type',
                        help='Output file for the inventory like identity insights or dashboard summaries',
                        default="identity_insights",
                        choices=["identity_insights", "dashboard_summary"])

    return parser.parse_args()

def _setup_logging():
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def _get_api_session(as_api_endpoint: str, as_session_token: str, as_api_token: str) -> api_utils.APIUtils:
    """
    Get the API session from the arguments or environment variables
    Args:
        args: argparse.ArgumentParser
    Returns:
        api_utils.APIUtils
    """
    au = api_utils.APIUtils(api_endpoint=as_api_endpoint)
    as_session_token = as_session_token or os.getenv("AS_SESSION_COOKIE")
    if as_session_token:
        return au.get_api_session_w_cookie(as_session_token)
    as_api_token = as_api_token or os.getenv("AS_API_TOKEN")
    if as_api_token:
        return au.get_api_session_w_api_token(as_api_token)
    raise api_utils.InvalidInputException(
        "Either as_api_token or as_session_token must be provided")

def _export_identities_with_ops_insights(
        as_inventory: AndromedaInventory, output_dir: str,
        ops_insights: str, risk_factors: str) -> None:
    """
    Export identities with ops insights to a file
    """
    json_output_f = f"{output_dir}/andromeda_inventory_sample_identities.json"
    csv_output_f = f"{output_dir}/andromeda_inventory_sample_identities.csv"
    with open(f"{json_output_f}", 'w', encoding='utf-8') as f, \
        open(f"{csv_output_f}", 'w', encoding='utf-8') as csv_f:
        humans = {}
        filters = {}
        if ops_insights:
            ops_insights = ops_insights.split(',')
            filters["significance"] = {"in": ops_insights}
        if risk_factors:
            risk_factors = risk_factors.split(',')
            filters["riskFactor"] = {"in": risk_factors}
        for h in as_inventory.as_humans_itr(filters=filters):
            #logger.debug("Identity: %s", h)
            if h["id"] not in humans:
                humans[h['id']] = h
        json.dump(list(humans.values()), f, indent=2)
        csv_f.write("id,name,email,ops_insights,risk_factors\n")
        for h in humans.values():
            h_risk_factors = [r['type'] for r in h['riskFactorsData']]
            h_ops_insights = [r['type'] for r in h['opsInsights']]
            csv_f.write(f"{h['id']},{h['name']},{h['email']},{h_ops_insights},{h_risk_factors}\n")
    logger.info("%s Identities with filters %s exported to \n json: %s\n csv:  %s",
                len(humans), filters, json_output_f, csv_output_f)

def _export_dashboard_summary(
        as_inventory: AndromedaInventory, output_dir: str) -> None:
    """
    Export dashboard summaries to a file
    """
    json_output_f = f"{output_dir}/andromeda_inventory_sample_dashboard_summaries.json"
    with open(f"{json_output_f}", 'w', encoding='utf-8') as f:
        summary = {}
        humans_summary = as_inventory.fetch_humans_summary()
        nhis_summary = as_inventory.fetch_nhis_summary()
        summary["humans_summary"] = humans_summary
        summary["nhis_summary"] = nhis_summary
        summary["providers_summary"] = as_inventory.fetch_providers_summary()
        summary["cloud_providers"] = []
        summary["application_providers"] = []
        for provider in as_inventory.cloud_provider_itr():
            summary["cloud_providers"].append(provider)
        for provider in as_inventory.app_provider_itr():
            summary["application_providers"].append(provider)
        json.dump(summary, f, indent=2)
    logger.info("Humans Summary and Service Identities Summary exported to \n json: %s",
               json_output_f)


if __name__ == '__main__':
    args = _setup_args()
    _setup_logging()
    as_api_endpoint = args.as_api_endpoint
    api_session = _get_api_session(args.as_api_endpoint, args.as_session_token, args.as_api_token)
    ai = AndromedaInventory(
        None, api_session=api_session,
        output_dir="/tmp/andromeda-inventory",
        as_endpoint=as_api_endpoint, gql_endpoint=args.as_gql_endpoint)

    if args.operation_type == "identity_insights":
        _export_identities_with_ops_insights(
            ai, args.as_output_dir, args.as_ops_insights, args.as_risk_factors)
    elif args.operation_type == "dashboard_summary":
        _export_dashboard_summary(ai, args.as_output_dir)
