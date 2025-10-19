# Production Dockerfile for Photostudio ComfyUI
# Optimized for GPU-accelerated ghost mannequin generation

FROM nvidia/cuda:11.8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgoogle-perftools4 \
    libtcmalloc-minimal4 \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app
RUN chown app:app /app

# Switch to app user
USER app

# Create Python virtual environment
RUN python3.11 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip and install base requirements
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY --chown=app:app ComfyUI/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Install additional production dependencies
RUN pip install \
    websockets \
    pyyaml \
    gunicorn \
    psutil \
    prometheus-client

# Copy application code
COPY --chown=app:app . /app/

# Create necessary directories
RUN mkdir -p /app/input \
             /app/output \
             /app/temp \
             /app/logs \
             /app/backups/config \
             /app/backups/output \
             /app/ComfyUI/models/checkpoints \
             /app/ComfyUI/models/controlnet \
             /app/ComfyUI/models/vae \
             /app/ComfyUI/models/loras

# Set permissions
RUN chmod +x /app/scripts/*.py

# Configure git for ComfyUI updates (if needed)
RUN git config --global user.name "ComfyUI App" && \
    git config --global user.email "app@photostudio.io"

# Environment variables for production
ENV COMFYUI_CONFIG_PATH="/app/config/production.yaml" \
    COMFYUI_LOG_LEVEL="INFO" \
    CUDA_VISIBLE_DEVICES="0" \
    PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512" \
    LD_PRELOAD="libtcmalloc_minimal.so.4"

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/health || exit 1

# Expose port
EXPOSE 8188

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Photostudio ComfyUI Production Server"
echo "=============================================="

# Check GPU availability
if nvidia-smi > /dev/null 2>&1; then
    echo "✅ GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)"
    GPU_ARGS=""
else
    echo "⚠️  No GPU detected, running in CPU mode"
    GPU_ARGS="--cpu"
fi

# Check and download models if needed
echo "📦 Checking required models..."
python scripts/model_manager.py --setup-ghost-mannequin --skip-optional

# Start ComfyUI server
echo "🌟 Starting ComfyUI server..."
exec python ComfyUI/main.py \
    --listen 0.0.0.0 \
    --port 8188 \
    $GPU_ARGS \
    "$@"
EOF

RUN chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]

# Labels for metadata
LABEL maintainer="photostudio.io" \
      version="1.0" \
      description="Production ComfyUI server for ghost mannequin generation" \
      com.photostudio.component="comfyui-server" \
      com.photostudio.environment="production"