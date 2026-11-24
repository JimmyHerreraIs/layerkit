import pytest
from PIL import Image

from layerkit.core.errors import NoObjectFoundError
from layerkit.core.validation import (
    MAX_COVERAGE,
    MIN_COVERAGE,
    mask_coverage,
    validate_mask,
)
from layerkit.models.fake import CenteredBoxModel


def make_mask(size: tuple[int, int], box: tuple[int, int, int, int]) -> Image.Image:
    """A black mask with a white rectangle at ``box`` (left, top, right, bottom)."""
    mask = Image.new("L", size, 0)
    mask.paste(255, box)
    return mask


def test_the_limits_are_half_a_percent_and_ninety_five_percent() -> None:
    assert (MIN_COVERAGE, MAX_COVERAGE) == (0.005, 0.95)


def test_an_empty_mask_has_zero_coverage() -> None:
    assert mask_coverage(Image.new("L", (40, 40), 0)) == 0


def test_a_full_mask_has_full_coverage() -> None:
    assert mask_coverage(Image.new("L", (40, 40), 255)) == 1


def test_measures_the_share_of_the_image() -> None:
    mask = make_mask((40, 40), (0, 0, 20, 40))

    assert mask_coverage(mask) == pytest.approx(0.5)


def test_soft_edges_count_in_proportion_to_their_opacity() -> None:
    assert mask_coverage(Image.new("L", (40, 40), 51)) == pytest.approx(0.2)


def test_large_masks_are_measured_on_a_reduced_copy() -> None:
    mask = make_mask((2000, 1000), (0, 0, 1000, 1000))

    assert mask_coverage(mask) == pytest.approx(0.5, abs=0.01)


def test_a_small_object_on_a_large_mask_is_not_lost() -> None:
    mask = make_mask((2000, 2000), (100, 100, 300, 300))

    assert mask_coverage(mask) == pytest.approx(0.01, abs=0.002)


def test_the_measure_does_not_modify_the_mask() -> None:
    mask = make_mask((400, 400), (10, 10, 200, 200))

    mask_coverage(mask)

    assert mask.size == (400, 400)


def test_accepts_a_clear_object_and_returns_its_coverage() -> None:
    mask = CenteredBoxModel(fraction=0.5).predict_mask(Image.new("RGB", (40, 40)))

    assert validate_mask(mask) == pytest.approx(0.25)


def test_rejects_an_empty_mask() -> None:
    with pytest.raises(NoObjectFoundError) as error:
        validate_mask(Image.new("L", (40, 40), 0))

    assert error.value.coverage == 0


def test_rejects_an_object_that_is_too_small() -> None:
    mask = make_mask((100, 100), (0, 0, 2, 2))  # 0.04 % of the image

    with pytest.raises(NoObjectFoundError):
        validate_mask(mask)


def test_rejects_a_mask_that_covers_almost_everything() -> None:
    with pytest.raises(NoObjectFoundError) as error:
        validate_mask(Image.new("L", (40, 40), 255))

    assert error.value.coverage == 1


def test_the_limits_can_be_changed() -> None:
    mask = make_mask((100, 100), (0, 0, 2, 2))

    assert validate_mask(mask, min_coverage=0.0001) == pytest.approx(0.0004)


@pytest.mark.parametrize(
    ("low", "high"), [(-0.1, 0.9), (0.5, 0.5), (0.6, 0.4), (0.1, 1.5)]
)
def test_rejects_invalid_limits(low: float, high: float) -> None:
    with pytest.raises(ValueError, match="coverage limits"):
        validate_mask(Image.new("L", (4, 4), 255), min_coverage=low, max_coverage=high)


def test_rejects_a_mask_that_is_not_grayscale() -> None:
    with pytest.raises(ValueError, match="grayscale"):
        mask_coverage(Image.new("RGB", (4, 4)))
