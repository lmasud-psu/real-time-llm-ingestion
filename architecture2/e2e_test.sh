#!/usr/bin/env bash

set -euo pipefail

# Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

log() { echo -e "${BLUE}[E2E]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
KAFKA_DIR="${ROOT_DIR}/kafka"

cd "${SCRIPT_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  err "docker is required for this test"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  err "curl is required for this test"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  err "python3 is required for this test"
  exit 1
fi

log "Checking embedding service health..."
if ! curl -fsS http://localhost:5000/health >/dev/null; then
  err "Embedding service not reachable on http://localhost:5000/health"
  exit 1
fi
ok "Embedding service healthy."

log "Checking Flink JobManager..."
if ! curl -fsS http://localhost:8081/overview >/dev/null; then
  err "Flink JobManager API not reachable on http://localhost:8081/overview"
  exit 1
fi

FLINK_STATE=$(curl -fsS http://localhost:8081/jobs/overview | python3 - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print("INVALID")
    sys.exit(0)
jobs = data.get("jobs", [])
running = [job for job in jobs if job.get("state") == "RUNNING"]
if running:
    print("RUNNING")
else:
    print("NOT_RUNNING")
PY
)

if [[ "${FLINK_STATE}" != "RUNNING" ]]; then
  err "No running Flink jobs detected. Current state: ${FLINK_STATE}"
  exit 1
fi
ok "Flink job is running."

log "Checking pgvector connectivity..."
COUNT_BEFORE_RAW=$(docker compose exec -T pgvector-postgres \
  psql -U postgres -d embeddings_db -At -c "SELECT COUNT(*) FROM text_message_embeddings;" 2>&1 || true)

if [[ "${COUNT_BEFORE_RAW}" == *"does not exist"* ]]; then
  warn "Table text_message_embeddings not found yet; treating existing row count as 0."
  COUNT_BEFORE=0
elif [[ "${COUNT_BEFORE_RAW}" =~ ^[0-9]+$ ]]; then
  COUNT_BEFORE=${COUNT_BEFORE_RAW}
else
  err "Failed to query pgvector: ${COUNT_BEFORE_RAW}"
  exit 1
fi
ok "Current vector row count: ${COUNT_BEFORE}"

log "Sending test message to Kafka topic 'text-messages'..."
pushd "${KAFKA_DIR}" >/dev/null
CLI_OUTPUT=$(python3 kafka_cli.py write text-messages "Flink pipeline E2E $(date -Iseconds)" 2>&1)
STATUS=$?
popd >/dev/null

log "Kafka CLI output:\n${CLI_OUTPUT}"

if [ ${STATUS} -ne 0 ]; then
  err "Failed to publish message to Kafka"
  exit 1
fi

MESSAGE_ID=$(echo "${CLI_OUTPUT}" | sed -n "s/.*ID '\([^']*\)'.*/\1/p" | tail -n1)
if [[ -z "${MESSAGE_ID}" ]]; then
  warn "Could not parse message ID from kafka_cli output; will rely on row count change."
else
  ok "Message published with ID ${MESSAGE_ID}"
fi

log "Waiting for pgvector insertion..."
ATTEMPTS=15
SLEEP_SEC=4
ROW_FOUND=0

for attempt in $(seq 1 ${ATTEMPTS}); do
  QUERY="SELECT COUNT(*) FROM text_message_embeddings"
  if [[ -n "${MESSAGE_ID}" ]]; then
    QUERY+=" WHERE id='${MESSAGE_ID}'"
  fi

  RESULT=$(docker compose exec -T pgvector-postgres \
    psql -U postgres -d embeddings_db -At -c "${QUERY};" 2>&1 || true)

  if [[ "${RESULT}" == *"does not exist"* ]]; then
    warn "Attempt ${attempt}/${ATTEMPTS}: table not ready yet."
  elif [[ "${RESULT}" =~ ^[0-9]+$ ]]; then
    if [[ -n "${MESSAGE_ID}" ]]; then
      if (( RESULT > 0 )); then
        ROW_FOUND=1
        ok "Message ${MESSAGE_ID} persisted to pgvector."
        break
      fi
    else
      TOTAL_COUNT=${RESULT}
      if (( TOTAL_COUNT > COUNT_BEFORE )); then
        ROW_FOUND=1
        ok "pgvector row count increased to ${TOTAL_COUNT}."
        break
      fi
    fi
    warn "Attempt ${attempt}/${ATTEMPTS}: record not visible yet."
  else
    warn "Attempt ${attempt}/${ATTEMPTS}: unexpected response '${RESULT}'."
  fi

  sleep ${SLEEP_SEC}
done

if [[ ${ROW_FOUND} -ne 1 ]]; then
  err "Timed out waiting for pgvector to contain the new embedding."
  exit 1
fi

log "E2E test completed successfully."
