.PHONY: run app docker-build docker-run docker-app docker-clean clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make run          - Run the candidate ranking pipeline locally"
	@echo "  make app          - Run the Streamlit interactive dashboard locally"
	@echo "  make docker-build - Build the Docker image for the pipeline"
	@echo "  make docker-run   - Run the ranking pipeline in a Docker container"
	@echo "  make docker-app   - Start the Streamlit dashboard in Docker"
	@echo "  make docker-clean - Tear down Docker containers and clean volumes"
	@echo "  make clean        - Clean local outputs, logs, and embedding caches"

run:
	python run_pipeline.py

app:
	streamlit run app/streamlit_app.py

docker-build:
	docker compose build

docker-run:
	docker compose run --rm pipeline

docker-app:
	docker compose up dashboard

docker-clean:
	docker compose down -v --rmi local

clean:
	rm -rf outputs/* reports/* logs/*
	rm -f models/embeddings.pkl models/faiss/index.faiss
