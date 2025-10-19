# 🚀 Production Deployment Guide

Complete guide for deploying the Photostudio ComfyUI ghost mannequin generation system to production environments.

## Overview

This deployment setup provides:
- **Scalable ghost mannequin generation** with ComfyUI
- **GPU-accelerated processing** with NVIDIA CUDA
- **Automated model management** and downloads
- **Production-grade monitoring** and logging
- **Docker containerization** for easy deployment
- **Batch processing capabilities** with comprehensive reporting

## Prerequisites

### Hardware Requirements

**Minimum Production Setup:**
- **CPU:** 8+ cores, 16+ threads
- **RAM:** 32GB+ system memory
- **GPU:** NVIDIA GPU with 8GB+ VRAM (RTX 3070/4070 or better)
- **Storage:** 500GB+ SSD storage
- **Network:** Gigabit ethernet

**Recommended Production Setup:**
- **CPU:** 16+ cores (Intel Xeon/AMD EPYC)
- **RAM:** 64GB+ system memory
- **GPU:** NVIDIA RTX A4000/A5000 or RTX 4080/4090 (16GB+ VRAM)
- **Storage:** 1TB+ NVMe SSD
- **Network:** 10Gbps network for high-throughput scenarios

### Software Requirements

- **Docker** 20.10+ with GPU support
- **Docker Compose** 2.0+
- **NVIDIA Container Toolkit**
- **Ubuntu 20.04/22.04** or **CentOS 8+**

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/photostudio/photostudio-comfyui.git
cd photostudio-comfyui
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
vim .env
```

**Required Environment Variables:**
```bash
# HuggingFace token for model downloads
HF_TOKEN=hf_your_token_here

# Webhook URL for notifications (optional)
WEBHOOK_URL=https://your-webhook-url.com/notify

# Data directories (will be created if they don't exist)
MODELS_PATH=/data/comfyui/models
INPUT_PATH=/data/comfyui/input
OUTPUT_PATH=/data/comfyui/output
LOGS_PATH=/data/comfyui/logs
BACKUPS_PATH=/data/comfyui/backups

# Grafana admin password (if using monitoring)
GRAFANA_ADMIN_PASSWORD=secure_password_here
```

### 3. Create Data Directories

```bash
sudo mkdir -p /data/comfyui/{models,input,output,logs,backups}
sudo chown -R $USER:$USER /data/comfyui
```

### 4. Build and Start Services

```bash
# Build the ComfyUI image
docker-compose build

# Start core ComfyUI service
docker-compose up -d comfyui

# Or start with monitoring stack
docker-compose --profile with-monitoring up -d
```

### 5. Verify Deployment

```bash
# Check service health
docker-compose ps

# Check logs
docker-compose logs -f comfyui

# Test API endpoint
curl http://localhost:8188/health
```

## Advanced Deployment Options

### High Availability Setup

For production environments requiring high availability:

```yaml
# docker-compose.ha.yml
services:
  comfyui:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
      placement:
        constraints:
          - node.labels.gpu==true
```

### Load Balancer Configuration

```bash
# Start with Nginx load balancer
docker-compose --profile with-nginx up -d
```

### Monitoring Stack

```bash
# Start with full monitoring
docker-compose --profile with-monitoring up -d

# Access Grafana dashboard
open http://localhost:3000
# Login: admin / <GRAFANA_ADMIN_PASSWORD>
```

## API Usage

### Single Image Processing

```bash
# Process single garment image
curl -X POST http://localhost:8188/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "input_image": "garment001.jpg",
    "facts_file": "garment001_facts.json",
    "workflow": "ghostmannequin_comfyui_v1.json"
  }'
```

### Batch Processing

```bash
# Submit batch processing job
python scripts/batch_processor.py \
  --input-dir /data/input/batch_001 \
  --output-dir /data/output/batch_001 \
  --concurrency 4
```

### Programmatic Integration

```python
import asyncio
from scripts.run_comfy import run_ghost_mannequin_workflow

# Process single item
results = asyncio.run(
    run_ghost_mannequin_workflow(
        workflow_path="workflows/ghostmannequin_comfyui_v1.json",
        input_image="input/dress_001.jpg",
        facts_file="input/dress_001_facts.json",
        server_address="localhost:8188"
    )
)

print(f"Generated images: {results}")
```

## Operations

### Model Management

```bash
# Check model status
python scripts/model_manager.py --status

# Download required models
python scripts/model_manager.py --setup-ghost-mannequin

