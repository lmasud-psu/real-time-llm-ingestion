#!/bin/bash

# Create a processed config file
envsubst < /app/config.yaml > /app/config_processed.yaml

# Start the writer service with the processed config
python /app/app.py -c /app/config_processed.yaml
