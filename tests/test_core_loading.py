import io
from pathlib import Path

import pytest
from PIL import Image

from layerkit.core.errors import ImageTooLargeError, UnsupportedImageError
from layerkit.core.loading import DEFAULT_MAX_PIXELS, load_image

EXIF_ORIENTATION = 0x0112
ROTATE_90_CLOCKWISE = 6  # the camera was held sideways


@pytest.mark.parametrize("extension", ["jpg", "png", "webp"])
def test_loads_every_supported_format_as_rgb(tmp_path: Path, extension: str) -> None:
    path = tmp_path / f"photo.{extension}"
    Image.new("RGB", (8, 6), (200, 30, 30)).save(path)

    image = load_image(path)

    assert image.mode == "RGB"
    assert image.size == (8, 6)


def test_accepts_a_path_given_as_a_string(tmp_path: Path) -> None:
    path = tmp_path / "photo.png"
    Image.new("RGB", (4, 4)).save(path)

    assert load_image(str(path)).size == (4, 4)


def test_accepts_a_binary_file_object() -> None:
    buffer = io.BytesIO()
    Image.new("RGB", (5, 3)).save(buffer, format="PNG")
    buffer.seek(0)

    assert load_image(buffer).size == (5, 3)


def test_applies_the_exif_orientation(tmp_path: Path) -> None:
    path = tmp_path / "sideways.jpg"
    original = Image.new("RGB", (8, 4))
    exif = original.getexif()
    exif[EXIF_ORIENTATION] = ROTATE_90_CLOCKWISE
    original.save(path, exif=exif)

    assert load_image(path).size == (4, 8)


@pytest.mark.parametrize("mode", ["L", "P", "CMYK"])
def test_converts_other_modes_to_rgb(tmp_path: Path, mode: str) -> None:
    path = tmp_path / "other.jpg" if mode != "P" else tmp_path / "other.png"
    Image.new(mode, (4, 4)).save(path)

    assert load_image(path).mode == "RGB"


def test_flattens_transparency_over_white(tmp_path: Path) -> None:
    path = tmp_path / "transparent.png"
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(path)

    assert load_image(path).getpixel((0, 0)) == (255, 255, 255)


def test_keeps_opaque_pixels_when_flattening(tmp_path: Path) -> None:
    path = tmp_path / "opaque.png"
    Image.new("RGBA", (4, 4), (10, 20, 30, 255)).save(path)

    assert load_image(path).getpixel((0, 0)) == (10, 20, 30)


def test_rejects_an_image_above_the_pixel_limit(tmp_path: Path) -> None:
    path = tmp_path / "big.png"
    Image.new("RGB", (4, 4)).save(path)

    with pytest.raises(ImageTooLargeError) as error:
        load_image(path, max_pixels=10)

    assert error.value.pixels == 16
    assert error.value.max_pixels == 10


def test_accepts_an_image_exactly_at_the_pixel_limit(tmp_path: Path) -> None:
    path = tmp_path / "exact.png"
    Image.new("RGB", (4, 4)).save(path)

    assert load_image(path, max_pixels=16).size == (4, 4)


def test_the_default_limit_is_25_megapixels() -> None:
    assert DEFAULT_MAX_PIXELS == 25_000_000


def test_rejects_a_file_that_is_not_an_image(tmp_path: Path) -> None:
    path = tmp_path / "notes.png"
    path.write_text("this is not an image")

    with pytest.raises(UnsupportedImageError, match="not a readable image"):
        load_image(path)


def test_rejects_an_unsupported_format(tmp_path: Path) -> None:
    path = tmp_path / "picture.bmp"
    Image.new("RGB", (4, 4)).save(path)

    with pytest.raises(UnsupportedImageError, match="BMP"):
        load_image(path)


def test_rejects_a_truncated_file(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    Image.effect_noise((64, 64), 80).convert("RGB").save(buffer, format="JPEG")
    path = tmp_path / "truncated.jpg"
    path.write_bytes(buffer.getvalue()[: len(buffer.getvalue()) // 2])

    with pytest.raises(UnsupportedImageError, match="truncated or corrupt"):
        load_image(path)


def test_rejects_a_decompression_bomb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "bomb.png"
    Image.new("RGB", (4, 4)).save(path)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 4)

    with pytest.raises(UnsupportedImageError, match="decompression-bomb"):
        load_image(path)


def test_a_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_image(tmp_path / "missing.jpg")
