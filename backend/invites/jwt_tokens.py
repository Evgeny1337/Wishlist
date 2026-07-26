import jwt
import time
from django.conf import settings

from invites.pydantic_models import TokenPair


def issue_token_pair(telegram_user_id: int) -> TokenPair:
    time_now = time.time()
    exp_access = int(time_now) + int(settings.JWT_ACCESS_TTL_SEC)
    exp_refresh = int(time_now) + int(settings.JWT_REFRESH_TTL_SEC)
    jwt_access = jwt.encode({
        'sub': telegram_user_id,
        'exp': exp_access,
        'iat': int(time_now),
        'type':'access'
    }, key=settings.JWT_SECRET, algorithm='HS256')
    jwt_refresh = jwt.encode({
        'sub': telegram_user_id,
        'exp': exp_refresh,
        'iat': int(time_now),
        'type':'refresh'
    }, key=settings.JWT_SECRET, algorithm='HS256')
    return TokenPair(
        access_token=jwt_access,
        refresh_token=jwt_refresh,
        expires_in=int(settings.JWT_ACCESS_TTL_SEC),
        refresh_expires_in=int(settings.JWT_REFRESH_TTL_SEC),
    )




def decode_token(token: str) -> dict:
    return jwt.decode(token, key=settings.JWT_SECRET, algorithms=['HS256'])
