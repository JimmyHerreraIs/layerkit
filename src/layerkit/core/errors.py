"""Exceptions raised on purpose by layerkit.

Every error derives from :class:`LayerkitError`, so callers can catch the whole
family with a single ``except`` clause.
"""

from __future__ import annotations

from collections.abc import Sequence

_PIXELS_PER_MEGAPIXEL = 1_000_000


class LayerkitError(Exception):
    """Base class for every error that layerkit raises deliberately."""


class UnsupportedImageError(LayerkitError):
    """The input is not an image that layerkit can read."""


class ImageTooLargeError(LayerkitError):
    """The image has more pixels than the configured maximum.

    Attributes:
        pixels: Number of pixels in the rejected image.
        max_pixels: Maximum number of pixels allowed.
    """

    def __init__(self, pixels: int, max_pixels: int) -> None:
        """Store both sizes and build a readable message.

        Args:
            pixels: Number of pixels in the rejected image.
            max_pixels: Maximum number of pixels allowed.
        """
        self.pixels = pixels
        self.max_pixels = max_pixels
        super().__init__(
            f"Image has {pixels / _PIXELS_PER_MEGAPIXEL:.1f} MP; "
            f"the maximum allowed is {max_pixels / _PIXELS_PER_MEGAPIXEL:.1f} MP."
        )


class InvalidManifestError(LayerkitError):
    """A manifest is malformed, unsafe or written in an unsupported format."""


class ModelNotAvailableError(LayerkitError):
    """A model needs an optional dependency that is not installed."""


class UnknownModelError(LayerkitError):
    """The requested model name does not exist.

    Attributes:
        name: The name that was requested.
        choices: The names that are available.
    """

    def __init__(self, name: str, choices: Sequence[str]) -> None:
        """Store the name and the valid choices and build a readable message.

        Args:
            name: The name that was requested.
            choices: The names that are available.
        """
        self.name = name
        self.choices = tuple(choices)
        super().__init__(
            f"Unknown model {name!r}. Available models: {', '.join(self.choices)}."
        )


class NoObjectFoundError(LayerkitError):
    """The model did not find a clear object in the image.

    Attributes:
        coverage: Fraction of the image (0 to 1) that the mask marked as object.
    """

    def __init__(self, coverage: float) -> None:
        """Store the mask coverage and build a readable message.

        Args:
            coverage: Fraction of the image (0 to 1) marked as object.
        """
        self.coverage = coverage
        super().__init__(
            f"No clear object was found (the mask covers {coverage:.1%} of the image)."
        )
