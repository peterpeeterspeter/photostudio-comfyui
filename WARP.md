# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Photostudio ComfyUI R&D repository that includes:
- A complete ComfyUI installation as a submodule/directory
- Custom nodes for photostudio-specific functionality
- Workflow templates for ghost mannequin processing
- Python scripts for ComfyUI automation

## Development Environment Setup

### Python Environment
- Python 3.11+ required (ComfyUI supports 3.9+, but 3.11+ recommended)
- Virtual environment is located in `venv/` directory
- Activate with: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)

### Dependencies
- Main dependencies are in `ComfyUI/requirements.txt`
- Includes PyTorch, transformers, PIL, and ComfyUI-specific packages
- Custom nodes may have additional requirements

## Common Commands

### Running ComfyUI
```bash
# Activate virtual environment
source venv/bin/activate

# Run ComfyUI server
python ComfyUI/main.py

# Run with specific options
python ComfyUI/main.py --listen --port 8188

# CPU-only mode
python ComfyUI/main.py --cpu
```

### Custom Script Execution
```bash
# Run custom ComfyUI script
python scripts/run_comfy.py
```

### Development and Testing
```bash
# Lint code using ruff (based on ComfyUI's pyproject.toml)
cd ComfyUI && python -m ruff check .

# Run with specific GPU memory settings
python ComfyUI/main.py --lowvram  # For GPUs with limited VRAM
python ComfyUI/main.py --novram   # Offload everything to CPU memory
```

## Architecture

### Directory Structure
- `ComfyUI/` - Complete ComfyUI installation with core functionality
- `custom_nodes/` - Project-specific custom nodes:
  - `load_facts_node.py` - Custom node for loading facts/data
  - `prompt_builder.py` - Custom node for building prompts
- `scripts/` - Automation and utility scripts:
  - `run_comfy.py` - Script for running ComfyUI programmatically
- `workflows/` - Workflow templates and configurations:
  - `ghostmannequin_comfyui_v1.json` - Ghost mannequin processing workflow
- `input/` - Input files for processing
- `output/` - Generated outputs
- `venv/` - Python virtual environment

### ComfyUI Architecture
ComfyUI uses a node-based graph system where:
- Workflows are defined as JSON graphs with nodes and connections
- Each node performs a specific operation (load model, generate image, etc.)
- The execution system automatically determines dependencies and runs efficiently
- Models are loaded on-demand and cached in GPU/CPU memory as needed

### Custom Nodes
Custom nodes extend ComfyUI's functionality:
- Located in `custom_nodes/` directory
- Must follow ComfyUI's node interface patterns
- Should define `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`
- Can implement custom processing logic for photostudio workflows

## Key Files

### Configuration
- `ComfyUI/extra_model_paths.yaml.example` - Template for configuring model search paths
- `ComfyUI/pyproject.toml` - Build configuration and linting rules

### Entry Points  
- `ComfyUI/main.py` - Main server entry point
- `ComfyUI/server.py` - Web server implementation
- `scripts/run_comfy.py` - Custom execution script

### Workflows
- JSON files in `workflows/` define complete processing pipelines
- Can be loaded into ComfyUI web interface or executed programmatically
- `ghostmannequin_comfyui_v1.json` contains the ghost mannequin processing workflow

## Model Management

Models should be placed in the ComfyUI models directory structure:
- Checkpoints: `ComfyUI/models/checkpoints/`
- VAE: `ComfyUI/models/vae/`
- ControlNet: `ComfyUI/models/controlnet/`
- LoRA: `ComfyUI/models/loras/`

Use `ComfyUI/extra_model_paths.yaml` to configure additional search paths.

## Development Notes

### Memory Management
- ComfyUI automatically manages GPU memory and model offloading
- Use `--lowvram` for GPUs with <6GB VRAM
- Use `--novram` to run entirely on CPU memory

### Workflow Development
- Workflows can be developed in the web interface and exported as JSON
- JSON workflows can be executed programmatically via the API
- Custom nodes should integrate seamlessly with the web interface

### API Usage
- ComfyUI provides a REST API for programmatic control
- Default server runs on `http://localhost:8188`
- API endpoints include `/prompt` for workflow execution and `/queue` for status