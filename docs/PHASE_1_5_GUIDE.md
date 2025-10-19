# Phase 1.5 Ghost Mannequin Pipeline Guide

## Overview

The Phase 1.5 Ghost Mannequin pipeline is a production-ready system for generating high-quality ghost mannequin images using ComfyUI, RMBG-1.4 segmentation, SDXL/FLUX generation, and automated quality gates.

## Architecture

```
Input Image → RMBG-1.4 Segmentation → Light Facts Analysis → 
Model Router (SDXL/FLUX) → ControlNet (Canny) → KSampler Generation → 
Quality Gates (Edge/BG) → Conditional Inpaint Polish → Output
```

## Target Metrics

- **Edge sharpness**: SSIM > 0.75
- **Color accuracy**: ΔE ≤ 3 (uni) / ≤ 5 (textured)
- **BG purity**: ≥ 95% white pixels > 250
- **Overall QA pass**: ≥ 85%

## Installation

### 1. Install Dependencies

```bash
# Install RMBG and quality validation dependencies
pip install rembg onnxruntime scikit-image colour-science

# Install ComfyUI requirements
cd ComfyUI
pip install -r requirements.txt
```

### 2. Download Models

Place models in the appropriate directories:

```
ComfyUI/models/
├── checkpoints/
│   └── sd_xl_base_1.0.safetensors
├── controlnet/
│   └── control_v11p_sd15_canny.pth
└── vae/
    └── (SDXL VAE files)
```

### 3. Start ComfyUI

```bash
cd ComfyUI
python main.py --listen --port 8188
```

## Usage

### Basic Workflow

1. **Load the complete workflow**: `workflows/phase1_5_complete.json`
2. **Set input image**: Place garment image in `input/` directory
3. **Configure facts**: Create Light Facts JSON file
4. **Run workflow**: Execute in ComfyUI interface

### Light Facts Schema

Create a JSON file with the following structure:

```json
{
  "schema_version": "3.1",
  "analysis_mode": "light",
  "garment": {
    "category": "oxford dress shirt",
    "silhouette": "tailored",
    "fabric": "mid-weight cotton twill",
    "finish": "matte",
    "color_hex": "#0A0A0A",
    "color_name": "near-black",
    "closures": "front button placket",
    "pockets_count": 1,
    "label_text": "ACME Fashions ©",
    "special_notes": "no hood; show interior neckline"
  },
  "photography": {
    "bg": "pure_white",
    "lighting": "soft_even_high_key",
    "frame": "4:5",
    "coverage_pct": 85
  },
  "routing": {
    "suggested_model": "sdxl"
  }
}
```

### Batch Processing

Use the batch processor for multiple images:

```bash
python scripts/batch_ghost_processor.py \
  --workflow workflows/phase1_5_complete.json \
  --input-dir input/images/ \
  --facts-dir input/facts/ \
  --output-dir output/ \
  --validate \
  --report-file processing_report.json
```

### Quality Validation

Run standalone quality validation:

```bash
python scripts/quality_validator.py \
  --output-dir output/ \
  --facts-dir input/facts/ \
  --output-report quality_report.json
```

## Node Reference

### Core Nodes

#### RMBGNode
- **Purpose**: Background removal and garment segmentation
- **Key Parameters**:
  - `threshold`: 0.30 (mask threshold)
  - `mask_blur`: 3 (edge smoothing)
  - `post_dilate`: 8 (halo removal)

#### PromptFromLightFacts
- **Purpose**: Generate structured prompts from Light Facts
- **Key Parameters**:
  - `prompt_style`: "detailed" (concise/detailed/technical)
  - `include_constraints`: true
  - `negative_boost`: 1.0

#### ModelRouter
- **Purpose**: Route between SDXL and FLUX models
- **Logic**: Analyzes garment characteristics for optimal model selection

#### QualityGateEdge
- **Purpose**: Assess edge quality using SSIM and alpha analysis
- **Thresholds**:
  - `ssim_threshold`: 0.75
  - `alpha_threshold`: 0.97

#### QualityGateBackground
- **Purpose**: Assess background purity and color consistency
- **Thresholds**:
  - `purity_threshold`: 0.95
  - `white_threshold`: 250.0

#### SmartInpaintPolish
- **Purpose**: Polish edges and correct color issues
- **Key Parameters**:
  - `denoise`: 0.35
  - `mask_dilate`: 12
  - `feather`: 3

### Utility Nodes

#### MaskDilation
- **Purpose**: Expand masks with feathering
- **Use Case**: Halo removal and edge refinement

#### MaskToAlphaBorder
- **Purpose**: Extract edge regions for analysis
- **Use Case**: Quality gate edge assessment

