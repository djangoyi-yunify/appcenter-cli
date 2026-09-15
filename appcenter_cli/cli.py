"""Command line interface for the AppCenter CLI (part of the qc-tools suite).

The CLI logic itself lives in the shared ``qc_cli.cli`` framework; this
module only wires the AppCenter action registry into it.
"""

import sys

from qc_cli.cli import (
    UsageError,
    build_parser,
    check_required,
    collect_params,
    run,
)

from . import __version__
from .actions import ACTIONS

PROG = "appcenter"
DESCRIPTION = "QingCloud AppCenter command line tool for AI agents"


def _build_parser():
    return build_parser(PROG, DESCRIPTION, ACTIONS, __version__)


def _check_required(params, action):
    return check_required(params, action)


def _collect_params(args, action):
    return collect_params(args, action)


def main(argv=None):
    return run(PROG, DESCRIPTION, ACTIONS, __version__, argv)


if __name__ == "__main__":
    sys.exit(main())
