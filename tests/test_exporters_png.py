from pathlib import Path

import pytest
from PIL import Image, ImageChops

from layerkit.core.errors import OutputExistsError
from layerkit.core.manifest import Manifest
from layerkit.core.types import BoundingBox, Decomposition, Layer
from layerkit.exporters.png import ExportResult, export_png


def make_layer(name: str, z: int, color: tuple[int, int, int, int]) -> Layer:
    return Layer(name, Image.new("RGBA", (4, 3), color), BoundingBox(z, 1, 4, 3), z)


def make_decomposition() -> Decomposition:
    return Decomposition(
        source_name="photo.jpg",
        width=20,
        height=10,
        layers=(
            make_layer("Cat", 2, (200, 10, 10, 255)),
            make_layer("Background", 0, (10, 10, 200, 128)),
        ),
    )


def test_writes_one_png_per_layer_and_the_manifest(tmp_path: Path) -> None:
    result = export_png(make_decomposition(), tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "00_background.png",
        "02_cat.png",
        "manifest.json",
    ]
    assert isinstance(result, ExportResult)


def test_reports_the_written_paths_from_back_to_front(tmp_path: Path) -> None:
    result = export_png(make_decomposition(), tmp_path)

    assert result.output_dir == tmp_path
    assert result.manifest_path == tmp_path / "manifest.json"
    assert result.layer_paths == (
        tmp_path / "00_background.png",
        tmp_path / "02_cat.png",
    )


def test_the_pngs_keep_the_pixels_and_the_transparency(tmp_path: Path) -> None:
    export_png(make_decomposition(), tmp_path)

    with Image.open(tmp_path / "00_background.png") as saved:
        assert saved.mode == "RGBA"
        assert saved.size == (4, 3)
        expected = Image.new("RGBA", (4, 3), (10, 10, 200, 128))
        assert ImageChops.difference(saved, expected).getbbox() is None


def test_the_manifest_describes_the_files_that_were_written(tmp_path: Path) -> None:
    export_png(make_decomposition(), tmp_path)

    manifest = Manifest.from_json((tmp_path / "manifest.json").read_text("utf-8"))

    assert manifest.source_name == "photo.jpg"
    assert [layer.file for layer in manifest.layers] == [
        "00_background.png",
        "02_cat.png",
    ]
    assert all((tmp_path / layer.file).is_file() for layer in manifest.layers)


def test_the_manifest_uses_unix_line_endings(tmp_path: Path) -> None:
    export_png(make_decomposition(), tmp_path)

    assert b"\r" not in (tmp_path / "manifest.json").read_bytes()


def test_creates_missing_folders(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"

    export_png(make_decomposition(), target)

    assert (target / "manifest.json").is_file()


def test_accepts_the_folder_as_text(tmp_path: Path) -> None:
    export_png(make_decomposition(), str(tmp_path / "out"))

    assert (tmp_path / "out" / "manifest.json").is_file()


def test_writes_into_an_existing_empty_folder(tmp_path: Path) -> None:
    export_png(make_decomposition(), tmp_path)

    assert (tmp_path / "manifest.json").is_file()


def test_leaves_unrelated_files_alone(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("keep me")

    export_png(make_decomposition(), tmp_path)

    assert (tmp_path / "notes.txt").read_text() == "keep me"


def test_refuses_to_overwrite_a_layer_file(tmp_path: Path) -> None:
    (tmp_path / "02_cat.png").write_bytes(b"precious")

    with pytest.raises(OutputExistsError) as error:
        export_png(make_decomposition(), tmp_path)

    assert error.value.paths == (tmp_path / "02_cat.png",)
    assert (tmp_path / "02_cat.png").read_bytes() == b"precious"


def test_refuses_to_overwrite_the_manifest(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text("old")

    with pytest.raises(OutputExistsError) as error:
        export_png(make_decomposition(), tmp_path)

    assert error.value.paths == (tmp_path / "manifest.json",)


def test_writes_nothing_when_something_blocks_the_export(tmp_path: Path) -> None:
    (tmp_path / "02_cat.png").write_bytes(b"precious")

    with pytest.raises(OutputExistsError):
        export_png(make_decomposition(), tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == ["02_cat.png"]


def test_lists_every_blocking_file_in_the_message(tmp_path: Path) -> None:
    export_png(make_decomposition(), tmp_path)

    with pytest.raises(OutputExistsError, match="manifest.json") as error:
        export_png(make_decomposition(), tmp_path)

    assert len(error.value.paths) == 3


def test_overwrites_when_asked(tmp_path: Path) -> None:
    (tmp_path / "02_cat.png").write_bytes(b"old")
    (tmp_path / "manifest.json").write_text("old")

    export_png(make_decomposition(), tmp_path, overwrite=True)

    with Image.open(tmp_path / "02_cat.png") as saved:
        assert saved.size == (4, 3)
    assert Manifest.from_json((tmp_path / "manifest.json").read_text("utf-8"))


def test_refuses_a_folder_path_that_is_a_file(tmp_path: Path) -> None:
    blocker = tmp_path / "out"
    blocker.write_text("i am a file")

    with pytest.raises(OutputExistsError) as error:
        export_png(make_decomposition(), blocker, overwrite=True)

    assert error.value.paths == (blocker,)
    assert blocker.read_text() == "i am a file"
