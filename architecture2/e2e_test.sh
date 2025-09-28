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

log "Checking Flink JobManager and job status..."
if ! OVERVIEW=$(curl -fsS http://localhost:8081/overview); then
  err "Flink JobManager API not reachable on http://localhost:8081/overview"
  exit 1
fi
ok "Flink JobManager is accessible"

log "Checking Flink job status..."
JOBS_RESPONSE=$(curl -fsS http://localhost:8081/jobs/overview)
log "Debug - Jobs response: ${JOBS_RESPONSE}"

FLINK_STATE=$(echo "${JOBS_RESPONSE}" | python3 - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
    print("Parsed JSON successfully", file=sys.stderr)
except json.JSONDecodeError as e:
    print(f"JSON Parse error: {e}", file=sys.stderr)
    print("INVALID")
    sys.exit(0)

jobs = data.get("jobs", [])
print(f"Found {len(jobs)} jobs", file=sys.stderr)
running = [job for job in jobs if job.get("state") == "RUNNING"]
print(f"Found {len(running)} running jobs", file=sys.stderr)

if running:
    print("RUNNING")
else:
    print("NOT_RUNNING")
PY
)

log "Debug - Flink state: ${FLINK_STATE}"

if [[ "${FLINK_STATE}" != "RUNNING" ]]; then
  err "No running Flink jobs detected. Current state: ${FLINK_STATE}"
  log "Debug - Starting flink-submit service to submit the job..."
  
  # Start the flink-submit service
  SUBMIT_OUTPUT=$(docker compose up -d flink-submit 2>&1 || true)
  log "Debug - Submit service start output: ${SUBMIT_OUTPUT}"
  
  # Wait for job submission
  log "Waiting for job to be submitted..."
  SUBMIT_ATTEMPTS=30
  for i in $(seq 1 $SUBMIT_ATTEMPTS); do
    log "Checking job status (attempt $i/$SUBMIT_ATTEMPTS)..."
    JOBS_RESPONSE=$(curl -fsS http://localhost:8081/jobs/overview 2>/dev/null || echo '{"jobs":[]}')
    if [[ $(echo "$JOBS_RESPONSE" | python3 -c '
import sys, json
data = json.load(sys.stdin)
running = [job for job in data.get("jobs", []) if job.get("state") == "RUNNING"]
print(len(running))
') -gt 0 ]]; then
      log "Job is now running"
      break
    fi
    if [ $i -eq $SUBMIT_ATTEMPTS ]; then
      log "Debug - Submit service logs:"
      docker compose logs flink-submit
      log "Debug - JobManager logs:"
      docker compose logs flink-jobmanager
    fi
    sleep 5
  done
  
  # Wait a few seconds and check status again
  sleep 5
  JOBS_RESPONSE=$(curl -fsS http://localhost:8081/jobs/overview)
  NEW_STATE=$(echo "${JOBS_RESPONSE}" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    jobs = data.get("jobs", [])
    running = [job for job in jobs if job.get("state") == "RUNNING"]
    print("RUNNING" if running else "NOT_RUNNING")
except:
    print("INVALID")
')
  
  if [[ "${NEW_STATE}" != "RUNNING" ]]; then
    err "Failed to start Flink job. Current state: ${NEW_STATE}"
    log "Debug - Latest Flink logs:"
    docker compose logs --tail 20 flink-jobmanager
    exit 1
  fi
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
  ok "✅ [1/3] Message successfully published to Kafka with ID: ${MESSAGE_ID}"
fi

# Check Kafka topic for the message
log "Verifying message in Kafka topic..."
pushd "${KAFKA_DIR}" >/dev/null
KAFKA_READ_OUTPUT=$(python3 kafka_cli.py read text-messages --n 1 2>&1)
popd >/dev/null

if [[ "${KAFKA_READ_OUTPUT}" == *"${MESSAGE_ID}"* ]]; then
  ok "✓ Confirmed message is available in Kafka topic"
else
  warn "Message not immediately visible in Kafka topic (this is normal)"
fi

log "Waiting for embedding generation and pgvector insertion..."
ATTEMPTS=15
SLEEP_SEC=4

# Check embedding service logs for our message processing
log "Monitoring embedding service processing..."
EMBEDDING_LOGS=$(docker compose logs --tail 50 embedding-service 2>&1)
if [[ "${EMBEDDING_LOGS}" == *"Processing text for embeddings"* ]]; then
    ok "✅ [2/3] Embedding service is actively processing messages"
else
    warn "No recent embedding processing activity visible in logs"
fi
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
  log "Debugging information:"
  log "- Flink job logs:"
  docker compose logs --tail 50 flink-jobmanager
  log "- Embedding service logs:"
  docker compose logs --tail 50 embedding-service
  log "- PGVector recent queries:"
  docker compose exec pgvector-postgres psql -U postgres -d embeddings_db -c "SELECT * FROM text_message_embeddings ORDER BY created_at DESC LIMIT 5;"
  exit 1
else
  ok "✅ [3/3] Message successfully processed through entire pipeline"
fi

log "E2E test completed successfully."
