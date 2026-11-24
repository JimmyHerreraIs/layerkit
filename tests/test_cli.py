import sys
from pathlib import Path

import pytest
from PIL import Image

from layerkit.cli import build_parser, main
from layerkit.core.interfaces import ForegroundModel
from layerkit.models.fake import CenteredBoxModel


@pytest.fixture
def photo(tmp_path: Path) -> Path:
    path = tmp_path / "photo.png"
    image = Image.new("RGB", (40, 40), (20, 80, 160))
    image.paste((200, 30, 30), (10, 10, 30, 30))
    image.save(path)
    return path


@pytest.fixture(autouse=True)
def fake_model(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace the real model by a fake one and record the requested names."""
    requested: list[str] = []

    def load(name: str) -> ForegroundModel:
        requested.append(name)
        return CenteredBoxModel(fraction=0.5)

    monkeypatch.setattr("layerkit.cli.load_model", load)
    return requested


def names(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.iterdir())


# --- success -----------------------------------------------------------------


def test_writes_the_layers_and_the_manifest(
    photo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"

    exit_code = main([str(photo), "-o", str(out)])

    assert exit_code == 0
    assert names(out) == ["00_background.png", "01_subject.png", "manifest.json"]
    assert capsys.readouterr().out.splitlines() == [
        f"Saved 2 layers to {out}",
        "  00_background.png",
        "  01_subject.png",
        "  manifest.json",
    ]


def test_the_default_folder_is_named_after_the_image(
    photo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main([str(photo)]) == 0

    assert (tmp_path / "photo-layers" / "manifest.json").is_file()


def test_uses_the_default_model_unless_told_otherwise(
    photo: Path, tmp_path: Path, fake_model: list[str]
) -> None:
    main([str(photo), "-o", str(tmp_path / "out")])

    assert fake_model == ["u2netp"]


def test_the_model_can_be_chosen(
    photo: Path, tmp_path: Path, fake_model: list[str]
) -> None:
    main([str(photo), "-o", str(tmp_path / "out"), "--model", "isnet-general-use"])

    assert fake_model == ["isnet-general-use"]


# --- overwriting -------------------------------------------------------------


def test_refuses_to_overwrite_and_suggests_the_flag(
    photo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"
    assert main([str(photo), "-o", str(out)]) == 0
    capsys.readouterr()

    exit_code = main([str(photo), "-o", str(out)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.startswith("error: Refusing to overwrite")
    assert "--overwrite" in captured.err


def test_overwrites_when_asked(photo: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    main([str(photo), "-o", str(out)])

    assert main([str(photo), "-o", str(out), "--overwrite"]) == 0


# --- errors ------------------------------------------------------------------


def test_reports_a_missing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.png"

    exit_code = main([str(missing), "-o", str(tmp_path / "out")])

    assert exit_code == 1
    assert capsys.readouterr().err == f"error: file not found: {missing}\n"


def test_reports_a_file_that_is_not_an_image(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "notes.png"
    path.write_text("not an image")

    exit_code = main([str(path), "-o", str(tmp_path / "out")])

    assert exit_code == 1
    assert "error: The input is not a readable image." in capsys.readouterr().err


def test_reports_an_image_that_is_too_large(
    photo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(photo), "-o", str(tmp_path / "out"), "--max-pixels", "100"])

    assert exit_code == 1
    assert "maximum allowed" in capsys.readouterr().err


def test_reports_when_no_object_is_found(
    photo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "layerkit.cli.load_model", lambda name: CenteredBoxModel(fraction=1)
    )

    exit_code = main([str(photo), "-o", str(tmp_path / "out")])

    assert exit_code == 1
    assert "No clear object was found" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_explains_how_to_install_the_model_package(
    photo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from layerkit.models.rembg_model import RembgModel

    monkeypatch.setattr("layerkit.cli.load_model", lambda name: RembgModel(name))
    monkeypatch.setitem(sys.modules, "rembg", None)

    exit_code = main([str(photo), "-o", str(tmp_path / "out")])

    assert exit_code == 1
    assert 'pip install "layerkit[rembg]"' in capsys.readouterr().err


def test_reports_an_output_path_that_cannot_be_used(
    photo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = tmp_path / "out"
    blocker.write_text("i am a file")

    exit_code = main([str(photo), "-o", str(blocker)])

    assert exit_code == 1
    assert capsys.readouterr().err.startswith("error: Refusing to overwrite")


# --- arguments ---------------------------------------------------------------


def test_rejects_an_unknown_model(
    photo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stop:
        main([str(photo), "--model", "nope"])

    assert stop.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


@pytest.mark.parametrize(("value", "reason"), [("0", "greater"), ("abc", "whole")])
def test_rejects_an_invalid_max_pixels(
    photo: Path, capsys: pytest.CaptureFixture[str], value: str, reason: str
) -> None:
    with pytest.raises(SystemExit) as stop:
        main([str(photo), "--max-pixels", value])

    assert stop.value.code == 2
    assert reason in capsys.readouterr().err


def test_the_help_mentions_every_option(capsys: pytest.CaptureFixture[str]) -> None:
    text = build_parser().format_help()

    for option in ("--output", "--model", "--max-pixels", "--overwrite", "--version"):
        assert option in text
