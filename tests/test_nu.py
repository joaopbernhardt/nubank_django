import os
from unittest import mock

import pytest

from nubank_django import nu


@pytest.mark.parametrize(
    ("cpf", "password", "cert_path"),
    [
        (None, None, None),
        ("some_cpf", None, None),
        (None, "some_password", None),
        (None, None, "/some/cert/path"),
    ],
)
def test_get_credentials_without_env_vars(cpf, password, cert_path):
    mocked_getenv = mock.MagicMock(side_effect=[cpf, password, cert_path])
    with mock.patch("os.getenv", mocked_getenv):
        with pytest.raises(ValueError):
            nu._get_credentials()


@mock.patch("os.path.exists", mock.MagicMock(return_value=True))
def test_get_credentials_with_all_env_vars():
    cert_path = "/some/cert/path"
    mocked_getenv = mock.MagicMock(side_effect=["some_cpf", "some_password", cert_path])
    with mock.patch("os.getenv", mocked_getenv):
        nu._get_credentials()
