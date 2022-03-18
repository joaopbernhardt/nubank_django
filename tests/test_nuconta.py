import pytest

from nubank_django.domain import (
    parse_account_statements,
    persist_parsed_account_statements,
)
from nubank_django.models import AccountStatement


@pytest.fixture
def parsed_statements(nubank):
    return parse_account_statements(nubank.get_account_statements())


def test_can_import_statement(nubank):
    statements = nubank.get_account_statements()
    parsed = parse_account_statements(statements)
    assert type(parsed[0]) == AccountStatement


def test_can_persist_parsed_account_statements(
    parsed_statements, db_queries
):
    persist_parsed_account_statements(parsed_statements)
    assert len(db_queries) == 3
    assert AccountStatement.objects.count() == len(parsed_statements)
