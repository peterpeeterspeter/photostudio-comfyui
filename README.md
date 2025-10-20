# Photostudio.io - ComfyUI Ghost Mannequin Pipeline

A production-grade AI pipeline for generating ghost mannequin product photos using ComfyUI, SDXL, and custom nodes. This system transforms flat garment photos into professional ghost mannequin images with invisible models.

## 🎯 Overview

The Photostudio.io pipeline automates the creation of ghost mannequin product photos - a technique where clothing appears to be worn by an invisible mannequin, creating clean, professional e-commerce imagery.

### Key Features

- **AI-Powered Segmentation**: RMBG + U²-Net ensemble for precise garment masking
- **Smart Generation**: SDXL with conditional IP-Adapter for pattern-aware texture preservation
- **Quality Assurance**: Multi-metric validation (color accuracy, edge quality, perceptual metrics)
- **Automated Polish**: ControlNet Inpaint for professional edge refinement
- **Batch Processing**: Scalable workflow for high-volume production

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- ComfyUI
- 16GB+ RAM (recommended)
- macOS/Linux/Windows

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/photostudio-comfyui.git
   cd photostudio-comfyui
   ```

2. **Install dependencies**:
   ```bash
   pip install -r ComfyUI/requirements.txt
   ```

3. **Start ComfyUI**:
   ```bash
   cd ComfyUI && python main.py --listen --port 8188
   ```

4. **Test the pipeline**:
   ```bash
   python test_phase1_5_workflow.py
   ```

### First Ghost Mannequin

1. Open ComfyUI at `http://localhost:8188`
2. Load `workflows/phase1_5_mvp_working.json`
3. Set input image: `input/test_garment.jpg`
4. Set facts file: `input/test_garment_facts.json`
5. Click "Queue Prompt"

## 📁 Project Structure

```
photostudio-comfyui/
├── ComfyUI/                          # ComfyUI installation
│   ├── custom_nodes/                 # Custom nodes for the pipeline
│   │   ├── load_facts_node.py        # Load garment facts from JSON
│   │   ├── light_facts_prompt.py     # Convert facts to prompts
│   │   ├── u2net_segmentation/       # U²-Net segmentation node
│   │   ├── mask_ensemble.py          # Combine RMBG + U²-Net masks
│   │   ├── ip_adapter_conditional.py # Pattern-aware IP-Adapter
│   │   ├── controlnet_inpaint_polish.py # Edge refinement
│   │   └── quality_gates/            # Real-time quality checks
│   └── requirements.txt              # Python dependencies
├── workflows/                        # ComfyUI workflow files
│   ├── phase1_5_mvp_working.json     # Main working pipeline
│   ├── phase1_5_enhanced.json        # Enhanced pipeline with all features
│   └── test_*.json                   # Test workflows
├── scripts/                          # Automation and validation
│   ├── quality_validator_enhanced.py # Batch quality validation
│   ├── generate_qa_report.py         # Generate QA reports
│   └── test_phase1_5_workflow.py     # Pipeline testing
├── input/                            # Input files
│   ├── test_garment.jpg              # Sample garment image
│   ├── test_garment_facts.json       # Sample facts file
│   └── light_facts_schema.json       # Facts schema definition
├── config/                           # Configuration files
│   └── phase1_5_params.yaml          # Pipeline parameters
└── docs/                             # Documentation
    ├── PHASE_1_5_STATUS.md           # Detailed status report
    ├── PHASE2_1_IMPLEMENTATION_GUIDE.md  # Phase 2.1 implementation details
    └── PHASE2_DEPLOYMENT_GUIDE.md    # Phase 2 deployment/testing
```

## 🔧 Pipeline Architecture

### Phase 1.5 Enhanced Pipeline

```
Input Image → [RMBG + U²-Net Ensemble] → Load Facts → Generate Prompt →
[IP-Adapter Conditional] → SDXL Generation → Quality Gates →
[ControlNet Inpaint Polish] → Final Output

### Phase 2.1 Additions (Truth-Aligned Quality)

```
Input → Pre-Analysis (colors, FFT complexity, OCR, exposure) →
Advanced Segmentation (RMBG+U²-Net with mask_quality_score) →
Dynamic Part Prompts (from Facts V3.1) → SDXL/FLUX Routing →
Generation → Semantic QA (Gemini) → Hierarchical QA (edge/bg/color/semantic) →
Report + Auto re-render recommendation
```

Key research-backed effects:
- Edge quality correlates most with human judgment (weight 0.4)
- Background purity (0.3), color ΔE (0.2), semantic alignment (0.1)
- Pre-analysis context reduces hallucinations and improves prompt grounding
```

### Key Components

1. **Segmentation Ensemble**
   - RMBG-1.4: Fast, reliable baseline masking
   - U²-Net: High-precision edge refinement
   - Weighted blending: 40% RMBG + 60% U²-Net

