package com.realtime.llm.model;

import java.io.Serializable;
import java.time.Instant;
import java.util.Arrays;

public class TextEmbedding implements Serializable {
    private String id;
    private String text;
    private float[] embedding;
    private Instant timestamp;
    private Instant processedAt;

    public TextEmbedding() {
    }

    public TextEmbedding(String id, String text, float[] embedding, Instant timestamp, Instant processedAt) {
        this.id = id;
        this.text = text;
        this.embedding = embedding;
        this.timestamp = timestamp;
        this.processedAt = processedAt;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public float[] getEmbedding() {
        return embedding;
    }

    public void setEmbedding(float[] embedding) {
        this.embedding = embedding;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public Instant getProcessedAt() {
        return processedAt;
    }

    public void setProcessedAt(Instant processedAt) {
        this.processedAt = processedAt;
    }

    @Override
    public String toString() {
        return "TextEmbedding{" +
                "id='" + id + '\'' +
                ", text='" + text + '\'' +
                ", embeddingLength=" + (embedding != null ? embedding.length : 0) +
                ", timestamp=" + timestamp +
                ", processedAt=" + processedAt +
                '}';
    }
}
