"""Write a decomposition as transparent PNG files plus a manifest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from layerkit.core.errors import OutputExistsError
from layerkit.core.manifest import MANIFEST_FILE_NAME, build_manifest
from layerkit.core.types import Decomposition


@dataclass(frozen=True, slots=True)
class ExportResult:
    """Where an export put its files.

    Attributes:
        output_dir: The folder that received the files.
        manifest_path: The ``manifest.json`` file.
        layer_paths: One PNG file per layer, ordered from back to front.
    """

    output_dir: Path
    manifest_path: Path
    layer_paths: tuple[Path, ...]


def export_png(
    decomposition: Decomposition,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> ExportResult:
    """Save every layer as a PNG file, with a ``manifest.json`` beside them.

    The folder is created if it does not exist. Existing files that layerkit
    would write are never replaced unless ``overwrite`` is true, and nothing is
    written at all when one of them blocks the export. Other files already in
    the folder are left alone.

    Args:
        decomposition: The layers to save.
        output_dir: Folder that receives the files.
        overwrite: Replace layerkit's own files if they already exist.

    Returns:
        The paths that were written.

    Raises:
        OutputExistsError: If ``output_dir`` is a file, or a file to write
            already exists and ``overwrite`` is false.
    """
    folder = Path(output_dir)
    manifest = build_manifest(decomposition)

    targets = [folder / entry.file for entry in manifest.layers]
    manifest_path = folder / MANIFEST_FILE_NAME

    if folder.exists() and not folder.is_dir():
        raise OutputExistsError([folder])
    if not overwrite:
        blocking = [path for path in (*targets, manifest_path) if path.exists()]
        if blocking:
            raise OutputExistsError(blocking)

    folder.mkdir(parents=True, exist_ok=True)
    layers = sorted(decomposition.layers, key=lambda layer: layer.z)
    for layer, path in zip(layers, targets, strict=True):
        layer.image.save(path, format="PNG")
    manifest_path.write_text(manifest.to_json(), encoding="utf-8", newline="\n")

    return ExportResult(
        output_dir=folder,
        manifest_path=manifest_path,
        layer_paths=tuple(targets),
    )
