# ADR 0003: Dependencies and minimum Python version

- **Status:** Accepted
- **Date:** 2026-11-22
- **Milestone:** v0.1

## Context

ADR 0001 proposed `u2netp`, run through [rembg](https://github.com/danielgatis/rembg),
as the default model. Before building the adapter we measured what installing
`rembg` actually brings, and compared it with running the same kind of model
directly on ONNX Runtime.

| | `rembg[cpu]` | `onnxruntime` + `numpy` + `Pillow` |
|---|---|---|
| Installed size | 484 MB | 143 MB |
| Notable contributors | `llvmlite` 122 MB, `scipy` 115 MB, `onnxruntime` 55 MB, `numba` 27 MB, `scikit-image` 24 MB, `networkx` 16 MB | `onnxruntime` 55 MB, `numpy` 54 MB, `Pillow` 16 MB |
| Install time (measured) | not measured | 24 s |
| Python | `>=3.11` | any |
| Pinned versions | `numpy>=2.3`, `pillow>=12.3` | none |

Most of the weight of `rembg` comes from `numba` and `llvmlite`, pulled in by
its alpha-matting dependency, which layerkit does not use.

## Decision

1. **Base install:** `Pillow` only for now. `numpy` and an image-processing
   library are added when a step needs them (mask validation, issue F).
2. **v0.1 default model:** run `u2netp` through `rembg`, as an **optional extra**:
   `pip install "layerkit[rembg]"`. `rembg` is imported lazily, so importing
   `layerkit` never requires it, and a clear error explains how to install it.
3. **Minimum Python:** 3.11. Python 3.10 reaches end of life in October 2026,
   and `rembg` already requires 3.11.
4. **Planned, before the PyPI release (v0.3):** replace the `rembg` adapter with
   a thin adapter that runs the ONNX model directly. The interface in
   `layerkit.core.interfaces` exists so this change does not touch the pipeline.
   The target is a base install of roughly the size of the right-hand column
   above.

## Alternatives considered

- **`rembg` in the base install:** simplest, but every user pays for ~480 MB and
  inherits its version pins, which can conflict with other projects.
- **Own ONNX adapter right now:** lighter, but more code to write and verify
  before the first release. Deferred, not rejected.

## Consequences

- Installing the extra is heavy until step 4 is done.
- The weights are downloaded by `rembg` on first use, from the `rembg` project's
  releases. The own adapter must verify them against a pinned hash.
- CI does not install `rembg`: unit tests use a fake model
  (`layerkit.models.fake.CenteredBoxModel`) and a simulated `rembg` module. One
  test marked `integration` exercises the real model and is run on demand with
  `pytest -m integration`.
- The README, the badge and the package metadata state Python 3.11+.
