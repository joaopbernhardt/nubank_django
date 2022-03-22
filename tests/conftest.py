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

@pytest.fixture
def nu_data_loader():
    """Fill DB with mock info via pynubank's test client"""
    def _inner():
        from nubank_django.domain import full_load_card_statements, full_load_nuconta_statements
        full_load_nuconta_statements()
        full_load_card_statements()
    return _inner
