-- Text Writer Service Database Schema
-- This script creates the text_messages table and related indexes

-- Enable pgvector extension (in case it's needed later)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the text_messages table (compatible with CQRS embedding service)
CREATE TABLE IF NOT EXISTS text_messages (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,  -- Changed from 'message' to 'content' for compatibility
    source VARCHAR(255) DEFAULT 'kafka',  -- Track message source
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_text_messages_created_at ON text_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_text_messages_processed_at ON text_messages(processed_at);

-- Optional: Create a view for recent messages (last 24 hours)
CREATE OR REPLACE VIEW recent_text_messages AS
SELECT 
    id,
    content as message,
    source,
    created_at,
    processed_at
FROM text_messages
WHERE processed_at > NOW() - INTERVAL '24 hours'
ORDER BY processed_at DESC;