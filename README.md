# Ghost Mannequin Generation System

Complete ComfyUI-based system for generating professional ghost mannequin images using SDXL + custom Photostudio nodes.

## 🚀 **Ready to Deploy on M4 MacBook**

**👉 See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for complete M4 setup guide**

This repo is fully isolated from production systems and ready for deployment.

## Structure

```
📂 workflows/     – Node graphs (.json) for ComfyUI
📂 custom_nodes/  – Python nodes extending ComfyUI (e.g. LoadFactsNode)
📂 scripts/       – Automation scripts (run_comfy.py)
📂 input/         – Input JSON / garment images
📂 output/        – Generated results
📂 ComfyUI/       – Cloned ComfyUI engine
```

## Getting Started

```bash
python3 -m venv venv  
source venv/bin/activate  
pip install torch torchvision torchaudio  
cd ComfyUI && pip install -r requirements.txt  
python main.py  
```

## Development Workflow

1. **Start ComfyUI Server**
   ```bash
   source venv/bin/activate
   python ComfyUI/main.py --listen --port 8188
   ```

2. **Access Web Interface**
   - Open `http://localhost:8188` in your browser
   - Load workflows from `workflows/` directory
   - Experiment with ghost mannequin processing

3. **Custom Node Development**
   - Add new nodes to `custom_nodes/`
   - Follow ComfyUI node interface patterns
   - Define `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`

4. **Workflow Export**
   - Design workflows in the web interface
   - Export as JSON to `workflows/` directory
   - Test programmatic execution via API

## Memory Management

For different hardware configurations:

```bash
# Standard GPU (8GB+ VRAM)
python ComfyUI/main.py

# Limited GPU memory (4-8GB VRAM)
python ComfyUI/main.py --lowvram

# CPU-only processing
python ComfyUI/main.py --cpu

# Minimal VRAM usage
python ComfyUI/main.py --novram
```

## Model Setup

Models should be placed in:
- Checkpoints: `ComfyUI/models/checkpoints/`
- VAE: `ComfyUI/models/vae/`
- ControlNet: `ComfyUI/models/controlnet/`
- LoRA: `ComfyUI/models/loras/`

Copy `ComfyUI/extra_model_paths.yaml.example` to `ComfyUI/extra_model_paths.yaml` to configure additional model search paths.

## API Usage

ComfyUI provides a REST API for programmatic control:

```bash
# Queue a workflow
curl -X POST http://localhost:8188/prompt \
  -H "Content-Type: application/json" \
  -d @workflows/ghostmannequin_comfyui_v1.json

# Check queue status
curl http://localhost:8188/queue
```

## Development Tools

```bash
# Lint code using ruff
cd ComfyUI && python -m ruff check .

# Run custom automation scripts
python scripts/run_comfy.py
```

## Requirements

- Python 3.11+ (3.9+ supported)
- PyTorch with CUDA support (for GPU acceleration)
- 8GB+ system RAM recommended
- GPU with 4GB+ VRAM recommended (CPU fallback available)

---

For detailed development guidance, see [WARP.md](./WARP.md).
