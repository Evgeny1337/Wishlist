import hashlib
import hmac

from invites.telegram_init_data import (
    build_data_check_string,
    init_data_secret_key,
    is_auth_date_fresh,
    is_valid_init_data_hash,
    parse_init_data_pairs,
)


def test_parse_init_data_pairs_decodes_percent_encoding():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash=abc"
    assert parse_init_data_pairs(test_str) == {
        "user": '{"id":1}',
        "a": "1",
        "b": "2",
        "hash": "abc",
    }


def test_build_data_check_string_matches_telegram_rules():
    pairs = {
        "user": '{"id":1}',
        "auth_date": "1672531200",
        "query_id": "AA",
        "hash": "ignored",
    }
    expected = 'auth_date=1672531200\nquery_id=AA\nuser={"id":1}'
    assert build_data_check_string(pairs) == expected


def test_init_data_secret_key_matches_telegram_formula():
    bot_token = "123456:ABCDEF"
    expected_hex = "b85c5dcb6eee1e844daed3e80fb928a3e86d719ccd96a3f410a29360ba5ba60b"
    assert init_data_secret_key(bot_token).hex() == expected_hex


def test_valid_init_data_hash():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash='abc'"
    pairs = parse_init_data_pairs(test_str)
    secret_key = init_data_secret_key(bot_token="123456:ABCDEF")
    data_check_string = build_data_check_string(pairs)
    received_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert is_valid_init_data_hash(data_check_string, received_hash, secret_key)


def test_invalid_init_data_hash():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash='abc'"
    pairs = parse_init_data_pairs(test_str)
    secret_key = init_data_secret_key(bot_token="123456:ABCDEF")
    secret_bad_key = init_data_secret_key(bot_token="123457:ABCDEF")
    data_check_string = build_data_check_string(pairs)
    bad_hash = hmac.new(
        secret_bad_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert not is_valid_init_data_hash(data_check_string, bad_hash, secret_key)


def test_is_auth_date_fresh_within_window():
    now_ts = 1_700_000_000
    auth_ts = now_ts - 3600
    assert is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_too_old():
    now_ts = 1_700_000_000
    auth_ts = now_ts - 100_000
    assert not is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_in_future_rejected():
    now_ts = 1_700_000_000
    auth_ts = now_ts + 10
    assert not is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_invalid_string():
    assert not is_auth_date_fresh(
        "not-a-number", max_age_seconds=86400, now_ts=1_700_000_000
    )
