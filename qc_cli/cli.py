"""Shared CLI framework for the qc-tools command line tools.

Both the AppCenter CLI and the IaaS CLI are thin wrappers around this
framework: each provides a program name, a description, an action registry
and a version, and this module builds the argparse parser, collects and
validates parameters, and runs the request.
"""

import argparse
import json
import re
import sys

from .client import APIError, Client
from .config import ConfigError, load_config
from .output import render

GLOBAL_FLAGS = [
    ("--access-key-id", "QINGCLOUD_ACCESS_KEY_ID", "API access key ID"),
    ("--secret-access-key", "QINGCLOUD_SECRET_ACCESS_KEY", "API secret access key"),
    ("--zone", "QINGCLOUD_ZONE", "zone ID, e.g. pek3 (region) or pek3b (zone)"),
    ("--host", "QINGCLOUD_HOST", "API host, default api.qingcloud.com"),
    ("--config", "QINGCLOUD_CONFIG", "path to the config file"),
]


class UsageError(ConfigError):
    """Raised for CLI usage problems (missing or invalid parameters).

    Subclasses ConfigError so existing callers that catch ConfigError keep
    working, but lets the CLI show the usage line for these errors.
    """


def add_global_flags(parser, action=None):
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
    parser.add_argument(
        "--trace",
        action="store_true",
        help="print the HTTP request that would be sent (signature masked)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="build and print the request without sending it",
    )


def build_epilog(action):
    """Build the Examples / Notes / required-any epilog for a subcommand."""
    parts = []
    for group in action.required_any:
        flags = ", ".join("--%s" % g.replace("_", "-") for g in group)
        parts.append("注意：%s 至少提供一个。" % flags)
    if action.examples:
        parts.append("示例：")
        parts.extend("  %s" % ex for ex in action.examples)
    if action.notes:
        parts.append("注意事项：")
        parts.extend("  - %s" % note for note in action.notes)
    return "\n".join(parts)


