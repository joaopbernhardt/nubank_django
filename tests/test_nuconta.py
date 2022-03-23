import pytest
from django.core.exceptions import ValidationError

from nubank_django.domain import (
    parse_account_statements,
    persist_parsed_account_statements,
)
from nubank_django.models import AccountStatement


@pytest.fixture
def parsed_account_statements(nubank):
    return parse_account_statements(nubank.get_account_statements())


@pytest.fixture
def transfer_in_raw_json():
    return {
        "id": "a04ae499-ac2c-45d9-9283-5fb39b798535",
        "__typename": "TransferInEvent",
        "title": "Transferência recebida",
        "detail": "R$ 3.429,00",
        "postDate": "2021-03-02",
        "amount": 3429.0,
        "originAccount": {"name": "John Sender"},
    }


@pytest.fixture
def transfer_in_account_statement(transfer_in_raw_json: dict) -> AccountStatement:
    return parse_account_statements([transfer_in_raw_json])[0]


@pytest.fixture
def transfer_out_raw_json():
    return {
        "id": "82c0d31c-c8ed-4059-8e7b-9c636baea20a",
        "__typename": "TransferOutEvent",
        "title": "Transferência enviada",
        "detail": "Jane Receiver - R$ 236,10",
        "postDate": "2021-01-13",
        "amount": 236.1,
        "destinationAccount": {"name": "Jane Receiver"},
    }


@pytest.fixture
def transfer_out_account_statement(transfer_out_raw_json: dict) -> AccountStatement:
    return parse_account_statements([transfer_out_raw_json])[0]


def test_can_import_statement(nubank):
    statements = nubank.get_account_statements()
    parsed = parse_account_statements(statements)
    assert type(parsed[0]) == AccountStatement


def test_can_persist_parsed_account_statements(parsed_account_statements, db_queries):
    persist_parsed_account_statements(parsed_account_statements)
    assert len(db_queries) == 3
    assert AccountStatement.objects.count() == len(parsed_account_statements)


def test_persisting_account_statements_avoids_duplication(parsed_account_statements):
    persist_parsed_account_statements(parsed_account_statements)
    count_after_first_run = AccountStatement.objects.count()

    persist_parsed_account_statements(parsed_account_statements)
    count_after_second_run = AccountStatement.objects.count()
    assert count_after_first_run == count_after_second_run


def test_account_statement_transfer_in_needs_origin_account(transfer_in_account_statement: AccountStatement):
    account_statement = transfer_in_account_statement
    account_statement.origin_account = None
    with pytest.raises(ValidationError):
        account_statement.full_clean()


def test_account_statement_transfer_out_needs_origin_account(transfer_out_account_statement: AccountStatement):
    account_statement = transfer_out_account_statement
    account_statement.destination_account = None
    with pytest.raises(ValidationError):
        account_statement.full_clean()


def test_account_statement_must_not_have_origin_and_destination(transfer_out_account_statement: AccountStatement):
    account_statement = transfer_out_account_statement
    account_statement.origin_account = {"name": "dummy"}
    with pytest.raises(ValidationError):
        account_statement.full_clean()


def test_account_statement_destination_account_name_relates_to_event(
    transfer_out_raw_json, transfer_out_account_statement
):
    assert transfer_out_account_statement.account_name == transfer_out_raw_json["destinationAccount"]["name"]


def test_account_statement_origin_account_name_relates_to_event(transfer_in_raw_json, transfer_in_account_statement):
    assert transfer_in_account_statement.account_name == transfer_in_raw_json["originAccount"]["name"]
