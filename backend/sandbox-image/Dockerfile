# Development sandbox for the built-in developer engine and the eval suite.
# Python + Node.js with the test tools tasks need, so runs don't download packages.
# Build: docker build -t medhkarm-sandbox:dev backend/sandbox-image
FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest fastapi httpx2 pydantic

WORKDIR /workspace
