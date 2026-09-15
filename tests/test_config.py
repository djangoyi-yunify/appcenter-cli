import os
from pathlib import Path

import pytest

from qc_cli.config import ConfigError, load_config


def test_load_config_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("QINGCLOUD_ACCESS_KEY_ID", "ENV_AK")
    monkeypatch.setenv("QINGCLOUD_SECRET_ACCESS_KEY", "ENV_SK")
    monkeypatch.setenv("QINGCLOUD_ZONE", "sh1a")
    monkeypatch.delenv("QINGCLOUD_CONFIG", raising=False)
    cfg = load_config()
    assert cfg.access_key_id == "ENV_AK"
    assert cfg.secret_access_key == "ENV_SK"
    assert cfg.zone == "sh1a"
    assert cfg.host == "api.qingcloud.com"


def test_load_config_from_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    config_file.write_text(
        "[default]\n"
        "access_key_id = FILE_AK\n"
        "secret_access_key = FILE_SK\n"
        "zone = gd2\n"
        "host = api.qingcloud.com\n"
    )
    monkeypatch.delenv("QINGCLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("QINGCLOUD_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("QINGCLOUD_ZONE", raising=False)
    cfg = load_config(config_path=str(config_file))
    assert cfg.access_key_id == "FILE_AK"
    assert cfg.secret_access_key == "FILE_SK"
    assert cfg.zone == "gd2"


def test_flags_override_env(monkeypatch):
    monkeypatch.setenv("QINGCLOUD_ACCESS_KEY_ID", "ENV_AK")
    monkeypatch.setenv("QINGCLOUD_SECRET_ACCESS_KEY", "ENV_SK")
    cfg = load_config(access_key_id="FLAG_AK", secret_access_key="FLAG_SK")
    assert cfg.access_key_id == "FLAG_AK"
    assert cfg.secret_access_key == "FLAG_SK"


def test_validate_missing_credentials():
    from qc_cli.config import Config

    cfg = Config()
    with pytest.raises(ConfigError):
        cfg.validate()
