# layerkit

[![CI](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml/badge.svg)](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

**Turn any flat image into editable layers: one transparent PNG per object, plus a manifest to put them back.**

English · [Español](README.es.md)

> **Status: v0.1.** Background removal works as a command and as a Python
> library: a photo becomes a background layer and a cut-out subject. Splitting
> into several objects arrives in v0.2. See the [roadmap](#roadmap).

## What it does

A flat photo goes in. A folder of layers comes out:

```text
photo-layers/
  00_background.png   <- the original image, whole
  01_subject.png      <- only the main subject, transparent background
  manifest.json       <- where each layer goes, and in what order
```

The manifest is what makes the output useful: every layer remembers its
position and stacking order, so the image can be put back together or edited
piece by piece in any editor.

Everything runs **locally on the CPU**. Your images are never sent anywhere.

## Install

The default model runs through [rembg](https://github.com/danielgatis/rembg),
which is an optional extra because it is a heavy install (about 480 MB with its
dependencies):

```bash
pip install "layerkit[rembg] @ git+https://github.com/JimmyHerreraIs/layerkit.git"
layerkit --version
```

The first run downloads the model weights once (4.6 MB for the default model)
and caches them under `~/.rembg/models/`. A PyPI release is planned for v0.3.

Without the extra, `pip install "git+https://github.com/JimmyHerreraIs/layerkit.git"`
installs only the light core (Pillow). You can then plug in your own model, see
[Use your own model](#use-your-own-model).

## Command line

```bash
layerkit photo.jpg                    # writes photo-layers/
layerkit photo.jpg -o result          # choose the folder
layerkit photo.jpg --model isnet-general-use --overwrite
```

```text
Saved 2 layers to photo-layers
  00_background.png
  01_subject.png
  manifest.json
```

| Option | Meaning |
|---|---|
| `-o`, `--output DIR` | Output folder (default: `<image name>-layers`) |
| `--model NAME` | `u2netp` (default, fast) or `isnet-general-use` (slower, better with several objects) |
| `--max-pixels N` | Largest image to accept (default: 25 million pixels) |
| `--overwrite` | Replace layer files that already exist (otherwise it refuses and writes nothing) |
| `--version` | Print the version |

Accepted inputs are JPEG, PNG and WebP. Errors are printed on one line starting
with `error:` and the exit code is `1`; invalid options exit with `2`.

## Python

```python
from layerkit import decompose
from layerkit.exporters.png import export_png

result = decompose("photo.jpg")          # background + subject
for layer in result.layers:
    print(layer.name, layer.box, layer.z)

export_png(result, "photo-layers")       # PNG files + manifest.json
```

`decompose` returns a `Decomposition` with immutable `Layer` objects (RGBA
Pillow image, bounding box and stacking order). Every error layerkit raises on
purpose derives from `layerkit.LayerkitError`.

### Use your own model

Any object with a `name` and a `predict_mask(image)` method that returns an
8-bit grayscale mask (`255` is foreground) of the same size works, so the
heavy `rembg` extra is optional:

```python
from PIL import Image
from layerkit import decompose

class MyModel:
    name = "my-model"

    def predict_mask(self, image: Image.Image) -> Image.Image:
        ...  # return a mode "L" mask with the same size as `image`

result = decompose("photo.jpg", model=MyModel())
```

## The manifest

```json
{
  "version": 1,
  "source": "photo.jpg",
  "width": 1920,
  "height": 1080,
  "layers": [
    {"name": "background", "file": "00_background.png", "x": 0,   "y": 0,   "width": 1920, "height": 1080, "z": 0},
    {"name": "subject",    "file": "01_subject.png",    "x": 640, "y": 300, "width": 410,  "height": 520,  "z": 1}
  ]
}
```

The file is indented; each layer is shown on one line here for readability.
`x`, `y` is the top-left corner of the layer in the full image; a higher `z` is
in front. Layers are listed from back to front. File names are plain names,
never paths, and layerkit rejects any manifest that tries to point elsewhere.
`version` lets the format evolve without breaking readers.

## Models

Measured on an 8-thread laptop CPU, see
[ADR 0001](docs/adr/0001-background-removal-model.md) for the method:

| Model | Weights | Time per image | Peak memory | Use it for |
|---|---|---|---|---|
| `u2netp` (default) | 4.6 MB | 0.75 s | 0.7 GB | a quick, light cut-out |
| `isnet-general-use` | 179 MB | 4.6 s | 1.7 GB | several objects, cleaner results |

Both model families are Apache-2.0 licensed upstream and layerkit does not
redistribute them: your machine downloads them from the rembg project. The
terms of the datasets they were trained on were not reviewed; check them before
any commercial use.

## Limits of v0.1

- **One subject layer.** Everything the model considers the main subject ends up
  in one layer. Splitting into several objects arrives in v0.2.
- **The background is the original image**, untouched. Filling the hole the
  subject leaves behind (inpainting) also arrives in v0.2.
- **No clear object, no output.** If the mask covers less than 0.5 % or more than
  95 % of the image, layerkit stops with `No clear object was found` instead of
  writing a bad cut-out.
- Images above 25 million pixels are rejected before any model runs.
- CPU only; no GPU support yet.

## Scope

| It does | It does NOT do (and why) |
|---|---|
| Remove the background of an image | Edit the image: no color changes, no added shadows. It is a separator, not an editor |
| Split each object into its own PNG layer | Recognize people or read text: no face recognition, no OCR |
| Store position and order in `manifest.json` | Process video in v1: still images only |
| Export PNGs, ZIP and layered files | Export real vector SVG in v1: converting pixels to vectors is another project |
| Run locally on CPU, sending images nowhere | Be a cloud service or have user accounts |
| Work as a library, a CLI or an API | Ship a desktop GUI |
| Let you swap the model | Train models: it uses open, pre-trained ones |

The rows above describe the v1 target; see the roadmap for what exists today.

## Roadmap

| Version | What lands |
|---|---|
| v0.0 | Skeleton: package layout, CI, pre-commit, templates, docs |
| **v0.1** | Background removal as a library and CLI *(current)* |
| v0.2 | Split into N layers, background inpainting, mask cleanup |
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

The tests use a fake model, so they need no downloads. One marked test runs the
real default model: `pip install -e ".[rembg]"` and `pytest -m integration`.

The code is split in three doors over one core: `layerkit.core` holds the
pipeline and knows nothing about the CLI or any web API. Design decisions are
recorded in [`docs/adr/`](docs/adr/).

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
first. To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Jimmy Herrera
