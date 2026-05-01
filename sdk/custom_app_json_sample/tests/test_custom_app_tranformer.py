import logging
import json
from pathlib import Path
from sdk.custom_app_json_sample.custom_app_transformer import CustomAppInventoryTransformer
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger(__name__)

def test_transform_custom_type1_inventory_csv():
    # Resolve paths relative to this test file's directory
    test_dir = Path(__file__).parent
    inventory_file = str(test_dir / "beatles-custom-app.csv")
    expected_file = test_dir / "beatles-custom-app.json"

    csv_transformer = CustomAppInventoryTransformer()
    inventory = csv_transformer.transform("beatles", inventory_file, "CUSTOM_TYPE1_INVENTORY_CSV")
    assert inventory

    with open(expected_file, 'r', encoding="utf-8") as f:
        expected_inventory = json.load(f)
        logger.info("Inventory %s", inventory)

        inventory_dict = MessageToDict(inventory)

        assert inventory_dict == expected_inventory, f"Inventory mismatch {len(inventory_dict)} {len(expected_inventory)}"
