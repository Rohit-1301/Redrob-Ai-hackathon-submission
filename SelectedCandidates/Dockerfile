# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables to optimize Python performance
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HF_HOME=/app/models/hf_cache

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY SelectedCandidates/requirements.txt /app/SelectedCandidates/requirements.txt
RUN pip install --no-cache-dir -r /app/SelectedCandidates/requirements.txt

# Pre-cache the semantic embedding model in the image to run fully offline
RUN mkdir -p /app/models/hf_cache && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Copy the application files and configurations
COPY configs/ /app/configs/
COPY Redrobsdataset/ /app/Redrobsdataset/
COPY Preprocessing\ pipeline/ /app/Preprocessing\ pipeline/
COPY SelectedCandidates/ /app/SelectedCandidates/

# Create a non-root user and assign ownership of the app directory
RUN useradd -u 8888 appuser && \
    chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Default command runs the entire scoring & ranking pipeline
CMD ["python", "SelectedCandidates/run_pipeline.py"]
