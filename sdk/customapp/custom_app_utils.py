# Utility Class for CustomApp

from typing import Any
import argparse


# Constants
DEFAULT_BATCH_SIZE = 100
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME_PREFIX = ""
DEFAULT_INVENTORY_TYPE = "CUSTOM_TYPE1_INVENTORY_CSV"

def convert_to_andromeda_dict(obj: Any) -> Any:
    """
    Recursively remove any items that are either empty or equal to null value
    """
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return {k: convert_to_andromeda_dict(v) for k, v in obj.items() if v}
    if isinstance(obj, list):
        return [convert_to_andromeda_dict(item) for item in obj if item]
    return obj


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    help_text = """
    This script converts different CSV imports into Andromeda custom inventory format.

    Example:
        python3 custom_app_inventory_transformer.py --inventory_type=CUSTOM_TYPE1_INVENTORY_CSV --inventory_file=<file> --output_dir=<dir>
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=help_text
    )

    parser.add_argument(
        '--app_name',
        help='Application name',
        default=DEFAULT_APP_NAME_PREFIX
    )

    parser.add_argument(
        '--output_dir',
        help='Output directory',
        default=DEFAULT_OUTPUT_DIR
    )

    parser.add_argument(
        '--inventory_type',
        help='Inventory type',
        default=DEFAULT_INVENTORY_TYPE
    )

    parser.add_argument(
        '--inventory_file', '-i',
        help='inventory file name. Eg. inventory.csv',
        default="")

    return parser.parse_args()
