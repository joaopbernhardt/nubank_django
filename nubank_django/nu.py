import os
import json
import logging
from typing import Tuple

from django.core.cache import cache
from pynubank import HttpClient, MockHttpClient, Nubank
from pynubank.utils.parsing import parse_float, parse_pix_transaction


logger = logging.getLogger(__name__)
NUBANK_CACHE_TTL = 60 * 60 * 2  # 2 hour


def _get_http_client():
    """This method makes it easier for mocking during tests."""
    # pragma: nocover
    return HttpClient()


def parse_reserve_events(transaction: dict) -> dict:
    if not transaction["__typename"] in ("AddToReserveEvent", "RemoveFromReserveEvent"):
        return transaction

    transaction["amount"] = parse_float(transaction["detail"])
    return transaction


class NubankClient(Nubank):
    def get_card_statements(self):
        cache_policy = os.getenv("NUBANK_CACHE_POLICY", "push-pull")
        CARD_STATEMENTS_CACHE_KEY = "card_statements.json"

        cached_card_statements = cache.get(CARD_STATEMENTS_CACHE_KEY)

        if "pull" in cache_policy and cached_card_statements:
            logger.info(f"Cache hit for '{CARD_STATEMENTS_CACHE_KEY}'.")
            raw_card_statements = json.loads(cached_card_statements)
            from_cache = True
        else:
            raw_card_statements = super().get_card_statements()
            from_cache = False

        if "push" in cache_policy and not from_cache:
            logger.info(f"Setting cache for '{CARD_STATEMENTS_CACHE_KEY}'.")
            cache.set(
                CARD_STATEMENTS_CACHE_KEY,
                json.dumps(raw_card_statements),
                NUBANK_CACHE_TTL,
            )

        return raw_card_statements

    def get_account_feed_with_pix_mapping(self):
        cache_policy = os.getenv("NUBANK_CACHE_POLICY", "push-pull")
        ACCOUNT_FEED_CACHE_KEY = "nuconta_feed.json"

        cached_account_feed = cache.get(ACCOUNT_FEED_CACHE_KEY)

        if "pull" in cache_policy and cached_account_feed:
            logger.info(f"Cache hit for '{ACCOUNT_FEED_CACHE_KEY}'.")
            raw_account_feed = json.loads(cached_account_feed)
            from_cache = True
        else:
            raw_account_feed = self.get_account_feed()
            from_cache = False

        if "push" in cache_policy and not from_cache:
            logger.info(f"Setting cache for '{ACCOUNT_FEED_CACHE_KEY}'.")
            cache.set(ACCOUNT_FEED_CACHE_KEY, json.dumps(raw_account_feed), NUBANK_CACHE_TTL)

        transactions_with_pix = map(parse_pix_transaction, raw_account_feed)
        transactions_without_generic_feed_events = filter(
            lambda t: t["__typename"] != "GenericFeedEvent", transactions_with_pix
        )
        transactions_with_reserve_events = map(parse_reserve_events, transactions_without_generic_feed_events)
        return list(transactions_with_reserve_events)


def get_authed_nu_client():
    http_client = _get_http_client()
    nu = NubankClient(http_client)
    if isinstance(http_client, MockHttpClient):
        nu.authenticate_with_cert("fake-cpf", "fake-password", "fake-cert_path")
    else:  # pragma: nocover
        cpf, password, cert_path = _get_credentials()
        nu.authenticate_with_cert(cpf, password, cert_path)
    return nu


def _get_credentials() -> Tuple[str]:
    cred_env_vars = ("NUBANK_CPF", "NUBANK_PASSWORD", "NUBANK_CERT_PATH")
    cpf, password, cert_path = tuple(os.getenv(env_var, None) for env_var in cred_env_vars)

    if not all([cpf, password, cert_path]):
        raise ValueError("Could not find NUBANK credentials in environment.")

    if not os.path.exists(cert_path):
        raise ValueError(f"Could not find certificate via environment variable on '{cert_path}'.")

    return cpf, password, cert_path
