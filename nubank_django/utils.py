from decimal import Decimal


def amount_to_decimal(amount: float) -> Decimal:
    return Decimal.from_float(amount).quantize(Decimal("1.00"))
