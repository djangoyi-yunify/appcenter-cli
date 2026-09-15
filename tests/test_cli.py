"""Unit tests for the CLI layer (param collection and validation)."""

import pytest

from appcenter_cli.actions import ACTIONS, Action, Param
from appcenter_cli.cli import (
    _build_parser,
    _check_required,
    _collect_params,
    UsageError,
    main,
)
from qc_cli.config import ConfigError


def test_check_required_any_satisfied():
    action = Action(
        "Test", params=[Param("a", "str"), Param("b", "str")], required_any=[["a", "b"]]
    )
    _check_required({"a": "x"}, action)  # must not raise


def test_check_required_any_violated():
    action = Action(
        "Test", params=[Param("a", "str"), Param("b", "str")], required_any=[["a", "b"]]
    )
    with pytest.raises(ConfigError) as exc:
        _check_required({}, action)
    assert "at least one of" in str(exc.value)
    assert "--a" in str(exc.value)
    assert "--b" in str(exc.value)


def test_check_required_any_after_required_params():
    action = Action(
        "Test",
        params=[Param("a", "str", True), Param("b", "str"), Param("c", "str")],
        required_any=[["b", "c"]],
    )
    # Required param provided, but none of the required_any group present.
    with pytest.raises(ConfigError) as exc:
        _check_required({"a": "x"}, action)
    assert "at least one of" in str(exc.value)


def test_describe_app_versions_has_required_any():
    action = ACTIONS["describe-app-versions"]
    assert ["app_ids", "version_ids"] in action.required_any_groups()


def test_deploy_app_version_has_multi_deploy_zones():
    action = ACTIONS["deploy-app-version"]
    assert "multi_deploy_zones" in action.param_names()
    param = next(p for p in action.params if p.name == "multi_deploy_zones")
    assert param.ptype == "list"


def test_collect_multi_deploy_zones_as_list():
    parser, _ = _build_parser()
    args = parser.parse_args(
        [
            "deploy-app-version",
            "--version-id", "appv-x",
            "--conf", "{}",
            "--multi-deploy-zones", "pek3b",
            "--multi-deploy-zones", "pek3d",
        ]
    )
    params = _collect_params(args, ACTIONS["deploy-app-version"])
    assert params["multi_deploy_zones"] == ["pek3b", "pek3d"]


def test_collect_multi_deploy_zones_absent():
    parser, _ = _build_parser()
    args = parser.parse_args(
        ["deploy-app-version", "--version-id", "appv-x", "--conf", "{}"]
    )
    params = _collect_params(args, ACTIONS["deploy-app-version"])
    assert "multi_deploy_zones" not in params


def test_resize_cluster_has_storage_size_and_instance_class():
    action = ACTIONS["resize-cluster"]
    names = action.param_names()
    assert "storage_size" in names
    assert "instance_class" in names
    assert "storage" not in names  # 旧参数名已修正为 storage_size


def test_collect_resize_cluster_params():
    parser, _ = _build_parser()
    args = parser.parse_args(
        [
            "resize-cluster",
            "--cluster", "cl-x",
            "--node-role", "",
            "--cpu", "2",
            "--memory", "2048",
            "--storage-size", "20",
            "--instance-class", "202",
        ]
    )
    params = _collect_params(args, ACTIONS["resize-cluster"])
    assert params["cluster"] == "cl-x"
    assert params["node_role"] == ""
    assert params["cpu"] == 2
    assert params["memory"] == 2048
    assert params["storage_size"] == 20
    assert params["instance_class"] == 202


def test_describe_app_versions_has_status_param():
    action = ACTIONS["describe-app-versions"]
    assert "status" in action.param_names()
    param = next(p for p in action.params if p.name == "status")
    assert param.ptype == "list"


def test_collect_status_as_list():
    parser, _ = _build_parser()
    args = parser.parse_args(
        [
            "describe-app-versions",
            "--app-ids", "app-zydumbxo",
            "--status", "active",
            "--status", "suspended",
        ]
    )
    params = _collect_params(args, ACTIONS["describe-app-versions"])
    assert params["app_ids"] == ["app-zydumbxo"]
    assert params["status"] == ["active", "suspended"]


def test_collect_status_absent():
    parser, _ = _build_parser()
    args = parser.parse_args(
        ["describe-app-versions", "--app-ids", "app-zydumbxo"]
    )
    params = _collect_params(args, ACTIONS["describe-app-versions"])
    assert "status" not in params


def test_upgrade_clusters_has_params():
    action = ACTIONS["upgrade-clusters"]
    names = action.param_names()
    assert "app_version" in names
    assert "clusters" in names
    param = next(p for p in action.params if p.name == "clusters")
    assert param.ptype == "list"


def test_collect_upgrade_clusters_params():
    parser, _ = _build_parser()
    args = parser.parse_args(
        [
            "upgrade-clusters",
            "--app-version", "appv-tvzeju2i",
            "--clusters", "cl-x",
            "--clusters", "cl-y",
        ]
    )
    params = _collect_params(args, ACTIONS["upgrade-clusters"])
    assert params["app_version"] == "appv-tvzeju2i"
    assert params["clusters"] == ["cl-x", "cl-y"]


# ---------------------------------------------------------------------------
# AI-agent friendliness: help output
# ---------------------------------------------------------------------------


