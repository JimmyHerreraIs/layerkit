"""The manifest: a JSON description of a decomposition.

The manifest records the size of the source image and, for every layer, its
name, its PNG file name, where it sits and its stacking order. File names are
plain names, never paths, so a manifest cannot point outside its own folder.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from layerkit.core.errors import InvalidManifestError
from layerkit.core.types import BoundingBox, Decomposition, Layer

MANIFEST_VERSION = 1
"""Version of the manifest format written by this release."""

MANIFEST_FILE_NAME = "manifest.json"

_NOT_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")
_PNG_SUFFIX = ".png"


def layer_file_name(layer: Layer) -> str:
    """Return the PNG file name used for a layer.

    The name combines the stacking order and a lowercase form of the layer name,
    for example ``"01_subject.png"``. The stacking order is unique within a
    decomposition, so file names never collide.

    Args:
        layer: The layer to name.

    Returns:
        A plain file name ending in ``.png``.
    """
    slug = _NOT_ALPHANUMERIC.sub("-", layer.name.lower()).strip("-") or "layer"
    return f"{layer.z:02d}_{slug}{_PNG_SUFFIX}"


def _is_plain_png_name(file_name: str) -> bool:
    """Tell whether a file name is a bare ``.png`` name, not a path."""
    return (
        file_name.lower().endswith(_PNG_SUFFIX)
        and not file_name.startswith(".")
        and "/" not in file_name
        and "\\" not in file_name
    )


@dataclass(frozen=True, slots=True)
class ManifestLayer:
    """One layer as recorded in the manifest.

    Attributes:
        name: Human-readable layer name.
        file: Plain PNG file name, relative to the manifest folder.
        box: Where the layer sits in the full image.
        z: Stacking order; a higher value is drawn in front.
    """

    name: str
    file: str
    box: BoundingBox
    z: int

    def __post_init__(self) -> None:
        """Validate the entry.

        Raises:
            ValueError: If the name is empty, the file is not a plain ``.png``
                name, or ``z`` is negative.
        """
        if not self.name.strip():
            raise ValueError("layer name must not be empty")
        if not _is_plain_png_name(self.file):
            raise ValueError(f"layer file must be a plain .png name, got {self.file!r}")
        if self.z < 0:
            raise ValueError(f"z must not be negative, got {self.z}")


@dataclass(frozen=True, slots=True)
class Manifest:
    """The description of a decomposition, ready to be saved as JSON.

    Attributes:
        source_name: File name of the original image.
        width: Width of the full image in pixels.
        height: Height of the full image in pixels.
        layers: The layers, ordered from back to front.
        version: Version of the manifest format.
    """

    source_name: str
    width: int
    height: int
    layers: tuple[ManifestLayer, ...]
    version: int = MANIFEST_VERSION

    def __post_init__(self) -> None:
        """Validate the manifest.

        Raises:
            ValueError: If the version is unsupported, the canvas size is not
                positive, there are no layers, a layer falls outside the
                canvas, or two layers share a ``z`` or a file name.
        """
        if self.version != MANIFEST_VERSION:
            raise ValueError(
                f"unsupported manifest version {self.version}; "
                f"this release reads version {MANIFEST_VERSION}"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"width and height must be positive, got {self.width}x{self.height}"
            )
        if not self.layers:
            raise ValueError("a manifest needs at least one layer")
        for layer in self.layers:
            box = layer.box
            if box.x + box.width > self.width or box.y + box.height > self.height:
                raise ValueError(
                    f"layer {layer.name!r} falls outside the "
                    f"{self.width}x{self.height} canvas"
                )
        if len({layer.z for layer in self.layers}) != len(self.layers):
            raise ValueError("layers must have unique z values")
        if len({layer.file for layer in self.layers}) != len(self.layers):
            raise ValueError("layers must have unique file names")

    def to_dict(self) -> dict[str, Any]:
        """Return the manifest as plain JSON-ready data."""
        return {
            "version": self.version,
            "source": self.source_name,
            "width": self.width,
            "height": self.height,
            "layers": [
                {
                    "name": layer.name,
                    "file": layer.file,
                    "x": layer.box.x,
                    "y": layer.box.y,
                    "width": layer.box.width,
                    "height": layer.box.height,
                    "z": layer.z,
                }
                for layer in self.layers
            ],
        }

    def to_json(self) -> str:
        """Return the manifest as indented JSON text ending in a newline."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n"

    @classmethod
    def from_dict(cls, data: object) -> Manifest:
        """Build a manifest from plain data, checking everything.

        Args:
            data: The decoded JSON content.

        Returns:
            The validated manifest.

        Raises:
            InvalidManifestError: If the data is malformed, unsafe or written
                in an unsupported version.
        """
        root = _as_mapping(data, "manifest")
        raw_layers = root.get("layers")
        if not isinstance(raw_layers, list):
            raise InvalidManifestError("'layers' must be a list")
        try:
            layers = tuple(_read_layer(raw) for raw in raw_layers)
            return cls(
                source_name=_read_str(root, "source"),
                width=_read_int(root, "width"),
                height=_read_int(root, "height"),
                layers=layers,
                version=_read_int(root, "version"),
            )
        except ValueError as exc:
            raise InvalidManifestError(str(exc)) from exc

    @classmethod
    def from_json(cls, text: str) -> Manifest:
        """Build a manifest from JSON text.

        Args:
            text: The content of a ``manifest.json`` file.

        Returns:
            The validated manifest.

        Raises:
            InvalidManifestError: If the text is not valid JSON or the content
                is not a valid manifest.
        """
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise InvalidManifestError(f"manifest is not valid JSON: {exc}") from exc
        return cls.from_dict(data)


def build_manifest(decomposition: Decomposition) -> Manifest:
    """Describe a decomposition, with its layers ordered from back to front.

    Args:
        decomposition: The layers and canvas to describe.

    Returns:
        The manifest, with one entry per layer.
    """
    ordered = sorted(decomposition.layers, key=lambda layer: layer.z)
    return Manifest(
        source_name=decomposition.source_name,
        width=decomposition.width,
        height=decomposition.height,
        layers=tuple(
            ManifestLayer(
                name=layer.name,
                file=layer_file_name(layer),
                box=layer.box,
                z=layer.z,
            )
            for layer in ordered
        ),
    )


def _as_mapping(value: object, what: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise InvalidManifestError(f"{what} must be a JSON object")
    return value


def _read_int(data: Mapping[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidManifestError(f"{key!r} must be an integer")
    return value


def _read_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise InvalidManifestError(f"{key!r} must be a string")
    return value


def _read_layer(raw: object) -> ManifestLayer:
    entry = _as_mapping(raw, "each layer")
    return ManifestLayer(
        name=_read_str(entry, "name"),
        file=_read_str(entry, "file"),
        box=BoundingBox(
            x=_read_int(entry, "x"),
            y=_read_int(entry, "y"),
            width=_read_int(entry, "width"),
            height=_read_int(entry, "height"),
        ),
        z=_read_int(entry, "z"),
    )
