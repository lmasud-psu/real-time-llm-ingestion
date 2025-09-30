package com.realtime.llm;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.realtime.llm.function.EmbeddingProcessFunction;
import com.realtime.llm.model.TextEmbedding;
import com.realtime.llm.model.TextMessage;
import com.realtime.llm.service.EmbeddingService;
import com.realtime.llm.sink.PgVectorSink;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;

public class TextEmbeddingJob {
    private static final Logger LOG = LoggerFactory.getLogger(TextEmbeddingJob.class);

    public static void main(String[] args) throws Exception {
        // Environment setup
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Configuration from environment variables
        String kafkaBootstrapServers = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
        String kafkaInputTopic = System.getenv("KAFKA_INPUT_TOPIC");
        String kafkaGroupId = System.getenv("KAFKA_GROUP_ID");
        String embeddingServiceUrl = System.getenv("EMBEDDING_SERVICE_URL");
        String pgVectorHost = System.getenv("PGVECTOR_HOST");
        String pgVectorDb = System.getenv("PGVECTOR_DB");
        String pgVectorUser = System.getenv("PGVECTOR_USER");
        String pgVectorPassword = System.getenv("PGVECTOR_PASSWORD");
        String pgVectorTable = System.getenv("PGVECTOR_TABLE");
        int pgVectorDimension = Integer.parseInt(System.getenv().getOrDefault("PGVECTOR_DIMENSION", "384"));
        int parallelism = Integer.parseInt(System.getenv().getOrDefault("FLINK_PARALLELISM", "1"));

        // Set up Kafka source
        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers(kafkaBootstrapServers)
                .setTopics(kafkaInputTopic)
                .setGroupId(kafkaGroupId)
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        // Set up the processing pipeline
        DataStream<String> kafkaStream = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "Kafka Source"
        ).setParallelism(parallelism);

        // Parse JSON messages and generate embeddings
        DataStream<TextEmbedding> embeddingStream = kafkaStream
                .process(new EmbeddingProcessFunction(embeddingServiceUrl))
                .setParallelism(parallelism);

        // Add PgVector sink
        embeddingStream.addSink(new PgVectorSink(
                pgVectorHost,
                5432,
                pgVectorDb,
                pgVectorUser,
                pgVectorPassword,
                pgVectorTable,
                pgVectorDimension
        )).setParallelism(parallelism);

        // Execute the job
        env.execute("Text Message Embedding Pipeline");
    }
}
