#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# dev.sh — Start ResearchMind in full-stack development mode
# Frontend (Vite dev server @ :5173) + Backend (FastAPI @ :8000)
# ──────────────────────────────────────────────────────────────────────────────
set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       ResearchMind — Full-Stack Dev Mode                     ║"
echo "║  Frontend : http://localhost:5173  (Vite + HMR)              ║"
echo "║  Backend  : http://localhost:8000  (FastAPI + auto-reload)   ║"
echo "║  API Docs : http://localhost:8000/docs                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Install frontend deps if needed
if [ ! -d "frontend/node_modules" ]; then
  echo "→ Installing frontend dependencies…"
  (cd frontend && npm install)
fi

# 2. Install backend deps if needed
if ! python -c "import fastapi" 2>/dev/null; then
  echo "→ Installing backend dependencies…"
  pip install -r requirements.txt
fi

# 3. Start backend in background
echo "→ Starting FastAPI backend on :8000…"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 4. Start frontend dev server
echo "→ Starting Vite frontend on :5173…"
(cd frontend && npm run dev)

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null || true
