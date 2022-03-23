from django.contrib import admin
from django_object_actions import DjangoObjectActions
from rangefilter.filters import DateRangeFilter

from nubank_django.domain import full_load_card_statements, full_load_nuconta_statements
from nubank_django.models import CardStatement, AccountStatement


@admin.register(CardStatement)
class CardStatementAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ("description", "title", "time", "amount")
    search_fields = ("amount", "description", "title")
    list_filter = (
        "title",
        "source",
        ("time", DateRangeFilter),
    )
    fields = (
        "nubank_id",
        "description",
        "amount",
        "time",
        "title",
        "source",
        "details",
    )

    changelist_actions = ["run_nubank_import"]

    def has_add_permission(self, request) -> bool:
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-time")

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def run_nubank_import(self, request, queryset):
        # TODO: error handling with admin message
        full_load_card_statements()


@admin.register(AccountStatement)
class AccountStatementAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "detail",
        "gql_typename",
        "post_date",
        "account_name",
        "amount",
    )
    search_fields = (
        "nubank_id",
        "title",
        "amount",
        "origin_account",
        "destination_account",
        "detail",
    )

    list_filter = (
        "gql_typename",
        ("post_date", DateRangeFilter),
    )

    changelist_actions = ["run_nuconta_import"]

    def has_add_permission(self, request) -> bool:
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-post_date")

    def run_nuconta_import(self, request, queryset):
        # TODO: error handling with admin message
        full_load_nuconta_statements()
