# AI Project - CPU-only Docker image.
#
# Build:   docker build -t ai-project .
# Run:     docker run -p 7860:7860 -v ai_data:/app/data -v ai_logs:/app/logs ai-project
# Or:      docker compose up
#
# Image size: ~1.8GB (CPU torch + gradio + python-docx + pypdf2).
# Works on:  any 64-bit Linux, macOS (with Docker Desktop), Windows (with Docker Desktop),
#            Raspberry Pi 4/5, cheap VPS, etc.

FROM python:3.11-slim

# System deps: build tools for some wheels + git for hf_hub_download fallback.
# We keep them in one layer so the image stays small after cleanup.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch: ~200MB instead of ~2GB for the CUDA build.
# Using the official CPU index keeps the install reproducible across platforms.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

WORKDIR /app

# Copy requirements first so Docker layer-caches the heavy pip install.
COPY requirements.txt .

# Install CPU torch separately to use the slim index, then everything else
# from the regular PyPI index. Two RUN steps so the torch layer caches
# independently of the rest.
RUN pip install --no-cache-dir \
        --index-url ${TORCH_INDEX_URL} \
        torch>=2.7.1
RUN pip install --no-cache-dir \
        -r requirements.txt

# Copy the rest of the project. .dockerignore keeps checkpoints and the
# virtualenv out of the image so it stays small.
COPY . .

# Pre-create writable directories for runtime artifacts.
RUN mkdir -p /app/data/uploads /app/logs /app/checkpoints

# Default env vars; can be overridden by `docker run -e ...` or compose.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AI_PROJECT_ROOT=/app \
    WEBUI_HOST=0.0.0.0 \
    WEBUI_PORT=7860

EXPOSE 7860

# Launch the Gradio web UI. The launcher imports the app module, which
# loads the RAG pipeline on first run (a few seconds).
CMD ["python", "-m", "webui_launcher"]
