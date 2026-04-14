"""
Custom App S3 CSV Downloader

Downloads a CSV file from S3 using static IAM user credentials,
transforms it into the standardized CustomApp JSON format for ingestion.

The output JSON matches the CustomAppUser proto definition (protojson format),
which is consumed by the ingester's customapp user transformer.

Auth config (via AS_CUSTOM_APP_AUTH_JSON env var):
{
    "aws_access_key_id": "AKIA...",
    "aws_secret_access_key": "...",
    "aws_region": "us-west-2",
    "s3_bucket": "my-bucket",
    "s3_key": "folder/path/users.csv"
}

Example:
    python3 custom_app_s3_csv_downloader.py --app_name=acme --output_dir=/tmp/customapp_export
"""

import os
import csv
import argparse
import logging
import datetime
import json
import tempfile
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME_PREFIX = "test"

# HR category string → proto HrType enum name mapping
HR_CATEGORY_MAP = {
    "employee": "EMPLOYEE",
    "contingent worker": "CONTINGENT_WORKER",
    "third party": "THIRD_PARTY",
}

# IdentityStatus enum name mapping
STATUS_ENABLED = "ENABLED"
STATUS_DEACTIVATED = "DEACTIVATED"


# Data Classes
class UserStatus(Enum):
    """Represents a user status in the custom application inventory."""
    ENABLED = "ENABLED"
    DEACTIVATED = "DEACTIVATED"
    IDENTITY_STATUS_UNRESOLVED = "IDENTITY_STATUS_UNRESOLVED"
    SUSPENDED = "SUSPENDED"

class PrincipalType(Enum):
    """Represents a principal type in the custom application inventory."""
    HUMAN = "HUMAN"
    NHI = "NHI"
    GROUP = "GROUP"

class RoleType(Enum):
    """Represents a role type in the custom application inventory."""
    CUSTOM_APP_ROLE = "CUSTOM_APP_ROLE"
    CUSTOM_APP_USER_ROLE = "CUSTOM_APP_USER_ROLE"

class PermissionAccessLevel(Enum):
    """Represents a permission access level in the custom application inventory."""
    UNSPECIFIED = "UNSPECIFIED"
    LIST = "LIST"
    WRITE_TAG = "WRITE_TAG"
    DELETE_TAG = "DELETE_TAG"
    READ_METADATA = "READ_METADATA"
    READ_DATA = "READ_DATA"
    WRITE_METADATA = "WRITE_METADATA"
    CREATE = "CREATE"
    WRITE_DATA = "WRITE_DATA"
    DELETE_DATA = "DELETE_DATA"
    DELETE = "DELETE"
    PERMISSIONS_MANAGEMENT = "PERMISSIONS_MANAGEMENT"

class ScopeType(Enum):
    """Represents a scope type in the custom application inventory."""
    UNSPECIFIED = "UNSPECIFIED"
    PROVIDER = "PROVIDER"
    FOLDER = "FOLDER"
    ACCOUNT = "ACCOUNT"
    RESOURCE_GROUP = "RESOURCE_GROUP"

class HrType(str, Enum):
    """Represents a HR type in the custom application inventory."""
    HR_TYPE_UNSPECIFIED = ""
    EMPLOYEE = "EMPLOYEE"
    CONTINGENT_WORKER = "CONTINGENT_WORKER"
    THIRD_PARTY = "THIRD_PARTY"

class NhiType(Enum):
    """Represents a service identity type in the custom application inventory."""
    CUSTOM_APP_NHI = "CUSTOM_APP_NHI"

@dataclass
class CustomAppUserHRISAttributes:
    """HRIS attributes for a custom app user (matches CustomAppUserHRISAttributes proto)."""
    email: Optional[str] = None
    org_name: Optional[str] = None
    business_title: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    position_title: Optional[str] = None
    division: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None

@dataclass
class CustomAppUser:
    """Represents a user in the custom application inventory (matches CustomAppUser proto)."""
    id: str
    username: str
    name: str
    status: Optional[str] = UserStatus.ENABLED.value
    hr_type: Optional[HrType] = None
    hris_attributes: Optional[CustomAppUserHRISAttributes] = None

