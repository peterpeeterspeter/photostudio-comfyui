# Installation Guide - Photostudio.io Ghost Mannequin Pipeline

This guide will walk you through setting up the complete Photostudio.io pipeline for generating ghost mannequin product photos.

## 📋 Prerequisites

### System Requirements

- **Operating System**: macOS 10.15+, Ubuntu 20.04+, or Windows 10+
- **Python**: 3.11 or higher
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 20GB free space for models and dependencies
- **GPU**: Optional but recommended (CUDA-compatible or Apple Silicon)

### Software Dependencies

- Git
- Python 3.11+
- pip (Python package manager)

## 🚀 Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/photostudio-comfyui.git
cd photostudio-comfyui
```

### 2. Set Up Python Environment

#### Option A: Using pyenv (Recommended)

```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Install Python 3.11.8
pyenv install 3.11.8
pyenv local 3.11.8

# Verify installation
python --version  # Should show Python 3.11.8
```

#### Option B: Using venv

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install ComfyUI Dependencies

```bash
cd ComfyUI
pip install -r requirements.txt
```

**Key Dependencies:**
- `torch>=2.2.2` - PyTorch for AI models
- `torchvision` - Computer vision utilities
- `transformers` - Hugging Face transformers
- `accelerate` - Model acceleration
- `xformers` - Memory-efficient attention
- `opencv-python` - Image processing
- `Pillow` - Image manipulation
- `numpy` - Numerical computing
- `scikit-image` - Image processing algorithms

### 4. Install Enhanced Pipeline Dependencies

```bash
# Install additional dependencies for enhanced features
pip install torchmetrics>=1.0.0
pip install git+https://github.com/openai/CLIP.git
pip install u2net
pip install opencv-python>=4.8.0
```

### 5. Download Required Models

The pipeline requires several AI models. Download them to the appropriate directories:

#### SDXL Models
```bash
# Create models directory
mkdir -p ComfyUI/models/checkpoints

# Download SDXL base model (recommended: sd_xl_base_1.0.safetensors)
# Place in: ComfyUI/models/checkpoints/
```

#### ControlNet Models
```bash
# Create ControlNet directory
mkdir -p ComfyUI/models/controlnet

# Download ControlNet Canny model
# Place in: ComfyUI/models/controlnet/
```

#### VAE Models
```bash
# Create VAE directory
mkdir -p ComfyUI/models/vae

# Download SDXL VAE (recommended: sdxl_vae.safetensors)
# Place in: ComfyUI/models/vae/
```

### 6. Verify Installation

```bash
# Test custom nodes import
python test_custom_nodes.py

# Test basic ComfyUI functionality
cd ComfyUI
python main.py --help
```

## 🔧 Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# ComfyUI Configuration
COMFYUI_PORT=8188
COMFYUI_HOST=127.0.0.1

# Model Paths
MODEL_PATH=./ComfyUI/models
CHECKPOINT_PATH=./ComfyUI/models/checkpoints
CONTROLNET_PATH=./ComfyUI/models/controlnet
VAE_PATH=./ComfyUI/models/vae

# Performance Settings
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### 2. Pipeline Parameters

Edit `config/phase1_5_params.yaml` to customize pipeline behavior:

```yaml
# Segmentation settings
segmentation:
  rmbg_threshold: 0.3
  u2net_threshold: 0.35
  ensemble_weight_rmbg: 0.4
  ensemble_weight_u2net: 0.6

# Generation settings
generation:
  steps: 20
  cfg: 7.0
  sampler: "dpmpp_2m_karras"
  scheduler: "karras"

# Quality settings
quality:
  edge_ssim_threshold: 0.75
  bg_purity_threshold: 0.95
  color_delta_e_threshold: 3.0
```

## 🧪 Testing the Installation

### 1. Start ComfyUI

```bash
cd ComfyUI
python main.py --listen --port 8188
```

You should see output like:
```
Starting server
To see the GUI go to: http://0.0.0.0:8188
```

### 2. Test Basic Functionality

```bash
# In a new terminal
python test_phase1_5_workflow.py
```

Expected output:
```
🚀 Phase 1.5 Complete Workflow Test
✅ ComfyUI server is running
✅ All required custom node files present
✅ Loaded workflow: workflows/phase1_5_mvp_working.json
✅ Test input files present
✅ Prompt queued with ID: [prompt-id]
✅ Workflow executed successfully!
```

### 3. Test Custom Nodes

```bash
python test_custom_nodes.py
```

Expected output:
```
🔍 Testing Custom Node Imports...
✅ load_facts_node.LoadFactsNode imported successfully
✅ light_facts_prompt.PromptFromLightFacts imported successfully
✅ u2net_segmentation.u2net_node.U2NetSegmentation imported successfully
✅ mask_ensemble.MaskEnsemble imported successfully
✅ ip_adapter_conditional.IPAdapterConditional imported successfully
✅ controlnet_inpaint_polish.ControlNetInpaintPolish imported successfully
```

## 🐛 Troubleshooting

### Common Issues

#### 1. PyTorch Installation Issues

**Problem**: CUDA/GPU not detected
```bash
# Check PyTorch installation
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA support
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### 2. Model Loading Errors

**Problem**: Models not found
```bash
# Check model paths
ls -la ComfyUI/models/checkpoints/
ls -la ComfyUI/models/controlnet/
ls -la ComfyUI/models/vae/

# Download missing models
# (See model download section above)
```

#### 3. Custom Node Import Errors

**Problem**: Custom nodes not loading
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify custom node files exist
ls -la ComfyUI/custom_nodes/

# Test individual imports
python -c "import sys; sys.path.append('ComfyUI'); import load_facts_node"
```

#### 4. Memory Issues

**Problem**: Out of memory errors
```bash
# Reduce batch size in config
# Edit config/phase1_5_params.yaml
generation:
  batch_size: 1  # Reduce from default

# Use CPU offloading
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
```

### Performance Optimization

#### 1. GPU Acceleration

```bash
# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# For Apple Silicon Macs
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

#### 2. Memory Optimization

```bash
# Enable memory efficient attention
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Use xformers for attention optimization
pip install xformers
```

## 📚 Next Steps

After successful installation:

1. **Read the Quick Start Guide**: `QUICK_START.md`
2. **Explore Workflows**: Check `workflows/` directory
3. **Test with Sample Data**: Use `input/test_garment.jpg`
4. **Run Quality Validation**: Execute `scripts/quality_validator_enhanced.py`
5. **Review Documentation**: Read `docs/PHASE_1_5_STATUS.md`

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: ComfyUI outputs detailed error messages
2. **Review documentation**: `docs/` directory has detailed guides
3. **Test components**: Use individual test scripts to isolate issues
4. **Community support**: GitHub Issues and Discussions

## 🔄 Updates

To update the pipeline:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r ComfyUI/requirements.txt --upgrade

# Test after update
python test_phase1_5_workflow.py
```

---

**Installation complete!** You're ready to start generating professional ghost mannequin product photos.
