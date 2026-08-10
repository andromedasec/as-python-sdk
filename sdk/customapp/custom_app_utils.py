# Utility Class for CustomApp

from typing import Any, List, Optional
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


def normalize_csv_fieldnames(fieldnames: Optional[List[str]]) -> Optional[List[str]]:
    """
    Strip the UTF-8 BOM and surrounding whitespace from CSV header names.

    Exports frequently carry a BOM on the first column and stray spaces after the
    delimiter, so a header line like `Name, Username` parses its second column as
    ' Username'. Lookups such as row.get('Username') then return None for every
    row rather than raising, and the empty value travels downstream as a missing
    id. Normalizing the header names keeps those lookups resolving.

    Raises:
        ValueError: if two or more headers normalize to the same name --
            csv.DictReader would silently keep only the last matching column's
            value for every row, dropping the others.
    """
    if fieldnames is None:
        return None
    normalized = [(name or '').replace('\ufeff', '').strip() for name in fieldnames]
    seen = set()
    duplicates = sorted({name for name in normalized if name in seen or seen.add(name)})
    if duplicates:
        raise ValueError(
            f"CSV contains duplicate header names after normalization: {duplicates}")
    return normalized


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
