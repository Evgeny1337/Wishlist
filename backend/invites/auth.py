import jwt
from ninja.security import HttpBearer

from invites.jwt_tokens import decode_token
from invites.models import TelegramProfile


class TelegramJWTAuth(HttpBearer):
    def authenticate(self, request, token: str) -> TelegramProfile | None:
        try:
            payload = decode_token(token)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
        if payload.get("type") != "access":
            return None
        if 'sub' not in payload:
            return None
        return TelegramProfile.objects.filter(telegram_user_id=int(payload["sub"])).first()
