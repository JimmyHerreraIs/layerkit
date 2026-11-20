import re

import pytest

import layerkit
from layerkit.cli import main


def test_version_follows_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", layerkit.__version__)


def test_cli_version_prints_installed_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--version"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == f"layerkit {layerkit.__version__}"


def test_cli_without_arguments_shows_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([])

    assert exit_code == 0
    assert "usage: layerkit" in capsys.readouterr().out
