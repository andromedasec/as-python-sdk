import logging
import requests
import requests_mock
from sdk.api_utils import APIUtils, InvalidInputException

logger = logging.getLogger(__name__)


def test_resource_url() -> None:
    # Identities(filters: { id: { in: "[$ids]" } }) {
    au = APIUtils()
    url = au.get_resource_url("providers", resource_id="1234")
    assert url == "https://api.staging.andromedasecurity.com/providers/1234"

    url = au.get_resource_url("providers", resource_name="my aws provider")
    assert url == "https://api.staging.andromedasecurity.com/providers?filter= name = my aws provider"

    url = au.get_resource_url(
        "providers", resource_name="my aws provider", resource_id="1234")
    assert url == "https://api.staging.andromedasecurity.com/providers/1234"

    url = au.get_resource_url(
        "providers", resource_name="my aws provider", resource_id="1234", subresource_path="aws/config")
    assert url == "https://api.staging.andromedasecurity.com/providers/1234/aws/config"

    try:
        url = au.get_resource_url(
            "providers", resource_name="my aws provider", subresource_path="aws/config")
    except InvalidInputException:
        pass
    else:
        assert False, "InvalidInputException not raised %s" % url


def test_create_or_update_resource():
    au = APIUtils(api_endpoint="mock://api.staging.andromedasecurity.com")
    url = au.get_resource_url("providers", resource_name="Foo")
    adapter = requests_mock.Adapter()
    session = au.get_api_session_w_cookie("foo")
    session.mount('mock://', adapter)
    provider_obj = {
        'name': 'Foo',
        'type': 'PROVIDER_TYPE_AWS'
    }
    provider_result_obj = {
        'name': 'Foo',
        'id': '1234',
        'type': 'PROVIDER_TYPE_AWS'
    }
    adapter.register_uri('GET', url, json={"results": []})
    # requests_mock.get(url, json={"results": []})
    post_url = au.get_resource_url("providers")
    adapter.register_uri('POST', post_url, json=provider_result_obj)
    # requests_mock.post(url, json=provider_obj, json=provider_result_obj)
    status_code, obj = au.create_or_update_resource(
        session, "providers", resource_name="Foo", resource_id="",
        obj=provider_obj)
    logger.info("obj %s", obj)
    assert obj['id'] == '1234'


def test_create_or_update_subresource():
    au = APIUtils(api_endpoint="mock://api.staging.andromedasecurity.com")
    adapter = requests_mock.Adapter()
    session = au.get_api_session_w_cookie("foo")
    session.mount('mock://', adapter)
    aws_config = {
        'name': 'Foo',
        'type': 'PROVIDER_TYPE_AWS'
    }
    aws_result_config = {
        'name': 'Foo',
        'id': '1234',
        'type': 'PROVIDER_TYPE_AWS'
    }

    url = au.get_resource_url(
        f"providers/1234/aws/config")
    adapter.register_uri('GET', url, json={"results": []})
    # requests_mock.get(url, json={"results": []})
    adapter.register_uri('POST', url, json=aws_result_config)
    # requests_mock.post(url, json=provider_obj, json=provider_result_obj)
    status_code, obj = au.create_or_update_resource(
        session, f"providers/1234/aws/config", obj=aws_config)
    logger.info("obj %s", obj)
    assert obj['id'] == '1234'
