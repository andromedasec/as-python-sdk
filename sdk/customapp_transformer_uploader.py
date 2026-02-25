###
# Uploader for custom app transformer script.
# It takes input as a filter for the app name and updates the custom app with the file
# file name.
# Steps
# 1. Use either the AS_API_TOKEN or AS_SESSION_COOKIE to create a login session
# 2. Upload the new file to the Andromeda
# 3. Get the file Id from the Andromeda
# 4. iterate over the custom apps and apply app filter.
# 5. Fetch the custom app using REST API
# 6. Update the custom app with the file name from step 3.


import argparse
import logging
import os
import platform
from typing import Optional
import requests
from api_utils import APIUtils
from as_inventory import AndromedaInventory


logger = logging.getLogger(__name__)


class CustomAppTransformerUploader:
    """
    Uploader for custom app transformer script.
    Handles authentication, file upload, and custom app updates.
    """

    def __init__(self, as_api_endpoint: str, as_gql_endpoint: str):
        self.api_endpoint = as_api_endpoint
        self.api_utils = APIUtils(as_api_endpoint)
        self.api_session: Optional[requests.Session] = self._create_session()
        output_dir = "/tmp/andromeda-inventory" \
            if platform.system() != "Windows" else "C:\\tmp\\andromeda-inventory"
        self.as_inventory = AndromedaInventory(
            None, api_session=self.api_session,
            output_dir=output_dir,
            as_endpoint=as_api_endpoint, gql_endpoint=as_gql_endpoint)

    def _create_session(self) -> requests.Session:
        """
        Create an authenticated session using either API token or session cookie.
        Returns:
            requests.Session: Authenticated session
        """
        # Check for API token first
        api_token = os.getenv('AS_API_TOKEN')
        if api_token:
            logger.debug("Using API token for authentication")
            return self.api_utils.get_api_session_w_api_token(api_token)

        # Check for session cookie
        session_cookie = os.getenv('AS_SESSION_COOKIE')
        if session_cookie:
            logger.debug("Using session cookie for authentication")
            return self.api_utils.get_api_session_w_cookie(session_cookie)

        raise ValueError(f"Neither AS_API_TOKEN {api_token} nor AS_SESSION_COOKIE {session_cookie} environment variables are set")

    def _upload_file(self, file_path: str, provider_id: str, provider_name: str,
                    file_type: str) -> str:
        """
        Upload a file to Andromeda and return the file ID.

        Args:
            file_path: Path to the file to upload
            provider_id: Provider ID for the upload

        Returns:
            str: File ID returned from the upload
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        file_url = f"{self.api_endpoint}/providers/{provider_id}/files/upload"
        with open(file_path, 'rb') as f:
            response = self.api_session.post(
                file_url, files={'file': f}, data={'fileType': file_type})
            response.raise_for_status()
            rsp_data = response.json()
            logger.debug('Uploaded file %s to provider %s: %s', rsp_data, provider_id, provider_name)
            workday_file_ref = rsp_data['file_id']
        return workday_file_ref


    def update_custom_app_config(self, provider_id: str, provider_name: str, file_id: str,
                                 file_type: str = "INVENTORY_TRANSLATOR_FILE_PYTHON") -> bool:
        """
        Update a custom app provider configuration with the new file ID.

        Args:
            provider_id: Provider ID to update
            file_id: File ID to set
            file_type: Type of file being uploaded

        Returns:
            bool: True if update was successful
        """
        # Get the custom app config object
        url = self.api_utils.get_resource_url(
                resoure_type=f"providers/{provider_id}/customapp/config")

        response = self.api_session.get(url)
        response.raise_for_status()
        current_config = response.json()
        logger.debug("Current config for provider %s: %s \n config:%s",
                    provider_id, provider_name, current_config)
        current_config['translatorFileId'] = file_id
        current_config['translatorFileType'] = file_type

        # Update the configuration
        status_code, updated_config = self.api_utils.create_or_update_provider_config(
            api_session=self.api_session, provider_id=provider_id,
            provider_obj=current_config, provider_type="customapp")
        logger.info("provider %s: updated config: %s error: %s",
                    provider_id, updated_config, status_code)
        return True

    def upload_and_update(self, app_names: str, file_name: str,
                          file_type: str = "INVENTORY_TRANSLATOR_FILE_PYTHON") -> None:
        """
        Main method to upload file and update custom apps.

        Args:
            app_name: Name of the app to filter by
            file_name: Path to the file to upload
            file_type: Type of file being uploaded
        """
        if not app_names:
            raise ValueError("app_names is required")
        if not file_name:
            raise ValueError("file_name is required")
        for app_name in app_names.split(","):
            provider_filter = {
                "name": {
                    "equals": app_name
                }
            }
            # Get the provider id for the app.
            app_obj = next(self.as_inventory.app_provider_itr(provider_filter))
            file_ref = self._upload_file(file_name, app_obj['id'], app_obj['name'], file_type)
            self.update_custom_app_config(app_obj['id'], app_obj['name'], file_ref, file_type)



def setup_logging() -> None:
    """Setup logging configuration."""
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:%(lineno)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)



def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    help_str = """
    This script get list of identities matching a significance / insight

    Step1:
        fetch the api token from the Andromeda UI and run the script with the api token
    Step2:
       export AS_SESSION_COOKIE=<session token> or
       export AS_API_TOKEN=<api token>
    Example:
        python3 sdk/samples/customapp_transformer_uploader.py --app_names="foo,bar" --file_name=samples/custom_app_transformer.py
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=help_str)
    parser.add_argument("--app_names", type=str,
                       help="Comma separated list of app names to update.")
    parser.add_argument("--file_name", type=str, required=True,
                       help="The path to the file to upload.")
    parser.add_argument("--file_type", type=str,
                        default="INVENTORY_TRANSLATOR_FILE_PYTHON",
                        choices=["INVENTORY_TRANSLATOR_FILE_PYTHON", "INVENTORY_DOWNLOADER_FILE_PYTHON"])
    parser.add_argument(
        '--as_api_endpoint',
        default="https://api.live.andromedasecurity.com",
        help='GQL endpoint for the inventory')
    parser.add_argument(
        '--as_gql_endpoint',
        default="https://api.live.andromedasecurity.com/graphql",
        help='GQL endpoint for the inventory')

    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the script.
    """
    args = parse_arguments()
    setup_logging()
    logger.info("Uploading file %s to apps %s", args.file_name, args.app_names)
    uploader = CustomAppTransformerUploader(args.as_api_endpoint, args.as_gql_endpoint)
    uploader.upload_and_update(args.app_names, args.file_name, args.file_type)
    logger.info("Successfully uploaded file %s and updated custom apps successfully", args.file_name)

if __name__ == "__main__":
    main()
