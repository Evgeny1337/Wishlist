# Снимок состояния: проект WishList (Telegram WebApp «вишлист»)

Текст для первого сообщения в новом чате с ассистентом или для быстрого входа в контекст.

## Режим работы с ИИ

Я пишу код сам; ассистент — **ментор**: даёт микро-шаги, ссылки на документацию, подсказки «куда смотреть», без готового решения целиком, пока явно не попрошу «сделай сам».

## Стек (цель обучения)

Poetry, Django + **Django Ninja**, Pydantic v2 (+ **pydantic-settings** для конфига), PostgreSQL, Docker Compose, pytest / pytest-django, flake8, mypy, black, isort; дальше по плану: HTTPX, pytest-httpx, Anyio, **tg-api**, GitLab CI, микросервисы, React.

## Структура репозитория

- **`WishList/`** — корень с `pyproject.toml`, `.env` / `.env.example`, `docker-compose.yml`.
- **`WishList/backend/`** — Django (`manage.py`, пакет проекта `wishlist/`, приложение **`wishlist_app`**).

## Уже сделано (по сути)

- Poetry, зависимости, Django + Ninja.
- `GET /api/health` — **может отсутствовать** в `wishlist/api.py`, если сознательно убран; раньше был тест `backend/test/test_health.py`.
- Подключение роутера: `wishlist/api.py` → `api.add_router('/wishlist/', wishlist_router)` из `wishlist_app.api`.
- Модель **`Wishlist`** (поля: `title`, `url`, `price`, `image_url`, `description`, `created_at`), админка, миграции.
- API: **`GET /api/wishlist/`** (список), **`POST /api/wishlist/`** (создание) — в процессе доводки схем Pydantic и тестов.
- Конфиг БД через **env** + **`wishlist/config.py`** (`BaseSettings`, `extra='ignore'`, `@lru_cache` на `get_settings()`), `.env` в корне `WishList/`.
- Тесты: pytest-django; для обращения к БД в тестах нужен **`@pytest.mark.django_db`**.

## Типичные грабли (уже разобраны)

- Импорт Ninja без настроенного Django (`DJANGO_SETTINGS_MODULE` / `django.setup()`) ломается в «голом» `python -c`.
- У `django.test.Client` надёжнее отправлять JSON так: **`json.dumps(data)` + `content_type='application/json'`**, а не полагаться на `json=` там, где он не поддерживается.
- Для POST нельзя использовать ту же Pydantic-схему, что и для ответа, с полем **`created_at` без default** — иначе **422** `missing created_at` в `body.wish_item.created_at`. Нужны **отдельные схемы Create / Out** (или костыль `= None`, хуже по смыслу).

## Отложено (не трогать без запроса, ещё несколько шагов)

Доработки конфига **A–D**: дефолты env, человекочитаемые ошибки конфигурации, разделение env Docker/Django, уход от чтения `.env` в рантайме в пользу чистых env в CI.

## Текущий фокус

Довести **POST + схемы (`WishlistCreate` / `WishlistOut`)** и тест **`test_post_wish_item...`**; проверить фактический HTTP-статус (**200 vs 201**). При **400/422** смотреть **`response.json()['detail']`**.

## Команды

Из **`backend/`**:

```bash
poetry run pytest -q
poetry run python manage.py check
poetry run python manage.py migrate
```

---

*Продолжаем с шага доведения POST и разделения Pydantic-схем.*
