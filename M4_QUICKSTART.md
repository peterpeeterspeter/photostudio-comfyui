# 🚀 M4 MacBook Quick Start

## One-Command Setup

```bash
# Clone the repo
git clone https://github.com/peterpeeterspeter/photostudio-comfyui.git
cd photostudio-comfyui

# Setup environment
python3 -m venv venv && source venv/bin/activate
cd ComfyUI && pip install -r requirements.txt && cd ..

# Download models (8.4GB - will take a few minutes)
python scripts/model_manager.py

# Install custom nodes
cp custom_nodes/*.py ComfyUI/custom_nodes/

# Copy test files
cp input/* ComfyUI/input/

# Start ComfyUI (GPU accelerated on M4)
cd ComfyUI && python main.py --listen --port 8188
```

## Test Generation

In a new terminal:
```bash
cd photostudio-comfyui
source venv/bin/activate
python debug_workflow.py
```

**Expected Result**: Ghost mannequin image generated in 30-60 seconds, saved to `ComfyUI/output/`

## Success Indicators

✅ ComfyUI starts with "Import times for custom nodes" showing load_facts_node.py and prompt_builder.py  
✅ Models download successfully (8.4GB total)  
✅ Workflow completes in under 60 seconds  
✅ Output image appears in `ComfyUI/output/simple_test_*.png`

---

**Full documentation**: [README_DEPLOYMENT.md](README_DEPLOYMENT.md)