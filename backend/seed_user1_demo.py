"""Заполнить демо-данными TelegramProfile telegram_user_id=1. Запуск из backend/:
python seed_user1_demo.py
"""
from __future__ import annotations

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wishlist.settings")
django.setup()

from datetime import timedelta

from django.utils import timezone

from invites.models import TelegramProfile
from wishlists.models import (
    Event,
    EventAccess,
    Reminder,
    Wish,
    WishList,
    WishListAccess,
    WishReservation,
)


def clear_owner_data(owner: TelegramProfile) -> None:
    Reminder.objects.filter(owner=owner).delete()
    EventAccess.objects.filter(event__owner=owner).delete()
    Event.objects.filter(owner=owner).delete()
    WishReservation.objects.filter(profile=owner).delete()
    WishReservation.objects.filter(wish__wishlist__owner=owner).delete()
    WishListAccess.objects.filter(wishlist__owner=owner).delete()
    WishListAccess.objects.filter(profile=owner).delete()
    Wish.objects.filter(wishlist__owner=owner).delete()
    WishList.objects.filter(owner=owner).delete()


def main() -> None:
    owner, _ = TelegramProfile.objects.update_or_create(
        telegram_user_id=1,
        defaults={
            "username": "evgeniy",
            "first_name": "Евгений",
            "last_name": "Созыкин",
        },
    )

    # Второй профиль — для access / reservation
    friend, _ = TelegramProfile.objects.update_or_create(
        telegram_user_id=42,
        defaults={
            "username": "anna_gift",
            "first_name": "Анна",
            "last_name": "Иванова",
        },
    )

    clear_owner_data(owner)

    now = timezone.now()

    birthday = WishList.objects.create(owner=owner, title="День рождения 2026")
    home = WishList.objects.create(owner=owner, title="Для дома")
    tech = WishList.objects.create(owner=owner, title="Гаджеты и техника")
    books = WishList.objects.create(owner=owner, title="Книги и обучение")
    travel = WishList.objects.create(owner=owner, title="Путешествия")

    wishes_birthday = [
        Wish.objects.create(
            wishlist=birthday,
            title="Наушники Sony WH-1000XM5",
            url="https://www.sony.ru/headphones/products/wh-1000xm5",
            note="Чёрный цвет, с шумодавом",
            priority=Wish.WishPriority.HIGH,
            preview_title="WH-1000XM5 | Sony",
            preview_image_url="https://picsum.photos/seed/xm5/400/300",
        ),
        Wish.objects.create(
            wishlist=birthday,
            title="Механическая клавиатура Keychron K2",
            url="https://www.keychron.com/products/keychron-k2-wireless-mechanical-keyboard",
            note="Brown switches, RGB",
            priority=Wish.WishPriority.MEDIUM,
            preview_title="Keychron K2",
            preview_image_url="https://picsum.photos/seed/k2/400/300",
        ),
        Wish.objects.create(
            wishlist=birthday,
            title="Сертификат в книжный",
            url="",
            note="Любой на 3000–5000 ₽",
            priority=Wish.WishPriority.LOW,
        ),
    ]

    wishes_home = [
        Wish.objects.create(
            wishlist=home,
            title="Увлажнитель воздуха Xiaomi",
            url="https://www.mi.com/",
            note="Для спальни",
            priority=Wish.WishPriority.MEDIUM,
            preview_title="Xiaomi Humidifier",
            preview_image_url="https://picsum.photos/seed/humid/400/300",
        ),
        Wish.objects.create(
            wishlist=home,
            title="Набор кастрюль",
            url="",
            note="Нержавейка, 3 штуки",
            priority=Wish.WishPriority.LOW,
        ),
        Wish.objects.create(
            wishlist=home,
            title="Плед крупной вязки",
            url="",
            note="Бежевый или серый",
            priority=Wish.WishPriority.MEDIUM,
            preview_image_url="https://picsum.photos/seed/blanket/400/300",
        ),
    ]

    wishes_tech = [
        Wish.objects.create(
            wishlist=tech,
            title="SSD Samsung 990 PRO 2TB",
            url="https://www.samsung.com/",
            note="Для рабочего Mac/PC",
            priority=Wish.WishPriority.HIGH,
            preview_title="990 PRO 2TB",
            preview_image_url="https://picsum.photos/seed/ssd/400/300",
        ),
        Wish.objects.create(
            wishlist=tech,
            title="Веб-камера Logitech Brio",
            url="https://www.logitech.com/",
            note="Для созвонов",
            priority=Wish.WishPriority.MEDIUM,
            preview_image_url="https://picsum.photos/seed/brio/400/300",
        ),
    ]

    Wish.objects.create(
        wishlist=books,
        title="Designing Data-Intensive Applications",
        url="https://dataintensive.net/",
        note="Мартин Клеппманн — бумажная или Kindle",
        priority=Wish.WishPriority.HIGH,
        preview_title="DDIA",
        preview_image_url="https://picsum.photos/seed/ddia/400/300",
    )
    Wish.objects.create(
        wishlist=books,
        title="Подписка на курсы (год)",
        url="",
        note="Frontend / архитектура",
        priority=Wish.WishPriority.MEDIUM,
    )

    Wish.objects.create(
        wishlist=travel,
        title="Чемодан Samsonite 70 см",
        url="",
        note="Тёмно-синий",
        priority=Wish.WishPriority.MEDIUM,
        preview_image_url="https://picsum.photos/seed/bag/400/300",
    )
    Wish.objects.create(
        wishlist=travel,
        title="Паowerbank Anker 20000 mAh",
        url="https://www.anker.com/",
        note="С USB-C PD",
        priority=Wish.WishPriority.HIGH,
        preview_title="Anker Power Bank",
        preview_image_url="https://picsum.photos/seed/anker/400/300",
    )

    # Друг видит «День рождения» и может бронировать
    WishListAccess.objects.create(profile=friend, wishlist=birthday)
    WishReservation.objects.create(
        wish=wishes_birthday[0],
        profile=friend,
        is_anonymous=False,
    )

    event_bday = Event.objects.create(
        title="День рождения Евгения",
        owner=owner,
        wishlist=birthday,
        starts_at=now + timedelta(days=45),
    )
    event_ny = Event.objects.create(
        title="Новый год дома",
        owner=owner,
        wishlist=home,
        starts_at=now.replace(month=12, day=31, hour=20, minute=0, second=0, microsecond=0),
    )
    EventAccess.objects.create(profile=friend, event=event_bday)

    Reminder.objects.create(
        owner=owner,
        title="Купить торт и свечи",
        remind_at=event_bday.starts_at - timedelta(days=3),
        event=event_bday,
    )
    Reminder.objects.create(
        owner=owner,
        title="Напомнить друзьям про вишлист",
        remind_at=event_bday.starts_at - timedelta(days=14),
        event=None,
    )

    print("OK seeded for telegram_user_id=1")
    print(f"  profile: {owner.first_name} @{owner.username}")
    print(f"  wishlists: {WishList.objects.filter(owner=owner).count()}")
    print(f"  wishes: {Wish.objects.filter(wishlist__owner=owner).count()}")
    print(f"  events: {Event.objects.filter(owner=owner).count()}")
    print(f"  reminders: {Reminder.objects.filter(owner=owner).count()}")
    print(f"  friend profile telegram_user_id={friend.telegram_user_id} (access + reservation)")


if __name__ == "__main__":
    main()
