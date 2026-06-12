import os
import pytest
from unittest.mock import patch
from kon.auth import (
    save_credential,
    load_credential,
    delete_credential,
    _rta_dir,
    _credentials_file,
)


@pytest.fixture
def isolated_creds(tmp_path):
    """Provide a temporary credentials directory."""
    fake_rta_dir = tmp_path / ".rta"
    fake_rta_dir.mkdir()
    creds_file = fake_rta_dir / "credentials"

    with patch("kon.auth._rta_dir", return_value=str(fake_rta_dir)):
        yield creds_file


def test_save_and_load_credential(isolated_creds):
    save_credential("test_key", "test_value_123")
    assert load_credential("test_key") == "test_value_123"


def test_load_nonexistent_credential(isolated_creds):
    assert load_credential("nonexistent") is None


def test_delete_credential(isolated_creds):
    save_credential("key_to_delete", "secret_data")
    assert load_credential("key_to_delete") == "secret_data"

    delete_credential("key_to_delete")
    assert load_credential("key_to_delete") is None


def test_delete_nonexistent_credential(isolated_creds):
    delete_credential("nonexistent")
    assert load_credential("nonexistent") is None


def test_multiple_credentials(isolated_creds):
    save_credential("key_a", "value_a")
    save_credential("key_b", "value_b")
    save_credential("key_c", "value_c")

    assert load_credential("key_a") == "value_a"
    assert load_credential("key_b") == "value_b"
    assert load_credential("key_c") == "value_c"

    delete_credential("key_b")
    assert load_credential("key_a") == "value_a"
    assert load_credential("key_b") is None
    assert load_credential("key_c") == "value_c"


def test_overwrite_credential(isolated_creds):
    save_credential("overwrite_key", "old_value")
    assert load_credential("overwrite_key") == "old_value"

    save_credential("overwrite_key", "new_value")
    assert load_credential("overwrite_key") == "new_value"


def test_credential_file_permissions(isolated_creds):
    save_credential("perm_test", "secret")
    if os.name != "nt":
        mode = os.stat(str(isolated_creds)).st_mode & 0o777
        assert mode == 0o600


def test_special_characters_in_value(isolated_creds):
    special = "rta_abc123!@#$%^&*()"
    save_credential("special_key", special)
    assert load_credential("special_key") == special


def test_empty_value(isolated_creds):
    save_credential("empty_key", "")
    assert load_credential("empty_key") == ""
