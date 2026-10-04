# Development sandbox for the built-in developer engine and the eval suite.
# Python + Node.js with the test tools tasks need, so runs don't download packages.
# Build: docker build -t medhkarm-sandbox:4 backend/sandbox-image (the worker builds it if missing)
FROM node:22-slim AS node

FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 with npm and corepack (Debian's nodejs package has no npm)
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && ln -s ../lib/node_modules/corepack/dist/corepack.js /usr/local/bin/corepack

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

# Starters (backend/starters/): the Next.js starter's packages in the npm cache, so a new
# project installs in seconds without downloading. Copies of its package.json and lockfile
# (a test keeps them in step).
ENV npm_config_cache=/opt/medhkarm/npm-cache
COPY starter-deps /opt/medhkarm/starter-deps
RUN cd /opt/medhkarm/starter-deps/nextjs \
    && npm ci --no-audit --no-fund \
    && rm -rf node_modules \
    && chmod -R a+rwX /opt/medhkarm/npm-cache

WORKDIR /workspace
