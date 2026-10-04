# Development sandbox for the built-in developer engine and the eval suite.
# Python + Node.js with the test tools tasks need, so runs don't download packages.
# Build: docker build -t medhkarm-sandbox:3 backend/sandbox-image (the worker builds it if missing)
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest fastapi httpx2 pydantic

# Code graph for the codebase map and explain_symbol (CODE_GRAPH=true); tree-sitter, no models
RUN pip install --no-cache-dir graphifyy==0.9.73

# Security engineer (Vikram): Semgrep with our offline rules, pip-audit for Python dependencies
RUN pip install --no-cache-dir semgrep==1.179.0 pip-audit==2.10.1
COPY semgrep.yml /opt/medhkarm/semgrep.yml

# QA (Tara): browser tests for web apps with Playwright and headless Chromium (adds ~1.6 GB)
RUN pip install --no-cache-dir playwright==1.63.0 pytest-playwright==0.9.0 uvicorn \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
