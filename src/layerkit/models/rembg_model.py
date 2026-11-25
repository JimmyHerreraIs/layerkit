"""Foreground model that runs through the optional ``rembg`` package.

``rembg`` is imported only when a mask is first requested, so importing
``layerkit`` never requires it. Install it with ``pip install "layerkit[rembg]"``.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

from PIL import Image

from layerkit.core.errors import ModelNotAvailableError

_INSTALL_HINT = 'Install it with: pip install "layerkit[rembg]"'
_CPU_ONLY = ["CPUExecutionProvider"]


def _import_rembg() -> ModuleType:
    """Import ``rembg`` or explain how to install it."""
    try:
        import rembg
    except ImportError as exc:
        raise ModelNotAvailableError(
            f"The 'rembg' package is required to run this model. {_INSTALL_HINT}"
        ) from exc
    module: ModuleType = rembg
    return module


class RembgModel:
    """A background-removal model executed by ``rembg`` on the CPU.

    The model weights are downloaded by ``rembg`` the first time the model is
    used, and the session is kept for later calls.
    """

    def __init__(self, model_name: str) -> None:
        """Remember which ``rembg`` model to run; nothing is loaded yet.

        Args:
            model_name: A model name understood by ``rembg``, for example
                ``"u2netp"``.
        """
        self._model_name = model_name
        self._session: Any = None

    @property
    def name(self) -> str:
        """Name of the ``rembg`` model."""
        return self._model_name

    def predict_mask(self, image: Image.Image) -> Image.Image:
        """Compute the foreground mask of an image.

        Args:
            image: The RGB image to analyze.

        Returns:
            An 8-bit grayscale mask with the same size as ``image``.

        Raises:
            ModelNotAvailableError: If ``rembg`` is not installed.
            RuntimeError: If ``rembg`` returns something that is not a mask of
                the expected size.
        """
        rembg = _import_rembg()
        if self._session is None:
            self._session = rembg.new_session(self._model_name, providers=_CPU_ONLY)
        result = rembg.remove(image, session=self._session, only_mask=True)
        if not isinstance(result, Image.Image) or result.size != image.size:
            raise RuntimeError(
                f"rembg returned an unexpected result for model {self._model_name!r}"
            )
        return result.convert("L")
