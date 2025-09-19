FROM apache/flink:1.17.2-scala_2.12-java11

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip curl \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/flink/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/flink/requirements.txt

# Install Kafka connector jars required for PyFlink KafkaSource
RUN curl -fsSL https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/1.17.2/flink-connector-kafka-1.17.2.jar \
    -o /opt/flink/lib/flink-connector-kafka-1.17.2.jar \
    && curl -fsSL https://repo1.maven.org/maven2/org/apache/flink/flink-connector-base/1.17.2/flink-connector-base-1.17.2.jar \
    -o /opt/flink/lib/flink-connector-base-1.17.2.jar \
    && curl -fsSL https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.17.2/flink-sql-connector-kafka-1.17.2.jar \
    -o /opt/flink/lib/flink-sql-connector-kafka-1.17.2.jar \
    && curl -fsSL https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.2.3/kafka-clients-3.2.3.jar \
    -o /opt/flink/lib/kafka-clients-3.2.3.jar

WORKDIR /opt/flink

COPY embedding_job.py /opt/flink/jobs/embedding_job.py
COPY submit_job.sh /opt/flink/bin/submit_job.sh
RUN chmod +x /opt/flink/bin/submit_job.sh

USER flink

# Set Python-related environment variables
ENV FLINK_PYTHON=python3 \
    PYTHONUNBUFFERED=1 \
    PYTHON_BIN=/usr/bin/python3 \
    PATH=/usr/local/bin:/usr/bin:/bin:$PATH
