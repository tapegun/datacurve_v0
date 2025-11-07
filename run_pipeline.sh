#!/usr/bin/env bash
set -e

TRACE_ID="1111-2222-3333"
BACKEND_PORT=8000
BACKEND_URL="http://localhost:${BACKEND_PORT}"
DB_FILE="telemetry.db"

echo "🚀 Starting full telemetry pipeline..."

# --- 1️⃣ Start backend server in background ---
echo "🟢 Launching FastAPI backend on port ${BACKEND_PORT}..."
uvicorn server:app --port ${BACKEND_PORT} --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# --- 2️⃣ Upload telemetry events ---
echo "📤 Uploading example trace events..."
python3 client_upload.py

# --- 3️⃣ Run validation ---
echo "🔍 Validating trace ${TRACE_ID}..."
python3 validate_trace.py ${TRACE_ID}

# --- 4️⃣ Cleanup ---
echo "🧹 Shutting down backend..."
kill $BACKEND_PID

echo "✅ Done!"
