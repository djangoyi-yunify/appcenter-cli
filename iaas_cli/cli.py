"""Command line interface for the IaaS CLI (part of the qc-tools suite).

The CLI logic itself lives in the shared ``qc_cli.cli`` framework; this
module only wires the IaaS action registry into it.
"""

import sys

from qc_cli.cli import run

from . import __version__
from .actions import ACTIONS

PROG = "iaas"
DESCRIPTION = "QingCloud IaaS command line tool for AI agents"


def main(argv=None):
    return run(PROG, DESCRIPTION, ACTIONS, __version__, argv)


if __name__ == "__main__":
    sys.exit(main())
