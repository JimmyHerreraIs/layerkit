"""Model adapters: one small module per segmentation model.

Swapping a model must never require touching ``layerkit.core``. Use
:func:`load_model` to get a model by name.
"""

from __future__ import annotations

from layerkit.core.errors import UnknownModelError
from layerkit.core.interfaces import ForegroundModel
from layerkit.models.rembg_model import RembgModel

DEFAULT_MODEL_NAME = "u2netp"
_REMBG_MODEL_NAMES = ("u2netp", "isnet-general-use")

__all__ = ["DEFAULT_MODEL_NAME", "available_models", "load_model"]


def available_models() -> tuple[str, ...]:
    """Return the names of the models that can be loaded.

    Returns:
        The model names, with the default one first.
    """
    return _REMBG_MODEL_NAMES


def load_model(name: str = DEFAULT_MODEL_NAME) -> ForegroundModel:
    """Create a model by name.

    The model is created but not loaded: weights are fetched the first time it
    is used.

    Args:
        name: One of :func:`available_models`.

    Returns:
        A model ready to compute masks.

    Raises:
        UnknownModelError: If ``name`` is not an available model.
    """
    if name not in _REMBG_MODEL_NAMES:
        raise UnknownModelError(name, _REMBG_MODEL_NAMES)
    return RembgModel(name)
