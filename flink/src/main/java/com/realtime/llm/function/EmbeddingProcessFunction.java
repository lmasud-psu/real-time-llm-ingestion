package com.realtime.llm.function;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.realtime.llm.model.TextEmbedding;
import com.realtime.llm.model.TextMessage;
import com.realtime.llm.service.EmbeddingService;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;

public class EmbeddingProcessFunction extends ProcessFunction<String, TextEmbedding> {
    private static final Logger LOG = LoggerFactory.getLogger(EmbeddingProcessFunction.class);
    
    private final String embeddingServiceUrl;
    private transient EmbeddingService embeddingService;
    private transient ObjectMapper objectMapper;

    public EmbeddingProcessFunction(String embeddingServiceUrl) {
        this.embeddingServiceUrl = embeddingServiceUrl;
    }

    @Override
    public void open(Configuration parameters) throws Exception {
        super.open(parameters);
        this.embeddingService = new EmbeddingService(embeddingServiceUrl);
        this.objectMapper = new ObjectMapper();
        LOG.info("🚀 EmbeddingProcessFunction initialized with service URL: {}", embeddingServiceUrl);
    }

    @Override
    public void processElement(String value, Context ctx, Collector<TextEmbedding> out) throws Exception {
        try {
            TextMessage message = objectMapper.readValue(value, TextMessage.class);
            LOG.info("📥 Processing message: {}", message.getId());

            float[] embedding = embeddingService.getEmbedding(message.getText());
            LOG.info("✨ Generated embedding for message: {}", message.getId());

            TextEmbedding textEmbedding = new TextEmbedding(
                    message.getId(),
                    message.getText(),
                    embedding,
                    message.getTimestamp(),
                    Instant.now()
            );

            out.collect(textEmbedding);
        } catch (Exception e) {
            LOG.error("Failed to process message: " + value, e);
        }
    }

    @Override
    public void close() throws Exception {
        if (embeddingService != null) {
            embeddingService.close();
        }
        super.close();
    }
}