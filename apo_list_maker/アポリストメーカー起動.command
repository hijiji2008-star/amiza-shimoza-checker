#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT="5001"
URL="http://localhost:${PORT}"
LOG_FILE="$(mktemp -t apo-list-maker.XXXXXX.log)"

if [[ -f "./app.py" ]]; then
  APP_PATH="./app.py"
elif [[ -f "./apo_list_maker/app.py" ]]; then
  APP_PATH="./apo_list_maker/app.py"
else
  echo "app.py が見つかりません（このフォルダ構成に未対応です）。" >&2
  exit 1
fi

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

python3 "$APP_PATH" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

# サーバが起動するまで待つ（最大20秒）
for _ in {1..200}; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "起動に失敗しました。ログ: $LOG_FILE" >&2
    exit 1
  fi
  if curl -fsS "$URL" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

if ! curl -fsS "$URL" >/dev/null 2>&1; then
  echo "起動確認に失敗しました（${URL} に接続できません）。ログ: $LOG_FILE" >&2
  exit 1
fi

open "$URL" >/dev/null 2>&1 || true
wait "$SERVER_PID"
