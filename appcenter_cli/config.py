"""Configuration loading for the AppCenter CLI.

Credentials and defaults are resolved in the following order (highest
priority first):

1. Command line flags (handled by the CLI layer)
2. Environment variables
3. Config file (~/.qingcloud/config or $QINGCLOUD_CONFIG)

Supported environment variables:

- QINGCLOUD_ACCESS_KEY_ID
- QINGCLOUD_SECRET_ACCESS_KEY
- QINGCLOUD_ZONE
- QINGCLOUD_HOST
- QINGCLOUD_CONFIG (path to the config file)
"""

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_HOST = "api.qingcloud.com"
DEFAULT_ZONE = "pek3a"
DEFAULT_CONFIG_PATH = Path.home() / ".qingcloud" / "config"

ENV_ACCESS_KEY_ID = "QINGCLOUD_ACCESS_KEY_ID"
ENV_SECRET_ACCESS_KEY = "QINGCLOUD_SECRET_ACCESS_KEY"
ENV_ZONE = "QINGCLOUD_ZONE"
ENV_HOST = "QINGCLOUD_HOST"
ENV_CONFIG = "QINGCLOUD_CONFIG"


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


@dataclass
class Config:
    access_key_id: str = ""
    secret_access_key: str = ""
    zone: str = DEFAULT_ZONE
    host: str = DEFAULT_HOST
    protocol: str = "https"
    port: int = 443
    timeout: int = 60
    retry_time: int = 2
    extra: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not self.access_key_id or not self.secret_access_key:
            raise ConfigError(
                "Missing credentials. Set QINGCLOUD_ACCESS_KEY_ID and "
                "QINGCLOUD_SECRET_ACCESS_KEY environment variables, or "
                "create a config file at %s" % DEFAULT_CONFIG_PATH
            )


def _read_config_file(path: Path) -> dict:
    """Read a config file in INI format and return a flat dict of values."""
    values: dict = {}
    if not path.exists():
        return values
    parser = configparser.ConfigParser()
    parser.read(path)
    for section in parser.sections():
        for key, value in parser.items(section):
            values[key] = value
    return values


def load_config(
    access_key_id: str = "",
    secret_access_key: str = "",
    zone: str = "",
    host: str = "",
    config_path: str = "",
) -> Config:
    """Load configuration from flags, environment and config file.

    Args:
        access_key_id: value from CLI flag (highest priority)
        secret_access_key: value from CLI flag (highest priority)
        zone: value from CLI flag (highest priority)
        host: value from CLI flag (highest priority)
        config_path: explicit path to a config file

    Returns:
        A populated Config.
    """
    file_values: dict = {}
    path = Path(config_path) if config_path else Path(
        os.environ.get(ENV_CONFIG, DEFAULT_CONFIG_PATH)
    )
    file_values = _read_config_file(path)

    def pick(flag_value: str, env_name: str, file_key: str) -> str:
        if flag_value:
            return flag_value
        env_value = os.environ.get(env_name, "")
        if env_value:
            return env_value
        return file_values.get(file_key, "")

    cfg = Config(
        access_key_id=pick(access_key_id, ENV_ACCESS_KEY_ID, "access_key_id"),
        secret_access_key=pick(secret_access_key, ENV_SECRET_ACCESS_KEY, "secret_access_key"),
        zone=pick(zone, ENV_ZONE, "zone") or DEFAULT_ZONE,
        host=pick(host, ENV_HOST, "host") or DEFAULT_HOST,
    )

    protocol = file_values.get("protocol", "https")
    if protocol in ("http", "https"):
        cfg.protocol = protocol
    cfg.port = int(file_values.get("port", 443 if cfg.protocol == "https" else 80))
    cfg.timeout = int(file_values.get("timeout", 60))
    cfg.retry_time = int(file_values.get("retry_time", 2))
    cfg.extra = file_values

    return cfg
