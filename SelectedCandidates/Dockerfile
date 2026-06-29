# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — RedRob Top-100 Streamlit Dashboard
#
# Build context: SelectedCandidates/   (run: docker compose build)
# Image purpose: Serve the Top-100 Candidates analytics dashboard
#
# The dashboard reads two pre-generated files that are baked into the image:
#   /app/outputs/top_100_candidates.csv
#   /app/outputs/top_100_explanations.json
#
# To rebuild the outputs from scratch, run the pipeline locally first
# (python run_pipeline.py) then rebuild this image.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Install dependencies ────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /install

# Copy only the lightweight dashboard requirements
COPY requirements-dashboard.txt .

# Install into a prefix so we can copy cleanly in the next stage
RUN pip install --no-cache-dir --prefix=/install/pkg -r requirements-dashboard.txt


# ── Stage 2: Runtime image ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy installed packages from builder
COPY --from=builder /install/pkg /usr/local

# Create a non-root user for security
RUN useradd --uid 8888 --create-home appuser

WORKDIR /app

# ── Copy only what the dashboard needs ───────────────────────────────────────
# 1. The Streamlit app itself
COPY app/               ./app/

# 2. Pre-generated pipeline outputs (CSV + JSON)
#    These are baked into the image at build time.
#    Mount a volume at /app/outputs to override at runtime.
COPY outputs/           ./outputs/

# Give ownership to the non-root user
RUN chown -R appuser:appuser /app

USER appuser

# Streamlit port
EXPOSE 8501

# Streamlit configuration: disable the telemetry prompt and set server options
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_THEME_BASE=dark

# Health-check so Docker knows when the app is ready
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Default: launch the dashboard
CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
