import pytest

from layerkit.core.errors import (
    ImageTooLargeError,
    LayerkitError,
    NoObjectFoundError,
    UnsupportedImageError,
)


@pytest.mark.parametrize(
    "error",
    [
        UnsupportedImageError("not an image"),
        ImageTooLargeError(pixels=48_000_000, max_pixels=25_000_000),
        NoObjectFoundError(coverage=0.0),
    ],
)
def test_every_error_derives_from_the_base_class(error: Exception) -> None:
    assert isinstance(error, LayerkitError)


def test_image_too_large_reports_both_sizes_in_megapixels() -> None:
    error = ImageTooLargeError(pixels=48_000_000, max_pixels=25_000_000)

    assert error.pixels == 48_000_000
    assert error.max_pixels == 25_000_000
    assert str(error) == "Image has 48.0 MP; the maximum allowed is 25.0 MP."


def test_no_object_found_reports_the_coverage_as_a_percentage() -> None:
    error = NoObjectFoundError(coverage=0.012)

    assert error.coverage == 0.012
    assert "1.2%" in str(error)


def test_base_error_catches_the_whole_family() -> None:
    with pytest.raises(LayerkitError):
        raise UnsupportedImageError("bad file")
