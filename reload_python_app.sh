#!/bin/sh
SCRIPT_DIR="/$0"; SCRIPT_DIR="${SCRIPT_DIR%/*}"; SCRIPT_DIR="${SCRIPT_DIR:-.}"; SCRIPT_DIR="${SCRIPT_DIR##/}/"; SCRIPT_DIR="$(cd -- "$SCRIPT_DIR"; pwd)"

docker compose -f "$SCRIPT_DIR/"docker-compose.yml exec python sh -c 'UWSGI_PID="$(ps | grep '\'' /opt/venv/bin/uwsgi '\'' | head -1 | sed '\''s/^ *\([^ ]*\) .*/\1/'\'')"; kill -1 "$UWSGI_PID"'
