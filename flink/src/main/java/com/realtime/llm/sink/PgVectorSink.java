package com.realtime.llm.sink;

import com.realtime.llm.model.TextEmbedding;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.sink.RichSinkFunction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.Arrays;

public class PgVectorSink extends RichSinkFunction<TextEmbedding> {
    private static final Logger LOG = LoggerFactory.getLogger(PgVectorSink.class);

    private final String host;
    private final int port;
    private final String database;
    private final String user;
    private final String password;
    private final String table;
    private final int dimension;

    private Connection connection;
    private PreparedStatement ps;

    public PgVectorSink(String host, int port, String database, String user, String password, String table, int dimension) {
        this.host = host;
        this.port = port;
        this.database = database;
        this.user = user;
        this.password = password;
        this.table = table;
        this.dimension = dimension;
    }

    @Override
    public void open(Configuration parameters) throws Exception {
        try {
            Class.forName("org.postgresql.Driver");
            connection = DriverManager.getConnection(
                    String.format("jdbc:postgresql://%s:%d/%s", host, port, database),
                    user,
                    password
            );

            // Create table if not exists
            String createTableSQL = String.format(
                    "CREATE TABLE IF NOT EXISTS %s (" +
                            "id TEXT PRIMARY KEY," +
                            "text TEXT NOT NULL," +
                            "embedding vector(%d) NOT NULL," +
                            "created_at TIMESTAMP WITH TIME ZONE NOT NULL," +
                            "processed_at TIMESTAMP WITH TIME ZONE NOT NULL" +
                            ")", table, dimension);
            
            try (PreparedStatement createTable = connection.prepareStatement(createTableSQL)) {
                createTable.execute();
            }

            // Prepare insert statement
            String insertSQL = String.format(
                    "INSERT INTO %s (id, text, embedding, created_at, processed_at) " +
                            "VALUES (?, ?, ?::vector, ?, ?) " +
                            "ON CONFLICT (id) DO UPDATE SET " +
                            "text = EXCLUDED.text, " +
                            "embedding = EXCLUDED.embedding, " +
                            "created_at = EXCLUDED.created_at, " +
                            "processed_at = EXCLUDED.processed_at",
                    table);
            
            ps = connection.prepareStatement(insertSQL);
        } catch (Exception e) {
            LOG.error("Failed to initialize PgVector sink", e);
            throw e;
        }
    }

    @Override
    public void invoke(TextEmbedding value, Context context) throws Exception {
        try {
            ps.setString(1, value.getId());
            ps.setString(2, value.getText());
            // Serialize float[] embedding into PostgreSQL vector literal format
            float[] emb = value.getEmbedding();
            StringBuilder sb = new StringBuilder();
            sb.append('[');
            for (int i = 0; i < emb.length; i++) {
                if (i > 0) sb.append(',');
                sb.append(emb[i]);
            }
            sb.append(']');
            ps.setString(3, sb.toString());
            ps.setTimestamp(4, Timestamp.from(value.getTimestamp()));
            ps.setTimestamp(5, Timestamp.from(value.getProcessedAt()));
            
            ps.executeUpdate();
            LOG.info("Successfully stored embedding for message id: {}", value.getId());
        } catch (SQLException e) {
            LOG.error("Failed to store embedding for message id: " + value.getId(), e);
            throw e;
        }
    }

    @Override
    public void close() throws Exception {
        if (ps != null) {
            ps.close();
        }
        if (connection != null) {
            connection.close();
        }
    }
}
