# AI Project - CPU-only Docker image.
#
# Build:   docker build -t ai-project .
# Run:     docker run -p 7860:7860 -v ai_data:/app/data -v ai_logs:/app/logs ai-project
# Or:      docker compose up

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir \
        --index-url ${TORCH_INDEX_URL} \
        torch>=2.7.1
RUN pip install --no-cache-dir \
        -r requirements.txt

COPY . .

# Gradio 4 accepts theme/css on Blocks(), not Blocks.launch(). Keep this small
# compatibility rewrite until the UI source is migrated as a whole.
RUN python - <<'PY'
from pathlib import Path
p = Path('/app/src/webui/app.py')
s = p.read_text(encoding='utf-8')
s = s.replace('with gr.Blocks(title=WEBUI_TITLE) as demo:', 'with gr.Blocks(title=WEBUI_TITLE, theme=gr.themes.Soft(), css=".gradio-container { max-width: 1200px !important; }") as demo:')
s = s.replace('        theme=gr.themes.Soft(),\n        css="""\n        .gradio-container { max-width: 1200px !important; }\n        """,\n', '')
p.write_text(s, encoding='utf-8')
PY

RUN mkdir -p /app/data/uploads /app/logs /app/checkpoints

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    AI_PROJECT_ROOT=/app \
    WEBUI_HOST=0.0.0.0 \
    WEBUI_PORT=7860

EXPOSE 7860

# Start through the runtime compatibility bootstrap so the Gradio schema patch
# is guaranteed to be active before the project UI is imported.
CMD ["python", "-m", "webui_bootstrap"]
