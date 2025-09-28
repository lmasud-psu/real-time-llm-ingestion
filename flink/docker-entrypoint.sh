#!/bin/bash

if [ "$1" = "submit" ]; then
    echo "Waiting for JobManager to be ready..."
    until curl -s "${JOBMANAGER_HOST}:${JOBMANAGER_PORT}" > /dev/null; do
        echo "JobManager is unavailable - sleeping"
        sleep 2
    done
    echo "JobManager is up - submitting job"
    flink run -d /opt/flink/usrlib/embedding-pipeline.jar
else
    /docker-entrypoint.sh "$@"
fi
