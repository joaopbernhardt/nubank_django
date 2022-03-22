from http import HTTPStatus

import pytest
from django.urls import reverse
from django.contrib.admin import site

from nubank_django.admin import CardStatementAdmin, AccountStatementAdmin
from nubank_django.models import CardStatement, AccountStatement


@pytest.fixture
def superuser(user_create):
    user = user_create(superuser=True)
    return user

@pytest.fixture
def card_statement_admin():
    return CardStatementAdmin(CardStatement, site)


@pytest.fixture
def account_statement_admin():
    return AccountStatementAdmin(AccountStatement, site)


def test_card_statements_list_viewed_with_permission(superuser, card_statement_admin, request_get):
    request = request_get(
        reverse("admin:nubank_django_cardstatement_changelist"), user=superuser
    )
    response = card_statement_admin.changelist_view(request)
    assert response.status_code == HTTPStatus.OK


def test_account_statements_list_viewed_with_permission(superuser, account_statement_admin, request_get):
    request = request_get(
        reverse("admin:nubank_django_accountstatement_changelist"), user=superuser
    )
    response = account_statement_admin.changelist_view(request)
    assert response.status_code == HTTPStatus.OK


def test_card_statements_details_viewed_with_permission(superuser, card_statement_admin, request_get, nu_data_loader):
    nu_data_loader()
    statement = CardStatement.objects.first()
    request = request_get(
        reverse("admin:nubank_django_cardstatement_change", args=[statement.id]), user=superuser
    )
    response = card_statement_admin.change_view(request, object_id=str(statement.id))
    assert response.status_code == HTTPStatus.OK


def test_account_statements_details_viewed_with_permission(superuser, account_statement_admin, request_get, nu_data_loader):
    nu_data_loader()
    statement = AccountStatement.objects.first()
    request = request_get(
        reverse("admin:nubank_django_accountstatement_change", args=[statement.id]), user=superuser
    )
    response = account_statement_admin.change_view(request, object_id=str(statement.id))
    assert response.status_code == HTTPStatus.OK


def test_account_import_action(superuser, account_statement_admin, request_get):
    # Make sure DB table is empty
    assert not AccountStatement.objects.exists()
    request = request_get(
        reverse("admin:nubank_django_accountstatement_actions", args=["run_nuconta_import"]), user=superuser
    )
    account_statement_admin.run_nuconta_import(request, queryset=None)

    # Confirm the correct execution by checking DB rows have been placed
    assert AccountStatement.objects.exists()


def test_card_import_action(superuser, card_statement_admin, request_get):
    # Make sure DB table is empty
    assert not CardStatement.objects.exists()
    request = request_get(
        reverse("admin:nubank_django_cardstatement_actions", args=["run_nubank_import"]), user=superuser
    )
    card_statement_admin.run_nubank_import(request, queryset=None)

    # Confirm the correct execution by checking DB rows have been placed
    assert CardStatement.objects.exists()