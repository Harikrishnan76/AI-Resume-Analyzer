#!/usr/bin/env bash
# ──────────────────────────────────────────────
# AI Resume Analyzer — Start All Services
# ──────────────────────────────────────────────
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 AI Resume Analyzer — Starting Services${NC}"
echo "──────────────────────────────────────────────"

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}   Please edit .env with your settings.${NC}"
fi

# Ensure upload directory exists
mkdir -p data/uploads

# Kill any stale processes on our ports
echo -e "${YELLOW}🧹 Cleaning up stale processes...${NC}"
fuser -k 8000/tcp 2>/dev/null && echo "   Freed port 8000" || true
fuser -k 8501/tcp 2>/dev/null && echo "   Freed port 8501" || true
sleep 1

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ All services stopped.${NC}"
}
trap cleanup EXIT INT TERM

# Start FastAPI backend
echo -e "${BLUE}📡 Starting FastAPI backend on http://localhost:8000${NC}"
cd "$PROJECT_ROOT"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 2

# Start Streamlit frontend
echo -e "${BLUE}🖥️  Starting Streamlit frontend on http://localhost:8501${NC}"
cd "$PROJECT_ROOT"
python -m streamlit run frontend/app.py --server.port 8501 --server.headless true &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ All services running!${NC}"
echo -e "${GREEN}  📡 Backend API:   http://localhost:8000${NC}"
echo -e "${GREEN}  📡 API Docs:      http://localhost:8000/docs${NC}"
echo -e "${GREEN}  🖥️  Frontend:      http://localhost:8501${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for any process to exit
wait
