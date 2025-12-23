#!/bin/bash
# Startup script for Railway deployment
# Ensures PORT environment variable is properly handled

# Default to 8501 if PORT is not set
PORT="${PORT:-8501}"

echo "Starting Streamlit on port $PORT..."

exec streamlit run app/streamlit_app.py \
    --server.port="$PORT" \
    --server.address=0.0.0.0 \
    --server.headless=true
