-- PostgreSQL Migration: Create embeddings table with pgvector
-- Run this script after ensuring pgvector extension is installed

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id VARCHAR(255) PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(384),  -- Default embedding dimension
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(255),
    metadata JSONB
);

-- Create index on embedding column for similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_embeddings_timestamp ON embeddings (timestamp DESC);

-- Create index on source for filtering
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings (source);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON TABLE embeddings TO your_user;
-- GRANT USAGE ON SCHEMA public TO your_user;
