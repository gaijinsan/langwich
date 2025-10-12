import pytest
import langwich.cli
from langwich.cli import get_hashes

def test_get_hashes_base(monkeypatch):
    monkeypatch.setattr(langwich.cli, "metadata_path", "./tests/data/metadata.json")
    hash_list = get_hashes("12345")

    assert len(hash_list) == 1

def test_get_hashes_linked_forward(monkeypatch):
    monkeypatch.setattr(langwich.cli, "metadata_path", "./tests/data/metadata.json")
    hash_list = get_hashes("12346")

    assert len(hash_list) == 2
    assert hash_list[0] == "12346"
    assert hash_list[1] == "12347"

def test_get_hashes_linked_reverse(monkeypatch):
    monkeypatch.setattr(langwich.cli, "metadata_path", "./tests/data/metadata.json")
    hash_list = get_hashes("12347")

    assert len(hash_list) == 2
    assert hash_list[0] == "12346"
    assert hash_list[1] == "12347"

def test_get_hashes_linked_forward_long(monkeypatch):
    monkeypatch.setattr(langwich.cli, "metadata_path", "./tests/data/metadata.json")
    hash_list = get_hashes("12348")

    assert len(hash_list) == 5
    assert hash_list[0] == "12348"
    assert hash_list[1] == "12349"
    assert hash_list[2] == "12350"
    assert hash_list[3] == "12351"
    assert hash_list[4] == "12352"

def test_get_hashes_linked_reverse_long(monkeypatch):
    monkeypatch.setattr(langwich.cli, "metadata_path", "./tests/data/metadata.json")
    hash_list = get_hashes("12352")

    assert len(hash_list) == 5
    assert hash_list[0] == "12348"
    assert hash_list[1] == "12349"
    assert hash_list[2] == "12350"
    assert hash_list[3] == "12351"
    assert hash_list[4] == "12352"