def build_parser(prog, description, actions, version):
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("--version", action="version", version="%s %s" % (prog, version))
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    for name, action in actions.items():
        sub = subparsers.add_parser(
            name,
            help=action.description or action.name,
            description=action.description or action.name,
            epilog=build_epilog(action),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_global_flags(sub, action)
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

    wiki = subparsers.add_parser(
        "wiki",
        help="查看命令的详细用法与注意事项",
        description="查看命令的详细用法与注意事项",
    )
    wiki.add_argument("topic", nargs="?", metavar="COMMAND", help="要查看的命令名，如 describe-clusters")

    # Expose the subparsers on the parser so callers/tests can fetch a
    # specific subparser (e.g. for its usage line or help text).
    parser.subparsers = subparsers
    return parser, subparsers


def collect_params(args, action):
    """Collect request parameters from parsed CLI args.

    Raises UsageError with the offending flag name on invalid input.
    """
    params = {}
    for param in action.params:
        value = getattr(args, param.name, None)
        if value is None:
            continue
        flag = "--%s" % param.name.replace("_", "-")
        if param.ptype == "list":
            params[param.name] = value
        elif param.ptype == "list_dict":
            parsed = []
            for item in value:
                if isinstance(item, str):
                    try:
                        item = json.loads(item)
                    except json.JSONDecodeError as e:
                        raise UsageError("invalid input for %s: not valid JSON (%s)" % (flag, e))
                parsed.append(item)
            params[param.name] = parsed
        elif param.ptype == "int":
            try:
                params[param.name] = int(value)
            except ValueError:
                raise UsageError("invalid input for %s: %r is not an integer" % (flag, value))
        elif param.ptype == "json":
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as e:
                raise UsageError("invalid input for %s: not valid JSON (%s)" % (flag, e))
            if param.json_object and not isinstance(parsed, dict):
                raise UsageError(
                    "invalid input for %s: expected a JSON object, got %s"
                    % (flag, type(parsed).__name__)
                )
            params[param.name] = json.dumps(parsed, separators=(",", ":"))
        else:
            params[param.name] = value
    return params


def check_required(params, action):
    missing = [p for p in action.required_params() if p not in params]
    if missing:
        raise UsageError(
            "Missing required parameter(s): %s" % ", ".join("--%s" % m.replace("_", "-") for m in missing)
        )
    for group in action.required_any_groups():
        if not any(p in params for p in group):
            raise UsageError(
                "Missing required parameter(s): at least one of %s"
                % ", ".join("--%s" % g.replace("_", "-") for g in group)
            )


def mask_signature(url):
    """Mask the signature value in a request URL (it is derived from the
    secret key and should not be echoed in full)."""
    return re.sub(r"(signature=)[^&]+", r"\1***", url)


def format_param_lines(action):
    lines = []
    for param in action.params:
        flag = "--%s" % param.name.replace("_", "-")
        req = " [required]" if param.required else ""
        if param.ptype == "list":
            suffix = " (repeatable)"
        elif param.ptype == "list_dict":
            suffix = " (repeatable, JSON object)"
        else:
            suffix = ""
        lines.append("  %s  %s%s%s" % (flag, param.description, suffix, req))
    return lines


def run_wiki(prog, actions, args):
    """Implement the `<prog> wiki` meta-command (no API call)."""
    if args.topic:
        if args.topic not in actions:
            print("error: unknown command: %s" % args.topic, file=sys.stderr)
            print("run '%s wiki' to list all commands" % prog, file=sys.stderr)
            return 2
        action = actions[args.topic]
        print("%s - %s" % (args.topic, action.description or action.name))
        print()
        print("API 动作: %s" % action.name)
        print("请求: %s %s" % (action.verb, action.path))
        print()
        print("参数:")
        for line in format_param_lines(action):
            print(line)
        if action.required_any:
            print()
            print("约束:")
            for group in action.required_any:
                flags = ", ".join("--%s" % g.replace("_", "-") for g in group)
                print("  - %s 至少提供一个" % flags)
        if action.examples:
            print()
            print("示例:")
            for ex in action.examples:
                print("  %s" % ex)
        if action.notes:
            print()
            print("注意事项:")
            for note in action.notes:
                print("  - %s" % note)
        return 0

    print("%s wiki - 查看命令的详细用法与注意事项" % prog)
    print()
    print("用法:")
    print("  %s wiki [COMMAND]" % prog)
    print()
    print("可用命令:")
    for name, action in sorted(actions.items()):
        print("  %-40s %s" % (name, action.description or action.name))
    print()
    print("示例:")
    print("  %s wiki describe-clusters" % prog)
    return 0


def run(prog, description, actions, version, argv=None):
    parser, subparsers = build_parser(prog, description, actions, version)
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(sys.stderr)
        return 2

    if args.command == "wiki":
        return run_wiki(prog, actions, args)

    action = actions[args.command]
    sub = subparsers.choices[args.command]

    try:
        # Validate parameters before loading config so that usage errors
        # (missing/invalid params) are reported even when credentials are
        # missing.
        params = collect_params(args, action)
        check_required(params, action)

        config = load_config(
            access_key_id=args.access_key_id,
            secret_access_key=args.secret_access_key,
            zone=args.zone,
            host=args.host,
            config_path=args.config,
        )
        config.validate()

        client = Client(config)
        url = client.build_request(action.name, params, verb=action.verb, path=action.path)
        if args.trace:
            print("[trace] %s %s" % (action.verb, mask_signature(url)), file=sys.stderr)
        if args.dry_run:
            print("[dry-run] %s %s" % (action.verb, mask_signature(url)))
            return 0
        data = client.send_request(action.name, params, verb=action.verb, path=action.path)
        render(data, args.output, table_columns=action.table_columns)
        return 0
    except UsageError as e:
        print(sub.format_usage(), file=sys.stderr, end="")
        print("error: %s" % e, file=sys.stderr)
        return 2
    except ConfigError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except APIError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
