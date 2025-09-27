#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="${COMPOSE:-docker compose}"
SERVICE="${SERVICE:-bot}"
DB_SERVICE="${DB_SERVICE:-db}"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found (create from .env.template)"; exit 1
fi

DB_DSN="$(grep -E '^DB_DSN=' "$ENV_FILE" | sed 's/^DB_DSN=//; s/^"//; s/"$$//')"
if [ -z "$DB_DSN" ]; then
  echo "Error: DB_DSN not set in $ENV_FILE"; exit 1
fi

PARSED="$(python3 - <<'PY' "$DB_DSN"
import sys
from urllib.parse import urlparse
dsn = sys.argv[1]
p = urlparse(dsn)
scheme = (p.scheme or '').split('+',1)[0]
if scheme.startswith('sqlite'):
    # Not supported in this script (we expect Postgres)
    print('sqlite||||')
else:
    user = p.username or ''
    host = p.hostname or ''
    port = p.port or ''
    db = p.path.lstrip('/') if p.path else ''
    print('postgres|{}|{}|{}|{}'.format(user, host, port, db))
PY
)"

if [ -z "$PARSED" ]; then
  echo "Failed to parse DB_DSN ($DB_DSN)"; exit 1
fi

IFS='|' read -r DBTYPE DB_USER DB_HOST DB_PORT DB_NAME <<< "$PARSED"

if [ "$DBTYPE" != "postgres" ]; then
  echo "Only Postgres supported. Found: $DBTYPE"
  exit 1
fi

DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-bot_db}"

if [ -z "$DB_HOST" ]; then
  echo "Could not parse DB host from DB_DSN ('$DB_DSN')"; exit 1
fi

echo "Postgres detected: host=$DB_HOST port=$DB_PORT user=$DB_USER db=$DB_NAME"

if [ "$DB_HOST" = "$DB_SERVICE" ] || [ "$DB_HOST" = "localhost" ] || [ "$DB_HOST" = "127.0.0.1" ]; then
  echo "Starting DB service (if needed) and waiting using pg_isready inside '$DB_SERVICE'..."
  $COMPOSE up -d "$DB_SERVICE" || true
  echo -n "Waiting for Postgres (pg_isready) ... "
  until $COMPOSE exec -T "$DB_SERVICE" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    printf "."
    sleep 1
  done
  echo " ready"
else
  echo -n "Waiting for TCP $DB_HOST:$DB_PORT ... "
  until nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; do
    printf "."
    sleep 1
  done
  echo " ready"
fi

CMD="${1:-}"
ARG2="${2:-}"

case "$CMD" in
  ""|"up"|"down"|"to")
    ;;
  *)
    if [ -n "$CMD" ]; then
      echo "Warning: ignoring unexpected argument '$CMD' (treating as no-arg)"
      CMD=""
    fi
    ;;
esac

if [ -z "$CMD" ] || [ "$CMD" = "up" ]; then
  if [ -n "$ARG2" ]; then
    echo "Running: alembic upgrade +$ARG2"
    $COMPOSE run --rm "$SERVICE" alembic upgrade +"$ARG2"
  else
    echo "Running: alembic upgrade head"
    $COMPOSE run --rm "$SERVICE" alembic upgrade head
  fi
elif [ "$CMD" = "down" ]; then
  if [ -n "$ARG2" ]; then
    echo "Running: alembic downgrade -$ARG2"
    $COMPOSE run --rm "$SERVICE" alembic downgrade -"$ARG2"
  else
    echo "Running: alembic downgrade -1"
    $COMPOSE run --rm "$SERVICE" alembic downgrade -1
  fi
elif [ "$CMD" = "to" ]; then
  if [ -z "$ARG2" ]; then
    echo "Usage: ./scripts/migrate.sh to <revision>"; exit 1
  fi
  echo "Running: alembic upgrade $ARG2"
  $COMPOSE run --rm "$SERVICE" alembic upgrade "$ARG2"
else
  echo "Unhandled command: $CMD"; exit 1
fi
