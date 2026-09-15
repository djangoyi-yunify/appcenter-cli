"""Unit tests for the IaaS CLI (action registry, param collection, wiki)."""

import pytest

from iaas_cli.actions import ACTIONS, Action, Param
from iaas_cli.cli import main
from qc_cli.cli import build_parser, check_required, collect_params
from qc_cli.config import ConfigError


def _parser():
    return build_parser("iaas", "test", ACTIONS, "0.0.0")


def test_action_registry_covers_instances_images():
    """The registry must cover cloud servers, instance groups and images."""
    expected = {
        # Cloud servers
        "describe-instances", "run-instances", "terminate-instances",
        "start-instances", "stop-instances", "restart-instances",
        "reset-instances", "resize-instances", "modify-instance-attributes",
        "describe-instance-types", "clone-instances", "cease-instances",
        # Instance groups
        "create-instance-groups", "delete-instance-groups",
        "join-instance-group", "leave-instance-group",
        "describe-instance-groups",
        # Images
        "describe-images", "capture-instance",
        "capture-image-from-snapshot", "clone-images", "delete-images",
        "modify-image-attributes", "describe-image-users",
        "grant-image-to-users", "revoke-image-from-users",
    }
    assert set(ACTIONS) == expected


def test_no_broker_actions():
    """Brokers are not implemented (the official SDK does not support them)."""
    assert "create-brokers" not in ACTIONS
    assert "delete-brokers" not in ACTIONS


def test_run_instances_requires_image_id():
    action = ACTIONS["run-instances"]
    assert "image_id" in action.required_params()


def test_terminate_instances_requires_instances():
    action = ACTIONS["terminate-instances"]
    assert "instances" in action.required_params()
    param = next(p for p in action.params if p.name == "instances")
    assert param.ptype == "list"


def test_create_instance_groups_requires_relation():
    action = ACTIONS["create-instance-groups"]
    assert "relation" in action.required_params()


def test_grant_image_to_users_requires_image_and_users():
    action = ACTIONS["grant-image-to-users"]
    assert "image" in action.required_params()
    assert "users" in action.required_params()
    param = next(p for p in action.params if p.name == "users")
    assert param.ptype == "list"


def test_collect_list_params():
    parser, _ = _parser()
    args = parser.parse_args(
        [
            "terminate-instances",
            "--instances", "i-1",
            "--instances", "i-2",
        ]
    )
    params = collect_params(args, ACTIONS["terminate-instances"])
    assert params["instances"] == ["i-1", "i-2"]


def test_collect_int_params():
    parser, _ = _parser()
    args = parser.parse_args(
        ["run-instances", "--image-id", "img-x", "--cpu", "2", "--memory", "2048"]
    )
    params = collect_params(args, ACTIONS["run-instances"])
    assert params["cpu"] == 2
    assert params["memory"] == 2048


def test_collect_int_invalid():
    parser, _ = _parser()
    args = parser.parse_args(
        ["run-instances", "--image-id", "img-x", "--cpu", "abc"]
    )
    with pytest.raises(ConfigError):
        collect_params(args, ACTIONS["run-instances"])


def test_check_required_missing():
    action = ACTIONS["run-instances"]
    with pytest.raises(ConfigError) as exc:
        check_required({}, action)
    assert "--image-id" in str(exc.value)


def test_describe_instances_has_table_columns():
    action = ACTIONS["describe-instances"]
    assert "instance_id" in action.table_columns
    assert "status" in action.table_columns


def test_describe_images_has_table_columns():
    action = ACTIONS["describe-images"]
    assert "image_id" in action.table_columns
    assert "visibility" in action.table_columns


def test_dry_run_builds_signed_url(capsys, monkeypatch):
    monkeypatch.setenv("QINGCLOUD_ACCESS_KEY_ID", "AK")
    monkeypatch.setenv("QINGCLOUD_SECRET_ACCESS_KEY", "SK")
    monkeypatch.setenv("QINGCLOUD_ZONE", "pek3")
    monkeypatch.delenv("QINGCLOUD_CONFIG", raising=False)
    assert main(["describe-instances", "--dry-run", "--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "action=DescribeInstances" in out
    assert "signature=" in out
    assert "***" in out  # signature masked


def test_wiki_lists_commands(capsys):
    assert main(["wiki"]) == 0
    out = capsys.readouterr().out
    assert "describe-instances" in out
    assert "describe-images" in out


def test_wiki_shows_action_details(capsys):
    assert main(["wiki", "run-instances"]) == 0
    out = capsys.readouterr().out
    assert "API 动作: RunInstances" in out
    assert "--image-id" in out


def test_wiki_unknown_command(capsys):
    assert main(["wiki", "no-such-command"]) == 2
    err = capsys.readouterr().err
    assert "unknown command" in err


def test_missing_command_returns_2(capsys):
    assert main([]) == 2
