from typing import Any, Optional

import httpx
from django.conf import settings


def lookup_telegram_chat(telegram_user_id: int) -> tuple[Optional[bool], Optional[dict[str, Any]]]:
    """Проверка через Bot API getChat.

    Работает надёжно для пользователей, которые уже писали боту / открывали Mini App.
    Для «чужих» id Telegram часто отвечает 400 — тогда in_telegram=False.
    Если токен бота не задан — (None, None).
    """
    bot_token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not bot_token or bot_token.startswith("your-bot-token"):
        return None, None

    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(url, params={"chat_id": telegram_user_id})
        data = response.json()
    except (httpx.HTTPError, ValueError):
        return None, None

    if not isinstance(data, dict):
        return None, None

    if data.get("ok") and isinstance(data.get("result"), dict):
        result = data["result"]
        return True, {
            "id": result.get("id"),
            "username": result.get("username"),
            "first_name": result.get("first_name"),
            "last_name": result.get("last_name"),
            "type": result.get("type"),
        }

    return False, None
