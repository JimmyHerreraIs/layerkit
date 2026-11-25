"""Interfaces that the pipeline depends on and that live outside ``core``.

``core`` defines what it needs; the adapters in ``layerkit.models`` provide it.
That way a model can be swapped without touching the pipeline.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from PIL import Image


@runtime_checkable
class ForegroundModel(Protocol):
    """A model that marks which pixels of an image belong to the main object."""

    @property
    def name(self) -> str:
        """Short identifier of the model, for example ``"u2netp"``."""
        ...

    def predict_mask(self, image: Image.Image) -> Image.Image:
        """Compute the foreground mask of an image.

        Args:
            image: The RGB image to analyze.

        Returns:
            An 8-bit grayscale (mode ``"L"``) image with the same size as
            ``image``: 255 where the object is, 0 where it is not, and
            intermediate values along soft edges.

        Raises:
            ModelNotAvailableError: If the model needs an optional dependency
                that is not installed.
        """
        ...
