import pytest
from PIL import Image

from layerkit.models import DEFAULT_MODEL_NAME, load_model


@pytest.mark.integration
def test_the_default_model_returns_a_mask_of_the_same_size() -> None:
    """Runs the real default model. Needs the rembg extra and downloads weights."""
    pytest.importorskip("rembg")
    image = Image.new("RGB", (160, 120), (30, 60, 200))

    mask = load_model(DEFAULT_MODEL_NAME).predict_mask(image)

    assert mask.mode == "L"
    assert mask.size == image.size
