import pytest
from PIL import Image

from layerkit.core.cutout import cut_out
from layerkit.core.errors import NoObjectFoundError
from layerkit.core.types import BoundingBox
from layerkit.models.fake import CenteredBoxModel

RED = (200, 30, 30)


def make_mask(size: tuple[int, int], box: tuple[int, int, int, int]) -> Image.Image:
    """A black mask with a white rectangle at ``box`` (left, top, right, bottom)."""
    mask = Image.new("L", size, 0)
    mask.paste(255, box)
    return mask


def test_crops_the_layer_to_the_object() -> None:
    image = Image.new("RGB", (20, 10), RED)

    layer = cut_out(image, make_mask((20, 10), (4, 2, 12, 8)))

    assert layer.box == BoundingBox(4, 2, 8, 6)
    assert layer.image.size == (8, 6)


def test_the_layer_is_rgba_and_keeps_the_object_colors() -> None:
    image = Image.new("RGB", (10, 10), RED)

    layer = cut_out(image, make_mask((10, 10), (2, 2, 8, 8)))

    assert layer.image.mode == "RGBA"
    assert layer.image.getpixel((0, 0)) == (*RED, 255)


def test_uses_the_mask_as_the_alpha_channel() -> None:
    image = Image.new("RGB", (4, 1), RED)
    mask = Image.new("L", (4, 1))
    mask.putdata([0, 40, 255, 0])

    layer = cut_out(image, mask)

    assert layer.box == BoundingBox(1, 0, 2, 1)
    assert list(layer.image.getchannel("A").tobytes()) == [40, 255]


def test_pixels_left_of_the_object_inside_the_box_are_transparent() -> None:
    image = Image.new("RGB", (6, 6), RED)
    mask = Image.new("L", (6, 6), 0)
    mask.putpixel((1, 1), 255)
    mask.putpixel((4, 4), 255)

    layer = cut_out(image, mask)

    assert layer.box == BoundingBox(1, 1, 4, 4)
    assert layer.image.getpixel((1, 1)) == (*RED, 0)


def test_a_full_mask_keeps_the_whole_image() -> None:
    layer = cut_out(Image.new("RGB", (7, 5), RED), Image.new("L", (7, 5), 255))

    assert layer.box == BoundingBox(0, 0, 7, 5)


def test_converts_other_modes_to_rgb_first() -> None:
    gray = Image.new("L", (6, 6), 128)

    layer = cut_out(gray, make_mask((6, 6), (1, 1, 5, 5)))

    assert layer.image.getpixel((0, 0)) == (128, 128, 128, 255)


def test_does_not_modify_the_inputs() -> None:
    image = Image.new("RGB", (6, 6), RED)
    mask = make_mask((6, 6), (1, 1, 5, 5))

    cut_out(image, mask)

    assert image.mode == "RGB"
    assert mask.getbbox() == (1, 1, 5, 5)


def test_applies_the_name_and_z_order() -> None:
    layer = cut_out(
        Image.new("RGB", (6, 6)), make_mask((6, 6), (1, 1, 5, 5)), name="cat", z=3
    )

    assert (layer.name, layer.z) == ("cat", 3)


def test_the_defaults_are_subject_and_z_one() -> None:
    layer = cut_out(Image.new("RGB", (6, 6)), make_mask((6, 6), (1, 1, 5, 5)))

    assert (layer.name, layer.z) == ("subject", 1)


def test_works_with_the_output_of_a_model() -> None:
    image = Image.new("RGB", (20, 20), RED)
    mask = CenteredBoxModel(fraction=0.5).predict_mask(image)

    layer = cut_out(image, mask)

    assert layer.box == BoundingBox(5, 5, 10, 10)


def test_an_empty_mask_means_there_is_no_object() -> None:
    with pytest.raises(NoObjectFoundError):
        cut_out(Image.new("RGB", (6, 6)), Image.new("L", (6, 6), 0))


def test_rejects_a_mask_that_is_not_grayscale() -> None:
    with pytest.raises(ValueError, match="grayscale"):
        cut_out(Image.new("RGB", (4, 4)), Image.new("RGB", (4, 4)))


def test_rejects_a_mask_of_a_different_size() -> None:
    with pytest.raises(ValueError, match="size"):
        cut_out(Image.new("RGB", (4, 4)), Image.new("L", (5, 4), 255))
