import sys
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest
from PIL import Image

from layerkit.core.errors import ModelNotAvailableError
from layerkit.core.interfaces import ForegroundModel
from layerkit.models.rembg_model import RembgModel


class FakeRembg:
    """Stands in for the rembg module: records calls, downloads nothing."""

    def __init__(self, result: object | None = None) -> None:
        self.sessions: list[tuple[str, list[str]]] = []
        self.removals: list[dict[str, Any]] = []
        self._result = result

    def new_session(self, name: str, providers: list[str]) -> str:
        self.sessions.append((name, providers))
        return f"session-{len(self.sessions)}"

    def remove(self, image: Image.Image, session: str, only_mask: bool) -> object:
        self.removals.append({"session": session, "only_mask": only_mask})
        if self._result is not None:
            return self._result
        return Image.new("L", image.size, 255)


def install_fake_rembg(
    monkeypatch: pytest.MonkeyPatch, fake: FakeRembg | None = None
) -> FakeRembg:
    fake = fake or FakeRembg()
    module = SimpleNamespace(new_session=fake.new_session, remove=fake.remove)
    monkeypatch.setitem(sys.modules, "rembg", cast(ModuleType, module))
    return fake


def test_conforms_to_the_foreground_model_interface() -> None:
    assert isinstance(RembgModel("u2netp"), ForegroundModel)


def test_exposes_the_model_name() -> None:
    assert RembgModel("isnet-general-use").name == "isnet-general-use"


def test_creating_the_model_does_not_import_rembg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "rembg", None)

    RembgModel("u2netp")  # must not raise


def test_explains_how_to_install_rembg_when_it_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "rembg", None)

    with pytest.raises(ModelNotAvailableError, match=r"layerkit\[rembg\]"):
        RembgModel("u2netp").predict_mask(Image.new("RGB", (4, 4)))


def test_runs_on_the_cpu_and_asks_only_for_the_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = install_fake_rembg(monkeypatch)

    mask = RembgModel("u2netp").predict_mask(Image.new("RGB", (8, 6)))

    assert fake.sessions == [("u2netp", ["CPUExecutionProvider"])]
    assert fake.removals == [{"session": "session-1", "only_mask": True}]
    assert mask.mode == "L"
    assert mask.size == (8, 6)


def test_reuses_the_session_between_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install_fake_rembg(monkeypatch)
    model = RembgModel("u2netp")

    model.predict_mask(Image.new("RGB", (4, 4)))
    model.predict_mask(Image.new("RGB", (4, 4)))

    assert len(fake.sessions) == 1
    assert len(fake.removals) == 2


def test_converts_the_result_to_grayscale(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_rembg(monkeypatch, FakeRembg(result=Image.new("RGBA", (4, 4))))

    assert RembgModel("u2netp").predict_mask(Image.new("RGB", (4, 4))).mode == "L"


@pytest.mark.parametrize(
    "bad_result", [b"not an image", Image.new("L", (3, 3))], ids=["not-image", "size"]
)
def test_rejects_an_unexpected_result(
    monkeypatch: pytest.MonkeyPatch, bad_result: object
) -> None:
    install_fake_rembg(monkeypatch, FakeRembg(result=bad_result))

    with pytest.raises(RuntimeError, match="unexpected result"):
        RembgModel("u2netp").predict_mask(Image.new("RGB", (4, 4)))
