#!/usr/bin/env python3
"""PyFlink job for enriching text messages with embeddings and writing to pgvector."""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

import psycopg2
import requests
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer, KafkaSource
from pyflink.datastream.functions import MapFunction
from pyflink.common import Types


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("embedding-job")


def _clean_vector_literal(values):
    return '[' + ','.join(f"{float(v):.8f}" for v in values) + ']'


class EmbeddingEnrichmentFunction(MapFunction):
    def __init__(self):
        self.session = requests.Session()
        base_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:5000")
        self.endpoint = base_url.rstrip('/') + '/generate'
        self.timeout = float(os.getenv("EMBEDDING_SERVICE_TIMEOUT", "15"))

    def _parse_message(self, raw_value: str) -> Optional[Dict[str, Any]]:
        try:
            payload = json.loads(raw_value)
            if not isinstance(payload, dict):
                logger.warning("Ignoring non-object message: %s", raw_value)
                return None
            return payload
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON message: %s", raw_value)
            return None

    def map(self, value):
        logger.info("📥 Received raw message from Kafka: %s...", value[:100] if value else None)
        
        message = self._parse_message(value)
        if not message:
            return None

        text = message.get('text')
        if not text or not str(text).strip():
            logger.info("Skipping message without text: %s", message.get('id'))
            return None
            
        logger.info("🔄 Processing message %s with text: %s...", 
                   message.get('id'), 
                   text[:100] if text else None)

        request_payload = {
            "id": message.get('id'),
            "text": text,
            "model": message.get('model') or message.get('model_name'),
            "metadata": message.get('metadata'),
            "source": message.get('source'),
            "timestamp": message.get('timestamp'),
        }

        try:
            response = self.session.post(self.endpoint, json=request_payload, timeout=self.timeout)
            response.raise_for_status()
            embedding_payload = response.json()
        except requests.RequestException as exc:
            logger.error("❌ Embedding service request failed: %s", exc)
            return None
        except ValueError as exc:
            logger.error("❌ Invalid response from embedding service: %s", exc)
            return None

        embedding = embedding_payload.get('embedding')
        if not embedding:
            logger.error("❌ Missing embedding in response for message %s", message.get('id'))
            return None

        enriched = {
            "id": embedding_payload.get('id') or message.get('id'),
            "text": embedding_payload.get('text') or text,
            "embedding": embedding,
            "embedding_dimension": embedding_payload.get('embedding_dimension'),
            "model_name": embedding_payload.get('model_name') or message.get('model_name'),
            "source": embedding_payload.get('source') or message.get('source'),
            "timestamp": message.get('timestamp'),
            "embedding_timestamp": embedding_payload.get('embedding_timestamp') or time.time(),
            "metadata": embedding_payload.get('metadata') or message.get('metadata') or {},
        }

        logger.info("✨ Generated embedding for message %s (dim: %d)", 
                   enriched['id'], len(embedding))
        return json.dumps(enriched)


