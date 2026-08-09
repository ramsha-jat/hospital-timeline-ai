.PHONY: setup backend frontend load-data test clean

setup:
    pip install -r backend/requirements.txt
    cd frontend && npm install

load-data:
    python -m backend.app.db.loader data/mimiciv

backend:
    cd backend && uvicorn app.main:app --reload --port 8000

frontend:
    cd frontend && npm run dev

test:
    curl -s http://localhost:8000/health | python -m json.tool
    curl -s http://localhost:8000/api/validation/census | python -m json.tool

clean:
    docker compose down -v
    find . -type d -name __pycache__ -exec rm -rf {} +