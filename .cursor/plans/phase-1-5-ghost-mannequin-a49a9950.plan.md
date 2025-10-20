<!-- a49a9950-2542-40dd-a574-accc60ec6600 93fa4ecc-8b2b-48f1-8107-5a22c88a5359 -->
# Phase 2 - Real Garment Processing Pipeline

## 1. Folder Structure Setup

Create new folder structure for Phase 2:

```
photostudio-comfyui/
├─ data/
│  ├─ input/real/          # real garment images
│  ├─ ref_swatches/        # color reference swatches
│  └─ parts/               # debug crops from segmentation
├─ facts/
│  ├─ facts_v3_1_schema.json
│  └─ cache/               # cached JSON per SKU
├─ scripts/
│  ├─ gemini_part_analyzer.py
│  ├─ batch_qc.py
│  └─ router_rules.json
└─ workflows/
   └─ phase2_real_garment.json
```

## 2. Advanced Segmentation (Person → Garment)

### Install GroundingDINO and SAM2 Custom Nodes

Install required custom nodes:

- `ComfyUI-GroundingDINO` (git clone from https://github.com/kijai/ComfyUI-GroundingDINO)
- `ComfyUI-SAM2` (git clone from https://github.com/kijai/ComfyUI-SAM2)
- `ComfyUI-HumanSeg` (optional, for on-model detection)

**Commands:**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/kijai/ComfyUI-GroundingDINO.git
git clone https://github.com/kijai/ComfyUI-SAM2.git
cd ../..
pip install -r ComfyUI/custom_nodes/ComfyUI-GroundingDINO/requirements.txt
pip install -r ComfyUI/custom_nodes/ComfyUI-SAM2/requirements.txt
```

### Create Advanced Segmentation Node

**File**: `ComfyUI/custom_nodes/advanced_garment_segmentation.py`

```python
class AdvancedGarmentSegmentation:
    """
    Multi-stage segmentation: RMBG + U²-Net + HumanSeg mask subtraction
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rmbg_threshold": ("FLOAT", {"default": 0.32, "min": 0.2, "max": 0.5}),
                "u2net_threshold": ("FLOAT", {"default": 0.35, "min": 0.2, "max": 0.5}),
                "use_human_subtract": ("BOOLEAN", {"default": True}),
                "mask_blur": ("INT", {"default": 3, "min": 0, "max": 10}),
                "edge_feather": ("INT", {"default": 4, "min": 0, "max": 10})
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "FLOAT")
    RETURN_NAMES = ("garment_only", "garment_mask", "confidence")
    FUNCTION = "segment_garment"
    CATEGORY = "photostudio/segmentation"
    
    def segment_garment(self, image, rmbg_threshold, u2net_threshold, 
                       use_human_subtract, mask_blur, edge_feather):
        # Logic: garment_mask = (RMBG ∧ U²-Net) ∧ ¬HumanSeg
        # Returns clean garment only, no person
        pass
```

## 3. Part Segmentation (Collar, Sleeves, Body)

### Create Dual-Path Part Segmentation Node

**File**: `ComfyUI/custom_nodes/garment_part_segmentation.py`

```python
class GarmentPartSegmentation:
    """
    Dual-path segmentation: GroundingDINO + SAM2 primary, ATR fallback
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "garment_mask": ("MASK",),
                "segmentation_mode": (["dino_sam2", "atr", "auto"], {"default": "auto"}),
                "part_prompts": ("STRING", {
                    "multiline": True, 
                    "default": "collar,left sleeve,right sleeve,front body,hem,placket,pocket"
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "IMAGE")  # JSON parts + debug visualization
    RETURN_NAMES = ("parts_json", "parts_overlay")
    FUNCTION = "segment_parts"
    CATEGORY = "photostudio/segmentation"
    
    def segment_parts(self, image, garment_mask, segmentation_mode, part_prompts):
        # Primary: GroundingDINO with prompts → SAM2 refinement
        # Fallback: If DINO detects <3 parts, use ATR ClothesParsing
        # Export: JSON with {part_name, bbox, mask_id, crop_path}
        pass
```

**File**: `scripts/router_rules.json`

```json
{
  "segmentation_routing": {
    "use_dino_sam2": {
      "conditions": [
        "garment.category in ['asymmetric', 'complex', 'dress']",
        "garment.pattern != 'solid'",
        "risk_score > 0.5"
      ]
    },
    "use_atr": {
      "conditions": [
        "garment.category in ['t-shirt', 'dress_shirt', 'polo']",
        "garment.pattern == 'solid'",
        "risk_score <= 0.5"
      ]
    }
  }
}
```

## 4. Gemini Part Analysis Integration

### Create Gemini Part Analyzer Script

**File**: `scripts/gemini_part_analyzer.py`

```python
import os
import json
from PIL import Image
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PART_PROMPT_TEMPLATE = """
Analyze this {part_name} from a {garment_category}.

Identify (JSON only):
{{
  "color_hex": "#RRGGBB",
  "texture": "smooth|ribbed|woven|knit",
  "pattern": "solid|striped|printed|textured",
  "condition": "clean|wrinkled|stained",
  "seam_quality": 0.0-1.0,
  "sharpness_needed": 0.0-1.0,
  "transparency": 0.0-1.0
}}
"""

def analyze_garment_part(image_path: str, part_name: str, garment_category: str) -> dict:
    """
    Analyze single garment part using Gemini Flash Lite 2.5
    Returns structured JSON with per-part attributes
    """
    model = genai.GenerativeModel('gemini-1.5-flash-002')  # Use existing API key
    
    image = Image.open(image_path)
    prompt = PART_PROMPT_TEMPLATE.format(
        part_name=part_name,
        garment_category=garment_category
    )
    
    try:
        response = model.generate_content([prompt, image])
        part_data = json.loads(response.text)
        part_data["part_name"] = part_name
        part_data["analyzed"] = True
        return part_data
    except Exception as e:
        print(f"Gemini analysis failed for {part_name}: {e}")
        return {
            "part_name": part_name,
            "analyzed": False,
            "error": str(e),
            "fallback_used": True
        }

def batch_analyze_garment(parts_json_path: str, crops_dir: str) -> dict:
    """
    Analyze all parts from segmentation output
    Returns complete Facts V3.1 JSON
    """
    with open(parts_json_path) as f:
        parts = json.load(f)
    
    analyzed_parts = []
    for part in parts["parts"]:
        crop_path = f"{crops_dir}/{parts['sku']}_{part['part_name']}.png"
        if os.path.exists(crop_path):
            analysis = analyze_garment_part(crop_path, part['part_name'], parts['garment_category'])
            analyzed_parts.append(analysis)
    
    # Aggregate into Facts V3.1 schema
    facts_v3_1 = {
        "schema_version": "3.1",
        "analysis_mode": "full",
        "garment": {
            "category": parts["garment_category"],
            "parts": analyzed_parts,
            # ... aggregate color, pattern from parts
        }
    }
    
    return facts_v3_1
```

### Create Gemini Analysis ComfyUI Node

**File**: `ComfyUI/custom_nodes/gemini_part_analyzer_node.py`

```python
class GeminiPartAnalyzer:
    """
    Calls Gemini Flash Lite to analyze each garment part
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "parts_json": ("STRING", {"multiline": True}),
                "crops_directory": ("STRING", {"default": "data/parts"}),
                "garment_category": ("STRING", {"default": "dress_shirt"})
            }
        }
    
    RETURN_TYPES = ("STRING",)  # Facts V3.1 JSON
    RETURN_NAMES = ("facts_v3_1_json",)
    FUNCTION = "analyze_parts"
    CATEGORY = "photostudio/analysis"
    
    def analyze_parts(self, parts_json, crops_directory, garment_category):
        # Call scripts/gemini_part_analyzer.py batch_analyze_garment
        # Return Facts V3.1 JSON string
        pass
```

## 5. Model Downloads and Integration

### Download FLUX Dev Model

**Commands:**

```bash
# Download FLUX dev model (~12GB)
cd ComfyUI/models/checkpoints
wget https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors
# Or use huggingface-cli
huggingface-cli download black-forest-labs/FLUX.1-dev flux1-dev.safetensors --local-dir .
```

### Download IP-Adapter SDXL Model

**Commands:**

```bash
# Download IP-Adapter (~1.2GB)
cd ComfyUI/models/ipadapter
mkdir -p ipadapter
cd ipadapter
wget https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl.safetensors
```

### Update Model Router Node

**File**: `ComfyUI/custom_nodes/model_router.py`

Update routing logic to include FLUX dev:

```python
def route_model(self, facts_json):
    facts = json.loads(facts_json)
    
    # Use FLUX dev if:
    # - Pattern is not solid
    # - Risk score > 0.6
    # - Has logos or text
    pattern = facts.get("garment", {}).get("pattern", "solid")
    risk_score = facts.get("risk_score", 0.0)
    
    if pattern != "solid" or risk_score > 0.6:
        return ("flux_dev", "flux1-dev.safetensors")
    else:
        return ("sdxl", "sd_xl_base_1.0.safetensors")
```

## 6. Facts V3.1 Schema Extension

### Create Facts V3.1 Schema

**File**: `facts/facts_v3_1_schema.json`

```json
{
  "schema_version": "3.1",
  "analysis_mode": "full",
  "garment": {
    "category": "string",
    "silhouette": "string",
    "fabric": "string",
    "color_hex": "#RRGGBB",
    "color_name": "string",
    "pattern": "solid|striped|printed|textured",
    "transparency_level": 0.0,
    "complexity_score": 0.0,
    "parts": [
      {
        "part_name": "string",
        "color_hex": "#RRGGBB",
        "texture": "string",
        "pattern": "string",
        "condition": "string",
        "seam_quality": 0.0,
        "sharpness_needed": 0.0,
        "transparency": 0.0,
        "analyzed": true
      }
    ]
  },
  "photography": {
    "bg": "pure_white",
    "lighting": "soft_even_high_key",
    "frame": "4:5",
    "coverage_pct": 85
  },
  "routing": {
    "suggested_model": "sdxl|flux_dev",
    "use_ip_adapter": false,
    "use_controlnet_inpaint": true
  },
  "risk_score": 0.0
}
```

### Update Light Facts Prompt Node

**File**: `ComfyUI/custom_nodes/light_facts_prompt.py`

Add support for Facts V3.1 with per-part data:

```python
def build_prompts(self, facts_json, prompt_style, include_constraints, ...):
    facts = json.loads(facts_json)
    
    # Handle V3.1 with parts
    if facts.get("schema_version") == "3.1" and "parts" in facts.get("garment", {}):
        # Aggregate part colors, textures, patterns
        parts = facts["garment"]["parts"]
        # Build composite prompt from analyzed parts
        pass
    
    # Fall back to V3.0 logic for backward compatibility
    pass
```

## 7. Complete Phase 2 Workflow

### Create Phase 2 Workflow JSON

**File**: `workflows/phase2_real_garment.json`

Architecture:

```
LoadImage (real garment on model/flat)
  ↓
[AdvancedGarmentSegmentation: RMBG + U²-Net + HumanSeg]
  ↓ (garment_only, garment_mask)
[GarmentPartSegmentation: DINO+SAM2 or ATR]
  ↓ (parts_json, crops saved to data/parts/)
[GeminiPartAnalyzer: Analyze each part]
  ↓ (facts_v3_1_json)
[ModelRouter: SDXL or FLUX dev]
  ↓
[IPAdapterConditional: Use if pattern != solid]
  ↓
[KSampler: Generate ghost mannequin]
  ↓
[ControlNetInpaintPolish: Edge refinement]
  ↓
[QualityGateEdge + QualityGateBackground]
  ↓
SaveImage
```

Use MVP format (numbered keys) for compatibility.

## 8. Batch QA Validation Script

### Create Enhanced Batch QA Script

**File**: `scripts/batch_qc.py`

```python
import json
from pathlib import Path
from scripts.quality_validator_enhanced import validate_perceptual_quality

def run_phase2_qa(output_dir: str, facts_dir: str) -> dict:
    """
    Run comprehensive QA on Phase 2 outputs
    Validates: ΔE, SSIM, LPIPS, CLIP, part accuracy
    """
    results = []
    
    for image_path in Path(output_dir).glob("*.png"):
        facts_path = Path(facts_dir) / f"{image_path.stem}_facts.json"
        
        if not facts_path.exists():
            continue
        
        with open(facts_path) as f:
            facts = json.load(f)
        
        # Run all validation metrics
        qa_result = {
            "image": str(image_path),
            "facts": str(facts_path),
            **validate_perceptual_quality(str(image_path)),
            # Additional Phase 2 checks
            "part_count_match": validate_part_count(facts),
            "gemini_analysis_present": "parts" in facts.get("garment", {})
        }
        
        results.append(qa_result)
    
    # Generate summary report
    summary = {
        "total_images": len(results),
        "qa_pass_rate": sum(r["overall_pass"] for r in results) / len(results),
        "avg_lpips": sum(r["lpips_score"] for r in results) / len(results),
        "avg_clip_similarity": sum(r["clip_similarity"] for r in results) / len(results)
    }
    
    return {"results": results, "summary": summary}
```

## 9. Testing with Real Garments

### Prepare Test Dataset

Create test dataset:

1. Place 5-10 real garment images in `data/input/real/`
2. Name them: `shirt_001.jpg`, `dress_001.jpg`, etc.
3. Include variety: on-model, flat lay, different categories

### Run Phase 2 Test Workflow

**File**: `test_phase2_workflow.py`

```python
#!/usr/bin/env python3
import sys
import json
import requests
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_FILE = "workflows/phase2_real_garment.json"

def test_phase2_pipeline(test_image: str):
    """Test Phase 2 with a real garment image"""
    with open(WORKFLOW_FILE) as f:
        workflow = json.load(f)
    
    # Update LoadImage node with test image
    workflow["1"]["inputs"]["image"] = test_image
    
    # Queue prompt
    response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
    
    if response.status_code == 200:
        print(f"✅ Queued Phase 2 workflow for {test_image}")
        return response.json()
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    test_images = [
        "shirt_001.jpg",
        "dress_001.jpg",
        "jacket_001.jpg"
    ]
    
    for img in test_images:
        result = test_phase2_pipeline(img)
        if result:
            print(f"Processing {img}...")
```

### Validation Commands

```bash
# 1. Test single image through Phase 2 pipeline
python test_phase2_workflow.py

# 2. Run Gemini part analysis on generated crops
python scripts/gemini_part_analyzer.py --crops data/parts --output facts/cache/

# 3. Run comprehensive QA validation
python scripts/batch_qc.py --input ComfyUI/output --facts facts/cache --report qa_phase2.json

# 4. Generate summary report
python scripts/generate_qa_report.py --input qa_phase2.json --output qa_phase2_summary.md
```

## 10. Configuration and Dependencies

### Update requirements.txt

**File**: `requirements.txt`

Add Phase 2 dependencies:

```
google-generativeai>=0.3.0
groundingdino-py>=0.1.0
segment-anything-2>=0.1.0
```

### Create Phase 2 Config

**File**: `config/phase2_params.yaml`

```yaml
phase_2_real_garment:
  segmentation:
    use_advanced: true
    rmbg_threshold: 0.32
    u2net_threshold: 0.35
    subtract_human: true
    
  part_segmentation:
    mode: "auto"  # auto, dino_sam2, atr
    min_parts_for_dino: 3
    part_prompts: ["collar", "left sleeve", "right sleeve", "front body", "hem", "placket", "pocket"]
    
  gemini_analysis:
    model: "gemini-1.5-flash-002"
    retry_attempts: 3
    cache_results: true
    cache_dir: "facts/cache"
    
  model_routing:
    use_flux_for_patterns: true
    use_flux_for_high_risk: true
    flux_risk_threshold: 0.6
    
  ip_adapter:
    enabled: true
    conditional_on_pattern: true
    weight: 0.75
    
  generation:
    default_model: "sdxl"
    fallback_model: "flux_dev"
    steps: 30
    cfg: 8.0
    
  quality_validation:
    lpips_threshold: 0.2
    clip_similarity_threshold: 0.75
    part_count_validation: true
```

## Expected Outcomes

Phase 2 Metrics (5-10 test images):

- QA Pass Rate: 90-92%
- Edge SSIM: 0.80-0.85
- Color ΔE: <2.5 (with per-part analysis)
- LPIPS: <0.2
- CLIP Similarity: >0.75
- Part Detection Accuracy: >95%
- Gemini Analysis Success Rate: >90%

Performance:

- Avg Pipeline Time: 4-6 min/image (segmentation + analysis + generation)
- VRAM Usage: 3.5-4.5GB peak (with model offloading)
- Part Analysis: ~15-20s per part (Gemini API)

Acceptance Criteria:

- [ ] GroundingDINO + SAM2 installed and working
- [ ] ATR fallback logic functional
- [ ] Gemini part analysis returns valid JSON
- [ ] FLUX dev model loaded correctly
- [ ] IP-Adapter activates for patterned fabrics
- [ ] Complete pipeline runs on 5 test images
- [ ] QA validation passes for 90%+ of outputs

### To-dos

- [ ] Create Phase 2 folder structure (data/, facts/, scripts/)
- [ ] Install GroundingDINO and SAM2 custom nodes
- [ ] Create AdvancedGarmentSegmentation node (RMBG + U²-Net + HumanSeg)
- [ ] Create GarmentPartSegmentation node with DINO+SAM2 and ATR fallback
- [ ] Create Gemini part analyzer script and ComfyUI node
- [ ] Download FLUX dev model (~12GB) to ComfyUI/models/checkpoints
- [ ] Download IP-Adapter SDXL model (~1.2GB)
- [ ] Update ModelRouter node to support FLUX dev routing
- [ ] Create Facts V3.1 schema with per-part analysis fields
- [ ] Update LightFactsPrompt node to support Facts V3.1
- [ ] Create complete Phase 2 workflow JSON in MVP format
- [ ] Create enhanced batch QA validation script
- [ ] Prepare 5-10 real garment test images
- [ ] Create test_phase2_workflow.py script
- [ ] Create phase2_params.yaml configuration file
- [ ] Run complete Phase 2 pipeline test and validate QA metrics