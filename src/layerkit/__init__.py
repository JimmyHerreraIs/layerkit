"""layerkit: turn any flat image into editable layers.

The public API will live here. Everything below ``layerkit.core`` is
independent of the command line and of any web API.
"""

from layerkit.core.errors import (
    ImageTooLargeError,
    LayerkitError,
    NoObjectFoundError,
    UnsupportedImageError,
)
from layerkit.core.types import BoundingBox, Decomposition, Layer

__version__ = "0.0.0"

__all__ = [
    "BoundingBox",
    "Decomposition",
    "ImageTooLargeError",
    "Layer",
    "LayerkitError",
    "NoObjectFoundError",
    "UnsupportedImageError",
    "__version__",
]
