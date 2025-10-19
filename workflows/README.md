# Ghost Mannequin ComfyUI Workflow Guide

## Overview

The `ghostmannequin_comfyui_v1.json` workflow provides a complete pipeline for generating professional ghost mannequin photos from garment images using AI.

## Workflow Architecture

### **18 Nodes | 22 Connections**

```
Input Image → LoadFactsNode → PromptBuilder → SDXL Generation → ControlNet → Output
     ↓              ↓             ↓              ↓              ↓          ↓
  [Node 1]      [Node 2]      [Node 3]       [Node 4]       [Node 8-10]  [Node 13]
```

### **Key Node Pipeline:**

1. **LoadImage** (Node 1) - Input garment photo
2. **LoadFactsNode** (Node 2) - Parse FactsV3.json garment data  
3. **PromptBuilder** (Node 3) - Generate structured rendering prompt
4. **CheckpointLoader** (Node 4) - Load SDXL base model
5. **ControlNet Pipeline** (Nodes 8-10) - Edge detection & control
6. **KSampler** (Node 11) - Generate ghost mannequin image
7. **VAEDecode + SaveImage** (Nodes 12-13) - Output final result

### **Additional Processing:**
- **Background Removal** (Node 18) - Clean white background
- **Image Blur/Refinement** (Node 17) - Edge softening  
- **Mask Generation** (Node 15) - Alpha channel processing
- **Inpainting Support** (Node 14) - Interior visibility

## Prerequisites

### **Models Required:**
```bash
ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors    # SDXL base model
ComfyUI/models/controlnet/control_v11p_sd15_canny.pth    # ControlNet Canny
```

### **Input Files Required:**
```bash
input/factsv3.json                    # Garment facts (FactsV3 format)
input/ccj_controlblock.json           # CCJ control parameters
input/input_garment.jpg               # Source garment image
```

### **Custom Nodes:**
- **LoadFactsNode** - Parse garment metadata
- **PromptBuilder** - Generate structured prompts

## Usage Instructions

### **1. Prepare Input Files**

**Garment Image:**
- Place your garment photo in `input/input_garment.jpg`
- Recommended: 1024x1024px or higher
- Format: JPG, PNG supported

**FactsV3 Data:**
```json
{
  "garment_type": "dress",
  "primary_color": "navy blue", 
  "primary_material": "cotton",
  "sleeve_length": "long",
  "neckline": "crew",
  "fit_type": "relaxed",
  "ghost_mannequin_requirements": {
    "interior_visibility_needed": true,
    "volume_preservation": "high",
    "drape_natural": true,
    "symmetry_critical": true,
    "edge_precision": "high"
  }
}
```

**CCJ ControlBlock:**
```json
{
  "core_contract": {
    "mandatory_specs": {
      "background": {"color": "#FFFFFF", "type": "solid"},
      "resolution": {"min_width": 2048, "min_height": 2048}
    },
    "forbidden_elements": ["visible mannequin", "harsh shadows"]
  },
  "rendering_hints": {
    "lighting": {"setup": "three-point studio"},
    "fabric_behavior": {"drape_weight": "natural"}
  }
}
```

### **2. Load Workflow in ComfyUI**

1. Start ComfyUI server:
   ```bash
   source venv/bin/activate
   python ComfyUI/main.py --listen --port 8188
   ```

2. Open `http://localhost:8188` in browser

3. Load workflow:
   - **Menu** → **Load** → Select `workflows/ghostmannequin_comfyui_v1.json`
   - Or drag the JSON file into the ComfyUI interface

### **3. Configure Parameters**

**Key Settings to Adjust:**

- **Node 2 (LoadFactsNode):**
  - `facts_file_path`: Path to your FactsV3.json

- **Node 3 (PromptBuilder):**
  - `ccj_path`: Path to CCJ ControlBlock  
  - `custom_additions`: Additional prompt text
  - `include_chinese`: Enable Chinese ghost mannequin terms

- **Node 11 (KSampler):**
  - `seed`: For reproducible results (42 = default)
  - `steps`: Generation steps (20 = balanced quality/speed)
  - `cfg`: Guidance scale (7.5 = recommended)

- **Node 13 (SaveImage):**
  - `filename_prefix`: Output file naming

### **4. Execute Workflow**

1. **Queue Prompt** - Click orange "Queue Prompt" button
2. **Monitor Progress** - Watch node execution in real-time
3. **View Results** - Generated images appear in `output/` directory

## Output Files

**Generated Images:**
- `output/ghost_mannequin_[timestamp].png` - Final ghost mannequin photo
- High-resolution (1024x1024+)
- Clean white background
- Professional studio lighting
- Invisible mannequin effect

## Customization Options

### **Prompt Customization:**
Edit Node 3 (PromptBuilder) inputs:
- Add specific styling instructions
- Include brand-specific requirements  
- Toggle Chinese terms for different AI models

### **Quality Settings:**
Adjust Node 11 (KSampler):
- Increase `steps` (20→30) for higher quality
- Adjust `cfg` (7.5→8.0) for stronger prompt adherence
- Change `sampler_name` for different generation styles

### **ControlNet Strength:**
Modify Node 10 (ControlNetApply):
- `strength`: 1.0 = full control, 0.5 = partial control
- `start_percent`/`end_percent`: Control application timing

## Troubleshooting

### **Common Issues:**

**"LoadFactsNode not found"**
- Ensure custom nodes are installed in `custom_nodes/`
- Restart ComfyUI after adding custom nodes

**"Model not found"**
- Download required models to correct directories
- Check model filenames match workflow configuration

**"Low quality output"**
- Increase KSampler steps (20→30)
- Verify input image quality (1024px+ recommended)
- Check FactsV3 data completeness

### **Performance Optimization:**

**GPU Memory:**
- Use `--lowvram` flag for 4-8GB VRAM
- Use `--cpu` for CPU-only processing

**Speed vs Quality:**
- Reduce steps for faster processing
- Use DPM++ SDE samplers for speed
- Lower resolution for testing (512x512)

## Integration with Production

This workflow is designed for:
- **E-commerce product photography**
- **Fashion catalog generation** 
- **Marketplace listing automation**
- **Brand consistency workflows**

The structured prompt system ensures consistent, professional results across different garment types and styles.

---

**Next Steps:** Ready for production ghost mannequin generation! 🚀