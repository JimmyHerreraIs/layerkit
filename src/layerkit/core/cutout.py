"""Cut an object out of an image using a foreground mask."""

from __future__ import annotations

from PIL import Image

from layerkit.core.errors import NoObjectFoundError
from layerkit.core.types import BoundingBox, Layer
from layerkit.core.validation import mask_coverage

ALPHA_FLOOR = 16
"""Mask values below this (out of 255) count as background, not as object."""

_FLOOR_TABLE = [value if value >= ALPHA_FLOOR else 0 for value in range(256)]


def cut_out(
    image: Image.Image,
    mask: Image.Image,
    *,
    name: str = "subject",
    z: int = 1,
) -> Layer:
    """Apply a foreground mask to an image and crop the result to the object.

    The mask becomes the alpha channel, so soft edges stay soft. Mask values
    below ``ALPHA_FLOOR`` are treated as background: models leave faint noise
    far from the object, and keeping it would stretch the crop over the whole
    image. The returned layer is cropped to the smallest rectangle that
    contains every remaining object pixel.

    Args:
        image: The source image. It is converted to RGB if needed.
        mask: An 8-bit grayscale mask (mode ``"L"``) with the same size as
            ``image``. ``255`` is fully foreground and ``0`` is background.
        name: Name given to the layer.
        z: Stacking order given to the layer.

    Returns:
        An RGBA layer whose box tells where it sits in the full image.

    Raises:
        ValueError: If the mask is not mode ``"L"`` or its size differs from
            the image size.
        NoObjectFoundError: If no mask value reaches ``ALPHA_FLOOR``.
    """
    if mask.mode != "L":
        raise ValueError(f"mask must be grayscale (mode 'L'), got {mask.mode!r}")
    if mask.size != image.size:
        raise ValueError(
            f"mask size {mask.size} does not match image size {image.size}"
        )

    alpha = mask.point(_FLOOR_TABLE)
    bounds = alpha.getbbox()
    if bounds is None:
        raise NoObjectFoundError(mask_coverage(mask))
    left, top, right, bottom = bounds

    cutout = image.convert("RGBA")
    cutout.putalpha(alpha)
    cutout = cutout.crop(bounds)

    box = BoundingBox(left, top, right - left, bottom - top)
    return Layer(name=name, image=cutout, box=box, z=z)
