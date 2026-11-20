# layerkit

[![CI](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml/badge.svg)](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**Turn any flat image into editable layers: one transparent PNG per object, plus a manifest to put them back.**

English · [Español](README.es.md)

> **Status: v0.0, project skeleton.** The tooling, CI and package layout are in place.
> The image features are **not implemented yet**. See the [roadmap](#roadmap).

## The idea

A flat photo goes in. A folder of layers comes out:

```text
output/
  00_background.png   <- the scene with the holes filled in
  01_mug.png          <- only the mug, transparent background
  02_plant.png        <- only the plant
  manifest.json       <- where each layer goes, and in what order
```

The manifest is what makes the output useful: every layer remembers its
position and stacking order, so the image can be put back together or edited
piece by piece in any editor.

```json
{
  "source": "mug.jpg",
  "width": 1920,
  "height": 1080,
  "layers": [
    {"name": "background", "file": "00_background.png", "x": 0,   "y": 0,   "w": 1920, "h": 1080, "z": 0},
    {"name": "mug",        "file": "01_mug.png",        "x": 640, "y": 300, "w": 410,  "h": 520,  "z": 1}
  ]
}
```

`x`, `y` is the top-left corner of the layer; a higher `z` is in front.

## Install

```bash
pip install "git+https://github.com/JimmyHerreraIs/layerkit.git"
layerkit --version
```

PyPI packaging is planned for v0.3.

## Planned usage

> This is the target interface. It is **not available yet**.

```bash
layerkit photo.jpg --out output/
```

```python
from layerkit import decompose

layers = decompose("photo.jpg")
```

## Scope

| It does | It does NOT do (and why) |
|---|---|
| Remove the background of an image | Edit the image: no color changes, no added shadows. It is a separator, not an editor |
| Split each object into its own PNG layer | Recognize people or read text: no face recognition, no OCR |
| Store position and order in `manifest.json` | Process video in v1: still images only |
| Export PNGs, ZIP and layered files | Export real vector SVG in v1: converting pixels to vectors is another project |
| Run locally on CPU, sending images nowhere | Be a cloud service or have user accounts |
| Work as a library, a CLI or an API | Ship a desktop GUI |
| Let you swap the model through configuration | Train models: it uses open, pre-trained ones |

## Roadmap

| Version | What lands |
|---|---|
| **v0.0** | Skeleton: package layout, CI, pre-commit, templates, docs *(current)* |
| v0.1 | Background removal as a library and CLI |
| v0.2 | Split into N layers, mask cleanup, `manifest.json` |
| v0.3 | ZIP export, layered-file export, PyPI release |
| v0.4 | Browser demo and benchmark |
| v1.0 | Optional FastAPI server, full documentation |

Ideas outside the current scope are tracked as issues and revisited after v1.0.

## Development

```bash
git clone https://github.com/JimmyHerreraIs/layerkit.git
cd layerkit
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate
pip install -e ".[dev]"
pre-commit install

ruff check . && ruff format --check . && mypy && pytest
```

The code is split in three doors over one core: `layerkit.core` holds the
pipeline and knows nothing about the CLI or any web API.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
first. To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Jimmy Herrera
