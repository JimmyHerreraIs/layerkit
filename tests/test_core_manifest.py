import copy
import json
from typing import Any

import pytest
from PIL import Image

from layerkit.core.errors import InvalidManifestError
from layerkit.core.manifest import (
    MANIFEST_FILE_NAME,
    MANIFEST_VERSION,
    Manifest,
    ManifestLayer,
    build_manifest,
    layer_file_name,
)
from layerkit.core.types import BoundingBox, Decomposition, Layer


def make_layer(name: str = "subject", z: int = 1, x: int = 2, y: int = 3) -> Layer:
    return Layer(name, Image.new("RGBA", (4, 5)), BoundingBox(x, y, 4, 5), z)


def make_decomposition() -> Decomposition:
    return Decomposition(
        source_name="photo.jpg",
        width=20,
        height=10,
        layers=(make_layer("Cat", z=2, x=10, y=1), make_layer("Background", z=0)),
    )


def valid_data() -> dict[str, Any]:
    return build_manifest(make_decomposition()).to_dict()


def test_the_format_version_is_one() -> None:
    assert MANIFEST_VERSION == 1
    assert MANIFEST_FILE_NAME == "manifest.json"


# --- layer_file_name ---------------------------------------------------------


def test_file_names_combine_the_order_and_the_name() -> None:
    assert layer_file_name(make_layer("Subject", z=1)) == "01_subject.png"


def test_file_names_replace_symbols_and_spaces() -> None:
    assert layer_file_name(make_layer("  Red Car!! / 2 ", z=12)) == "12_red-car-2.png"


def test_file_names_fall_back_when_the_name_has_no_letters() -> None:
    assert layer_file_name(make_layer("???", z=3)) == "03_layer.png"


# --- build_manifest ----------------------------------------------------------


def test_describes_the_canvas_and_the_source() -> None:
    manifest = build_manifest(make_decomposition())

    assert (manifest.source_name, manifest.width, manifest.height) == (
        "photo.jpg",
        20,
        10,
    )
    assert manifest.version == MANIFEST_VERSION


def test_layers_are_ordered_from_back_to_front() -> None:
    manifest = build_manifest(make_decomposition())

    assert [layer.z for layer in manifest.layers] == [0, 2]
    assert [layer.file for layer in manifest.layers] == [
        "00_background.png",
        "02_cat.png",
    ]


def test_every_layer_keeps_its_name_and_position() -> None:
    cat = build_manifest(make_decomposition()).layers[1]

    assert cat.name == "Cat"
    assert cat.box == BoundingBox(10, 1, 4, 5)


# --- serialization -----------------------------------------------------------


def test_the_dictionary_uses_flat_layer_entries() -> None:
    data = valid_data()

    assert list(data) == ["version", "source", "width", "height", "layers"]
    assert data["layers"][1] == {
        "name": "Cat",
        "file": "02_cat.png",
        "x": 10,
        "y": 1,
        "width": 4,
        "height": 5,
        "z": 2,
    }


def test_the_json_is_indented_and_ends_with_a_newline() -> None:
    text = build_manifest(make_decomposition()).to_json()

    assert text.endswith("}\n")
    assert '\n  "version": 1,' in text
    assert json.loads(text) == valid_data()


def test_non_ascii_names_are_written_as_they_are() -> None:
    decomposition = Decomposition("a.png", 10, 10, (make_layer("niño"),))

    assert "niño" in build_manifest(decomposition).to_json()


def test_the_manifest_survives_a_round_trip() -> None:
    manifest = build_manifest(make_decomposition())

    assert Manifest.from_json(manifest.to_json()) == manifest
    assert Manifest.from_dict(manifest.to_dict()) == manifest


# --- reading: structure ------------------------------------------------------


def test_rejects_text_that_is_not_json() -> None:
    with pytest.raises(InvalidManifestError, match="not valid JSON"):
        Manifest.from_json("{nope")


@pytest.mark.parametrize("data", [[], "text", 3, None])
def test_rejects_content_that_is_not_an_object(data: object) -> None:
    with pytest.raises(InvalidManifestError, match="JSON object"):
        Manifest.from_dict(data)


def test_rejects_layers_that_are_not_a_list() -> None:
    data = valid_data()
    data["layers"] = "none"

    with pytest.raises(InvalidManifestError, match="'layers' must be a list"):
        Manifest.from_dict(data)


