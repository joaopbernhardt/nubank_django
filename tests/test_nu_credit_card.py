from unittest import mock

import pytest
from pynubank import MockHttpClient

from nubank_django import domain
from nubank_django.models import CardStatement


@pytest.fixture
def parsed_card_statements(nubank):
    return domain.parse_card_statements(nubank.get_card_statements())


def test_can_import_card_statements(nubank):
    card_statements = nubank.get_card_statements()
    parsed = domain.parse_card_statements(card_statements)
    assert type(parsed[0]) == CardStatement


@mock.patch("nubank_django.nu._get_http_client", mock.MagicMock(return_value=MockHttpClient()))
def test_can_get_raw_card_statements_from_source():
    raw_card_statements = domain.get_raw_card_statements(cache_policy="ignore")
    assert type(raw_card_statements) == list


@mock.patch("nubank_django.nu._get_http_client", mock.MagicMock(return_value=MockHttpClient()))
def test_can_persist_card_statements():
    raw_card_statements = domain.get_raw_card_statements(cache_policy="ignore")
    parsed_card_statements = domain.parse_card_statements(raw_card_statements)
    domain.persist_card_statements(parsed_card_statements)
    assert CardStatement.objects.count() == len(raw_card_statements)


def test_persisting_card_statements_avoids_duplication(parsed_card_statements):
    domain.persist_card_statements(parsed_card_statements)
    count_after_first_run = CardStatement.objects.count()

    domain.persist_card_statements(parsed_card_statements)
    count_after_second_run = CardStatement.objects.count()
    assert count_after_first_run == count_after_second_run
