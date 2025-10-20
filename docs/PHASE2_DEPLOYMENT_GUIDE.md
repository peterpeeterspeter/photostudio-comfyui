# Phase 2 Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Phase 2 Ghost Mannequin Pipeline with real components, including GroundingDINO, SAM2, FLUX, and Gemini integration.

## Prerequisites

- **Hardware**: Mac M4 Max 16GB RAM (or equivalent)
- **Software**: Python 3.11+, ComfyUI, PyTorch 2.2+
- **Storage**: ~20GB free space for models
- **Network**: Stable internet for model downloads

## Installation Steps

### 1. Install ComfyUI Extensions

```bash
cd ComfyUI/custom_nodes

# Install SAM2 extension
git clone https://github.com/neverbiasu/ComfyUI-SAM2.git
cd ComfyUI-SAM2
pip install -r requirements.txt

# Install RMBG extension (includes GroundingDINO)
cd ..
git clone https://github.com/1038lab/ComfyUI-RMBG.git
cd ComfyUI-RMBG
pip install "transparent-background>=1.1.2" "segment-anything>=1.0" "groundingdino-py>=0.4.0"
```

### 2. Download Required Models

#### FLUX.1-dev Model (12GB)
```bash
cd ComfyUI/models/checkpoints
huggingface-cli download black-forest-labs/FLUX.1-dev flux1-dev.safetensors --local-dir . --local-dir-use-symlinks False
```

#### SAM2 Model (308MB)
```bash
cd ComfyUI/models/sam2
curl -L -o sam2_hiera_base_plus.pt https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt
```

#### IP-Adapter Model (666MB)
```bash
cd ComfyUI/models/ipadapter
curl -L -o ip-adapter_sdxl_vit-h.safetensors https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl_vit-h.safetensors
```

#### GroundingDINO Model (661MB)
```bash
cd ComfyUI/models/groundingdino
curl -L -o groundingdino_swint_ogc.pth https://huggingface.co/ShilongLiu/GroundingDINO/resolve/main/groundingdino_swint_ogc.pth
```

#### SDXL CLIP Models
```bash
cd ComfyUI/models/clip
curl -L -o clip_l.safetensors https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/text_encoder.safetensors
curl -L -o clip_g.safetensors https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/text_encoder_2.safetensors
```

### 3. Configure Environment

#### Set up Gemini API Key
```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
chmod 600 .env
```

#### Install Python Dependencies
```bash
pip install python-dotenv google-generativeai
```

### 4. Verify Installation

#### Check Model Files
```bash
# Verify all models are downloaded
ls -lh ComfyUI/models/checkpoints/flux1-dev.safetensors  # Should be ~12GB
ls -lh ComfyUI/models/sam2/sam2_hiera_base_plus.pt      # Should be ~308MB
ls -lh ComfyUI/models/ipadapter/ip-adapter_sdxl_vit-h.safetensors  # Should be ~666MB
ls -lh ComfyUI/models/groundingdino/groundingdino_swint_ogc.pth    # Should be ~661MB
ls -lh ComfyUI/models/clip/clip_*.safetensors           # Should be ~2.3GB each
```

#### Test Components
```bash
# Run component tests
python tests/test_phase2_components.py

# Run end-to-end tests
python tests/test_phase2_e2e.py
```

## Usage

### 1. Start ComfyUI

```bash
cd ComfyUI
python main.py --listen --port 8188 --lowvram
```

### 2. Load Phase 2 Workflow

1. Open ComfyUI in browser: `http://localhost:8188`
2. Load workflow: `workflows/phase2_production.json`
3. Set input image: `input/test_garment.jpg`
4. Set input facts: `input/test_garment_facts.json`
5. Click "Queue Prompt"

### 3. Batch Processing

```bash
# Run batch validation
python scripts/validate_phase2_production.py --save-report

# Process multiple garments
python scripts/batch_processor.py --input-dir input/garments --output-dir output/
```

## Configuration

### Memory Optimization (M4 Max)

```python
# In ComfyUI/model_management.py
def get_torch_device():
    return torch.device("mps")  # Use MPS for M4

def get_free_memory():
    return 16384  # 16GB RAM
```

### Quality Thresholds

```python
# In custom nodes
QA_THRESHOLDS = {
    "edge_sharpness": 0.8,
    "background_purity": 0.95,
    "color_delta_e": 5.0,
    "clip_adherence": 0.7,
    "constraint_check": 0.9
}
```

## Troubleshooting

### Common Issues

#### 1. FLUX Model Download Fails
```bash
# Try alternative download method
wget --continue -O flux1-dev.safetensors "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors"
```

#### 2. GroundingDINO Import Error
```bash
# Reinstall groundingdino-py
pip uninstall groundingdino-py
pip install groundingdino-py>=0.4.0
```

#### 3. SAM2 Model Not Found
```bash
# Check model path
ls -la ComfyUI/models/sam2/
# Should contain sam2_hiera_base_plus.pt
```

#### 4. Gemini API Errors
```bash
# Check API key
cat .env | grep GEMINI_API_KEY
# Verify key is valid at https://makersuite.google.com/app/apikey
```

#### 5. Memory Issues
```bash
# Use low VRAM mode
python main.py --lowvram --cpu
# Or reduce batch size in workflows
```

### Performance Optimization

#### 1. Model Caching
```python
# Enable model caching
import torch
torch.backends.mps.empty_cache()
```

#### 2. Batch Processing
```python
# Process multiple images efficiently
for image_path in image_paths:
    # Process single image
    result = process_single_image(image_path)
    # Clear cache between images
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
```

## Monitoring

### 1. System Resources
```bash
# Monitor memory usage
htop
# Monitor disk usage
df -h
```

### 2. ComfyUI Logs
```bash
# Check ComfyUI logs
tail -f ComfyUI/logs/comfyui.log
```

### 3. QA Metrics
```bash
# Generate QA report
python scripts/validate_phase2_production.py --save-report
```

## Production Deployment

### 1. Docker Deployment
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy ComfyUI
COPY ComfyUI/ /app/ComfyUI/
COPY custom_nodes/ /app/ComfyUI/custom_nodes/

# Set environment
ENV PYTHONPATH=/app/ComfyUI
WORKDIR /app/ComfyUI

# Start ComfyUI
CMD ["python", "main.py", "--listen", "--port", "8188"]
```

### 2. Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: phase2-pipeline
spec:
  replicas: 1
  selector:
    matchLabels:
      app: phase2-pipeline
  template:
    metadata:
      labels:
        app: phase2-pipeline
    spec:
      containers:
      - name: comfyui
        image: phase2-pipeline:latest
        ports:
        - containerPort: 8188
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
```

## Support

### Documentation
- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)
- [GroundingDINO Documentation](https://github.com/IDEA-Research/GroundingDINO)
- [SAM2 Documentation](https://github.com/facebookresearch/segment-anything-2)

### Community
- [ComfyUI Discord](https://discord.gg/comfyui)
- [GitHub Issues](https://github.com/your-repo/issues)

### Contact
- Email: support@photostudio.io
- Discord: #phase2-support

## Changelog

### Version 2.0.0 (Current)
- ✅ Real GroundingDINO + SAM2 integration
- ✅ FLUX.1-dev model support
- ✅ Gemini 2.5 Flash Lite integration
- ✅ IP-Adapter conditional processing
- ✅ Enhanced QA metrics
- ✅ Batch validation system

### Version 1.5.0 (Previous)
- ✅ Basic SDXL pipeline
- ✅ Mock components
- ✅ Light Facts schema
- ✅ Quality gates

## License

This project is licensed under the MIT License. See LICENSE file for details.