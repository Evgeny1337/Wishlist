from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from invites.jwt_tokens import issue_token_pair
from invites.models import Invite, InviteActivation, TelegramProfile
from wishlists.models import (
    Event,
    EventAccess,
    GiftPlan,
    GiftPlanItem,
    Reminder,
    Wish,
    WishList,
    WishListAccess,
    WishReservation,
)


class Command(BaseCommand):
    help = "Заполняет БД демо-данными для разработки фронтенда"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Удалить существующие демо-данные перед заполнением",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        if TelegramProfile.objects.filter(telegram_user_id=100001).exists():
            self.stdout.write(self.style.WARNING("Демо-данные уже есть. Используйте --flush для пересоздания."))
            self._print_tokens()
            return

        now = timezone.now()

        alice = TelegramProfile.objects.create(
            telegram_user_id=100001,
            username="alice_demo",
            first_name="Алиса",
            last_name="Иванова",
        )
        bob = TelegramProfile.objects.create(
            telegram_user_id=100002,
            username="bob_demo",
            first_name="Боб",
            last_name="Петров",
        )
        carol = TelegramProfile.objects.create(
            telegram_user_id=100003,
            username="carol_demo",
            first_name="Каролина",
            last_name="Смирнова",
        )

        invite = Invite.objects.create(
            token="demo-invite-token",
            max_uses=10,
            used_count=2,
            is_active=True,
            expires_at=now + timedelta(days=90),
        )
        InviteActivation.objects.create(invite=invite, telegram_profile=alice)
        InviteActivation.objects.create(invite=invite, telegram_profile=bob)

        alice_birthday = WishList.objects.create(owner=alice, title="День рождения Алисы")
        alice_ny = WishList.objects.create(owner=alice, title="Новый год")
        bob_tech = WishList.objects.create(owner=bob, title="Гаджеты Боба")

        WishListAccess.objects.create(profile=bob, wishlist=alice_birthday)
        WishListAccess.objects.create(profile=carol, wishlist=alice_birthday)
        WishListAccess.objects.create(profile=alice, wishlist=bob_tech)

        wishes_birthday = [
            Wish.objects.create(
                wishlist=alice_birthday,
                title="Беспроводные наушники Sony WH-1000XM5",
                url="https://www.sony.ru/headphones/wh-1000xm5",
                note="Чёрный цвет, с шумодавом",
                priority=Wish.WishPriority.HIGH,
                preview_title="Sony WH-1000XM5",
                preview_image_url="https://picsum.photos/seed/sony/400/300",
            ),
            Wish.objects.create(
                wishlist=alice_birthday,
                title="Книга «Чистый код»",
                url="https://www.labirint.ru/books/clean-code/",
                note="Мягкая обложка",
                priority=Wish.WishPriority.MEDIUM,
                preview_title="Чистый код",
                preview_image_url="https://picsum.photos/seed/book/400/300",
            ),
            Wish.objects.create(
                wishlist=alice_birthday,
                title="Набор свечей",
                url="",
                note="Любые ароматические, без ванили",
                priority=Wish.WishPriority.LOW,
            ),
            Wish.objects.create(
                wishlist=alice_birthday,
                title="Механическая клавиатура Keychron Q1",
                url="https://www.keychron.com/products/keychron-q1",
                note="Brown switches",
                priority=Wish.WishPriority.HIGH,
                preview_title="Keychron Q1",
                preview_image_url="https://picsum.photos/seed/keychron/400/300",
            ),
        ]

        Wish.objects.create(
            wishlist=alice_ny,
            title="Термокружка",
            url="https://example.com/mug",
            note="Объём 500 мл",
            priority=Wish.WishPriority.MEDIUM,
        )
        Wish.objects.create(
            wishlist=alice_ny,
            title="Шерстяной плед",
            url="",
            note="Серый или бежевый",
            priority=Wish.WishPriority.LOW,
        )

        bob_wishes = [
            Wish.objects.create(
                wishlist=bob_tech,
                title="Монитор Dell UltraSharp 27\"",
                url="https://www.dell.com/ultrasharp-27",
                note="4K, USB-C",
                priority=Wish.WishPriority.HIGH,
                preview_title="Dell UltraSharp 27",
                preview_image_url="https://picsum.photos/seed/dell/400/300",
            ),
            Wish.objects.create(
                wishlist=bob_tech,
                title="SSD Samsung 2TB",
                url="https://www.samsung.com/ssd-2tb",
                note="",
                priority=Wish.WishPriority.MEDIUM,
            ),
        ]

        WishReservation.objects.create(wish=wishes_birthday[0], profile=bob, is_anonymous=True)
        WishReservation.objects.create(wish=wishes_birthday[1], profile=carol, is_anonymous=False)
        WishReservation.objects.create(wish=bob_wishes[1], profile=alice, is_anonymous=True)

        event_bday = Event.objects.create(
            title="ДР Алисы",
            owner=alice,
            wishlist=alice_birthday,
            starts_at=now + timedelta(days=21),
        )
        event_ny = Event.objects.create(
            title="Новогодний обмен",
            owner=alice,
            wishlist=alice_ny,
            starts_at=now + timedelta(days=60),
        )
        event_bob = Event.objects.create(
            title="Домашний кинотеатр у Боба",
            owner=bob,
            wishlist=bob_tech,
            starts_at=now + timedelta(days=14),
        )

        EventAccess.objects.create(profile=bob, event=event_bday)
        EventAccess.objects.create(profile=carol, event=event_bday)
        EventAccess.objects.create(profile=alice, event=event_bob)
        EventAccess.objects.create(profile=bob, event=event_ny)

        plan = GiftPlan.objects.create(
            owner=bob,
            title="Подарки на ДР Алисы",
            occurs_at=event_bday.starts_at,
        )
        GiftPlanItem.objects.create(plan=plan, wish=wishes_birthday[0])
        GiftPlanItem.objects.create(
            plan=plan,
            title="Открытка ручной работы",
            url="https://example.com/card",
        )

        alice_plan = GiftPlan.objects.create(
            owner=alice,
            title="Подарки Бобу",
            occurs_at=event_bob.starts_at,
        )
        GiftPlanItem.objects.create(plan=alice_plan, wish=bob_wishes[0])

        Reminder.objects.create(
            owner=bob,
            title="Купить подарок Алисе",
            remind_at=event_bday.starts_at - timedelta(days=3),
            event=event_bday,
        )
        Reminder.objects.create(
            owner=alice,
            title="Напомнить про ДР",
            remind_at=event_bday.starts_at - timedelta(days=1),
            event=None,
        )
        Reminder.objects.create(
            owner=alice,
            title=None,
            remind_at=event_bob.starts_at - timedelta(days=2),
            event=event_bob,
        )

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы."))
        self.stdout.write(
            f"Профили: alice={alice.telegram_user_id}, bob={bob.telegram_user_id}, carol={carol.telegram_user_id}"
        )
        self.stdout.write(f"Инвайт-токен: {invite.token}")
        self.stdout.write(
            f"Вишлисты: birthday={alice_birthday.id}, ny={alice_ny.id}, bob_tech={bob_tech.id}"
        )
        self._print_tokens()

    def _flush(self):
        demo_ids = [100001, 100002, 100003]
        profiles = TelegramProfile.objects.filter(telegram_user_id__in=demo_ids)
        WishReservation.objects.filter(profile__in=profiles).delete()
        WishReservation.objects.filter(wish__wishlist__owner__in=profiles).delete()
        GiftPlanItem.objects.filter(plan__owner__in=profiles).delete()
        GiftPlan.objects.filter(owner__in=profiles).delete()
        Reminder.objects.filter(owner__in=profiles).delete()
        EventAccess.objects.filter(profile__in=profiles).delete()
        EventAccess.objects.filter(event__owner__in=profiles).delete()
        Event.objects.filter(owner__in=profiles).delete()
        WishListAccess.objects.filter(profile__in=profiles).delete()
        WishListAccess.objects.filter(wishlist__owner__in=profiles).delete()
        Wish.objects.filter(wishlist__owner__in=profiles).delete()
        WishList.objects.filter(owner__in=profiles).delete()
        InviteActivation.objects.filter(telegram_profile__in=profiles).delete()
        Invite.objects.filter(token="demo-invite-token").delete()
        profiles.delete()
        self.stdout.write(self.style.WARNING("Старые демо-данные удалены."))

    def _print_tokens(self):
        self.stdout.write("")
        self.stdout.write("JWT access-токены (Authorization: Bearer <token>):")
        for tid, label in ((100001, "alice"), (100002, "bob"), (100003, "carol")):
            if not TelegramProfile.objects.filter(telegram_user_id=tid).exists():
                continue
            pair = issue_token_pair(tid)
            self.stdout.write(f"  {label} ({tid}):")
            self.stdout.write(pair.access_token)
