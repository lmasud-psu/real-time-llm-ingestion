package com.realtime.llm.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.Map;

public class EmbeddingService {
    private static final Logger LOG = LoggerFactory.getLogger(EmbeddingService.class);
    private final String serviceUrl;
    private final ObjectMapper objectMapper;
    private final CloseableHttpClient httpClient;

    public EmbeddingService(String serviceUrl) {
        this.serviceUrl = serviceUrl;
        this.objectMapper = new ObjectMapper();
        this.httpClient = HttpClients.createDefault();
    }

    public float[] getEmbedding(String text) throws IOException {
        HttpPost request = new HttpPost(serviceUrl + "/embeddings");
        request.setEntity(new StringEntity(
                objectMapper.writeValueAsString(Map.of("text", text)),
                ContentType.APPLICATION_JSON));

        String response = httpClient.execute(request, response1 -> {
            if (response1.getCode() != 200) {
                throw new IOException("Failed to get embedding: " + response1.getCode());
            }
            return new String(response1.getEntity().getContent().readAllBytes());
        });

        JsonNode jsonResponse = objectMapper.readTree(response);
        JsonNode embeddingNode = jsonResponse.get("embedding");
        if (embeddingNode == null || !embeddingNode.isArray()) {
            throw new IOException("Invalid embedding response format");
        }

        float[] embedding = new float[embeddingNode.size()];
        for (int i = 0; i < embeddingNode.size(); i++) {
            embedding[i] = (float) embeddingNode.get(i).asDouble();
        }

        return embedding;
    }

    public void close() throws IOException {
        httpClient.close();
    }
}