2. **Smart Generation**
   - SDXL: Primary generation model
   - IP-Adapter: Conditional texture preservation for patterned fabrics
   - ControlNet Canny: Structural guidance

3. **Quality Assurance**
   - Real-time edge quality checks
   - Background purity validation
   - Batch perceptual quality assessment (LPIPS, CLIP)

4. **Automated Polish**
   - ControlNet Inpaint: Professional edge refinement
   - Halo removal and color correction
   - Smart mask dilation and feathering

## 📊 Performance & Research

### Current Performance (Phase 1.5)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| QA Pass Rate | 90%+ | 85% | ✅ Good |
| Edge SSIM | 0.80+ | 0.75 | ⚠️ Improving |
| Color ΔE (uniform) | ≤2.4 | 3.0 | ⚠️ Improving |
| BG Purity | 0.97+ | 0.95 | ⚠️ Improving |
| Render Time | <3min | 2:45 | ✅ Excellent |

### Enhanced Pipeline (Phase 2.1)

| Metric | Expected | Improvement |
|--------|----------|-------------|
| QA Pass Rate | 0.85+ | +5-7% |
| Edge SSIM | 0.80+ | +7-11% |
| Color ΔE | ≤ 3.0 (solids), ≤ 5.0 (patterns) | -20% |
| BG Purity | 0.97 | +2% |

References:
- LPIPS: Learned Perceptual Image Patch Similarity (Zhang et al.)
- SSIM: Structural Similarity Index (Wang et al.)
- CIELAB ΔE color difference (CIEDE2000)
- CLIP-based anomaly detection for artifact discovery
| Manual Fix Rate | <8% | -47% |

## 🎨 Usage Examples

### Basic Ghost Mannequin Generation

```python
# Load workflow
workflow = load_workflow("workflows/phase1_5_mvp_working.json")

# Set inputs
workflow["1"]["inputs"]["image"] = "input/garment.jpg"
workflow["2"]["inputs"]["facts_json"] = "input/garment_facts.json"

# Queue for processing
prompt_id = queue_prompt(workflow)
```

### Batch Processing & QA Dashboard

```bash
# Process multiple images
python scripts/batch_ghost_processor.py --input_dir garments/ --facts_dir facts/ --output_dir results/

# Validate results with hierarchical QA
python scripts/quality_validator.py --input results/ --facts facts/ --report qa_report.json

# Generate metrics dashboard (ΔE, EdgeGate, Semantic)
python scripts/metrics_dashboard.py --results-dir results --output-dir dashboard_output
```

## 📋 Facts Schema

The pipeline uses structured JSON facts to describe garments:

```json
{
  "analysis_mode": "light",
  "garment": {
    "category": "dress shirt",
    "color_hex": "#0A0A0A",
    "color_name": "near-black",
    "fabric": "cotton twill",
    "silhouette": "tailored",
    "pattern": "solid",
    "transparency_level": 0.0,
    "complexity_score": 0.3
  },
  "photography": {
    "bg": "pure_white",
    "lighting": "soft_even_high_key",
    "frame": "4:5"
  },
  "risk_score": 0.2
}
```

## 🔍 Quality Validation

### Real-time Quality Gates

- **Edge Quality**: SSIM-based edge sharpness assessment
- **Background Purity**: Alpha channel analysis for clean backgrounds
- **Color Accuracy**: CIELAB ΔE color difference measurement

### Batch Validation

- **LPIPS**: Perceptual similarity assessment
- **CLIP**: AI-driven quality and artifact detection
- **Constraint Validation**: Feature compliance checking

## 🛠️ Custom Nodes

### Core Nodes

- **LoadFactsNode**: Load and validate garment facts
- **PromptFromLightFacts**: Convert facts to generation prompts
- **U2NetSegmentation**: High-precision segmentation
- **MaskEnsemble**: Combine multiple segmentation masks
- **IPAdapterConditional**: Pattern-aware texture preservation
- **ControlNetInpaintPolish**: Professional edge refinement

### Quality Gates

- **QualityGateEdge**: Real-time edge quality assessment
- **QualityGateBackground**: Background purity validation

## 📈 Roadmap

### Phase 1.6 (Next)
- Automated re-render logic for failed images
- Multi-view consistency checks
- Gemini 1.5 Flash Lite integration

### Phase 2 (Future)
- Advanced pattern recognition
- 3D garment understanding
- Real-time quality optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check `docs/PHASE_1_5_STATUS.md` for detailed status
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join our community discussions

## 🙏 Acknowledgments

- ComfyUI community for the excellent framework
- Stability AI for SDXL
- OpenAI for CLIP
- All contributors and testers

---

**Photostudio.io** - Professional AI-powered product photography automation.