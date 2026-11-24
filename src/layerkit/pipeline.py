"""The decompose pipeline: from an image file to a set of layers.

This module ties the building blocks together. It lives above ``layerkit.core``
because it needs the model registry; the core never depends on it.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO

from layerkit.core.cutout import cut_out
from layerkit.core.interfaces import ForegroundModel
from layerkit.core.loading import DEFAULT_MAX_PIXELS, load_image
from layerkit.core.types import BoundingBox, Decomposition, Layer
from layerkit.core.validation import validate_mask
from layerkit.models import load_model

BACKGROUND_NAME = "background"
SUBJECT_NAME = "subject"
_ANONYMOUS_SOURCE = "image"


def decompose(
    source: str | os.PathLike[str] | IO[bytes],
    *,
    model: ForegroundModel | None = None,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> Decomposition:
    """Split an image into a background layer and a cut-out subject.

    The steps are: load and normalize the image, compute a foreground mask,
    check that the mask describes a clear object, and cut the object out. The
    background layer is the original image, whole, behind the subject.

    Args:
        source: Path to the image file, or a binary file object.
        model: The model that computes the foreground mask. When omitted, the
            default model is used, which needs the ``rembg`` extra.
        max_pixels: Maximum number of pixels (width times height) allowed.

    Returns:
        A decomposition with two layers: ``background`` (stacking order 0) and
        ``subject`` (stacking order 1).

    Raises:
        FileNotFoundError: If ``source`` is a path that does not exist.
        UnsupportedImageError: If the input is not a readable JPEG, PNG or WebP
            image.
        ImageTooLargeError: If the image has more than ``max_pixels`` pixels.
        ModelNotAvailableError: If the model needs a package that is missing.
        NoObjectFoundError: If the mask does not describe a clear object.
    """
    image = load_image(source, max_pixels=max_pixels)
    active_model = model if model is not None else load_model()

    mask = active_model.predict_mask(image)
    validate_mask(mask)
    subject = cut_out(image, mask, name=SUBJECT_NAME, z=1)

    width, height = image.size
    background = Layer(
        name=BACKGROUND_NAME,
        image=image.convert("RGBA"),
        box=BoundingBox(0, 0, width, height),
        z=0,
    )
    return Decomposition(
        source_name=_source_name(source),
        width=width,
        height=height,
        layers=(background, subject),
    )


def _source_name(source: str | os.PathLike[str] | IO[bytes]) -> str:
    """Name the source after its file, or ``"image"`` when it has none."""
    if isinstance(source, str | os.PathLike):
        return Path(source).name
    name = getattr(source, "name", None)
    if isinstance(name, str) and Path(name).name:
        return Path(name).name
    return _ANONYMOUS_SOURCE
