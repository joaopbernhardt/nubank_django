from typing import Optional

from django.db import models
from django.forms import ValidationError


class CardStatement(models.Model):
    """
    Example of card statement object from pynubank:

    {'_links': {
        'self': {'href': 'https://prod-s0-facade.nubank.com.br/api/transactions/4ecd9a59-3747-4af4-9192-a969b23cf513'}},
      'account': '0cedea55-3fa8-4c4d-b72a-1bab24f0fb0a',
      'amount': 3290,
      'amount_without_iof': 3290,
      'category': 'transaction',
      'description': 'Netflix.Com',
      'details': {'status': 'settled', 'subcategory': 'card_not_present'},
      'href': 'nuapp://transaction/4ecd9a59-3747-4af4-9192-a969b23cf513',
      'id': '4ecd9a59-3747-4af4-9192-a969b23cf513',
      'source': 'upfront_national',
      'time': '2021-03-21T10:56:13Z',
      'title': 'serviÃ§os',
      'tokenized': True}
    """

    nubank_id = models.UUIDField()

    account = models.UUIDField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_without_iof = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=128)
    description = models.TextField()
    details = models.JSONField()
    source = models.CharField(max_length=64, null=True, blank=True)
    time = models.DateTimeField(db_index=True)
    title = models.CharField(max_length=128)
    tokenized = models.BooleanField(null=True, blank=True)

    def __str__(self) -> str:
        return f"({self.time.date().strftime('%d/%b/%Y')}) {self.description}: R$ {self.amount}"


DEBIT_STATEMENT_TYPES = (
    "TransferOutEvent",
    "BillPaymentEvent",
    "BarcodePaymentEvent",
    "PixTransferOutEvent",
)
CREDIT_STATEMENT_TYPES = ("TransferInEvent", "TransferOutReversalEvent")


class AccountStatement(models.Model):
    ACCOUNT_STATEMENT_TYPE = (
        # DEBIT
        ("TransferOutEvent", "TransferOutEvent"),
        ("BillPaymentEvent", "BillPaymentEvent"),
        ("BarcodePaymentEvent", "BarcodePaymentEvent"),
        ("PixTransferOutEvent", "PixTransferOutEvent"),
        # CREDIT
        ("TransferOutReversalEvent", "TransferOutReversalEvent"),
        ("TransferInEvent", "TransferInEvent"),
        # RESERVE
        ("RemoveFromReserveEvent", "RemoveFromReserveEvent"),
        ("AddToReserveEvent", "AddToReserveEvent"),
        # UNKNOWN
        ("DebitPurchaseEvent", "DebitPurchaseEvent"),
        ("DebitWithdrawalFeeEvent", "DebitWithdrawalFeeEvent"),
        ("DebitWithdrawalEvent", "DebitWithdrawalEvent"),
    )

    nubank_id = models.UUIDField(unique=True)
    destination_account = models.CharField(max_length=256, null=True, blank=True)
    origin_account = models.CharField(max_length=256, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    detail = models.TextField()
    post_date = models.DateField()
    title = models.CharField(max_length=128)
    gql_typename = models.CharField("Statement Type", choices=ACCOUNT_STATEMENT_TYPE, max_length=64)

    def __str__(self):
        return f"({self.post_date}) {self.detail}: R$ {self.amount}"

    @property
    def is_transfer_out(self):
        return "TransferOutEvent" in self.gql_typename

    @property
    def is_transfer_in(self):
        return self.gql_typename == "TransferInEvent"

    @property
    def account_name(self) -> Optional[str]:
        if self.is_transfer_out:
            return self.destination_account
        elif self.is_transfer_in:
            return self.origin_account

    def clean(self):
        if self.destination_account and self.origin_account:
            raise ValidationError("Destination and Origin accounts are mutually exclusive.")

        if self.is_transfer_in and not getattr(self, "origin_account", None):
            raise ValidationError("TransferInEvent must have an associated origin_account.")

        if self.is_transfer_out and not getattr(self, "destination_account", None):
            raise ValidationError("*TransferOutEvent must have an associated destination_account.")
