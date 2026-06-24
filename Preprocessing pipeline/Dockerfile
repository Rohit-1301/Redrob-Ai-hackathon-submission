# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables to optimize Python performance inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application directories and files
COPY configs/ ./configs/
COPY validators/ ./validators/
COPY scoring/ ./scoring/
COPY hover_details_builder.py .
COPY preprocess.py .

# Create directories for mounting data and outputs
RUN mkdir -p /app/data /app/output

# Set entrypoint to run the preprocessing script
ENTRYPOINT ["python", "preprocess.py"]

# Default command-line arguments to preprocess (expects files to be mounted)
CMD ["/app/data/candidates.jsonl", "/app/output"]
