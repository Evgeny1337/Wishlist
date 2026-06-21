import pytest
from urllib.parse import urlencode

from invites.telegram_init_data import InvalidInitData, verify_init_data

from .helpers import BOT_TOKEN_VERIFY, signed_init_data


def test_verify_init_data_success():
    now_ts = 1_700_000_000
    fields = {
        "user": '{"id":1}',
        "auth_date": str(now_ts - 3600),
        "query_id": "AA",
    }
    raw = signed_init_data(fields)
    out = verify_init_data(raw, BOT_TOKEN_VERIFY, now_ts=now_ts)
    assert out["user"] == fields["user"]
    assert out["auth_date"] == fields["auth_date"]
    assert out["hash"]


def test_verify_init_data_raises_on_missing_hash():
    now_ts = 1_700_000_000
    raw = urlencode({"user": '{"id":1}', "auth_date": str(now_ts - 3600)})
    with pytest.raises(InvalidInitData, match="hash"):
        verify_init_data(raw, BOT_TOKEN_VERIFY, now_ts=now_ts)


def test_verify_init_data_raises_on_missing_auth_date():
    fields = {"user": '{"id":1}', "query_id": "AA"}
    raw = signed_init_data(fields)
    with pytest.raises(InvalidInitData, match="auth_date"):
        verify_init_data(raw, BOT_TOKEN_VERIFY, now_ts=1_700_000_000)


def test_verify_init_data_raises_on_bad_signature():
    now_ts = 1_700_000_000
    fields = {
        "user": '{"id":1}',
        "auth_date": str(now_ts - 3600),
    }
    forged = urlencode({**fields, "hash": "0" * 64})
    with pytest.raises(InvalidInitData, match="подпись"):
        verify_init_data(forged, BOT_TOKEN_VERIFY, now_ts=now_ts)


def test_verify_init_data_raises_on_stale_auth_date():
    now_ts = 1_700_000_000
    fields = {
        "user": '{"id":1}',
        "auth_date": str(now_ts - 200_000),
    }
    raw = signed_init_data(fields)
    with pytest.raises(InvalidInitData, match="устарел|auth_date"):
        verify_init_data(raw, BOT_TOKEN_VERIFY, now_ts=now_ts)


def test_verify_init_data_raises_on_future_auth_date():
    now_ts = 1_700_000_000
    fields = {
        "user": '{"id":1}',
        "auth_date": str(now_ts + 60),
    }
    raw = signed_init_data(fields)
    with pytest.raises(InvalidInitData):
        verify_init_data(raw, BOT_TOKEN_VERIFY, now_ts=now_ts)


def test_verify_init_data_rejects_wrong_bot_token():
    now_ts = 1_700_000_000
    fields = {
        "user": '{"id":1}',
        "auth_date": str(now_ts - 3600),
    }
    raw = signed_init_data(fields)
    with pytest.raises(InvalidInitData, match="подпись"):
        verify_init_data(raw, "999999:WRONGTOKEN", now_ts=now_ts)
