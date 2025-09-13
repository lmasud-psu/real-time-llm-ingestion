#!/usr/bin/env python3

import os
import sys
import json
import time
import uuid
import argparse
from dataclasses import dataclass
from typing import Optional, List, Dict, Iterable

import psycopg2
from psycopg2 import sql as _psql_sql
from kafka import KafkaProducer, KafkaConsumer


@dataclass
class Timings:
    start: float
    produced_at: Optional[float] = None
    embedding_seen_at: Optional[float] = None
    finished_at: Optional[float] = None

    def total_ms(self) -> Optional[float]:
        return None if self.finished_at is None else (self.finished_at - self.start) * 1000.0

    def produce_to_embed_ms(self) -> Optional[float]:
        if self.produced_at is None or self.embedding_seen_at is None:
            return None
        return (self.embedding_seen_at - self.produced_at) * 1000.0

    def embed_to_finish_ms(self) -> Optional[float]:
        if self.embedding_seen_at is None or self.finished_at is None:
            return None
        return (self.finished_at - self.embedding_seen_at) * 1000.0


def read_text_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def get_pg_conn():
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = int(os.getenv('DATABASE_PORT', '5432'))
    database = os.getenv('DATABASE_NAME', 'embeddings_db')
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', 'postgres')
    return psycopg2.connect(host=host, port=port, database=database, user=user, password=password)


