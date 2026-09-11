"""Unit tests for the CLI layer (param collection and validation)."""

import pytest

from appcenter_cli.actions import ACTIONS, Action, Param
from appcenter_cli.cli import _check_required
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
