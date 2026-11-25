from dataclasses import FrozenInstanceError

import pytest
from PIL import Image

from layerkit.core.types import BoundingBox, Decomposition, Layer


def make_layer(
    name: str = "subject",
    *,
    x: int = 0,
    y: int = 0,
    width: int = 4,
    height: int = 3,
    z: int = 1,
) -> Layer:
    return Layer(
        name=name,
        image=Image.new("RGBA", (width, height)),
        box=BoundingBox(x, y, width, height),
        z=z,
    )


class TestBoundingBox:
    def test_area_is_width_times_height(self) -> None:
        assert BoundingBox(10, 20, 4, 3).area == 12

    @pytest.mark.parametrize("width, height", [(0, 5), (5, 0), (-1, 5), (5, -1)])
    def test_rejects_a_non_positive_size(self, width: int, height: int) -> None:
        with pytest.raises(ValueError, match="positive"):
            BoundingBox(0, 0, width, height)

    @pytest.mark.parametrize("x, y", [(-1, 0), (0, -1)])
    def test_rejects_a_negative_origin(self, x: int, y: int) -> None:
        with pytest.raises(ValueError, match="negative"):
            BoundingBox(x, y, 5, 5)

    def test_is_immutable(self) -> None:
        box = BoundingBox(0, 0, 5, 5)

        with pytest.raises(FrozenInstanceError):
            box.x = 1  # type: ignore[misc]


class TestLayer:
    def test_keeps_its_fields(self) -> None:
        layer = make_layer("mug", x=2, y=3, width=4, height=3, z=2)

        assert layer.name == "mug"
        assert layer.box == BoundingBox(2, 3, 4, 3)
        assert layer.z == 2

    def test_rejects_an_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name"):
            make_layer("   ")

    def test_rejects_an_image_that_is_not_rgba(self) -> None:
        with pytest.raises(ValueError, match="RGBA"):
            Layer("subject", Image.new("RGB", (4, 3)), BoundingBox(0, 0, 4, 3), z=1)

    def test_rejects_an_image_that_does_not_match_its_box(self) -> None:
        with pytest.raises(ValueError, match="does not match"):
            Layer("subject", Image.new("RGBA", (5, 3)), BoundingBox(0, 0, 4, 3), z=1)

    def test_rejects_a_negative_z(self) -> None:
        with pytest.raises(ValueError, match="z"):
            make_layer(z=-1)

    def test_is_immutable(self) -> None:
        layer = make_layer()

        with pytest.raises(FrozenInstanceError):
            layer.z = 5  # type: ignore[misc]


class TestDecomposition:
    def test_keeps_its_fields(self) -> None:
        background = make_layer("background", width=10, height=8, z=0)
        subject = make_layer("subject", x=2, y=2, z=1)

        result = Decomposition("photo.jpg", 10, 8, (background, subject))

        assert result.source_name == "photo.jpg"
        assert (result.width, result.height) == (10, 8)
        assert result.layers == (background, subject)

    @pytest.mark.parametrize("width, height", [(0, 8), (10, 0), (-1, 8)])
    def test_rejects_a_non_positive_canvas(self, width: int, height: int) -> None:
        with pytest.raises(ValueError, match="positive"):
            Decomposition("photo.jpg", width, height, (make_layer(),))

    def test_rejects_an_empty_layer_list(self) -> None:
        with pytest.raises(ValueError, match="at least one layer"):
            Decomposition("photo.jpg", 10, 8, ())

    def test_rejects_a_layer_outside_the_canvas(self) -> None:
        outside = make_layer("subject", x=8, y=0, width=4, height=3)

        with pytest.raises(ValueError, match="outside"):
            Decomposition("photo.jpg", 10, 8, (outside,))

    def test_rejects_duplicate_z_values(self) -> None:
        first = make_layer("one", z=1)
        second = make_layer("two", z=1)

        with pytest.raises(ValueError, match="unique z"):
            Decomposition("photo.jpg", 10, 8, (first, second))
