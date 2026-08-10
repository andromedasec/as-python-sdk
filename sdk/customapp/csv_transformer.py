
"""
Custom App CSV Transformer

This module provides functionality to transform CSV inventory files into
a standardized JSON format for custom applications.

The single app is set up to be used for multiple custom apps to make it easy
to share common code and maintainability. It is not a requirement to share the
transformer code between app but framework allows for that.

The transformer is based on three important parts

1. Base Class `CustomAppCSVTransformer` that implements most common
utilities for the custom app. It implements utilities like csv readers, writers
validators etc. Important functions to be overriden are:
1.1 process_csv_row: This is callback invoked on every row.
1.2 constructor: for any set up for that app

2. Per Application Transformer Classes: These implement the logic for processing
every csv row and extract, user, role, assignments from it.

3. main function: It has the mapper for application name to Application Transformer class
Everytime a new application is created it needs to be updated.

4. tests: these are unit tests that can be used to validate application
transforming logic.

## Checklist for adding new Application

1. Take sample export of the application from real production data
2. Create a test data from the production data removing any PII
3. Add an Application Transformer class with following items
3.1 process_csv_row, create_user, create_role, create_role_assignment, create_permission
3.2 Add validators for the data specially assignment.
4. Add unit test for the Application
4.1 test the transform with sample data
5. Register the appplication in the `app_to_transformer_map`
6. Create Custom App Provider in Andromeda
7. Check custom app transfomer via `python3 custom_app_fsastore_transformer.py --app_name=billing --inventory_file=billing_inventory.csv`
8. Upload the application and CSV to the UI
9. Optionally, use the sample app upload script to update the scripts
10. Validate the data in the Andromeda UI

"""

import logging
import csv
import datetime
import json
from functools import partial
import traceback
from dataclasses import asdict
from typing import Dict, List, Optional, Generator, Tuple
from pathlib import Path
from sdk.customapp.custom_app_models import (
    CustomAppInventory, validate_inventory_consistency
)
from sdk.customapp.custom_app_utils import (
    convert_to_andromeda_dict, normalize_csv_fieldnames
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 100
DEFAULT_OUTPUT_DIR = "/tmp/customapp_export"
DEFAULT_APP_NAME = "custom_app_sample"
ID_SEPARATOR = "|"

class CustomAppCsvTransformer:
    """
    Abstract class for custom app type1 inventory transformer.
    Implements all the common helper methods different custom apps
    """

    def __init__(self, app_name: str, inventory_file: str,
                 output_dir: str, has_extra_header_rows: bool=False,
                 field_names: Optional[List[str]]=None):
        self.app_name = app_name
        self.inventory_file = inventory_file
        self.inventory_type = 'CUSTOM_TYPE1_INVENTORY_CSV'
        self.output_dir = output_dir
        self.inventory = CustomAppInventory()
        self.has_extra_header_rows = has_extra_header_rows
        self.field_names = field_names

    def convert_snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case string to camelCase."""
        parts = snake_str.split('_')
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])

    def csv_batch_reader(self, csv_file: str, batch_size: int=100) -> Generator[list, None, None]:
        """ Read CSV file in batches """
        with open(csv_file, 'r', encoding="utf-8-sig", newline='', errors='ignore') as f:
            csv_reader = csv.DictReader(f)
            # Reading .fieldnames consumes the header row; normalize it before any
            # data row is mapped so a stray BOM or space cannot make a column
            # permanently unreachable to row.get().
            original_fieldnames = csv_reader.fieldnames
            normalized_fieldnames = normalize_csv_fieldnames(original_fieldnames)
            if normalized_fieldnames is not None and normalized_fieldnames != original_fieldnames:
                logger.warning("Normalized CSV header names in %s: %s -> %s",
                               csv_file, original_fieldnames, normalized_fieldnames)
                csv_reader.fieldnames = normalized_fieldnames
            batch = []
            for row in csv_reader:
                batch.append(row)
                if len(batch) == batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    def csv_batch_reader_with_extra_header(
            self, csv_file: str, field_names: List[str],
            batch_size: int=100) -> Generator[list, None, None]:
        """ Read CSV file in batches """
        with open(csv_file, 'r', encoding="utf-8-sig", newline='', errors='ignore') as f:
            csv_reader = csv.reader(f)
            batch = []
            is_first_row = True
            for row in csv_reader:
                if not row:
                    # skip empty rows
                    continue
                if len(row) != len(field_names):
                    logger.info("Row has %d columns, expected %d",
                                len(row), len(field_names))
                # skip the first row
                if is_first_row:
                    is_first_row = False
                    continue
                # convert the row to a dictionary with the field names
                row_dict = dict(zip(field_names, row))
                batch.append(row_dict)
                if len(batch) == batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch


    def summarize(self) -> Dict[str, int]:
        """Generate summary statistics for inventory."""
        return {
            'users': len(self.inventory.users),
            'roles': len(self.inventory.roles),
            'assignments': len(self.inventory.assignments),
            'permissions': len(self.inventory.permissions),
            'groups': len(self.inventory.groups),
        }

    def transform_and_export(self) -> Tuple[CustomAppInventory, str]:
        """
        Transform the inventory csv into Andromeda Inventory and export it to a json file
        provided in the constructor
        Returns:
            Tuple[CustomAppInventory, str]: The inventory and the output file path
        """
        errors = self.transform()
        if errors:
            logger.error("Ignored errors found in inventory file %s\n %s",
                         len(errors), errors)
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Generate output filename
        timestamp = datetime.datetime.now().replace(
            microsecond=0, second=0, tzinfo=datetime.timezone.utc).isoformat()
        output_file = Path(f"{self.output_dir}/{self.app_name}-{timestamp}.json")

        # Log summary
        summary = self.summarize()
        logger.info("Summary of inventory file %s output to %s\n %s",
                    self.inventory, output_file, json.dumps(summary, indent=2))
        # Export to JSON
        try:
            # Convert to dictionary, camelize keys, and remove empty values

            # perform validation
            self.inventory_validation()

            inventory_dict = asdict(self.inventory)
            result_dict = convert_to_andromeda_dict(inventory_dict)

            with open(output_file, 'w', encoding="utf-8") as file:
                json.dump(result_dict, file, indent=2)
            # return full path of the output file
            return result_dict, str(output_file)
        except Exception as e:
            logger.error("Error writing output file %s: %s", output_file, e)
            logger.error("Stack trace: %s", traceback.format_exc())
            raise

    def transform(self) -> List[Dict[str, str]]:
        """Transform Builder CSV inventory file."""
        errors = []
        try:
            csv_reader = (
                partial(self.csv_batch_reader_with_extra_header,
                        self.inventory_file, self.field_names)
                if self.has_extra_header_rows and self.field_names
                else partial(self.csv_batch_reader, self.inventory_file)
            )
            # read the csv file in batches
            for batch in csv_reader():
                for row in batch:
                    self.process_csv_row(row, errors)
        except Exception as e:
            logger.error("Error processing inventory file %s: %s", self.inventory_file, e)
            raise

        return errors

    def inventory_validation(self) -> None:
        """Validate the inventory."""
        errors = validate_inventory_consistency(self.inventory, strict_enums=True)
        if errors:
            error_msg = f"Inventory validation failed with {len(errors)} error(s):\n"
            error_msg += "\n".join(f"  - {err}" for err in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def process_csv_row(self, row: Dict[str, str], errors: List[Dict[str, str]]):
        """Process a single CSV row and update inventory."""
        raise NotImplementedError("Subclass must implement this method")