def test_rejects_a_layer_that_is_not_an_object() -> None:
    data = valid_data()
    data["layers"] = [1]

    with pytest.raises(InvalidManifestError, match="each layer"):
        Manifest.from_dict(data)


@pytest.mark.parametrize("key", ["version", "width", "height"])
@pytest.mark.parametrize("bad", ["20", 1.5, True, None])
def test_rejects_top_level_numbers_of_the_wrong_type(key: str, bad: object) -> None:
    data = valid_data()
    data[key] = bad

    with pytest.raises(InvalidManifestError, match="must be an integer"):
        Manifest.from_dict(data)


def test_rejects_a_missing_source() -> None:
    data = valid_data()
    del data["source"]

    with pytest.raises(InvalidManifestError, match="'source' must be a string"):
        Manifest.from_dict(data)


@pytest.mark.parametrize("key", ["x", "y", "width", "height", "z"])
def test_rejects_layer_numbers_of_the_wrong_type(key: str) -> None:
    data = valid_data()
    data["layers"][0][key] = "1"

    with pytest.raises(InvalidManifestError, match=f"'{key}' must be an integer"):
        Manifest.from_dict(data)


@pytest.mark.parametrize("key", ["name", "file"])
def test_rejects_layer_texts_of_the_wrong_type(key: str) -> None:
    data = valid_data()
    data["layers"][0][key] = 5

    with pytest.raises(InvalidManifestError, match=f"'{key}' must be a string"):
        Manifest.from_dict(data)


# --- reading: content --------------------------------------------------------


def test_rejects_an_unsupported_version() -> None:
    data = valid_data()
    data["version"] = 2

    with pytest.raises(InvalidManifestError, match="unsupported manifest version 2"):
        Manifest.from_dict(data)


@pytest.mark.parametrize(
    "bad_file",
    ["../secret.png", "dir/a.png", "dir\\a.png", "/etc/a.png", ".hidden.png", "a.jpg"],
)
def test_rejects_file_names_that_are_paths_or_not_png(bad_file: str) -> None:
    data = valid_data()
    data["layers"][0]["file"] = bad_file

    with pytest.raises(InvalidManifestError, match="plain .png name"):
        Manifest.from_dict(data)


def test_rejects_an_empty_layer_name() -> None:
    data = valid_data()
    data["layers"][0]["name"] = "  "

    with pytest.raises(InvalidManifestError, match="name must not be empty"):
        Manifest.from_dict(data)


def test_rejects_a_negative_z() -> None:
    data = valid_data()
    data["layers"][0]["z"] = -1

    with pytest.raises(InvalidManifestError, match="z must not be negative"):
        Manifest.from_dict(data)


def test_rejects_an_invalid_box() -> None:
    data = valid_data()
    data["layers"][0]["width"] = 0

    with pytest.raises(InvalidManifestError, match="positive"):
        Manifest.from_dict(data)


def test_rejects_a_layer_outside_the_canvas() -> None:
    data = valid_data()
    data["width"] = 5

    with pytest.raises(InvalidManifestError, match="outside"):
        Manifest.from_dict(data)


def test_rejects_a_canvas_that_is_not_positive() -> None:
    data = valid_data()
    data["height"] = 0

    with pytest.raises(InvalidManifestError, match="positive"):
        Manifest.from_dict(data)


def test_rejects_a_manifest_without_layers() -> None:
    data = valid_data()
    data["layers"] = []

    with pytest.raises(InvalidManifestError, match="at least one layer"):
        Manifest.from_dict(data)


def test_rejects_repeated_z_values() -> None:
    data = valid_data()
    data["layers"][1]["z"] = data["layers"][0]["z"]

    with pytest.raises(InvalidManifestError, match="unique z"):
        Manifest.from_dict(data)


def test_rejects_repeated_file_names() -> None:
    data = valid_data()
    data["layers"][1]["file"] = data["layers"][0]["file"]

    with pytest.raises(InvalidManifestError, match="unique file"):
        Manifest.from_dict(data)


def test_reading_does_not_modify_the_data() -> None:
    data = valid_data()
    before = copy.deepcopy(data)

    Manifest.from_dict(data)

    assert data == before


# --- direct construction -----------------------------------------------------


def test_the_entries_validate_themselves_when_built_directly() -> None:
    with pytest.raises(ValueError, match="plain .png name"):
        ManifestLayer("a", "../a.png", BoundingBox(0, 0, 1, 1), 0)
