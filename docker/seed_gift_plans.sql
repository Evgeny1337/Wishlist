-- Тестовые планы подарков (GiftPlan / GiftPlanItem).

\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    -- NULL = взять первый профиль из invites_telegramprofile;
    -- подставьте ваш telegram_user_id, чтобы заполнить данные именно для вашего аккаунта
    v_target_tg_id  bigint := NULL;

    v_profile_id    bigint;
    v_tg_id         bigint;
    v_plan_id       bigint;
    v_wish_ids      bigint[];
BEGIN
    IF v_target_tg_id IS NOT NULL THEN
        SELECT id INTO v_profile_id
        FROM invites_telegramprofile
        WHERE telegram_user_id = v_target_tg_id;
    ELSE
        SELECT id INTO v_profile_id
        FROM invites_telegramprofile
        ORDER BY id
        LIMIT 1;
    END IF;

    IF v_profile_id IS NULL THEN
        v_tg_id := coalesce(v_target_tg_id, 900001);
        INSERT INTO invites_telegramprofile
            (telegram_user_id, username, first_name, last_name, created_at)
        VALUES
            (v_tg_id, 'seed_demo', 'Демо', 'Профиль', now())
        ON CONFLICT (telegram_user_id) DO NOTHING
        RETURNING id INTO v_profile_id;

        IF v_profile_id IS NULL THEN
            SELECT id INTO v_profile_id
            FROM invites_telegramprofile
            WHERE telegram_user_id = v_tg_id;
        END IF;
        RAISE NOTICE 'Создан профиль telegram_user_id=% (id=%)', v_tg_id, v_profile_id;
    END IF;

    SELECT telegram_user_id INTO v_tg_id
    FROM invites_telegramprofile
    WHERE id = v_profile_id;

    RAISE NOTICE 'Целевой профиль: id=%, telegram_user_id=%', v_profile_id, v_tg_id;

    -- До трёх желаний, доступных профилю (свои вишлисты + расшаренные)
    SELECT array_agg(id) INTO v_wish_ids
    FROM (
        SELECT w.id, w.priority, w.created_at
        FROM wishlists_wish w
        JOIN wishlists_wishlist wl ON wl.id = w.wishlist_id
        LEFT JOIN wishlists_wishlistaccess wa ON wa.wishlist_id = wl.id
        WHERE wl.owner_id = v_profile_id
           OR wa.profile_id = v_profile_id
        GROUP BY w.id, w.priority, w.created_at
        ORDER BY w.priority DESC, w.created_at DESC
        LIMIT 3
    ) s;

    -- Идемпотентность: пересоздаём только эти три плана (позиции удалятся каскадом)
    DELETE FROM wishlists_giftplan
    WHERE owner_id = v_profile_id
      AND title IN ('Новогодние подарки', 'День рождения коллеги', 'Секретный Санта');

    -- План 1: будущее событие + ссылки на реальные желания
    INSERT INTO wishlists_giftplan (owner_id, title, occurs_at, created_at)
    VALUES (v_profile_id, 'Новогодние подарки', now() + interval '45 days', now())
    RETURNING id INTO v_plan_id;

    IF coalesce(array_length(v_wish_ids, 1), 0) >= 1 THEN
        INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
        SELECT v_plan_id, w.id, w.title, w.url, now()
        FROM wishlists_wish w
        WHERE w.id = v_wish_ids[1];
    END IF;

    IF coalesce(array_length(v_wish_ids, 1), 0) >= 2 THEN
        INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
        SELECT v_plan_id, w.id, w.title, w.url, now()
        FROM wishlists_wish w
        WHERE w.id = v_wish_ids[2];
    END IF;

    INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
    VALUES
        (v_plan_id, NULL, 'Подарочная упаковка', 'https://example.com/gift-wrap', now()),
        (v_plan_id, NULL, 'Открытка с пожеланиями', '', now());

    -- План 2: ближайшее событие
    INSERT INTO wishlists_giftplan (owner_id, title, occurs_at, created_at)
    VALUES (v_profile_id, 'День рождения коллеги', now() + interval '12 days', now())
    RETURNING id INTO v_plan_id;

    INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
    VALUES
        (v_plan_id, NULL, 'Кофейный набор', 'https://example.com/coffee-set', now());

    IF coalesce(array_length(v_wish_ids, 1), 0) >= 3 THEN
        INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
        SELECT v_plan_id, w.id, w.title, w.url, now()
        FROM wishlists_wish w
        WHERE w.id = v_wish_ids[3];
    END IF;

    -- План 3: прошедшее событие
    INSERT INTO wishlists_giftplan (owner_id, title, occurs_at, created_at)
    VALUES (v_profile_id, 'Секретный Санта', now() - interval '40 days', now())
    RETURNING id INTO v_plan_id;

    INSERT INTO wishlists_giftplanitem (plan_id, wish_id, title, url, created_at)
    VALUES
        (v_plan_id, NULL, 'Настольная игра', 'https://example.com/board-game', now()),
        (v_plan_id, NULL, 'Термокружка', 'https://example.com/mug', now());

    RAISE NOTICE 'Готово: планов у профиля = %, позиций = %',
        (SELECT count(*) FROM wishlists_giftplan WHERE owner_id = v_profile_id),
        (SELECT count(*)
         FROM wishlists_giftplanitem i
         JOIN wishlists_giftplan p ON p.id = i.plan_id
         WHERE p.owner_id = v_profile_id);
END
$$;

COMMIT;

-- Проверка результата
SELECT p.id            AS plan_id,
       p.owner_id,
       p.title,
       p.occurs_at::date AS occurs_at,
       count(i.id)     AS items,
       count(i.wish_id) AS linked_to_wish
FROM wishlists_giftplan p
LEFT JOIN wishlists_giftplanitem i ON i.plan_id = p.id
GROUP BY p.id, p.owner_id, p.title, p.occurs_at
ORDER BY p.id;
