import json
import logging
from decimal import Decimal
from typing import List, Optional

from django.core.cache import cache

from nubank_django.models import (
    CREDIT_STATEMENT_TYPES,
    DEBIT_STATEMENT_TYPES,
    AccountStatement,
    CardStatement,
)
from nubank_django.nu import get_authed_nu_client
from nubank_django.utils import amount_to_decimal


logger = logging.getLogger(__name__)
NUBANK_CACHE_TTL = 60 * 60 * 2  # 2 hours


def persist_card_statements(parsed_card_statements: List[CardStatement]):
    existing_card_statements_ids = CardStatement.objects.values_list("nubank_id", flat=True)
    card_statements_to_create = []
    for statement in parsed_card_statements:
        if statement.nubank_id in existing_card_statements_ids:
            continue

        card_statements_to_create.append(statement)

    CardStatement.objects.bulk_create(card_statements_to_create)


def parse_card_statements(raw_card_statements: List[dict]) -> List[CardStatement]:
    logger.info(
        "Starting parsing of card statements.",
        extra={"card_statements_count": len(raw_card_statements)},
    )
    parsed_card_statements = []
    for raw_card_statement in raw_card_statements:
        try:
            parsed_card_statement = CardStatement(
                nubank_id=raw_card_statement["id"],
                account=raw_card_statement.get("account"),
                amount=amount_to_decimal(raw_card_statement["amount"] / 100),
                amount_without_iof=amount_to_decimal(raw_card_statement.get("amount_without_iof", 0) / 100) or None,
                category=raw_card_statement["category"],
                description=raw_card_statement["description"],
                details=raw_card_statement["details"],
                source=raw_card_statement.get("source"),
                time=raw_card_statement["time"],
                title=raw_card_statement["title"],
                tokenized=raw_card_statement.get("tokenized"),
            )

            parsed_card_statement.clean_fields()
            parsed_card_statement.clean()
            parsed_card_statements.append(parsed_card_statement)
        except Exception:
            logger.exception("Could not parse statement.", extra={"statement": raw_card_statement})

    logger.info(
        "Parsed card statements.",
        extra={"parsed_card_statements_count": len(parsed_card_statements)},
    )
    return parsed_card_statements


def get_raw_card_statements(cache_policy: str = "push-pull") -> List[dict]:
    logger.info("Starting to get raw card statement.", extra={cache_policy: cache_policy})

    CARD_STATEMENTS_CACHE_KEY = "card_statements.json"

    cached_statements = cache.get(CARD_STATEMENTS_CACHE_KEY)
    if "pull" in cache_policy and cached_statements:
        logger.info(f"Cache hit for '{CARD_STATEMENTS_CACHE_KEY}'.")
        return json.loads(cached_statements)

    nu = get_authed_nu_client()
    raw_statements = nu.get_card_statements()

    if "push" in cache_policy:
        logger.info(f"Setting cache for '{CARD_STATEMENTS_CACHE_KEY}'.")
        cache.set(CARD_STATEMENTS_CACHE_KEY, json.dumps(raw_statements), NUBANK_CACHE_TTL)
    return raw_statements


def full_load_card_statements():
    raw = get_raw_card_statements()
    parsed = parse_card_statements(raw)
    persist_card_statements(parsed)


def get_raw_account_statements(cache_policy: str = "push-pull") -> List[dict]:
    logger.info("Starting to get raw nuconta statement.", extra={cache_policy: cache_policy})

    nu = get_authed_nu_client()
    raw_statements = nu.get_account_feed_with_pix_mapping()

    logger.info("Returning nuconta statements", extra={"statements_count": len(raw_statements)})
    return raw_statements


def persist_parsed_account_statements(
    parsed_statements: List[AccountStatement],
) -> None:
    logger.info(
        "Started persisting statements.",
        extra={"parsed_statements_count": len(parsed_statements)},
    )
    existing_statement_ids = AccountStatement.objects.values_list("nubank_id", flat=True)

    statements_to_create = []
    statements_already_existing = []
    for statement in parsed_statements:
        if statement.nubank_id in existing_statement_ids:
            statements_already_existing.append(statement)
            continue

        statements_to_create.append(statement)

    AccountStatement.objects.bulk_create(statements_to_create)

    logger.info(
        "Persisted statements to database.",
        extra={
            "statements_count": len(statements_to_create),
            "already_existed_count": len(statements_already_existing),
        },
    )


def _account_name_from_statement(statement: dict) -> Optional[str]:
    if statement.get("destinationAccount"):
        account_name = statement["destinationAccount"]["name"]
    elif statement["__typename"] == "PixTransferOutEvent":
        account_name = statement["detail"].split("\n")[0]
    elif statement["__typename"] == "TransferInEvent":
        origin_account = statement.get("originAccount") or {}
        account_name = origin_account.get("name", "DESCONHECIDO")
    else:
        account_name = None
    return account_name


def parse_account_statements(raw_statements: List[dict]) -> List[AccountStatement]:
    logger.info(
        "Starting parsing of statements",
        extra={"statements_count": len(raw_statements)},
    )
    parsed_statements = []
    for raw_statement in raw_statements:
        try:
            parsed_statement = AccountStatement(
                nubank_id=raw_statement["id"],
                amount=amount_to_decimal(raw_statement["amount"]),
                detail=raw_statement["detail"],
                post_date=raw_statement["postDate"],
                title=raw_statement["title"],
                gql_typename=raw_statement["__typename"],
            )

            if parsed_statement.is_transfer_out:
                parsed_statement.destination_account = _account_name_from_statement(raw_statement)
            elif parsed_statement.is_transfer_in:
                parsed_statement.origin_account = _account_name_from_statement(raw_statement)

            # uniqueness is checked before persistence attempts, not here.
            parsed_statement.clean_fields()
            parsed_statement.clean()
            parsed_statements.append(parsed_statement)
        except Exception:
            logger.exception("Could not parse statement.", extra={"statement": raw_statement})

    logger.info("Parsed statements.", extra={"parsed_statements_count": len(parsed_statements)})
    return parsed_statements


def full_load_nuconta_statements():
    raw = get_raw_account_statements()
    parsed = parse_account_statements(raw)
    persist_parsed_account_statements(parsed)