def wait_for_embedding(conn, table: str, message_id: str, timeout_s: int = 60) -> bool:
    conn.autocommit = True
    with conn.cursor() as cur:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            cur.execute(f"SELECT 1 FROM {table} WHERE id = %s", (message_id,))
            found = cur.fetchone() is not None
            if found:
                return True
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='Run ingestion experiment over a dataset directory and measure latency to pgvector.')
    default_dataset_dir = os.path.join(os.path.dirname(__file__), 'datasets/smoke')
    parser.add_argument('--dataset-dir', default=default_dataset_dir, help='Directory under experiments/datasets containing input .txt files')
    parser.add_argument('--bootstrap-servers', default=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    parser.add_argument('--input-topic', default=os.getenv('KAFKA_INPUT_TOPIC', 'text-messages'))
    parser.add_argument('--output-topic', default=os.getenv('KAFKA_OUTPUT_TOPIC', 'embeddings'))
    parser.add_argument('--table', default=os.getenv('EMBEDDINGS_TABLE', 'embeddings'))
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--model', default=os.getenv('EMBEDDING_MODEL'), help='Override embedding model to use for generation (optional)')
    parser.add_argument('--models', nargs='+', help='Space-separated list of embedding models to compare (overrides --model)')
    # NDJSON options
    parser.add_argument('--ndjson-text-field', default=os.getenv('NDJSON_TEXT_FIELD', 'text'), help='Field in NDJSON records containing text')
    parser.add_argument('--ndjson-id-field', default=os.getenv('NDJSON_ID_FIELD', 'id'), help='Field in NDJSON records containing id (optional)')
    parser.add_argument('--ndjson-chunk-size', type=int, default=int(os.getenv('NDJSON_CHUNK_SIZE', '100')), help='Number of records to send before flushing')
    parser.add_argument('--verify-each', action='store_true', help='Verify persistence for each NDJSON record (default: only last in file)')
    args = parser.parse_args()

    dataset_dir = os.path.abspath(args.dataset_dir)
    if not os.path.isdir(dataset_dir):
        print(json.dumps({'status': 'error', 'message': f'dataset dir not found: {dataset_dir}'}))
        sys.exit(1)

    print(f"[INGEST] Using dataset directory: {dataset_dir}")

    # Collect files
    txt_files: List[str] = sorted([os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.lower().endswith('.txt')])
    ndjson_files: List[str] = sorted([os.path.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.lower().endswith('.ndjson') or f.lower().endswith('.jsonl')])
    if not txt_files and not ndjson_files:
        print(json.dumps({'status': 'error', 'message': f'no .txt or .ndjson files found in: {dataset_dir}'}))
        sys.exit(1)
    print(f"[INGEST] Found {len(txt_files)} text files and {len(ndjson_files)} ndjson/jsonl files")
    if args.models:
        print(f"[INGEST] Comparative run over models: {', '.join(args.models)}")
    elif args.model:
        print(f"[INGEST] Using model override: {args.model}")

    # Derive dataset name from directory (for logging)
    dataset_name = os.path.basename(os.path.normpath(dataset_dir)) or 'unknown'

    def run_for_model(model_name: Optional[str]) -> Dict:
        print(f"[INGEST] ==== Starting run for model: {model_name or 'default-from-config'} ====")
        overall_start = time.time()
        per_file_results: List[Dict] = []

        producer = KafkaProducer(
            bootstrap_servers=args.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            retries=3,
        )

        # Process text files
        for path in txt_files:
            print(f"[INGEST] Processing text file: {os.path.basename(path)}")
            text = read_text_file(path)
            timings = Timings(start=time.time())

            message_id = str(uuid.uuid4())
            payload = {
                'id': message_id,
                'text': text,
                'timestamp': time.time(),
                'source': 'ingestion-experiment'
            }
            if model_name:
                payload['model'] = model_name
            future = producer.send(args.input_topic, value=payload, key=message_id)
            future.get(timeout=10)
            timings.produced_at = time.time()
            print(f"[INGEST] Produced message id={message_id} to topic={args.input_topic}")

            consumer = KafkaConsumer(
                args.output_topic,
                bootstrap_servers=args.bootstrap_servers,
                group_id=f'ingestion-exp-{uuid.uuid4()}',
                auto_offset_reset='latest',
                enable_auto_commit=False,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                consumer_timeout_ms=500
            )

            print(f"[INGEST] Waiting for embedding on topic={args.output_topic} (timeout={args.timeout}s)...")
            deadline = time.time() + args.timeout
            saw_output = False
            while time.time() < deadline:
                batch = consumer.poll(timeout_ms=500)
                if batch:
                    for _, records in batch.items():
                        for rec in records:
                            val = rec.value or {}
                            if val.get('id') == message_id:
                                timings.embedding_seen_at = time.time()
                                saw_output = True
                                break
                if saw_output:
                    break
                time.sleep(0.2)
            consumer.close()

            with get_pg_conn() as conn:
                remaining = max(1, args.timeout - int(time.time() - timings.start))
                print(f"[INGEST] Verifying persistence in Postgres table={args.table} (timeout={remaining}s)...")
                ok = wait_for_embedding(conn, args.table, message_id, timeout_s=remaining)
                if not ok:
                    per_file_results.append({
                        'file': os.path.basename(path),
                        'message_id': message_id,
                        'status': 'error',
                        'error': 'embedding not found in Postgres within timeout',
                    })
                    print(f"[INGEST][ERROR] Not persisted in time: id={message_id}")
                    continue

            timings.finished_at = time.time()
            print(f"[INGEST][OK] Completed file: {os.path.basename(path)} in {timings.total_ms():.1f} ms")

            per_file_results.append({
                'file': os.path.basename(path),
                'message_id': message_id,
                'status': 'ok',
                'timings_ms': {
                    'total': timings.total_ms(),
                    'produce_to_embedding_seen': timings.produce_to_embed_ms(),
                    'embedding_seen_to_persisted': timings.embed_to_finish_ms()
                }
            })

        # Process NDJSON files (chunked)
        for path in ndjson_files:
            print(f"[INGEST] Processing NDJSON file: {os.path.basename(path)}")
            file_start = time.time()
            produced_ids: List[str] = []
            persisted_ids: List[str] = []
            produced_count = 0
            import json as _json
            with open(path, 'r', encoding='utf-8') as f:
                buffer_count = 0
                consumer = KafkaConsumer(
                    args.output_topic,
                    bootstrap_servers=args.bootstrap_servers,
                    group_id=f'ingestion-exp-{uuid.uuid4()}',
                    auto_offset_reset='latest',
                    enable_auto_commit=False,
                    value_deserializer=lambda m: _json.loads(m.decode('utf-8')),
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    consumer_timeout_ms=500
                )
                try:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = _json.loads(line)
                        except Exception:
                            continue
                        msg_id = str(rec.get(args.ndjson_id_field) or uuid.uuid4())
                        text_val = rec.get(args.ndjson_text_field)
                        if not isinstance(text_val, str) or not text_val.strip():
                            continue
                        payload = {
                            'id': msg_id,
                            'text': text_val,
                            'timestamp': time.time(),
                            'source': 'ingestion-experiment-ndjson'
                        }
                        if model_name:
                            payload['model'] = model_name
                        producer.send(args.input_topic, value=payload, key=msg_id)
                        produced_ids.append(msg_id)
                        produced_count += 1
                        buffer_count += 1
                        if buffer_count >= args.ndjson_chunk_size:
                            producer.flush()
                            print(f"[INGEST] Flushed chunk: produced={produced_count} so far from {os.path.basename(path)}")
                            buffer_count = 0

                    producer.flush()
                    print(f"[INGEST] Final flush complete: total produced from file={produced_count}")

                    print(f"[INGEST] Observing output topic={args.output_topic} for produced ids (timeout={args.timeout}s)...")
                    deadline = time.time() + args.timeout
                    seen = set()
                    while time.time() < deadline and len(seen) < len(produced_ids):
                        batch = consumer.poll(timeout_ms=500)
                        if batch:
                            for _, records in batch.items():
                                for r in records:
                                    v = r.value or {}
                                    rid = v.get('id')
                                    if rid in produced_ids:
                                        seen.add(rid)
                        if len(seen) >= len(produced_ids):
                            break
                    ids_to_check = produced_ids if args.verify_each else ([produced_ids[-1]] if produced_ids else [])
                    with get_pg_conn() as conn:
                        for rid in ids_to_check:
                            remaining = max(1, args.timeout - int(time.time() - file_start))
                            ok = wait_for_embedding(conn, args.table, rid, timeout_s=remaining)
                            if ok:
                                persisted_ids.append(rid)
                finally:
                    consumer.close()

            per_file_results.append({
                'file': os.path.basename(path),
                'status': 'ok',
                'records_produced': produced_count,
                'records_seen_on_output_topic': len(persisted_ids) if args.verify_each else (1 if persisted_ids else 0),
                'duration_ms': (time.time() - file_start) * 1000.0
            })
            print(f"[INGEST][OK] Completed NDJSON file: {os.path.basename(path)} produced={produced_count} verified={(len(persisted_ids) if args.verify_each else (1 if persisted_ids else 0))} in {(time.time() - file_start) * 1000.0:.1f} ms")

        overall_finished = time.time()
        result = {
            'status': 'ok',
            'dataset_dir': dataset_dir,
            'model': model_name or 'default',
            'overall_ms': (overall_finished - overall_start) * 1000.0,
            'per_file': per_file_results,
            'config': {
                'bootstrap_servers': args.bootstrap_servers,
                'input_topic': args.input_topic,
                'output_topic': args.output_topic,
                'table': args.table,
                'model': model_name
            }
        }
        print("[INGEST] Experiment complete for model:", model_name or 'default')
        print(json.dumps(result, indent=2))

        try:
            print(f"[INGEST] Clearing table '{args.table}'...")
            with get_pg_conn() as _conn:
                with _conn.cursor() as _cur:
                    stmt = _psql_sql.SQL("TRUNCATE TABLE {};").format(_psql_sql.Identifier(args.table))
                    _cur.execute(stmt)
                    _conn.commit()
            print(f"[INGEST][OK] Cleared table '{args.table}'.")
        except Exception as e:
            print(f"[INGEST][WARN] Failed to clear table '{args.table}': {e}")

        return result

    # Run either single or comparative
    comparative_results: List[Dict] = []
    if args.models:
        for m in args.models:
            res = run_for_model(m)
            comparative_results.append(res)
    else:
        res = run_for_model(args.model)
        comparative_results.append(res)

    # Print comparison table
    print("\n[INGEST] Comparison Summary")
    headers = ["Model", "Total ms"]
    rows = []
    for r in comparative_results:
        rows.append([str(r.get('model', 'default')), f"{r.get('overall_ms', 0):.1f}"])

    # Simple ASCII table
    col_widths = [max(len(headers[0]), max(len(row[0]) for row in rows) if rows else 0),
                  max(len(headers[1]), max(len(row[1]) for row in rows) if rows else 0)]
    def fmt_row(a, b):
        return f"| {a.ljust(col_widths[0])} | {b.rjust(col_widths[1])} |"
    sep = f"+-{'-'*col_widths[0]}-+-{'-'*col_widths[1]}-+"
    print(sep)
    print(fmt_row(*headers))
    print(sep)
    for row in rows:
        print(fmt_row(*row))
    print(sep)


if __name__ == '__main__':
    main()


