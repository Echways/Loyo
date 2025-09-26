#!/bin/sh
set -e

if [ -n "$DB_DSN" ] && [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="$DB_DSN"
  echo "Exported DATABASE_URL from DB_DSN"
fi

get_host_port() {
  url="$1"
  hostport=$(echo "$url" | sed -E 's|^[^@]*@||' | sed -E 's|/.*$||')
  host=$(echo "$hostport" | cut -d: -f1)
  port=$(echo "$hostport" | cut -s -d: -f2)
  if [ -z "$port" ]; then port=5432; fi
  echo "$host" "$port"
}

if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -qi "postgres"; then
  read host port <<EOF
$(get_host_port "$DATABASE_URL")
EOF

  echo "Waiting for database at $host:$port ..."

  tries=0
  max_tries=60
  while : ; do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "Database $host:$port is reachable"
      break
    else
      tries=$((tries+1))
      echo "Waiting for $host:$port... try $tries/$max_tries"
      if [ "$tries" -ge "$max_tries" ]; then
        echo "Timed out waiting for database"
        break
      fi
      sleep 2
    fi
  done

  if command -v alembic >/dev/null 2>&1; then
    echo "Running alembic upgrade head..."
    alembic upgrade head || echo "alembic failed or no migrations to apply"
  else
    echo "alembic not found, skipping migrations"
  fi
fi

exec "$@"
