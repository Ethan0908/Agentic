FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:/root/.codex/bin:${PATH}" \
    CODEX_HOME="/root/.codex"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl ca-certificates bubblewrap \
    && rm -rf /var/lib/apt/lists/*

# Install Codex CLI in the backend container so the website pipeline can run
# account-authenticated `codex exec` using the mounted /root/.codex auth cache.
RUN curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
