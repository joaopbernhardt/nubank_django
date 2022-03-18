import pytest
from pynubank import MockHttpClient, Nubank
from pytest_djangoapp import configure_djangoapp_plugin


pytest_plugins = configure_djangoapp_plugin(settings="settings")


@pytest.fixture
def nubank():
    nu = Nubank(MockHttpClient())
    nu.authenticate_with_cert(
        "qualquer-cpf", "qualquer-senha", "caminho/do_certificado.p12"
    )
    return nu
