"""End-to-end tests for the AppCenter CLI against the real QingCloud API.

These tests require real credentials in ``.qingcloud/config`` (gitignored).
They are skipped automatically when the config file is absent.

Safety: read-only commands are called against the real API; mutating
commands are only exercised on their error paths (non-existent resource
IDs), so no real cloud resources are created or modified.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = str(PROJECT_ROOT / ".venv" / "bin" / "appcenter")
CONFIG = str(PROJECT_ROOT / ".qingcloud" / "config")

pytestmark = pytest.mark.skipif(
    not Path(CONFIG).exists(),
    reason="real API credentials not configured (.qingcloud/config missing)",
)

# Read-only commands with no required parameters (safe to call directly).
# Note: describe-app-versions is excluded because the API requires at least
# one of app_ids/version_ids (not reflected in the action definition).
READONLY_NO_PARAM = [
    "describe-apps",
    "describe-clusters",
]

# Read-only commands that need required params; tested with non-existent
# IDs to verify graceful handling (no crash, valid exit code).
READONLY_ERROR_PATH = {
    "describe-app-versions": ["--version-ids", "appv-nonexistent"],
    "describe-cluster-nodes": ["--cluster", "cl-nonexistent"],
    "describe-cluster-jobs": ["--app", "app-nonexistent"],
    "describe-cluster-env": ["--cluster-id", "cl-nonexistent"],
    "describe-cluster-display-tabs": [
        "--cluster", "cl-nonexistent", "--display-tabs", "tab-nonexistent",
    ],
    "describe-app-version-attachments": [
        "--attachment-ids", "att-nonexistent", "--version-id", "appv-nonexistent",
    ],
    "get-cluster-monitor": [
        "--resource", "cln-nonexistent", "--step", "5m",
        "--start-time", "2026-09-10T00:00:00Z", "--end-time", "2026-09-10T01:00:00Z",
        "--meters", "cpu",
    ],
}

# Mutating commands with required-param args. Tested ONLY on error paths
# (non-existent resource IDs) so no real mutation happens.
MUTATING_COMMANDS = {
    "deploy-app-version": ["--version-id", "appv-nonexistent", "--conf", '{"name":"e2e-test"}'],
    "start-clusters": ["--clusters", "cl-nonexistent"],
    "stop-clusters": ["--clusters", "cl-nonexistent"],
    "restart-cluster-service": ["--cluster", "cl-nonexistent"],
    "delete-clusters": ["--clusters", "cl-nonexistent"],
    "cease-clusters": ["--clusters", "cl-nonexistent"],
    "recover-clusters": ["--clusters", "cl-nonexistent", "--zone", "pek3a"],
    "resize-cluster": ["--cluster", "cl-nonexistent"],
    "change-cluster-vxnet": ["--cluster", "cl-nonexistent", "--vxnet", "vxnet-nonexistent"],
    "update-cluster-env": ["--cluster", "cl-nonexistent", "--env", '{"key":"value"}'],
    "add-cluster-nodes": ["--cluster", "cl-nonexistent", "--node-count", "1"],
    "delete-cluster-nodes": ["--cluster", "cl-nonexistent", "--nodes", "cln-nonexistent"],
    "associate-eip-to-cluster-node": ["--eip", "eip-nonexistent", "--cluster-node", "cln-nonexistent"],
    "dissociate-eip-from-cluster-node": ["--eips", "eip-nonexistent"],
}


def run_cli(*args, env_extra=None):
    """Run the CLI as a subprocess, isolated from credential env vars."""
    env = dict(os.environ)
    for key in (
        "QINGCLOUD_ACCESS_KEY_ID",
        "QINGCLOUD_SECRET_ACCESS_KEY",
        "QINGCLOUD_ZONE",
        "QINGCLOUD_HOST",
        "QINGCLOUD_CONFIG",
    ):
        env.pop(key, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [CLI, *args], capture_output=True, text=True, env=env, timeout=90
    )


def parse_json(result):
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Group A: CLI basics (no API calls)
# ---------------------------------------------------------------------------


def test_version():
    r = run_cli("--version")
    assert r.returncode == 0
    assert "appcenter 0.1.0" in r.stdout


def test_help_lists_all_commands():
    r = run_cli("--help")
    assert r.returncode == 0
    for cmd in READONLY_NO_PARAM + list(MUTATING_COMMANDS):
        assert cmd in r.stdout


def test_no_command_prints_help():
    r = run_cli()
    assert r.returncode == 0
    assert "usage:" in r.stdout


def test_unknown_command():
    r = run_cli("no-such-command")
    assert r.returncode == 2


def test_subcommand_help():
    r = run_cli("describe-clusters", "--help")
    assert r.returncode == 0
    assert "--clusters" in r.stdout
    assert "--output" in r.stdout


# ---------------------------------------------------------------------------
# Group B: Auth & config
# ---------------------------------------------------------------------------


def test_missing_credentials():
    r = run_cli("describe-clusters")
    assert r.returncode == 2
    assert "Missing credentials" in r.stderr


def test_config_file_works():
    r = run_cli("describe-clusters", "--config", CONFIG, "--limit", "1")
    assert r.returncode == 0, r.stderr
    data = parse_json(r)
    assert data.get("ret_code") == 0


def test_flag_overrides_config():
    # A wrong access key must fail auth, proving the flag takes precedence
    # over the config file (the config key alone would have succeeded).
    r = run_cli(
        "describe-clusters", "--config", CONFIG,
        "--access-key-id", "WRONGKEY", "--limit", "1",
    )
    assert r.returncode == 1
    assert "AuthFailure" in r.stderr or "signature" in r.stderr.lower()


# ---------------------------------------------------------------------------
# Group C: Read-only commands against the real API
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", READONLY_NO_PARAM)
def test_readonly_command(cmd):
    r = run_cli(cmd, "--config", CONFIG, "--limit", "1")
    assert r.returncode == 0, r.stderr
    data = parse_json(r)
    assert data.get("ret_code") == 0


def test_describe_clusters_has_cluster_set():
    r = run_cli("describe-clusters", "--config", CONFIG, "--limit", "1")
    assert r.returncode == 0
    data = parse_json(r)
    assert "cluster_set" in data


def test_describe_clusters_table_output():
    r = run_cli(
        "describe-clusters", "--config", CONFIG,
        "--output", "table", "--limit", "1",
    )
    assert r.returncode == 0
    assert "cluster_id" in r.stdout
    assert "status" in r.stdout


@pytest.fixture(scope="session")
def real_cluster_id():
    r = run_cli("describe-clusters", "--config", CONFIG, "--limit", "1")
    if r.returncode != 0:
        return None
    data = parse_json(r)
    clusters = data.get("cluster_set") or []
    return clusters[0]["cluster_id"] if clusters else None


def test_describe_cluster_nodes_with_real_cluster(real_cluster_id):
    if not real_cluster_id:
        pytest.skip("no real cluster available")
    r = run_cli("describe-cluster-nodes", "--config", CONFIG, "--cluster", real_cluster_id)
    assert r.returncode == 0, r.stderr
    data = parse_json(r)
    assert data.get("ret_code") == 0


def test_describe_cluster_env_with_real_cluster(real_cluster_id):
    if not real_cluster_id:
        pytest.skip("no real cluster available")
    r = run_cli("describe-cluster-env", "--config", CONFIG, "--cluster-id", real_cluster_id)
    # The request is well-formed; the API may deny based on cluster state or
    # account permission, so accept either a success or a clean API error.
    assert r.returncode in (0, 1), "unexpected crash: %s" % r.stderr
    assert "Traceback" not in r.stderr
    if r.returncode == 0:
        data = parse_json(r)
        assert data.get("ret_code") == 0


@pytest.mark.parametrize("cmd,args", sorted(READONLY_ERROR_PATH.items()))
def test_readonly_with_nonexistent_id(cmd, args):
    r = run_cli(cmd, "--config", CONFIG, *args)
    assert r.returncode in (0, 1), "unexpected crash: %s" % r.stderr
    assert "Traceback" not in r.stderr
    if r.returncode == 0:
        data = parse_json(r)
        assert data.get("ret_code") == 0
    else:
        assert "error:" in r.stderr


# ---------------------------------------------------------------------------
# Group D: Parameter validation (fails before any API call)
# ---------------------------------------------------------------------------


def test_missing_required_param():
    r = run_cli("describe-cluster-nodes", "--config", CONFIG)
    assert r.returncode == 2
    assert "Missing required parameter" in r.stderr


def test_invalid_json_input():
    r = run_cli(
        "deploy-app-version", "--config", CONFIG,
        "--version-id", "appv-x", "--conf", "not-json",
    )
    assert r.returncode == 2
    assert "invalid input" in r.stderr


def test_invalid_int_input():
    r = run_cli("describe-apps", "--config", CONFIG, "--limit", "abc")
    assert r.returncode == 2
    assert "invalid input" in r.stderr


# ---------------------------------------------------------------------------
# Group E: Error handling (real API)
# ---------------------------------------------------------------------------


def test_nonexistent_resource_returns_empty():
    # Describe queries return an empty result (ret_code 0) for non-existent
    # resources rather than an error.
    r = run_cli(
        "describe-cluster-nodes", "--config", CONFIG,
        "--cluster", "cl-nonexistent-xyz",
    )
    assert r.returncode == 0, r.stderr
    data = parse_json(r)
    assert data.get("ret_code") == 0
    assert data.get("node_set") == []


# ---------------------------------------------------------------------------
# Group F: Mutating commands - error paths only (no real side effects)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd,args", sorted(MUTATING_COMMANDS.items()))
def test_mutating_command_error_path(cmd, args):
    r = run_cli(cmd, "--config", CONFIG, *args)
    # Must NOT succeed: a returncode of 0 would mean a real mutation happened.
    assert r.returncode in (1, 2), (
        "mutating command unexpectedly succeeded: %s" % r.stdout
    )
    assert "Traceback" not in r.stderr
    assert "error:" in r.stderr


@pytest.mark.parametrize("cmd", sorted(MUTATING_COMMANDS))
def test_mutating_command_missing_required(cmd):
    r = run_cli(cmd, "--config", CONFIG)
    assert r.returncode == 2
    assert "Missing required parameter" in r.stderr
