import io
from pathlib import Path

import pytest
from PIL import Image, ImageChops

import layerkit
from layerkit.core.errors import (
    ImageTooLargeError,
    NoObjectFoundError,
    UnsupportedImageError,
)
from layerkit.core.types import BoundingBox
from layerkit.exporters.png import export_png
from layerkit.models.fake import CenteredBoxModel
from layerkit.pipeline import decompose


class FixedMaskModel:
    """A model that always returns the same mask."""

    name = "fixed"

    def __init__(self, mask: Image.Image) -> None:
        self._mask = mask

    def predict_mask(self, image: Image.Image) -> Image.Image:
        return self._mask


@pytest.fixture
def photo(tmp_path: Path) -> Path:
    path = tmp_path / "photo.png"
    image = Image.new("RGB", (40, 40), (20, 80, 160))
    image.paste((200, 30, 30), (10, 10, 30, 30))
    image.save(path)
    return path


def test_returns_a_background_and_a_subject(photo: Path) -> None:
    result = decompose(photo, model=CenteredBoxModel(fraction=0.5))

    assert [(layer.name, layer.z) for layer in result.layers] == [
        ("background", 0),
        ("subject", 1),
    ]


def test_the_canvas_and_the_source_name_come_from_the_file(photo: Path) -> None:
    result = decompose(photo, model=CenteredBoxModel())

    assert (result.source_name, result.width, result.height) == ("photo.png", 40, 40)


def test_the_background_is_the_whole_original_image(photo: Path) -> None:
    background = decompose(photo, model=CenteredBoxModel()).layers[0]

    assert background.box == BoundingBox(0, 0, 40, 40)
    assert background.image.mode == "RGBA"
    with Image.open(photo) as original:
        difference = ImageChops.difference(
            background.image.convert("RGB"), original.convert("RGB")
        )
    assert difference.getbbox() is None


def test_the_subject_is_cut_out_where_the_model_found_it(photo: Path) -> None:
    subject = decompose(photo, model=CenteredBoxModel(fraction=0.5)).layers[1]

    assert subject.box == BoundingBox(10, 10, 20, 20)
    assert subject.image.getpixel((0, 0)) == (200, 30, 30, 255)


def test_accepts_a_path_given_as_text(photo: Path) -> None:
    assert decompose(str(photo), model=CenteredBoxModel()).source_name == "photo.png"


def test_accepts_an_open_file(photo: Path) -> None:
    with photo.open("rb") as handle:
        result = decompose(handle, model=CenteredBoxModel())

    assert result.source_name == "photo.png"


def test_an_anonymous_stream_is_named_image(photo: Path) -> None:
    stream = io.BytesIO(photo.read_bytes())

    assert decompose(stream, model=CenteredBoxModel()).source_name == "image"


def test_uses_the_default_model_when_none_is_given(
    photo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_load_model() -> CenteredBoxModel:
        calls.append("loaded")
        return CenteredBoxModel()

    monkeypatch.setattr("layerkit.pipeline.load_model", fake_load_model)

    decompose(photo)

    assert calls == ["loaded"]


def test_does_not_load_the_default_model_when_one_is_given(
    photo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> CenteredBoxModel:
        raise AssertionError("the default model must not be loaded")

    monkeypatch.setattr("layerkit.pipeline.load_model", fail)

    decompose(photo, model=CenteredBoxModel())


def test_the_size_limit_is_applied_before_the_model_runs(photo: Path) -> None:
    class ExplodingModel:
        name = "exploding"

        def predict_mask(self, image: Image.Image) -> Image.Image:
            raise AssertionError("the model must not run")

    with pytest.raises(ImageTooLargeError):
        decompose(photo, model=ExplodingModel(), max_pixels=100)


def test_rejects_a_file_that_is_not_an_image(tmp_path: Path) -> None:
    path = tmp_path / "notes.png"
    path.write_text("not an image")

    with pytest.raises(UnsupportedImageError):
        decompose(path, model=CenteredBoxModel())


def test_a_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        decompose(tmp_path / "missing.png", model=CenteredBoxModel())


def test_rejects_an_empty_mask(photo: Path) -> None:
    model = FixedMaskModel(Image.new("L", (40, 40), 0))

    with pytest.raises(NoObjectFoundError):
        decompose(photo, model=model)


def test_rejects_a_mask_that_covers_everything(photo: Path) -> None:
    with pytest.raises(NoObjectFoundError):
        decompose(photo, model=CenteredBoxModel(fraction=1))


def test_a_mask_of_the_wrong_size_is_an_error(photo: Path) -> None:
    mask = Image.new("L", (20, 20), 0)
    mask.paste(255, (5, 5, 15, 15))

    with pytest.raises(ValueError, match="size"):
        decompose(photo, model=FixedMaskModel(mask))


def test_the_result_can_be_exported(photo: Path, tmp_path: Path) -> None:
    result = decompose(photo, model=CenteredBoxModel())

    exported = export_png(result, tmp_path / "out")

    assert [path.name for path in exported.layer_paths] == [
        "00_background.png",
        "01_subject.png",
    ]


def test_decompose_is_part_of_the_public_api() -> None:
    assert layerkit.decompose is decompose
    assert "decompose" in layerkit.__all__
