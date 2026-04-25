import hashlib
import hmac
import time
from urllib.parse import parse_qs


def parse_init_data_pairs(init_data: str) -> dict[str, str]:
    parsed_data = parse_qs(init_data)
    return {key: parsed_data[key][0] for key in parsed_data.keys()}


def build_data_check_string(pairs: dict[str, str]) -> str:
    """Строка для проверки подписи initData (без поля hash), порядок ключей — лексикографический."""
    keys = sorted(k for k in pairs if k != "hash")
    return "\n".join(f"{k}={pairs[k]}" for k in keys)


def init_data_secret_key(bot_token: str) -> bytes:
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def is_valid_init_data_hash(
    data_check_string: str, received_hash: str, secret_key: bytes
) -> bool:
    hex_hmac = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(received_hash, hex_hmac)


def is_auth_date_fresh(
    auth_date: str,
    max_age_seconds: int = 86400,
    now_ts: int | None = None,
) -> bool:
    """Проверка, что auth_date из initData не старше max_age_seconds относительно now_ts (или текущего времени)."""
    if max_age_seconds < 0:
        return False
    try:
        auth_ts = int(auth_date.strip())
    except (TypeError, ValueError):
        return False
    reference = int(time.time()) if now_ts is None else now_ts
    age = reference - auth_ts
    return 0 <= age <= max_age_seconds
