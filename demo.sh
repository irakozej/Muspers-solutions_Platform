#!/usr/bin/env bash
# Start the whole MusperSolutions platform for a local demo.
#
#   ./demo.sh          start everything
#   ./demo.sh --stop   shut everything down
#
# Leaves Postgres running in Docker; the API and the web server run in the
# foreground of this script and stop together when you press Ctrl-C.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

API_PORT=8001
WEB_PORT=5173
LOG_DIR="$ROOT/.demo-logs"

say() { printf '\033[32m▸\033[0m %s\n' "$1"; }
die() { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

if [[ "${1:-}" == "--stop" ]]; then
  say "Stopping web and API..."
  lsof -ti :"$WEB_PORT" -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
  lsof -ti :"$API_PORT" -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
  say "Stopping Postgres..."
  docker compose down
  say "Stopped."
  exit 0
fi

mkdir -p "$LOG_DIR"

# ── 1. Docker ────────────────────────────────────────────────────────
if ! docker info >/dev/null 2>&1; then
  say "Starting Docker Desktop (this takes ~30s the first time)..."
  open -a Docker || die "Could not launch Docker Desktop. Start it manually and re-run."
  until docker info >/dev/null 2>&1; do sleep 2; done
fi
say "Docker is up."

# ── 2. Postgres ──────────────────────────────────────────────────────
docker compose up -d >/dev/null
until docker exec musper-postgres pg_isready -U musper -d musper >/dev/null 2>&1; do sleep 1; done
say "Postgres ready on :5434."

# ── 3. Migrations ────────────────────────────────────────────────────
(cd backend && uv run alembic upgrade head >"$LOG_DIR/alembic.log" 2>&1) \
  || die "Migrations failed. See $LOG_DIR/alembic.log"
say "Database schema up to date."

# ── 4. Warn early if the chatbot will not work ───────────────────────
# A missing, stale, or unfunded key does not surface until someone sends
# the first chat message, which is a bad way to find out mid-demo. A
# revoked key still looks well-formed, so actually call the API.
warn() { printf '\033[33m⚠  %s\033[0m\n' "$1"; }

CHAT_KEY="$(grep -E '^ANTHROPIC_API_KEY=' backend/.env 2>/dev/null | cut -d= -f2- || true)"
if [[ -z "$CHAT_KEY" ]]; then
  warn "No ANTHROPIC_API_KEY in backend/.env — the diagnostic chatbot will not respond."
else
  CHAT_MODEL="$(grep -E '^CLAUDE_MODEL=' backend/.env 2>/dev/null | cut -d= -f2- || true)"
  CHAT_MODEL="${CHAT_MODEL:-claude-sonnet-4-6}"
  CHAT_CODE="$(curl -s -m 20 -o /dev/null -w '%{http_code}' \
    https://api.anthropic.com/v1/messages \
    -H "x-api-key: $CHAT_KEY" \
    -H 'anthropic-version: 2023-06-01' \
    -H 'content-type: application/json' \
    -d "{\"model\":\"$CHAT_MODEL\",\"max_tokens\":1,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}" \
    || echo 000)"
  case "$CHAT_CODE" in
    200) say "Claude API reachable ($CHAT_MODEL) — chatbot ready." ;;
    401) warn "ANTHROPIC_API_KEY is rejected (401). The chatbot will not respond." ;;
    400) warn "Claude rejected the request (400) — is CLAUDE_MODEL=$CHAT_MODEL correct?" ;;
    402|429) warn "Claude returned $CHAT_CODE — out of credits or rate limited. The chatbot may fail." ;;
    000) warn "Could not reach the Claude API. Check the network; the chatbot needs it." ;;
    *)   warn "Claude API returned $CHAT_CODE. The chatbot may not respond." ;;
  esac
fi

# ── 5. Backend + frontend ────────────────────────────────────────────
cleanup() {
  say "Shutting down..."
  kill "${API_PID:-}" "${WEB_PID:-}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd backend && uv run uvicorn app.main:app --port "$API_PORT" >"$LOG_DIR/api.log" 2>&1) &
API_PID=$!
until curl -sf -m 2 "http://localhost:$API_PORT/health" >/dev/null 2>&1; do
  kill -0 "$API_PID" 2>/dev/null || die "API died on startup. See $LOG_DIR/api.log"
  sleep 1
done
say "API ready on :$API_PORT."

(cd frontend && npm run dev >"$LOG_DIR/web.log" 2>&1) &
WEB_PID=$!
until curl -sf -m 2 "http://localhost:$WEB_PORT" >/dev/null 2>&1; do
  kill -0 "$WEB_PID" 2>/dev/null || die "Web server died on startup. See $LOG_DIR/web.log"
  sleep 1
done

cat <<BANNER

  ────────────────────────────────────────────────
   MusperSolutions is running.

   Site      http://localhost:$WEB_PORT
   API docs  http://localhost:$API_PORT/docs

   Advisor   penny@muspersolutions.com
   Password  ChangeMe2026!

   Logs in $LOG_DIR/ · Ctrl-C to stop everything
  ────────────────────────────────────────────────

BANNER

wait
