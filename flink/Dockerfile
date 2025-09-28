### Multi-stage Dockerfile for building and running the Java Flink job
# Stage 1: Build the fat JAR using Maven
FROM maven:3.8.6-openjdk-11 AS builder
WORKDIR /build
COPY pom.xml ./
COPY src ./src
RUN mvn -e -B -DskipTests clean package

# Stage 2: Use official Flink image as runtime base
FROM flink:1.17.2-scala_2.12-java11

# Put the job jar into flink's usrlib so flink run/submit can find it
COPY --from=builder /build/target/embedding-pipeline-1.0-SNAPSHOT.jar /opt/flink/usrlib/embedding-pipeline.jar

# Add an entrypoint wrapper that supports a 'submit' command to wait for JobManager then submit
COPY docker-entrypoint.sh /docker-entrypoint-flink.sh
RUN chmod +x /docker-entrypoint-flink.sh

ENTRYPOINT ["/docker-entrypoint-flink.sh"]
