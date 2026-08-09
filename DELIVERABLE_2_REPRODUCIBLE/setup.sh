# setup.sh — One command to reproduce everything
#!/bin/bash
set -e

echo "=========================================="
echo "Hospital Timeline AI — Setup"
echo "=========================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker recommended"; exit 1; }

# Backend setup
echo ""
echo "[1/5] Setting up backend..."
cd backend
pip install -r requirements.txt
python -m app.db.loader ../data/mimiciv
cd ..

# Frontend setup
echo ""
echo "[2/5] Setting up frontend..."
cd frontend
npm install
cd ..

# Start backend
echo ""
echo "[3/5] Starting backend on :8000..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!
cd ..

# Start frontend
echo ""
echo "[4/5] Starting frontend on :5173..."
cd frontend
npm run dev &
FRONT_PID=$!
cd ..

echo ""
echo "[5/5] Done!"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
wait