#!/usr/bin/env bash

set -euo pipefail

# Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

log() { echo -e "${BLUE}[E2E]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; }

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
KAFKA_DIR="${ROOT_DIR}/../kafka"

cd "${ROOT_DIR}"

log "Checking service health..."
if ! curl -fsS http://localhost:5000/health >/dev/null; then
  warn "Embedding service not reporting healthy yet. Proceeding anyway."
else
  ok "Embedding service healthy."
fi

if ! curl -fsS http://localhost:5001/health >/dev/null; then
  err "Writer service not healthy. Aborting."
  exit 1
else
  ok "Writer service healthy."
fi

log "1) Sending test message to topic 'text-messages'..."
pushd "${KAFKA_DIR}" >/dev/null
python kafka_cli.py write text-messages "Test message for end-to-end validation" || {
  err "Failed to send Kafka message"; exit 1;
}
popd >/dev/null
ok "Test message sent."

log "2) Waiting for writer-service to process..."
COUNT_BEFORE=$(curl -s http://localhost:5001/stats | python -c 'import sys,json; print(json.load(sys.stdin).get("messages_processed",0))')
ATTEMPTS=10
SLEEP_SEC=2
for i in $(seq 1 ${ATTEMPTS}); do
  COUNT_NOW=$(curl -s http://localhost:5001/stats | python -c 'import sys,json; print(json.load(sys.stdin).get("messages_processed",0))')
  echo -e "${YELLOW}  attempt ${i}/${ATTEMPTS}${NC}: processed=${COUNT_NOW} (was ${COUNT_BEFORE})"
  if [ "${COUNT_NOW}" -gt "${COUNT_BEFORE}" ]; then
    ok "Writer processed a new message (processed=${COUNT_NOW})."
    break
  fi
  sleep ${SLEEP_SEC}
done

if [ "${COUNT_NOW}" -le "${COUNT_BEFORE}" ]; then
  err "Writer did not process a new message within timeout."
  exit 1
fi

log "3) Verifying Postgres has records in 'embeddings'..."
set +e
COUNT_SQL=$(docker compose exec -T postgres psql -U postgres -d embeddings_db -At -c "SELECT COUNT(*) FROM embeddings;" 2>/dev/null)
RC=$?
set -e
if [ ${RC} -ne 0 ] || ! [[ "${COUNT_SQL}" =~ ^[0-9]+$ ]]; then
  err "Failed to query Postgres for embeddings count."
  exit 1
fi

ok "Embeddings row count: ${COUNT_SQL}"
log "E2E test completed."