class PgVectorWriter(MapFunction):
    """A function that processes enriched messages and writes them to PostgreSQL with pgvector."""
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.messages_processed = 0
        self.table_name = os.getenv("PGVECTOR_TABLE", "text_message_embeddings")
        self.expected_dim = int(os.getenv("PGVECTOR_DIMENSION", "384"))
        self.host = os.getenv("PGVECTOR_HOST", "pgvector-postgres")
        self.port = int(os.getenv("PGVECTOR_PORT", "5432"))
        self.database = os.getenv("PGVECTOR_DB", "embeddings_db")
        self.user = os.getenv("PGVECTOR_USER", "postgres")
        self.password = os.getenv("PGVECTOR_PASSWORD", "postgres")
        self.sslmode = os.getenv("PGVECTOR_SSLMODE")
        self.table_ready = False

    def _connect(self):
        dsn = {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
        }
        if self.sslmode:
            dsn["sslmode"] = self.sslmode

        self.connection = psycopg2.connect(**dsn)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    def _ensure_table(self):
        if self.table_ready:
            return

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                text TEXT,
                embedding vector({self.expected_dim}),
                model_name TEXT,
                source TEXT,
                message_timestamp TIMESTAMPTZ,
                embedding_timestamp TIMESTAMPTZ,
                metadata JSONB
            );
        """
        self.cursor.execute(create_sql)
        self.table_ready = True

    def map(self, value):
        logger.info("📝 PgVector Writer processing message %d", self.messages_processed)
        
        if not self.cursor:
            logger.info("🔌 Connecting to PostgreSQL database at %s:%d", self.host, self.port)
            self._connect()
            self._ensure_table()
            logger.info("✅ Database connection and table ready")
            
        try:
            payload = json.loads(value)
            logger.info("📄 Processing payload for message ID: %s", payload.get('id'))
        except json.JSONDecodeError:
            logger.error("❌ Failed to decode enriched payload: %s", value)
            return None

        embedding = payload.get('embedding')
        if not embedding:
            logger.error("❌ No embedding present for message %s", payload.get('id'))
            return None

        if len(embedding) != self.expected_dim:
            logger.error(
                "❌ Embedding dimension mismatch for message %s (expected %s, got %s)",
                payload.get('id'),
                self.expected_dim,
                len(embedding)
            )
            return None

        vector_literal = _clean_vector_literal(embedding)
        message_timestamp = payload.get('timestamp')
        embedding_timestamp = payload.get('embedding_timestamp')

        insert_sql = f"""
            INSERT INTO {self.table_name} (
                id, text, embedding, model_name, source, message_timestamp, embedding_timestamp, metadata
            ) VALUES (
                %(id)s,
                %(text)s,
                %(embedding)s::vector,
                %(model_name)s,
                %(source)s,
                to_timestamp(%(message_ts)s),
                to_timestamp(%(embedding_ts)s),
                %(metadata)s::jsonb
            )
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding,
                model_name = EXCLUDED.model_name,
                source = EXCLUDED.source,
                message_timestamp = COALESCE(EXCLUDED.message_timestamp, {self.table_name}.message_timestamp),
                embedding_timestamp = EXCLUDED.embedding_timestamp,
                metadata = COALESCE(EXCLUDED.metadata, {self.table_name}.metadata);
        """

        message_ts_value: Optional[float] = None
        if message_timestamp is not None:
            try:
                message_ts_value = float(message_timestamp)
            except (TypeError, ValueError):
                logger.warning("⚠️ Unable to convert message timestamp to float for %s", payload.get('id'))

        embedding_ts_value: float
        if embedding_timestamp is not None:
            try:
                embedding_ts_value = float(embedding_timestamp)
            except (TypeError, ValueError):
                embedding_ts_value = time.time()
        else:
            embedding_ts_value = time.time()

        params = {
            "id": payload.get('id'),
            "text": payload.get('text'),
            "embedding": vector_literal,
            "model_name": payload.get('model_name'),
            "source": payload.get('source'),
            "message_ts": message_ts_value,
            "embedding_ts": embedding_ts_value,
            "metadata": json.dumps(payload.get('metadata') or {}),
        }

        try:
            logger.info("💾 Writing embedding for message %s to pgvector", payload.get('id'))
            self.cursor.execute(insert_sql, params)
        except Exception as exc:
            logger.error("❌ Failed to upsert embedding into pgvector: %s", exc)
            # Try to reconnect and retry once
            try:
                logger.info("🔄 Attempting to reconnect to database and retry...")
                self._connect()
                self.cursor.execute(insert_sql, params)
            except Exception as exc:
                logger.error("❌ Failed to upsert embedding after reconnect: %s", exc)
                return None
        else:
            self.messages_processed += 1
            logger.info("✅ Successfully persisted embedding %d for message %s (text: %s...)", 
                       self.messages_processed, 
                       payload.get('id'),
                       str(payload.get('text'))[:50] if payload.get('text') else None)
        
        return value  # Return the original message for chaining


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(int(os.getenv("FLINK_PARALLELISM", "1")))
    env.enable_checkpointing(int(os.getenv("FLINK_CHECKPOINT_INTERVAL_MS", "10000")))

    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"))
        .set_topics(os.getenv("KAFKA_INPUT_TOPIC", "text-messages"))
        .set_group_id(os.getenv("KAFKA_GROUP_ID", "flink-embedding-consumer"))
        .set_value_only_deserializer(SimpleStringSchema())
        .set_starting_offsets(KafkaOffsetsInitializer.earliest())
        .build()
    )

    stream = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "text-messages-source",
        type_info=Types.STRING()
    )

    enriched_stream = stream.map(
        EmbeddingEnrichmentFunction(),
        output_type=Types.STRING()
    ).filter(lambda x: x is not None)  # Filter out None results

    # Use map instead of add_sink to write to pgvector
    enriched_stream.map(
        PgVectorWriter(),
        output_type=Types.STRING()
    )

    env.execute(os.getenv("FLINK_JOB_NAME", "text-messages-embedding-pipeline"))


if __name__ == "__main__":
    main()
