# syntax=docker/dockerfile:1
# Terminal Zero Governance Control Plane
# Multi-stage build — pins python:3.12-slim in BOTH stages.
# Do NOT change to python:3-slim or python:latest; PYTHONPATH relies on 3.12.

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only what pip needs to install the package
COPY pyproject.toml constraints.txt ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install the full package (entrypoint + all sop.scripts.* modules) into /install
# Using --prefix so the runtime stage can copy a self-contained tree.
RUN pip install --no-cache-dir --prefix=/install .

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for container security
RUN groupadd --system governance && useradd --system --gid governance governance

# Copy installed package tree from builder
COPY --from=builder /install /install

# Make the installed sop entrypoint and Python packages visible
ENV PATH=/install/bin:$PATH \
    PYTHONPATH=/install/lib/python3.12/site-packages

# Default working directory — operators volume-mount their repo here
WORKDIR /workspace

# Switch to non-root user
USER governance

# Docker daemon health probe (separate from CMD)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD sop healthcheck

# Default command when no arguments are passed
CMD ["--help"]