def test_help_shows_human_description():
    parser, _ = _build_parser()
    sub = parser.subparsers.choices["describe-clusters"]
    assert "获取集群信息" in sub.description
    # The top-level listing uses the description, not the raw API action name.
    assert "获取集群信息" in parser.format_help()


def test_help_shows_examples():
    parser, _ = _build_parser()
    sub = parser.subparsers.choices["describe-clusters"]
    assert "示例" in sub.epilog
    assert "appcenter describe-clusters" in sub.epilog


def test_help_marks_required_any():
    parser, _ = _build_parser()
    sub = parser.subparsers.choices["describe-app-versions"]
    assert "至少提供一个" in sub.epilog
    assert "--app-ids" in sub.epilog
    assert "--version-ids" in sub.epilog


def test_help_shows_notes():
    parser, _ = _build_parser()
    sub = parser.subparsers.choices["upgrade-clusters"]
    assert "注意事项" in sub.epilog
    assert "upgrade_policy" in sub.epilog


def test_help_has_trace_and_dry_run():
    parser, _ = _build_parser()
    sub = parser.subparsers.choices["describe-clusters"]
    assert "--trace" in sub.format_help()
    assert "--dry-run" in sub.format_help()


# ---------------------------------------------------------------------------
# AI-agent friendliness: wiki subcommand
# ---------------------------------------------------------------------------


def test_wiki_index_lists_commands(capsys):
    assert main(["wiki"]) == 0
    out = capsys.readouterr().out
    assert "describe-clusters" in out
    assert "获取集群信息" in out
    assert "wiki" in out


def test_wiki_detail(capsys):
    assert main(["wiki", "describe-clusters"]) == 0
    out = capsys.readouterr().out
    assert "DescribeClusters" in out
    assert "参数" in out
    assert "示例" in out
    assert "注意事项" in out


def test_wiki_unknown_command(capsys):
    assert main(["wiki", "no-such-command"]) == 2
    err = capsys.readouterr().err
    assert "unknown command" in err


# ---------------------------------------------------------------------------
# AI-agent friendliness: error output
# ---------------------------------------------------------------------------


def test_no_command_exit_2(capsys):
    assert main([]) == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err


def test_collect_invalid_json_reports_param():
    parser, _ = _build_parser()
    args = parser.parse_args(
        ["deploy-app-version", "--version-id", "appv-x", "--conf", "not-json"]
    )
    with pytest.raises(UsageError) as exc:
        _collect_params(args, ACTIONS["deploy-app-version"])
    assert "--conf" in str(exc.value)


def test_collect_invalid_int_reports_param():
    parser, _ = _build_parser()
    args = parser.parse_args(["describe-apps", "--limit", "abc"])
    with pytest.raises(UsageError) as exc:
        _collect_params(args, ACTIONS["describe-apps"])
    assert "--limit" in str(exc.value)


def test_collect_conf_must_be_object():
    parser, _ = _build_parser()
    args = parser.parse_args(
        ["deploy-app-version", "--version-id", "appv-x", "--conf", "[]"]
    )
    with pytest.raises(UsageError) as exc:
        _collect_params(args, ACTIONS["deploy-app-version"])
    assert "JSON object" in str(exc.value)


def test_collect_conf_object_ok():
    parser, _ = _build_parser()
    args = parser.parse_args(
        ["deploy-app-version", "--version-id", "appv-x", "--conf", '{"name":"demo"}']
    )
    params = _collect_params(args, ACTIONS["deploy-app-version"])
    assert params["conf"] == '{"name":"demo"}'


def test_usage_error_shows_usage_line(capsys, monkeypatch):
    # Missing required params must be reported even without credentials,
    # and the error must include the usage line.
    monkeypatch.delenv("QINGCLOUD_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("QINGCLOUD_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("QINGCLOUD_CONFIG", raising=False)
    monkeypatch.setenv("HOME", "/tmp/nonexistent-home-for-test")
    assert main(["deploy-app-version"]) == 2
    err = capsys.readouterr().err
    assert "usage:" in err
    assert "Missing required parameter" in err
    assert "Missing credentials" not in err


def test_dry_run_prints_request_without_sending(capsys, monkeypatch):
    monkeypatch.setenv("QINGCLOUD_ACCESS_KEY_ID", "AK")
    monkeypatch.setenv("QINGCLOUD_SECRET_ACCESS_KEY", "SK")
    monkeypatch.setenv("QINGCLOUD_ZONE", "pek3")
    monkeypatch.delenv("QINGCLOUD_CONFIG", raising=False)
    assert main(["describe-clusters", "--dry-run", "--limit", "1"]) == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out
    assert "action=DescribeClusters" in out
    assert "signature=" in out
    assert "***" in out  # signature masked


def test_trace_prints_request_to_stderr(capsys, monkeypatch):
    monkeypatch.setenv("QINGCLOUD_ACCESS_KEY_ID", "AK")
    monkeypatch.setenv("QINGCLOUD_SECRET_ACCESS_KEY", "SK")
    monkeypatch.setenv("QINGCLOUD_ZONE", "pek3")
    monkeypatch.delenv("QINGCLOUD_CONFIG", raising=False)
    # --trace + --dry-run: no real API call is made.
    assert main(["describe-clusters", "--trace", "--dry-run", "--limit", "1"]) == 0
    captured = capsys.readouterr()
    assert "[trace]" in captured.err
    assert "[dry-run]" in captured.out
