.PHONY: dev dev-backend dev-frontend install install-backend install-frontend build up down

# ── Desarrollo local ────────────────────────────────────────────────────────

dev-backend:
	cd . && python -m uvicorn backend.api.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Instalación ─────────────────────────────────────────────────────────────

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

# ── Docker ──────────────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down
