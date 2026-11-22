"""Load an image from disk and normalize it for the rest of the pipeline.

This is step 1 of the pipeline and the first line of defense: it rejects files
that are not images, formats we do not support, and images that are too large,
before any model runs.
"""

from __future__ import annotations

import os
from typing import IO

from PIL import Image, ImageOps, UnidentifiedImageError

from layerkit.core.errors import ImageTooLargeError, UnsupportedImageError

DEFAULT_MAX_PIXELS = 25_000_000  # 25 megapixels
SUPPORTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})

_WHITE = (255, 255, 255, 255)


def load_image(
    source: str | os.PathLike[str] | IO[bytes],
    *,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> Image.Image:
    """Read an image and return it upright, in RGB mode.

    The size check runs on the file header, before the pixels are decoded, so
    an oversized image is rejected without loading it into memory. Transparent
    images are flattened over a white background.

    Args:
        source: Path to the image file, or a binary file object.
        max_pixels: Maximum number of pixels (width times height) allowed.

    Returns:
        An RGB image with the EXIF orientation already applied.

    Raises:
        FileNotFoundError: If ``source`` is a path that does not exist.
        UnsupportedImageError: If the input is not a readable JPEG, PNG or WebP
            image, or the file is truncated or corrupt.
        ImageTooLargeError: If the image has more than ``max_pixels`` pixels.
    """
    try:
        image = Image.open(source)
    except UnidentifiedImageError as exc:
        raise UnsupportedImageError("The input is not a readable image.") from exc
    except Image.DecompressionBombError as exc:
        raise UnsupportedImageError(
            "The image exceeds Pillow's decompression-bomb limit."
        ) from exc

    with image:
        if image.format not in SUPPORTED_FORMATS:
            raise UnsupportedImageError(
                f"Unsupported image format {image.format!r}; "
                "supported formats are JPEG, PNG and WebP."
            )
        pixels = image.width * image.height
        if pixels > max_pixels:
            raise ImageTooLargeError(pixels, max_pixels)
        try:
            image.load()
        except OSError as exc:
            raise UnsupportedImageError(
                "The image file is truncated or corrupt."
            ) from exc
        return _to_rgb(ImageOps.exif_transpose(image))


def _to_rgb(image: Image.Image) -> Image.Image:
    """Convert any Pillow mode to RGB, flattening transparency over white."""
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, _WHITE)
        return Image.alpha_composite(canvas, rgba).convert("RGB")
    return image.convert("RGB")
