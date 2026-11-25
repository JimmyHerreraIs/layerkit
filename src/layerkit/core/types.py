"""Immutable data types shared by every step of the pipeline.

``Layer`` and ``Decomposition`` use identity equality (``eq=False``) because
they hold Pillow images, which are not meant to be compared or hashed by value.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

_RGBA = "RGBA"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """A rectangle in pixel coordinates.

    ``x`` and ``y`` are the top-left corner, measured from the top-left corner
    of the full image.

    Attributes:
        x: Horizontal position of the left edge.
        y: Vertical position of the top edge.
        width: Width in pixels.
        height: Height in pixels.
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate the rectangle.

        Raises:
            ValueError: If the size is not positive or the origin is negative.
        """
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"width and height must be positive, got {self.width}x{self.height}"
            )
        if self.x < 0 or self.y < 0:
            raise ValueError(f"x and y must not be negative, got ({self.x}, {self.y})")

    @property
    def area(self) -> int:
        """Number of pixels inside the rectangle."""
        return self.width * self.height


@dataclass(frozen=True, slots=True, eq=False)
class Layer:
    """One cut-out piece of the source image.

    Attributes:
        name: Human-readable name, for example ``"subject"``.
        image: RGBA image cropped to ``box``; pixels outside the object are
            transparent.
        box: Where the layer sits in the full image.
        z: Stacking order; a higher value is drawn in front.
    """

    name: str
    image: Image.Image
    box: BoundingBox
    z: int

    def __post_init__(self) -> None:
        """Validate the layer.

        Raises:
            ValueError: If the name is empty, the image is not RGBA, the image
                size differs from the box size, or ``z`` is negative.
        """
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if self.image.mode != _RGBA:
            raise ValueError(f"image must be RGBA, got {self.image.mode}")
        if self.image.size != (self.box.width, self.box.height):
            raise ValueError(
                f"image size {self.image.size} does not match "
                f"box size {(self.box.width, self.box.height)}"
            )
        if self.z < 0:
            raise ValueError(f"z must not be negative, got {self.z}")


@dataclass(frozen=True, slots=True, eq=False)
class Decomposition:
    """The result of splitting an image into layers.

    Attributes:
        source_name: File name of the original image.
        width: Width of the full image in pixels.
        height: Height of the full image in pixels.
        layers: The layers, with unique ``z`` values.
    """

    source_name: str
    width: int
    height: int
    layers: tuple[Layer, ...]

    def __post_init__(self) -> None:
        """Validate the decomposition.

        Raises:
            ValueError: If the canvas size is not positive, there are no layers,
                a layer falls outside the canvas, or two layers share a ``z``.
        """
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"width and height must be positive, got {self.width}x{self.height}"
            )
        if not self.layers:
            raise ValueError("a decomposition needs at least one layer")
        for layer in self.layers:
            box = layer.box
            if box.x + box.width > self.width or box.y + box.height > self.height:
                raise ValueError(
                    f"layer {layer.name!r} falls outside the "
                    f"{self.width}x{self.height} canvas"
                )
        z_values = [layer.z for layer in self.layers]
        if len(set(z_values)) != len(z_values):
            raise ValueError("layers must have unique z values")
