# ADR 0001: Default background-removal model

- **Status:** Accepted (upstream licenses and weight downloads verified on 2026-11-24, see "Licenses")
- **Date:** 2026-11-20
- **Milestone:** v0.1

## Context

layerkit v0.1 removes the background of an image on CPU, locally, without
sending images anywhere. The model sits behind a small interface in
`layerkit.models`, so the default can change without touching `layerkit.core`.
We need a default that installs quickly, runs fast on a laptop CPU, and gives
clean cutouts. A second, slower "quality" option is acceptable.

## Candidates

Five models available through [rembg](https://github.com/danielgatis/rembg)
(code license: MIT), run with ONNX Runtime on the CPU provider:

`u2netp`, `silueta`, `u2net`, `isnet-general-use`, `birefnet-general-lite`.

## Method

- Machine: Windows 11, 8 logical cores (Intel Family 6 Model 140), Python 3.12.3,
  rembg 2.0.87, onnxruntime 1.32.0.
- Images: 9 samples from scikit-image's bundled data (see its documentation for
  per-image licenses): 6 with a clear subject (portrait, grayscale scene, cat,
  cup, coins, rocket) and 3 texture images with no subject (brick, grass,
  gravel), which a good pipeline should treat as "no object".
- One process per model, one warm-up call, then one timed call per image.
  Memory is the peak resident set size of the process.
- Quality was judged by eye on a contact sheet. There are no ground-truth masks,
  so no IoU or similar metric is reported.

## Results

| Model | Weights | Load (cached) | Median per image | Peak memory |
|---|---|---|---|---|
| `u2netp` | 4.6 MB | 1.0 s | 0.75 s | 0.7 GB |
| `silueta` | 44.2 MB | 0.7 s | 2.05 s | 0.8 GB |
| `u2net` | 176.0 MB | 1.6 s | 1.79 s | 1.0 GB |
| `isnet-general-use` | 178.6 MB | 1.6 s | 4.60 s | 1.7 GB |
| `birefnet-general-lite` | 224.0 MB | 10.2 s | 22.7 s (max 36.8 s) | 7.0 GB |

Observations:

- **Textures without a subject:** `u2netp`, `silueta` and `u2net` return an
  almost empty mask (coverage at or below 1 %), which is easy to reject.
  `isnet-general-use` and `birefnet-general-lite` keep part of the brick
  pattern (22 % and 14 % coverage), a false positive.
- **Coins (many small objects):** `u2netp`, `isnet-general-use` and
  `birefnet-general-lite` separate the individual coins. `silueta` and `u2net`
  leave a semi-transparent haze over them.
- **Edges (cat fur):** `birefnet-general-lite` gives the cleanest edges, with a
  small artifact at the bottom right. The U²-Net family leaves a soft,
  semi-transparent fringe.
- **Rocket scene:** the U²-Net family keeps only the main subject;
  `isnet-general-use` and `birefnet-general-lite` also keep the surrounding
  towers.
- **Portrait, grayscale scene and cup:** all five are good.

## Decision

- Default model: **`u2netp`**. It is by far the fastest and lightest (4.6 MB,
  under a second per image, under 1 GB of memory), and its quality is
  acceptable on every positive sample.
- "Quality" option (`--model isnet-general-use`): better multi-object behavior
  at about 6 times the time and 2.4 times the memory.
- `birefnet-general-lite` is **not offered in v0.1**: 22 s per image and 7 GB of
  memory on CPU is not usable. Revisit it when GPU support is considered.
- `silueta` and `u2net` add nothing over `u2netp` for this use case.

## Consequences

- The first run downloads the weights (4.6 MB for the default). `rembg` 2.0.87
  fetches them from its own GitHub release (`v0.0.0`) and checks an MD5 sum
  before using them; the check can be turned off with the
  `MODEL_CHECKSUM_DISABLED` environment variable, and layerkit never does. The
  files are cached under `~/.rembg/models/<name>` (or `REMBG_HOME`). MD5 guards
  against a corrupt download, not against a malicious one, so a pinned hash of
  our own is part of the own-adapter work planned before the PyPI release.
- The model adapter depends on `rembg` and `onnxruntime`. Whether it ships in
  the base install or as an optional extra is decided in ADR 0003
  (dependencies).
- Mask validation (reject empty or near-full masks) stays in `layerkit.core`,
  because no model is reliable on images without a subject.
- Unit tests use a fake model; a single marked integration test exercises the
  real default model.

## Limitations of this benchmark

Small sample (6 positive images), no ground truth, one machine, one timed run
per image, small images (at most 640 px). Absolute times will be longer for
large photos. Treat the ranking as indicative, not definitive.

## Licenses

Checked on 2026-11-24 against the upstream repositories:

- rembg (code): MIT, `Copyright (c) 2020 Daniel Gatis`.
- U²-Net (`u2netp`, the default): the repository `LICENSE` is Apache-2.0.
- ISNet / DIS (`isnet-general-use`): the repository `LICENSE.md` is Apache-2.0.
- BiRefNet: MIT, per its model card (not offered in v0.1).

Both Apache-2.0 files are the unmodified license text with no named copyright
holder. layerkit does not bundle or redistribute any weights: the user's machine
downloads them from the rembg project on first use.

Not reviewed: the terms of the datasets the models were trained on. This matters
if layerkit ever redistributes weights or makes claims about commercial use of
the models; for now the README tells users to check them.
