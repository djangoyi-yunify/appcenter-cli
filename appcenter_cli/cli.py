"""Command line interface for the AppCenter CLI."""

import argparse
import json
import sys

from . import __version__
from .actions import ACTIONS
from .client import APIError, Client
from .config import ConfigError, load_config
from .output import render

GLOBAL_FLAGS = [
    ("--access-key-id", "QINGCLOUD_ACCESS_KEY_ID", "API access key ID"),
    ("--secret-access-key", "QINGCLOUD_SECRET_ACCESS_KEY", "API secret access key"),
    ("--zone", "QINGCLOUD_ZONE", "zone ID, e.g. pek3a"),
    ("--host", "QINGCLOUD_HOST", "API host, default api.qingcloud.com"),
    ("--config", "QINGCLOUD_CONFIG", "path to the config file"),
]


def _add_global_flags(parser, action=None):
    for flag, env, help_text in GLOBAL_FLAGS:
        param_name = flag.lstrip("-").replace("-", "_")
        if action is not None and param_name in action.param_names():
            # The action defines its own parameter with the same name
            # (e.g. RecoverClusters has a required "zone" parameter).
            continue
        parser.add_argument(flag, default="", help="%s (env: %s)" % (help_text, env))
    parser.add_argument(
        "--output",
        choices=["json", "table"],
        default="json",
        help="output format, default json",
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="appcenter",
        description="QingCloud AppCenter command line tool for AI agents",
    )
    parser.add_argument("--version", action="version", version="appcenter %s" % __version__)
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    for name, action in ACTIONS.items():
        sub = subparsers.add_parser(name, help="%s" % action.name)
        _add_global_flags(sub, action)
        for param in action.params:
            flag = "--%s" % param.name.replace("_", "-")
            if param.ptype == "list":
                sub.add_argument(
                    flag,
                    action="append",
                    default=None,
                    metavar="VALUE",
                    help="%s (repeatable)%s" % (param.description, " [required]" if param.required else ""),
                )
            elif param.ptype == "list_dict":
                sub.add_argument(
                    flag,
                    action="append",
                    default=None,
                    metavar="JSON",
                    help="%s (repeatable, JSON object)%s" % (param.description, " [required]" if param.required else ""),
                )
            else:
                sub.add_argument(
                    flag,
                    default=None,
                    metavar="VALUE",
                    help="%s%s" % (param.description, " [required]" if param.required else ""),
                )
    return parser


def _collect_params(args, action):
    """Collect request parameters from parsed CLI args."""
    params = {}
    for param in action.params:
        value = getattr(args, param.name, None)
        if value is None:
            continue
        if param.ptype == "list":
            params[param.name] = value
        elif param.ptype == "list_dict":
            parsed = []
            for item in value:
                if isinstance(item, str):
                    item = json.loads(item)
                parsed.append(item)
            params[param.name] = parsed
        elif param.ptype == "int":
            params[param.name] = int(value)
        elif param.ptype == "json":
            params[param.name] = json.dumps(json.loads(value), separators=(",", ":"))
        else:
            params[param.name] = value
    return params


def _check_required(params, action):
    missing = [p for p in action.required_params() if p not in params]
    if missing:
        raise ConfigError(
            "Missing required parameter(s): %s" % ", ".join("--%s" % m.replace("_", "-") for m in missing)
        )


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    action = ACTIONS[args.command]

    try:
        config = load_config(
            access_key_id=args.access_key_id,
            secret_access_key=args.secret_access_key,
            zone=args.zone,
            host=args.host,
            config_path=args.config,
        )
        config.validate()

        params = _collect_params(args, action)
        _check_required(params, action)

        client = Client(config)
        data = client.send_request(action.name, params, verb=action.verb, path=action.path)
        render(data, args.output, table_columns=action.table_columns)
        return 0
    except ConfigError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except APIError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as e:
        print("error: invalid input: %s" % e, file=sys.stderr)
        return 2
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