# Verify model integrity
python scripts/model_manager.py --verify
```

### Log Management

```bash
# View live logs
docker-compose logs -f comfyui

# Export logs for analysis
docker cp photostudio-comfyui:/app/logs ./exported-logs

# Log rotation (automatically handled)
# Logs are rotated at 100MB with 10 backup files
```

### Performance Monitoring

```bash
# Check resource usage
docker stats photostudio-comfyui

# Monitor GPU usage
nvidia-smi -l 1

# Check queue status
curl http://localhost:8188/queue | jq .
```

### Backup and Recovery

```bash
# Backup configuration
docker exec photostudio-comfyui python scripts/backup_config.py

# Backup models (optional - models can be re-downloaded)
docker exec photostudio-comfyui tar -czf /app/backups/models.tar.gz /app/ComfyUI/models/

# Restore from backup
docker exec photostudio-comfyui tar -xzf /app/backups/models.tar.gz -C /
```

## Scaling

### Horizontal Scaling

```bash
# Scale ComfyUI instances
docker-compose up --scale comfyui=3

# Use external load balancer (HAProxy/Nginx)
# Configure round-robin to multiple instances
```

### GPU Multi-Instance

```yaml
# Use MIG (Multi-Instance GPU) for A100
services:
  comfyui-worker-1:
    environment:
      - CUDA_VISIBLE_DEVICES=0
  comfyui-worker-2:
    environment:
      - CUDA_VISIBLE_DEVICES=1
```

## Security

### Network Security

```bash
# Use firewall to restrict access
sudo ufw allow from <trusted-ip> to any port 8188
sudo ufw deny 8188

# Enable HTTPS with Let's Encrypt
certbot certonly --webroot -w /var/www/html -d your-domain.com
```

### API Security

```yaml
# Add API authentication
environment:
  - API_KEY=your-secure-api-key
  - ENABLE_AUTH=true
```

### Container Security

```bash
# Run security scan
docker scan photostudio/comfyui:latest

# Update base images regularly
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Common Issues

**GPU Not Detected:**
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi

# Verify Docker GPU support
docker info | grep -i runtime
```

**Out of Memory Errors:**
```bash
# Use memory optimization
docker-compose exec comfyui python ComfyUI/main.py --lowvram

# Or CPU-only mode
docker-compose exec comfyui python ComfyUI/main.py --cpu
```

**Model Download Failures:**
```bash
# Check HuggingFace token
echo $HF_TOKEN

# Manual model download
docker-compose exec comfyui python scripts/model_manager.py --setup-ghost-mannequin --force
```

**Performance Issues:**
```bash
# Check resource limits
docker stats

# Monitor GPU utilization
nvidia-smi dmon

# Check disk I/O
iotop
```

### Log Analysis

```bash
# Search for errors
docker-compose logs comfyui | grep ERROR

# Monitor workflow execution
docker-compose logs -f comfyui | grep "workflow\|prompt"

# Export structured logs
docker-compose logs --no-color comfyui > comfyui.log
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor disk usage and clean temporary files
- Check error logs for issues
- Verify batch processing completion

**Weekly:**
- Update ComfyUI and custom nodes
- Backup configuration and critical data
- Review performance metrics

**Monthly:**
- Update Docker images and security patches
- Review and archive old logs
- Validate model integrity

### Updates

```bash
# Update ComfyUI
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Update Docker images
docker-compose pull
docker-compose up -d
```

## Performance Benchmarks

### Expected Performance

**Single Image Processing:**
- **RTX 4090:** ~15-25 seconds per image (SDXL, 20 steps)
- **RTX 4080:** ~20-30 seconds per image
- **RTX 3080:** ~25-40 seconds per image

**Batch Processing:**
- **4x RTX 4090:** ~500-800 images/hour
- **2x RTX 4080:** ~300-500 images/hour
- **1x RTX 4090:** ~150-250 images/hour

### Optimization Tips

1. **Use appropriate batch concurrency** based on VRAM
2. **Enable model caching** for repeated workflows
3. **Use SSD storage** for input/output operations
4. **Optimize image resolution** for your use case
5. **Use `--lowvram`** for GPUs with <12GB VRAM

## Support

For deployment issues:

1. **Check logs:** `docker-compose logs comfyui`
2. **Verify configuration:** Review config files
3. **Test connectivity:** `curl http://localhost:8188/health`
4. **Review documentation:** Check WARP.md and README.md

---

🎉 **Your ComfyUI ghost mannequin generation system is now ready for production!**