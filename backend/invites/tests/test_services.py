import pytest

from invites.models import TelegramProfile
from invites.services import ensure_telegram_profile
from invites.telegram_webapp_user import UserModel


@pytest.fixture
def sample_webapp_user() -> UserModel:
    return UserModel(
        id=777_888_001,
        username="srv_user",
        first_name="Srv",
        last_name="Test",
    )


@pytest.mark.django_db
def test_ensure_telegram_profile_creates_profile(sample_webapp_user):
    assert TelegramProfile.objects.filter(
        telegram_user_id=777_888_001
    ).count() == 0

    profile = ensure_telegram_profile(sample_webapp_user)

    assert profile.pk is not None
    assert profile.telegram_user_id == 777_888_001
    assert profile.username == "srv_user"
    assert profile.first_name == "Srv"
    assert profile.last_name == "Test"
    assert TelegramProfile.objects.filter(
        telegram_user_id=777_888_001
    ).count() == 1


@pytest.mark.django_db
def test_ensure_telegram_profile_second_call_returns_same_row(sample_webapp_user):
    first = ensure_telegram_profile(sample_webapp_user)
    second = ensure_telegram_profile(sample_webapp_user)
    assert first.pk == second.pk
    assert TelegramProfile.objects.filter(
        telegram_user_id=777_888_001
    ).count() == 1


@pytest.mark.django_db
def test_ensure_telegram_profile_defaults_not_updated_on_repeat(sample_webapp_user):
    """get_or_create: defaults не применяются к уже существующей строке."""
    ensure_telegram_profile(sample_webapp_user)
    revised = UserModel(
        id=777_888_001,
        username="renamed_user",
        first_name="New",
        last_name="Name",
    )
    stored = ensure_telegram_profile(revised)
    stored.refresh_from_db()
    assert stored.username == "srv_user"
    assert stored.first_name == "Srv"
    assert stored.last_name == "Test"


@pytest.mark.django_db
def test_ensure_telegram_profile_allows_optional_names_null():
    user = UserModel(id=777_888_002)
    profile = ensure_telegram_profile(user)
    assert profile.telegram_user_id == 777_888_002
    assert profile.username is None
    assert profile.first_name is None
    assert profile.last_name is None
