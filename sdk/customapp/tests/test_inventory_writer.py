"""Tests for the streaming InventoryWriter."""

import glob
import json
import os

import pytest

from sdk.customapp.custom_app_models import CustomAppChildApplication, CustomAppGroup, CustomAppRoleAssignmentV2, CustomAppUser
from sdk.customapp.inventory_writer import MANIFEST_FILE, InventoryWriter


def user(i):
    return CustomAppUser(id=f"u{i}", username=f"u{i}", name=f"User {i}")


class TestSinglePart:
    def test_file_target_writes_exactly_that_file(self, tmp_path):
        target = str(tmp_path / "data.json")
        writer = InventoryWriter(target)
        for i in range(3):
            writer.add_user(user(i))
        writer.add_group(CustomAppGroup(id="g1", name="G", member_user_ids=["u0", "u1"]))

        assert writer.close() == [target]
        doc = json.load(open(target))
        assert set(doc) == {"users", "groups"}
        assert len(doc["users"]) == 3
        assert doc["groups"]["g1"]["member_user_ids"] == ["u0", "u1"]
        assert not (tmp_path / MANIFEST_FILE).exists()

    def test_directory_target_uses_app_name_and_timestamp(self, tmp_path):
        writer = InventoryWriter(str(tmp_path), app_name="monday")
        writer.add_user(user(1))

        (path,) = writer.close()
        assert os.path.basename(path).startswith("monday-") and path.endswith(".json")
        assert list(json.load(open(path))["users"]) == ["u1"]

    def test_empty_inventory_is_an_empty_object(self, tmp_path):
        (path,) = InventoryWriter(str(tmp_path / "data.json")).close()
        assert json.load(open(path)) == {}


@pytest.mark.parametrize("count", [0, 1, 12])
def test_discovery_explicitly_reports_empty_results(tmp_path, count):
    writer = InventoryWriter(str(tmp_path), max_part_bytes=100, empty_section="child_applications")
    with writer:
        for i in range(count):
            writer.add_child_application(CustomAppChildApplication(id=f"app{i}", name=f"App {i}"))

    apps = {}
    for part in writer.close():
        doc = json.load(open(part))
        assert set(doc) == {"child_applications"}
        apps.update(doc["child_applications"])
    assert set(apps) == {f"app{i}" for i in range(count)}


def test_empty_section_rejects_unknown_section(tmp_path):
    with pytest.raises(ValueError):
        InventoryWriter(str(tmp_path), empty_section="child_application")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("features", [None, {}, {"riskSupported": False}, {
    "objMapping": [{"andromedaObjType": "GROUP", "supported": False, "label": "Team"}],
    "nhiTypes": [],
}])
def test_discovery_preserves_feature_overrides(tmp_path, features):
    with InventoryWriter(str(tmp_path / "data.json")) as writer:
        writer.add_child_application(CustomAppChildApplication(id="app", name="App", provider_features=features))
    with (tmp_path / "data.json").open() as source:
        app = json.load(source)["child_applications"]["app"]
    if features is None:
        assert "provider_features" not in app
    else:
        assert app["provider_features"] == features


class TestMultiPart:
    def test_rotates_parts_and_writes_manifest(self, tmp_path):
        with InventoryWriter(str(tmp_path / "data.json"), max_part_bytes=600) as writer:
            for i in range(20):
                writer.add_user(user(i))
            for i in range(5):
                writer.add_group(CustomAppGroup(id=f"g{i}", name=f"G{i}", member_user_ids=[f"u{i}"]))
            for i in range(20):
                writer.add_assignment(CustomAppRoleAssignmentV2(id=f"a{i}", principal_id=f"u{i}", principal_type="HUMAN", role_id="r"))
            writer.add_user(user(99))  # users reopened after other sections -> new part

        parts = sorted(glob.glob(str(tmp_path / "data.part-*.json")))
        manifest = json.load(open(tmp_path / MANIFEST_FILE))
        assert len(parts) > 1
        assert manifest["parts"] == [os.path.basename(p) for p in parts]
        assert set(manifest) == {"schema", "parts"}
        assert not (tmp_path / "data.json").exists()

        seen = set()
        for part in parts:
            doc = json.load(open(part))  # every part is a complete document
            assert os.path.getsize(part) <= 600
            for section, items in doc.items():
                for key in items:
                    assert (section, key) not in seen
                    seen.add((section, key))
        assert sum(1 for section, _ in seen if section == "users") == 21

    def test_section_reopened_in_same_part_starts_new_part(self, tmp_path):
        writer = InventoryWriter(str(tmp_path / "data.json"))
        writer.add_user(user(1))
        writer.add_group(CustomAppGroup(id="g", name="G"))
        writer.add_user(user(2))
        parts = writer.close()

        assert len(parts) == 2
        assert list(json.load(open(parts[0]))) == ["users", "groups"]
        assert list(json.load(open(parts[1]))) == ["users"]