@dataclass
class CustomAppInventory:
    """Container for all custom application inventory data."""
    users: Dict[str, CustomAppUser] = field(default_factory=dict)

class InventoryBuilder:
    """Builds CustomAppUser objects from CSV row data."""

    @staticmethod
    def _get_csv_field(row: dict, field: str, default: str = "") -> str:
        """Get a trimmed CSV field value using the column map."""
        return row.get(field, default).strip()

    @staticmethod
    def parse_hr_type(category: str) -> Optional[HrType]:
        """Convert CSV category value to HrType enum."""
        if not category:
            return None
        name = HR_CATEGORY_MAP.get(category.strip().lower())
        if name is None:
            return None
        return HrType(name)

    @staticmethod
    def parse_active_status(active: str) -> str:
        """Convert CSV active boolean string to proto IdentityStatus enum string."""
        if active.strip().lower() == "true":
            return STATUS_ENABLED
        return STATUS_DEACTIVATED

    @staticmethod
    def format_timestamp(date_str: str) -> Optional[str]:
        """Convert a date string (YYYY-MM-DD) to RFC 3339 format for protojson Timestamp."""
        if not date_str:
            return None
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            logger.warning("Could not parse date: %s", date_str)
            return None

    def create_user_from_mapped_row(self, row: dict) -> Optional[CustomAppUser]:
        """Create a CustomAppUser from a CSV row.

        Returns None if the row has no user_id.
        """
        g = lambda field, default="": self._get_csv_field(row, field, default)

        user_id = g("user_id")
        if not user_id:
            logger.warning("Skipping row with empty user_id: %s", row)
            return None

        first_name = g("first_name")
        last_name = g("last_name")
        email = g("email")
        username = g("username") or email or user_id

        hris_attrs = CustomAppUserHRISAttributes(
            email=email or None,
            org_name=g("org_name") or None,
            business_title=g("business_title") or None,
            manager_id=g("super_ref") or None,
            manager_name=g("managername") or None,
            position_title=g("position_title") or None,
            division=g("division") or None,
            city=g("city") or None,
            state=g("state") or None,
            country=g("country") or None,
            hire_date=self.format_timestamp(g("hire_date")),
            termination_date=self.format_timestamp(g("termination_date")),
        )

        return CustomAppUser(
            id=user_id,
            username=username,
            name=f"{first_name} {last_name}".strip(),
            status=self.parse_active_status(g("active", "true")),
            hr_type=self.parse_hr_type(g("category")),
            hris_attributes=hris_attrs,
        )

class CustomAppInventoryTransformer:
    """Transforms CSV inventory files into a CustomAppInventory."""
    inventory: CustomAppInventory
    _builder: InventoryBuilder

    def __init__(self) -> None:
        self.inventory = CustomAppInventory()
        self._builder = InventoryBuilder()

    def transform_csv(self, csv_path: str) -> None:
        """Parse a CSV file and populate self.inventory with CustomAppUser objects."""
        users: Dict[str, CustomAppUser] = {}

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user = self._builder.create_user_from_mapped_row(row)
                if user is not None:
                    users[user.username] = user

        self.inventory.users = users
        logger.info("Parsed %d users from CSV", len(users))

    @staticmethod
    def convert_to_andromeda_dict(obj: Any) -> Any:
        """Recursively remove empty values from nested dicts/lists."""
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return {
                k: CustomAppInventoryTransformer.convert_to_andromeda_dict(v)
                for k, v in obj.items() if v
            }
        if isinstance(obj, list):
            return [
                CustomAppInventoryTransformer.convert_to_andromeda_dict(item)
                for item in obj if item
            ]
        return obj