#### MaskStats
- **Purpose**: Calculate mask statistics
- **Use Case**: Quality monitoring and debugging

#### ConditionalSwitch
- **Purpose**: Route outputs based on conditions
- **Use Case**: Quality gate routing

## Configuration

### Core Parameters (`config/phase1_5_params.yaml`)

```yaml
segmentation:
  rmbg_threshold: 0.30
  mask_blur: 3
  post_dilate: 8

generation:
  steps: 24
  cfg: 6.5
  sampler: "dpmpp_2m_karras"

quality_thresholds:
  edge_ssim_min: 0.75
  bg_purity_min: 0.95
  color_delta_e_uni_max: 3.0
```

## Quality Metrics

### Edge Quality (SSIM)
- **Target**: > 0.75
- **Measurement**: Structural similarity against pure white background
- **Improvement**: Adjust RMBG threshold and mask blur

### Background Purity
- **Target**: ≥ 95% white pixels
- **Measurement**: L* channel analysis in LAB color space
- **Improvement**: Increase generation steps or adjust negative prompts

### Color Accuracy (ΔE)
- **Target**: ≤ 3 (uni-color) / ≤ 5 (textured)
- **Measurement**: CIEDE2000 color difference in LAB space
- **Improvement**: Use SmartInpaintPolish with color-snap prompts

### Constraint Validation
- **Target**: 100% compliance
- **Measurement**: Heuristic detection of structural features
- **Improvement**: Refine prompts and increase CFG scale

## Troubleshooting

### Common Issues

#### Low Edge Quality (SSIM < 0.75)
- **Cause**: Poor segmentation or mask quality
- **Solution**: 
  - Adjust RMBG threshold (0.25-0.35)
  - Increase mask blur (2-5)
  - Use SmartInpaintPolish for edge refinement

#### Background Not Pure White
- **Cause**: Generation artifacts or poor negative prompts
- **Solution**:
  - Strengthen negative prompts
  - Increase generation steps
  - Use background inpaint pass

#### Color Inaccuracy (ΔE > 3)
- **Cause**: Model color drift or poor prompting
- **Solution**:
  - Use exact hex color in prompts
  - Apply SmartInpaintPolish with color-snap
  - Increase CFG scale for better prompt adherence

#### Constraint Violations
- **Cause**: Model not following structural requirements
- **Solution**:
  - Strengthen constraint prompts
  - Use ControlNet for structure preservation
  - Increase CFG scale

### Performance Optimization

#### Memory Usage
- **Low VRAM**: Use `--lowvram` flag
- **CPU Only**: Use `--cpu` flag
- **Batch Size**: Reduce to 1 for large images

#### Processing Speed
- **Steps**: Reduce to 16-20 for faster processing
- **Resolution**: Use 1024x1024 for optimal speed/quality balance
- **Concurrent**: Limit to 2 concurrent tasks

## Upgrade Path to Phase 2

### Planned Enhancements

1. **IP-Adapter Integration**
   - Texture preservation from original garment
   - Staggered generation passes

2. **Advanced Segmentation**
   - GroundingDINO + SAM ensemble
   - Component-level segmentation

3. **Enhanced Quality Gates**
   - Real-time constraint validation
   - Automatic re-rendering logic

4. **Full Facts V3 Support**
   - Complete garment analysis
   - Advanced routing logic

### Migration Guide

1. **Backup Current Workflows**
2. **Update Node Dependencies**
3. **Test New Features in Staging**
4. **Gradual Rollout with A/B Testing**

## Support

### Logging
- ComfyUI logs: `ComfyUI/logs/`
- Batch processing logs: `output/comfyui_automation.log`
- Quality validation reports: JSON format with timestamps

### Debug Mode
Enable debug mode in quality gates for visual feedback:
- Edge gate: Shows edge regions in red/green
- Background gate: Shows background regions in blue/yellow

### Performance Monitoring
- Processing time per image
- Quality gate pass rates
- Memory usage patterns
- Error rates and types

## Best Practices

### Input Preparation
- Use high-resolution images (1024x1024+)
- Ensure good lighting and contrast
- Remove background distractions
- Use consistent garment positioning

### Facts JSON Creation
- Use precise color hex values
- Include all structural details
- Specify exact pocket/button counts
- Add special requirements in notes

### Quality Monitoring
- Run validation after each batch
- Monitor pass rates over time
- Adjust thresholds based on results
- Document successful parameter combinations

### Batch Processing
- Process similar garments together
- Use consistent facts structure
- Monitor system resources
- Implement proper error handling

---

For technical support or feature requests, refer to the project documentation or create an issue in the repository.
