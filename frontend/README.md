# Статика клиента (WishlistClient)

Сюда кладётся результат `npm run build:prod`.

```bash
cd /path/to/WishlistClient
npm ci && npm run build:prod
rsync -a --delete build/ /path/to/Wishlist/frontend/
```

Нужен `frontend/index.html`. Без него GitHub deploy / `docker/check-frontend.sh` завершатся с ошибкой.

После копирования добавь файлы в git:

```bash
git add frontend/
git status   # должны быть видны index.html, *.js, css/
```
