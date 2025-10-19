# Ghost Mannequin Generation System - M4 Deployment Guide

## 🚀 Quick Start for M4 MacBook

This system generates professional ghost mannequin images using ComfyUI + SDXL with custom Photostudio nodes.

### 1. Clone and Setup

```bash
git clone https://github.com/peterpeeterspeter/photostudio-comfyui.git
cd photostudio-comfyui

# Create virtual environment (Python 3.11+ required)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd ComfyUI && pip install -r requirements.txt
cd ..
```

### 2. Download Models (8.4GB total)

```bash
# Activate environment
source venv/bin/activate

# Download SDXL base model (6.94GB) + ControlNet (1.44GB)
python scripts/model_manager.py
```

### 3. Install Custom Nodes

```bash
# Copy custom nodes to ComfyUI
cp custom_nodes/*.py ComfyUI/custom_nodes/

# Verify installation
ls ComfyUI/custom_nodes/
# Should show: load_facts_node.py, prompt_builder.py, __init__.py
```

### 4. Prepare Input Files

```bash
# Copy test files to ComfyUI input directory
cp input/* ComfyUI/input/
```

### 5. Start ComfyUI Server

```bash
# For M4 MacBook (GPU acceleration)
cd ComfyUI && python main.py --listen --port 8188

# Server will be available at: http://localhost:8188
```

### 6. Run Ghost Mannequin Generation

**Option A: Simple Test**
```bash
# Run the simple test workflow
python debug_workflow.py
```

**Option B: Full API**
```bash
# Run with custom parameters
python scripts/run_comfy.py --workflow workflows/simple_test_workflow.json --input-image input/test_garment.jpg --server http://127.0.0.1:8188
```

### 7. View Results

```bash
# Check generated images
ls ComfyUI/output/
# Images will be named: simple_test_*.png
```

## 🏗️ System Architecture

### Custom Nodes
- **LoadFactsNode**: Parses FactsV3.json → garment descriptions
- **PromptBuilder**: Combines facts + CCJ → structured prompts with Chinese terms

### Workflow Pipeline
```
LoadImage → LoadFactsNode → PromptBuilder → SDXL → SaveImage
```

### Input Files Required
- `test_garment.jpg` - Source garment image
- `test_factsv3.json` - Garment metadata  
- `test_ccj_controlblock.json` - CCJ rendering parameters

## ⚡ Performance on M4

Expected performance with M4 GPU acceleration:
- **Image Generation**: 3-5 seconds/step (10 steps = 30-60 seconds)
- **Model Loading**: ~10-15 seconds first time
- **Memory Usage**: ~8-10GB RAM

## 🔧 Troubleshooting

### PyTorch Compatibility Fixed
The ComfyUI/comfy/ops.py file has been patched for PyTorch 2.2.2 compatibility. No action needed.

### Missing Input Files
If you get "File not found" errors:
```bash
cp input/* ComfyUI/input/
```

### Port Conflicts
If port 8188 is busy:
```bash
cd ComfyUI && python main.py --listen --port 8189
# Then use --server http://127.0.0.1:8189 in scripts
```

## 📦 Production Ready Features

### Batch Processing
```bash
python scripts/batch_processor.py input_directory/ output_directory/
```

### Docker Deployment
```bash
docker-compose up -d
# Access at http://localhost:8188
```

### API Integration
The system provides REST API endpoints for integration with other services.

## 🎯 Success Criteria

A successful deployment should:
1. Load both custom nodes without errors
2. Download models successfully (8.4GB)
3. Generate ghost mannequin images in <60 seconds
4. Save output images to ComfyUI/output/

## 📝 Next Steps After Deployment

1. **Test Generation**: Run simple workflow to verify everything works
2. **Quality Check**: Review generated ghost mannequin images
3. **Batch Testing**: Process multiple garments
4. **API Integration**: Connect to your production systems

---

**Note**: This R&D repo is separate from production systems. All changes stay here until ready for production integration.