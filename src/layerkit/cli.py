"""Command-line entry point for layerkit.

This is one of the three doors into the library (CLI, API, Python import).
It may import from ``layerkit.core``; ``layerkit.core`` must never import it.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from layerkit import __version__
from layerkit.core.errors import LayerkitError, OutputExistsError
from layerkit.core.loading import DEFAULT_MAX_PIXELS
from layerkit.exporters.png import export_png
from layerkit.models import DEFAULT_MODEL_NAME, available_models, load_model
from layerkit.pipeline import decompose


def _positive_int(text: str) -> int:
    """Parse a strictly positive integer for ``argparse``."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a whole number") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``layerkit`` command.

    Returns:
        A configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        prog="layerkit",
        description=(
            "Turn a flat image into editable layers: one transparent PNG per "
            "layer plus a manifest.json."
        ),
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="path to a JPEG, PNG or WebP image",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="DIR",
        help="folder for the layers (default: <image name>-layers)",
    )
    parser.add_argument(
        "--model",
        choices=available_models(),
        default=DEFAULT_MODEL_NAME,
        help="foreground model to use (default: %(default)s)",
    )
    parser.add_argument(
        "--max-pixels",
        type=_positive_int,
        default=DEFAULT_MAX_PIXELS,
        metavar="N",
        help="largest image to accept, in pixels (default: %(default)s)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace layer files that already exist in the output folder",
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
        The process exit code: 0 on success, 1 when the image cannot be
        processed. Invalid arguments exit with code 2, as ``argparse`` does.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"layerkit {__version__}")
        return 0
    if args.image is None:
        parser.print_help()
        return 0
    return _split(args)


def _split(args: argparse.Namespace) -> int:
    """Decompose the image and write the result, reporting errors briefly."""
    image_path = Path(args.image)
    output_dir = Path(args.output) if args.output else Path(f"{image_path.stem}-layers")
    try:
        result = decompose(
            image_path,
            model=load_model(args.model),
            max_pixels=args.max_pixels,
        )
        exported = export_png(result, output_dir, overwrite=args.overwrite)
    except FileNotFoundError:
        print(f"error: file not found: {image_path}", file=sys.stderr)
        return 1
    except OutputExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --overwrite to replace them.", file=sys.stderr)
        return 1
    except (LayerkitError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Saved {len(exported.layer_paths)} layers to {exported.output_dir}")
    for path in (*exported.layer_paths, exported.manifest_path):
        print(f"  {path.name}")
    return 0
