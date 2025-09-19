#!/usr/bin/env bash
set -euo pipefail

JOBMANAGER_HOST="${JOBMANAGER_HOST:-flink-jobmanager}"
JOBMANAGER_PORT="${JOBMANAGER_PORT:-8081}"
JOB_FILE="${FLINK_JOB_FILE:-/opt/flink/jobs/embedding_job.py}"

printf 'Waiting for Flink JobManager at %s:%s' "$JOBMANAGER_HOST" "$JOBMANAGER_PORT"
until curl -fsS "http://${JOBMANAGER_HOST}:${JOBMANAGER_PORT}/overview" > /dev/null; do
  printf '.'
  sleep 2
done
printf '\nSubmitting job %s\n' "$JOB_FILE"

/opt/flink/bin/flink run \
  -py "$JOB_FILE" \
  --jarfile /opt/flink/lib/flink-sql-connector-kafka-1.17.2.jar \
  --jarfile /opt/flink/lib/kafka-clients-3.2.3.jar

# Keep the container alive for log inspection
exec tail -f /opt/flink/log/*.log
