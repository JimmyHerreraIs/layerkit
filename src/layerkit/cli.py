"""Command-line entry point for layerkit.

This is one of the three doors into the library (CLI, API, Python import).
It may import from ``layerkit.core``; ``layerkit.core`` must never import it.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from layerkit import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``layerkit`` command.

    Returns:
        A configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        prog="layerkit",
        description="Turn any flat image into editable layers.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the installed version and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``layerkit`` command.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code (0 on success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"layerkit {__version__}")
        return 0
    parser.print_help()
    return 0
