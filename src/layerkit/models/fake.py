"""A deterministic model for tests: no dependencies, no downloads.

It marks a centered rectangle as the object, so tests of the pipeline know
exactly what mask to expect.
"""

from __future__ import annotations

from PIL import Image


class CenteredBoxModel:
    """Marks a centered rectangle of the image as the object.

    Attributes:
        fraction: Size of the rectangle as a fraction of each side of the image.
    """

    def __init__(self, fraction: float = 0.5) -> None:
        """Choose how large the marked rectangle is.

        Args:
            fraction: Fraction of the width and height covered, in ``(0, 1]``.

        Raises:
            ValueError: If ``fraction`` is not in ``(0, 1]``.
        """
        if not 0 < fraction <= 1:
            raise ValueError(f"fraction must be in (0, 1], got {fraction}")
        self.fraction = fraction

    @property
    def name(self) -> str:
        """Identifier of this model."""
        return "fake-centered-box"

    def predict_mask(self, image: Image.Image) -> Image.Image:
        """Return a mask with a centered white rectangle.

        Args:
            image: The image whose size the mask must match.

        Returns:
            An 8-bit grayscale mask: 255 inside the rectangle, 0 outside.
        """
        width, height = image.size
        box_width = max(1, round(width * self.fraction))
        box_height = max(1, round(height * self.fraction))
        left = (width - box_width) // 2
        top = (height - box_height) // 2
        mask = Image.new("L", image.size, 0)
        mask.paste(255, (left, top, left + box_width, top + box_height))
        return mask
