"""Unit tests for the CLI layer (param collection and validation)."""

import pytest

from appcenter_cli.actions import ACTIONS, Action, Param
from appcenter_cli.cli import _build_parser, _check_required, _collect_params
from appcenter_cli.config import ConfigError


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
    parser = _build_parser()
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
    parser = _build_parser()
    args = parser.parse_args(
        ["deploy-app-version", "--version-id", "appv-x", "--conf", "{}"]
    )
    params = _collect_params(args, ACTIONS["deploy-app-version"])
    assert "multi_deploy_zones" not in params
