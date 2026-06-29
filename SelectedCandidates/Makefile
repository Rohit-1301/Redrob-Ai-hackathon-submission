.PHONY: help build up down restart logs shell clean prune app

# ─────────────────────────────────────────────────────────────────────────────
# RedRob — Top-100 Candidates Dashboard
# All commands must be run from inside SelectedCandidates/
# ─────────────────────────────────────────────────────────────────────────────

IMAGE   = redrob-dashboard
SERVICE = dashboard
PORT    = 8501

## help   → show this message (default)
help:
	@echo ""
	@echo "  RedRob Dashboard — Docker Commands"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make build     Build (or rebuild) the Docker image"
	@echo "  make up        Build + start the dashboard in the foreground"
	@echo "  make up-bg     Build + start the dashboard in the background"
	@echo "  make down      Stop and remove the running container"
	@echo "  make restart   Restart the dashboard container"
	@echo "  make logs      Tail live container logs"
	@echo "  make shell     Open a bash shell inside the running container"
	@echo "  make clean     Stop container + remove image"
	@echo "  make prune     Remove ALL stopped containers and dangling images"
	@echo "  make app       Run the dashboard locally (no Docker)"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  Dashboard URL: http://localhost:$(PORT)"
	@echo ""

## build  → build the Docker image (uses cache; add --no-cache to force fresh)
build:
	docker compose build

## up     → build image if needed, then start dashboard (foreground)
up:
	docker compose up --build

## up-bg  → build image if needed, then start dashboard (background / detached)
up-bg:
	docker compose up --build -d
	@echo ""
	@echo "  Dashboard is starting..."
	@echo "  Open http://localhost:$(PORT) in your browser."
	@echo "  Use 'make logs' to tail the logs."
	@echo ""

## down   → stop and remove the container (data volumes kept)
down:
	docker compose down

## restart → restart the dashboard container without rebuilding
restart:
	docker compose restart $(SERVICE)

## logs   → stream container logs (Ctrl+C to exit)
logs:
	docker compose logs -f $(SERVICE)

## shell  → open an interactive bash shell inside the running container
shell:
	docker compose exec $(SERVICE) /bin/bash

## clean  → stop container and delete the local image
clean:
	docker compose down
	docker rmi $(IMAGE):latest 2>/dev/null || true
	@echo "Image removed."

## prune  → remove ALL stopped containers and dangling images (system-wide)
prune:
	docker system prune -f
	@echo "Docker system pruned."

## app    → run dashboard locally without Docker (requires local Python env)
app:
	streamlit run app/streamlit_app.py --server.port $(PORT)
