-- Initialize database for CQRS embedding generation service

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE realtime_llm'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'realtime_llm');

-- Connect to the database
\c realtime_llm;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create text_messages table (source table from text_writer_svc)
CREATE TABLE IF NOT EXISTS text_messages (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    source VARCHAR(255) DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create text_embeddings table (target table for embeddings)
CREATE TABLE IF NOT EXISTS text_embeddings (
    id SERIAL PRIMARY KEY,
    text_message_id UUID REFERENCES text_messages(id),
    text_content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,  -- 384 dimensions for all-MiniLM-L6-v2
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(text_message_id)
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS text_embeddings_embedding_idx 
ON text_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS text_messages_id_idx ON text_messages(id);
CREATE INDEX IF NOT EXISTS text_embeddings_text_message_id_idx ON text_embeddings(text_message_id);

-- Insert some sample data for testing
INSERT INTO text_messages (id, content, source) VALUES
(gen_random_uuid(), 'The quick brown fox jumps over the lazy dog.', 'sample'),
(gen_random_uuid(), 'Machine learning is a subset of artificial intelligence.', 'sample'),
(gen_random_uuid(), 'PostgreSQL is a powerful open-source relational database system.', 'sample'),
(gen_random_uuid(), 'Vector databases are optimized for similarity search.', 'sample'),
(gen_random_uuid(), 'Natural language processing enables computers to understand human language.', 'sample')
ON CONFLICT DO NOTHING;