class TestErrors:
    def test_unknown_section_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            InventoryWriter(str(tmp_path / "data.json")).add("widgets", {"id": "w"})

    def test_missing_id_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            InventoryWriter(str(tmp_path / "data.json")).add("users", {"name": "no id"})

    def test_exception_removes_partial_output(self, tmp_path):
        with pytest.raises(RuntimeError):
            with InventoryWriter(str(tmp_path / "data.json")) as writer:
                writer.add_user(user(1))
                raise RuntimeError("boom")
        assert os.listdir(tmp_path) == []

    def test_add_after_close_rejected(self, tmp_path):
        writer = InventoryWriter(str(tmp_path / "data.json"))
        writer.close()
        with pytest.raises(RuntimeError):
            writer.add_user(user(1))

    def test_single_object_larger_than_cap_is_written_alone(self, tmp_path):
        writer = InventoryWriter(str(tmp_path / "data.json"), max_part_bytes=100)
        writer.add_user({"id": "u1", "name": "x" * 200})
        (part,) = writer.close()

        assert os.path.getsize(part) > 100
        assert json.load(open(part))["users"]["u1"]["name"] == "x" * 200


def test_every_part_obeys_the_strict_cap(tmp_path):
    cap = 1_000
    writer = InventoryWriter(str(tmp_path / "data.json"), max_part_bytes=cap)
    for i in range(30):
        writer.add_user({"id": f"u{i}", "blob": "x" * 160})
    parts = writer.close()

    assert len(parts) > 1
    assert all(os.path.getsize(part) <= cap for part in parts)


def test_unicode_objects_obey_byte_cap(tmp_path):
    cap = 180
    writer = InventoryWriter(str(tmp_path / "data.json"), max_part_bytes=cap)
    for i in range(8):
        writer.add_user({"id": f"u{i}", "name": "☃" * 8})
    parts = writer.close()

    assert len(parts) > 1
    assert all(os.path.getsize(part) <= cap for part in parts)


def test_explicit_key_supports_objects_without_id(tmp_path):
    target = str(tmp_path / "data.json")
    writer = InventoryWriter(target)
    writer.add("users", {"username": "external"}, key="external-id")
    writer.close()

    assert json.load(open(target))["users"] == {"external-id": {"username": "external"}}


def test_child_applications_section(tmp_path):
    from sdk.customapp.custom_app_models import CustomAppChildApplication

    target = str(tmp_path / "data.json")
    with InventoryWriter(target) as writer:
        writer.add_child_application(CustomAppChildApplication(id="sfdc", name="Salesforce", attributes={"owner": "alice"}))
        writer.add_child_application(CustomAppChildApplication(id="wd", name="Workday"))

    doc = json.load(open(target))
    assert list(doc) == ["child_applications"]
    assert doc["child_applications"]["sfdc"] == {"id": "sfdc", "name": "Salesforce", "attributes": {"owner": "alice"}}
    assert doc["child_applications"]["wd"] == {"id": "wd", "name": "Workday"}


def test_close_is_idempotent(tmp_path):
    writer = InventoryWriter(str(tmp_path / "data.json"))
    writer.add_user(user(1))
    first = writer.close()

    assert writer.close() == first
    assert len(list(tmp_path.iterdir())) == 1

@pytest.mark.parametrize("directory_target", [False, True])
def test_single_part_replaces_previous_multipart_inventory(tmp_path, directory_target):
    output = str(tmp_path if directory_target else tmp_path / "data.json")
    with InventoryWriter(output, max_part_bytes=300) as writer:
        for i in range(20):
            writer.add_user(user(i))
    assert (tmp_path / MANIFEST_FILE).exists()
    writer = InventoryWriter(output)
    writer.add_user(user(99))
    [published] = writer.close()
    assert not (tmp_path / MANIFEST_FILE).exists()
    assert not list(tmp_path.glob("data.part-*.json"))
    assert list(json.loads(open(published).read())["users"]) == ["u99"]