class CustomAppInventoryIOHandler:
    """Handles input and output of custom application inventory data."""
    def download_csv_from_s3(self, auth_config: dict, metadata: dict) -> str:
        """Download a CSV file from S3 and return the local file path.

        Requires static IAM user credentials (aws_access_key_id,
        aws_secret_access_key, aws_region) plus s3_bucket and s3_key.
        """
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 is required for S3 downloads. Install it with: pip install boto3")

        aws_access_key_id = auth_config.get("aws_access_key_id")
        aws_secret_access_key = auth_config.get("aws_secret_access_key")
        aws_region = metadata.get("aws_region")
        s3_bucket = metadata.get("s3_bucket")
        file_path = metadata.get("file_path")

        missing = [
            k for k, v in {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
                "aws_region": aws_region,
                "s3_bucket": s3_bucket,
                "file_path": file_path,
            }.items() if not v
        ]
        if missing:
            raise ValueError(f"Missing required fields in auth config: {', '.join(missing)}")

        logger.info("Downloading CSV from S3 bucket=%s file_path=%s region=%s", s3_bucket, file_path, aws_region)

        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
        s3_client = session.client("s3")

        tmp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        try:
            s3_client.download_file(s3_bucket, file_path, tmp_file.name)
            logger.info("Downloaded CSV to %s", tmp_file.name)
            return tmp_file.name
        except Exception:
            os.unlink(tmp_file.name)
            raise

    def export_inventory(self, inventory: CustomAppInventory, app_name_prefix: str, output_dir: str) -> str:
        """Export inventory to a timestamped JSON file.

        Converts dataclass objects to dicts, strips empty values, and writes JSON.

        Returns:
            Path to the written JSON file.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().replace(microsecond=0, second=0).isoformat()
        output_file = Path(output_dir) / f"{app_name_prefix}-{timestamp}.json"

        users_dict = {k: asdict(v) for k, v in inventory.users.items()}
        cleaned = CustomAppInventoryTransformer.convert_to_andromeda_dict({"users": users_dict})

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)

        logger.info("Written inventory to file %s", output_file)
        return str(output_file)


def setup_logging() -> None:
    """Setup logging configuration."""
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    help_text = """
    Downloads a CSV from S3 and transforms it into
    the Andromeda custom app inventory JSON format.

    Auth config (via AS_CUSTOM_APP_AUTH_JSON env var):

        AS_CUSTOM_APP_AUTH_JSON='{"aws_access_key_id":"AKIA...","aws_secret_access_key":"...","aws_region":"us-west-2","s3_bucket":"my-bucket","s3_key":"folder/users.csv"}'
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=help_text,
    )

    parser.add_argument(
        "--app_name",
        help="Application name prefix for output file",
        default=DEFAULT_APP_NAME_PREFIX,
    )
    parser.add_argument(
        "--output_dir",
        help="Output directory for JSON file",
        default=DEFAULT_OUTPUT_DIR,
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    setup_logging()
    args = parse_arguments()

    csv_path = None
    auth_config: Optional[dict] = None
    metadata: Optional[dict] = None

    try:
        auth_json = os.environ.get('AS_CUSTOM_APP_AUTH_JSON', '')
        if auth_json:
            # load the auth JSON as a dictionary
            auth_config = json.loads(auth_json)
            logger.info("Auth JSON found for app: %s", args.app_name.strip())
        else:
            logger.error("No auth JSON found for app: %s", args.app_name.strip())
            raise ValueError("No auth JSON found for app: %s", args.app_name.strip())

        metadata_json = os.environ.get('AS_CUSTOM_APP_METADATA', '')
        if metadata_json:
            metadata = json.loads(metadata_json)
            logger.info("Metadata JSON found for app: %s", args.app_name.strip())
        else:
            logger.info("No metadata JSON found for app: %s", args.app_name.strip())
            raise ValueError("No metadata JSON found for app: %s, s3 bucked name, path-to-file, aws-region is required", args.app_name.strip())

        io_handler = CustomAppInventoryIOHandler()
        csv_path = io_handler.download_csv_from_s3(auth_config or {}, metadata or {})

        transformer = CustomAppInventoryTransformer()
        transformer.transform_csv(csv_path)

        output_file = io_handler.export_inventory(
            transformer.inventory,
            app_name_prefix=args.app_name.strip(),
            output_dir=args.output_dir.strip(),
        )
        logger.info("Transformation completed successfully of file: %s for app: %s", output_file, args.app_name.strip())

    except Exception as e:
        logger.error("Transformation failed for app: %s: %s", args.app_name.strip(), e)
        raise
    finally:
        if csv_path and os.path.exists(csv_path):
            os.unlink(csv_path)
            logger.info("Cleaned up temporary CSV file for app: %s", args.app_name.strip())


if __name__ == "__main__":
    main()
