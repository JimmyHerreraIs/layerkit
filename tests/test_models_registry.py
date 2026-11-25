import pytest

from layerkit.core.errors import UnknownModelError
from layerkit.core.interfaces import ForegroundModel
from layerkit.models import DEFAULT_MODEL_NAME, available_models, load_model


def test_the_default_model_is_the_first_available_one() -> None:
    assert available_models()[0] == DEFAULT_MODEL_NAME == "u2netp"


def test_lists_the_models_chosen_in_the_adr() -> None:
    assert available_models() == ("u2netp", "isnet-general-use")


def test_loads_the_default_model_without_arguments() -> None:
    model = load_model()

    assert isinstance(model, ForegroundModel)
    assert model.name == DEFAULT_MODEL_NAME


@pytest.mark.parametrize("name", ["u2netp", "isnet-general-use"])
def test_loads_every_available_model_by_name(name: str) -> None:
    assert load_model(name).name == name


def test_an_unknown_name_lists_the_valid_choices() -> None:
    with pytest.raises(UnknownModelError) as error:
        load_model("does-not-exist")

    assert error.value.name == "does-not-exist"
    assert error.value.choices == available_models()
    assert "u2netp" in str(error.value)
