#!/bin/bash

# Architecture 3 End-to-End Test Script
# Tests: Kafka → Text Writer Service → PostgreSQL pipeline

set -e

BASE_URL="http://localhost:5002"
KAFKA_URL="http://localhost:8080"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5434"
POSTGRES_DB="text_messages_db"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"

log() {
    echo "[E2E] $1"
}

ok() {
    echo "[OK] $1"
}

err() {
    echo "[ERR] $1" >&2
}

# Function to generate UUID (simple version)
generate_uuid() {
    python3 -c "import uuid; print(str(uuid.uuid4()))"
}

log "Starting Architecture 3 End-to-End Test"

# Test 1: Service Health Check
log "Testing Text Writer Service health..."
if curl -fsS "${BASE_URL}/health" > /dev/null; then
    ok "Text Writer Service is healthy"
else
    err "Text Writer Service health check failed"
    exit 1
fi

# Test 2: Database Connectivity
log "Testing PostgreSQL connectivity..."
if docker compose exec postgres pg_isready -U postgres -d text_messages_db > /dev/null 2>&1; then
    ok "PostgreSQL is accessible"
else
    err "PostgreSQL connection failed"
    exit 1
fi

# Test 3: Check table exists
log "Checking if text_messages table exists..."
TABLE_EXISTS=$(docker compose exec postgres psql -U postgres -d text_messages_db -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'text_messages');" | xargs)
if [ "${TABLE_EXISTS}" = "t" ]; then
    ok "text_messages table exists"
else
    err "text_messages table does not exist"
    exit 1
fi

# Test 4: Get initial message count
log "Getting initial message count..."
INITIAL_COUNT=$(docker compose exec postgres psql -U postgres -d text_messages_db -t -c "SELECT COUNT(*) FROM text_messages;" | xargs)
log "Initial message count: ${INITIAL_COUNT}"

# Test 5: Create a message via API
log "Creating a test message via API..."
TEST_MESSAGE="Test message $(date '+%Y-%m-%d %H:%M:%S')"
TEST_ID=$(generate_uuid)

API_RESPONSE=$(curl -fsS -X POST "${BASE_URL}/messages" \
    -H "Content-Type: application/json" \
    -d "{\"id\":\"${TEST_ID}\",\"message\":\"${TEST_MESSAGE}\"}")

if echo "${API_RESPONSE}" | grep -q "created"; then
    ok "Message created via API: ${TEST_ID}"
else
    err "Failed to create message via API"
    echo "Response: ${API_RESPONSE}"
    exit 1
fi

# Test 6: Verify message in database
log "Verifying message was stored in database..."
sleep 2  # Give it a moment to be stored
DB_MESSAGE=$(docker compose exec postgres psql -U postgres -d text_messages_db -t -c "SELECT message FROM text_messages WHERE id = '${TEST_ID}';" | xargs)

if [ -n "${DB_MESSAGE}" ] && [ "${DB_MESSAGE}" = "${TEST_MESSAGE}" ]; then
    ok "Message found in database: ${DB_MESSAGE}"
else
    err "Message not found in database or content mismatch"
    echo "Expected: ${TEST_MESSAGE}"
    echo "Got: ${DB_MESSAGE}"
    exit 1
fi

# Test 7: Test Kafka message processing
log "Testing Kafka message processing..."
KAFKA_TEST_ID=$(generate_uuid)
KAFKA_TEST_MESSAGE="Kafka test message $(date '+%Y-%m-%d %H:%M:%S')"

# Send message to Kafka topic using docker exec
log "Sending message to Kafka topic 'text-messages'..."
MESSAGE_JSON="{\"id\":\"${KAFKA_TEST_ID}\",\"text\":\"${KAFKA_TEST_MESSAGE}\"}"
echo "${MESSAGE_JSON}" | docker compose exec -T kafka kafka-console-producer --topic text-messages --bootstrap-server localhost:9092 || {
    err "Failed to send message to Kafka"
    exit 1
}

# Wait for message to be processed
log "Waiting for Kafka message to be processed (up to 30 seconds)..."
TIMEOUT=30
PROCESSED=false

for i in $(seq 1 $TIMEOUT); do
    KAFKA_DB_MESSAGE=$(docker compose exec postgres psql -U postgres -d text_messages_db -t -c "SELECT message FROM text_messages WHERE id = '${KAFKA_TEST_ID}';" | xargs)
    
    if [ -n "${KAFKA_DB_MESSAGE}" ]; then
        ok "Kafka message processed and stored: ${KAFKA_DB_MESSAGE}"
        PROCESSED=true
        break
    fi
    
    sleep 1
done

if [ "${PROCESSED}" = false ]; then
    err "Kafka message was not processed within ${TIMEOUT} seconds"
    exit 1
fi

# Test 8: Get final message count
log "Getting final message count..."
FINAL_COUNT=$(docker compose exec postgres psql -U postgres -d text_messages_db -t -c "SELECT COUNT(*) FROM text_messages;" | xargs)
log "Final message count: ${FINAL_COUNT}"

EXPECTED_COUNT=$((INITIAL_COUNT + 2))
if [ "${FINAL_COUNT}" -eq "${EXPECTED_COUNT}" ]; then
    ok "Message count increased correctly (${INITIAL_COUNT} → ${FINAL_COUNT})"
else
    err "Unexpected message count. Expected: ${EXPECTED_COUNT}, Got: ${FINAL_COUNT}"
    exit 1
fi

# Test 9: Test API endpoints
log "Testing API endpoints..."

# Test list messages
if curl -fsS "${BASE_URL}/messages?limit=5" | grep -q "messages"; then
    ok "List messages endpoint working"
else
    err "List messages endpoint failed"
    exit 1
fi

# Test get specific message
if curl -fsS "${BASE_URL}/messages/${TEST_ID}" | grep -q "${TEST_MESSAGE}"; then
    ok "Get message endpoint working"
else
    err "Get message endpoint failed"
    exit 1
fi

# Test stats endpoint
if curl -fsS "${BASE_URL}/stats" | grep -q "total_messages"; then
    ok "Stats endpoint working"
else
    err "Stats endpoint failed"
    exit 1
fi

# Clean up test messages (optional)
log "Cleaning up test messages..."
docker compose exec postgres psql -U postgres -d text_messages_db -c "DELETE FROM text_messages WHERE id IN ('${TEST_ID}', '${KAFKA_TEST_ID}');" > /dev/null
ok "Test messages cleaned up"

log "🎉 All tests passed! Architecture 3 is working correctly."
echo ""
echo "Test Summary:"
echo "  ✅ Text Writer Service health check"
echo "  ✅ PostgreSQL connectivity"
echo "  ✅ Database table structure"
echo "  ✅ API message creation"
echo "  ✅ Database message storage"
echo "  ✅ Kafka message processing"
echo "  ✅ End-to-end pipeline (Kafka → Service → PostgreSQL)"
echo "  ✅ API endpoints (list, get, stats)"
echo ""
echo "Architecture 3 pipeline is fully functional!"