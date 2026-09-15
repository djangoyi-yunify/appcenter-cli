"""End-to-end tests for the IaaS CLI SSH key management against the real API.

These tests require real credentials in ``.qingcloud/config`` (gitignored)
and a local SSH public key under ``~/.ssh``. They are skipped automatically
when either is absent.

Safety: only resources created by this test module are ever modified or
deleted. The module-scoped fixture creates one keypair from the local SSH
public key and guarantees its deletion in teardown, even if a test fails.
The delete test creates its own throwaway keypair. No existing keypairs
are ever touched.

Note: attach-key-pairs / detach-key-pairs are intentionally NOT covered here;
they are exercised in a separate e2e test that binds keys to instances.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = str(PROJECT_ROOT / ".venv" / "bin" / "iaas")
CONFIG = str(PROJECT_ROOT / ".qingcloud" / "config")
# Region used for the tests. The account's keypair quota in pek3 is exhausted,
# so the tests run in sh1 where quota is available.
ZONE = "sh1"

# Local SSH public keys, in preference order.
SSH_PUB_KEY_CANDIDATES = [
    Path.home() / ".ssh" / "id_ed25519.pub",
    Path.home() / ".ssh" / "id_rsa.pub",
    Path.home() / ".ssh" / "id_ecdsa.pub",
]


def _find_ssh_pub_key():
    for p in SSH_PUB_KEY_CANDIDATES:
        if p.exists():
            return p
    return None


SSH_PUB_KEY = _find_ssh_pub_key()

pytestmark = pytest.mark.skipif(
    not Path(CONFIG).exists() or SSH_PUB_KEY is None,
    reason="real API credentials or local SSH public key not available",
)


def run_cli(*args):
    """Run the iaas CLI as a subprocess, isolated from credential env vars."""
    env = dict(os.environ)
    for key in (
        "QINGCLOUD_ACCESS_KEY_ID",
        "QINGCLOUD_SECRET_ACCESS_KEY",
        "QINGCLOUD_ZONE",
        "QINGCLOUD_HOST",
        "QINGCLOUD_CONFIG",
    ):
        env.pop(key, None)
    return subprocess.run(
        [CLI, args[0], "--zone", ZONE, *args[1:]],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def parse_json(r):
    return json.loads(r.stdout)


def _key_type(pubkey_text):
    """Return the key type (first field) of an OpenSSH public key."""
    return pubkey_text.split()[0]


def _create_keypair(name):
    """Create a keypair from the local SSH public key; return its ID."""
    pubkey = SSH_PUB_KEY.read_text().strip()
    r = run_cli(
        "create-key-pair",
        "--config", CONFIG,
        "--keypair-name", name,
        "--mode", "user",
        "--encrypt-method", _key_type(pubkey),
        "--public-key", pubkey,
    )
    assert r.returncode == 0, "create-key-pair failed: %s" % r.stderr
    return parse_json(r)["keypair_id"]


def _describe_keypair(keypair_id):
    """Describe a single keypair by ID; return the dict or None."""
    r = run_cli("describe-key-pairs", "--config", CONFIG, "--keypairs", keypair_id)
    assert r.returncode == 0, "describe-key-pairs failed: %s" % r.stderr
    for kp in parse_json(r).get("keypair_set", []):
        if kp.get("keypair_id") == keypair_id:
            return kp
    return None


@pytest.fixture(scope="module")
def created_keypair():
    """Create one keypair from the local SSH public key; delete it afterwards.

    Only this created keypair is ever modified or deleted by the tests.
    """
    name = "e2e-ssh-%d" % int(time.time())
    keypair_id = _create_keypair(name)
    yield {"id": keypair_id, "name": name}
    # Teardown: delete only the keypair this fixture created.
    run_cli("delete-key-pairs", "--config", CONFIG, "--keypairs", keypair_id)


# ---------------------------------------------------------------------------
# Read-only
# ---------------------------------------------------------------------------


def test_describe_key_pairs_readonly():
    """describe-key-pairs against the real API returns a keypair_set."""
    r = run_cli("describe-key-pairs", "--config", CONFIG)
    assert r.returncode == 0, r.stderr
    data = parse_json(r)
    assert "keypair_set" in data
    assert "total_count" in data


# ---------------------------------------------------------------------------
# Create (uses the local ~/.ssh public key)
# ---------------------------------------------------------------------------


def test_create_key_pair_uses_local_ssh_key(created_keypair):
    """The fixture created a keypair from the local SSH public key."""
    kp = _describe_keypair(created_keypair["id"])
    assert kp is not None, "created keypair not found: %s" % created_keypair["id"]
    assert kp["keypair_name"] == created_keypair["name"]
    # The key type reported by the API should match the local key type.
    assert kp["encrypt_method"] == _key_type(SSH_PUB_KEY.read_text().strip())


def test_describe_shows_created_keypair(created_keypair):
    """describe-key-pairs can find the keypair created by the fixture."""
    kp = _describe_keypair(created_keypair["id"])
    assert kp is not None
    assert kp["keypair_id"] == created_keypair["id"]


# ---------------------------------------------------------------------------
# Modify (only the fixture-created keypair)
# ---------------------------------------------------------------------------


def test_modify_key_pair_attributes(created_keypair):
    """modify-key-pair-attributes renames the created keypair; verify it."""
    new_name = created_keypair["name"] + "-renamed"
    r = run_cli(
        "modify-key-pair-attributes",
        "--config", CONFIG,
        "--keypair", created_keypair["id"],
        "--keypair-name", new_name,
        "--description", "e2e test rename",
    )
    assert r.returncode == 0, r.stderr
    kp = _describe_keypair(created_keypair["id"])
    assert kp is not None
    assert kp["keypair_name"] == new_name
    assert kp.get("description") == "e2e test rename"


# ---------------------------------------------------------------------------
# Delete (only a throwaway keypair created within this test)
# ---------------------------------------------------------------------------


def test_delete_key_pairs():
    """delete-key-pairs removes a throwaway keypair; verify it is gone."""
    name = "e2e-ssh-del-%d" % int(time.time())
    keypair_id = _create_keypair(name)
    try:
        r = run_cli("delete-key-pairs", "--config", CONFIG, "--keypairs", keypair_id)
        assert r.returncode == 0, r.stderr
        assert _describe_keypair(keypair_id) is None, (
            "keypair still present after delete: %s" % keypair_id
        )
    finally:
        # Best-effort cleanup of the throwaway keypair.
        run_cli("delete-key-pairs", "--config", CONFIG, "--keypairs", keypair_id)


# ---------------------------------------------------------------------------
# Local validation (no API call)
# ---------------------------------------------------------------------------


def test_create_key_pair_missing_name():
    """create-key-pair without --keypair-name fails locally with exit code 2."""
    r = run_cli("create-key-pair", "--config", CONFIG)
    assert r.returncode == 2
    assert "Missing required parameter" in r.stderr


def test_delete_key_pairs_missing_required():
    """delete-key-pairs without --keypairs fails locally with exit code 2."""
    r = run_cli("delete-key-pairs", "--config", CONFIG)
    assert r.returncode == 2
    assert "Missing required parameter" in r.stderr
