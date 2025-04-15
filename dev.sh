#!/bin/bash

echo "🛑 Stopping any running containers..."
docker compose down

echo "🧹 Pruning unused Docker resources..."
docker system prune -af --volumes

echo "🔨 Rebuilding Docker image from scratch..."
docker compose build --no-cache

echo "🚀 Starting STT server..."
docker compose up
