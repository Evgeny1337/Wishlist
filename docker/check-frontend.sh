#!/bin/sh
# Проверка, что статика клиента залита перед деплоем.
set -e

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="${FRONTEND_DIR:-$ROOT/frontend}"
INDEX="$FRONTEND_DIR/index.html"

if [ ! -f "$INDEX" ]; then
  echo "ERROR: нет статики клиента."
  echo "Ожидается файл: $INDEX"
  echo "Собери фронт и скопируй build/ в frontend/:"
  echo "  cd WishlistClient && npm ci && npm run build:prod"
  echo "  rsync -a --delete build/ $FRONTEND_DIR/"
  exit 1
fi

echo "frontend ok: $INDEX"
