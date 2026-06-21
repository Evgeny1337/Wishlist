import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from invites.telegram_init_data import (
    build_data_check_string,
    init_data_secret_key,
)

BOT_TOKEN_VERIFY = "123456:ABCDEF"

VERIFY_INIT_ENDPOINT = "/api/telegram_webapp/verify-init-data"

ACTIVATE_INVITE_VIA_WEBAPP_ENDPOINT = "/api/telegram_webapp/activate-invite"


def signed_init_data(fields_without_hash: dict[str, str]) -> str:
    secret = init_data_secret_key(BOT_TOKEN_VERIFY)
    data_check_string = build_data_check_string(fields_without_hash)
    good_hash = hmac.new(
        secret, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return urlencode({**fields_without_hash, "hash": good_hash})


def fresh_signed_init_data() -> str:
    now_ts = int(time.time())
    fields = {"user": '{"id":1}', "auth_date": str(now_ts - 3600), "query_id": "AA"}
    return signed_init_data(fields)


def fresh_signed_init_data_user_id(telegram_user_id: int) -> str:
    """Свежий auth_date и подпись; user.id = telegram_user_id (для личных инвайтов в тестах)."""
    now_ts = int(time.time())
    fields = {
        "user": json.dumps({"id": telegram_user_id}),
        "auth_date": str(now_ts - 3600),
        "query_id": "AA",
    }
    return signed_init_data(fields)


def pairs_with_user(payload: dict) -> dict[str, str]:
    return {"user": json.dumps(payload)}


def post_activate(client, token: str, telegram_user_id: int, **kwargs):
    payload = {
        "token": token,
        "telegram_user": {
            "telegram_user_id": telegram_user_id,
            "username": kwargs.get("username", "user"),
            "first_name": kwargs.get("first_name", "User"),
            "last_name": kwargs.get("last_name", "Test"),
        },
    }
    return client.post(
        "/api/invites/activate",
        data=json.dumps(payload),
        content_type="application/json",
    )


def post_verify_init(client, raw_init_data: str):
    return client.post(
        VERIFY_INIT_ENDPOINT,
        data=json.dumps({"init_data": raw_init_data}),
        content_type="application/json",
    )


def post_activate_invite_via_webapp(client, raw_init_data: str, invite_token: str):
    return client.post(
        ACTIVATE_INVITE_VIA_WEBAPP_ENDPOINT,
        data=json.dumps(
            {"init_data": raw_init_data, "token": invite_token},
        ),
        content_type="application/json",
    )
