import pytest
from PIL import Image

from layerkit.core.interfaces import ForegroundModel
from layerkit.models.fake import CenteredBoxModel


def test_conforms_to_the_foreground_model_interface() -> None:
    assert isinstance(CenteredBoxModel(), ForegroundModel)


def test_has_a_stable_name() -> None:
    assert CenteredBoxModel().name == "fake-centered-box"


def test_returns_a_grayscale_mask_of_the_same_size() -> None:
    mask = CenteredBoxModel().predict_mask(Image.new("RGB", (20, 10)))

    assert mask.mode == "L"
    assert mask.size == (20, 10)


def test_marks_the_center_and_leaves_the_corners_empty() -> None:
    mask = CenteredBoxModel(fraction=0.5).predict_mask(Image.new("RGB", (20, 20)))

    assert mask.getpixel((10, 10)) == 255
    assert mask.getpixel((0, 0)) == 0
    assert mask.getpixel((19, 19)) == 0


def test_the_marked_area_follows_the_fraction() -> None:
    mask = CenteredBoxModel(fraction=0.5).predict_mask(Image.new("RGB", (20, 20)))

    marked = mask.histogram()[255]

    assert marked == 10 * 10


def test_a_fraction_of_one_marks_the_whole_image() -> None:
    mask = CenteredBoxModel(fraction=1).predict_mask(Image.new("RGB", (6, 4)))

    assert mask.getextrema() == (255, 255)


@pytest.mark.parametrize("fraction", [0, -0.5, 1.5])
def test_rejects_an_invalid_fraction(fraction: float) -> None:
    with pytest.raises(ValueError, match="fraction"):
        CenteredBoxModel(fraction=fraction)
