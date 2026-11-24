"""Check that a foreground mask describes a clear object."""

from __future__ import annotations

from PIL import Image

from layerkit.core.errors import NoObjectFoundError

MIN_COVERAGE = 0.005
"""Smallest share of the image an object may cover (0.5 %)."""

MAX_COVERAGE = 0.95
"""Largest share of the image an object may cover (95 %)."""

_ANALYSIS_SIZE = 128
_FULL_OPACITY = 255


def mask_coverage(mask: Image.Image) -> float:
    """Measure how much of the image the mask marks as object.

    The mask is shrunk to at most 128 pixels on its longest side with an
    averaging filter, which keeps the mean value, so the measure is cheap on
    large images and soft edges count in proportion to their opacity.

    Args:
        mask: An 8-bit grayscale mask (mode ``"L"``).

    Returns:
        A number from 0 (nothing marked) to 1 (everything marked).

    Raises:
        ValueError: If the mask is not mode ``"L"``.
    """
    if mask.mode != "L":
        raise ValueError(f"mask must be grayscale (mode 'L'), got {mask.mode!r}")
    small = mask.copy()
    small.thumbnail((_ANALYSIS_SIZE, _ANALYSIS_SIZE), Image.Resampling.BOX)
    histogram = small.histogram()
    total = sum(histogram)
    weighted = sum(value * count for value, count in enumerate(histogram))
    return weighted / (total * _FULL_OPACITY)


def validate_mask(
    mask: Image.Image,
    *,
    min_coverage: float = MIN_COVERAGE,
    max_coverage: float = MAX_COVERAGE,
) -> float:
    """Reject masks that do not describe a clear object.

    A mask that marks almost nothing means the model saw no object. One that
    marks almost everything means it could not tell the object from the
    background.

    Args:
        mask: An 8-bit grayscale mask (mode ``"L"``).
        min_coverage: Smallest accepted coverage, from 0 to 1.
        max_coverage: Largest accepted coverage, from 0 to 1.

    Returns:
        The measured coverage, so callers can report it.

    Raises:
        ValueError: If the mask is not mode ``"L"`` or the limits are not
            ``0 <= min_coverage < max_coverage <= 1``.
        NoObjectFoundError: If the coverage is outside the accepted range.
    """
    if not 0 <= min_coverage < max_coverage <= 1:
        raise ValueError(
            "coverage limits must satisfy 0 <= min < max <= 1, "
            f"got min={min_coverage} and max={max_coverage}"
        )
    coverage = mask_coverage(mask)
    if coverage < min_coverage or coverage > max_coverage:
        raise NoObjectFoundError(coverage)
    return coverage
