# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `layerkit photo.jpg` command: splits an image into a background layer and a cut-out subject, written as transparent PNG files plus a `manifest.json`. Options: `--output`, `--model`, `--max-pixels`, `--overwrite`.
- `decompose()` in the Python API, and `layerkit.exporters.png.export_png()` to write the result.
- Versioned `manifest.json` format with strict validation on read (plain file names only).
- Image loading with size limits, EXIF orientation and transparency flattening.
- Foreground-mask validation that rejects masks with no clear object.
- Model interface (`ForegroundModel`) with a `rembg` adapter for `u2netp` (default) and `isnet-general-use`; `rembg` is the optional extra `layerkit[rembg]`.
- CI jobs for lint, tests on Python 3.11 to 3.13, package build and pull request title format, with a 90% coverage threshold.
- Architecture decision records for the default model and the dependencies.

## [0.0.0] - 2026-11-20

First release: the project skeleton. The image features are not implemented yet.

### Added

- Python package skeleton with a `src/` layout, a `layerkit --version` command and smoke tests.
- Tooling: `ruff`, `mypy --strict`, `pytest` with coverage, and `pre-commit` hooks.
- GitHub Actions workflow that runs the quality checks on every pull request.
- Pull request template, issue forms and Dependabot configuration.
- Documentation: README (English and Spanish), contributing guide and security policy.
- MIT license.

[Unreleased]: https://github.com/JimmyHerreraIs/layerkit/compare/v0.0.0...HEAD
[0.0.0]: https://github.com/JimmyHerreraIs/layerkit/releases/tag/v0.0.0
