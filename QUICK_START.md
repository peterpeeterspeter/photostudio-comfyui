# Quick Start Guide - Photostudio.io Ghost Mannequin Pipeline

Get up and running with professional ghost mannequin generation in under 10 minutes!

## 🚀 5-Minute Setup

### 1. Start ComfyUI
```bash
cd ComfyUI && python main.py --listen --port 8188
```

### 2. Open ComfyUI Interface
Navigate to: `http://localhost:8188`

### 3. Load the Working Pipeline
- Click "Load" button
- Select: `workflows/phase1_5_mvp_working.json`

### 4. Set Your Inputs
- **Image**: `input/test_garment.jpg` (or your garment photo)
- **Facts**: `input/test_garment_facts.json` (or your facts file)

### 5. Generate!
Click "Queue Prompt" and wait ~3 minutes for your first ghost mannequin!

## 📸 Your First Ghost Mannequin

### What You'll Get
- **Input**: Flat garment photo
- **Output**: Professional ghost mannequin image
- **Quality**: E-commerce ready, clean background, invisible model

### Expected Results
- ✅ Clean white background
- ✅ Sharp garment edges
- ✅ Natural draping and fit
- ✅ Professional lighting
- ✅ No visible mannequin or model

## 🎯 Quick Test

Run this command to test everything is working:

```bash
python test_phase1_5_workflow.py
```

**Success indicators:**
- ✅ ComfyUI server running
- ✅ Custom nodes loaded
- ✅ Workflow executed
- ✅ Image generated in `ComfyUI/output/`

## 📁 Key Files

| File | Purpose |
|------|---------|
| `workflows/phase1_5_mvp_working.json` | Main pipeline workflow |
| `input/test_garment.jpg` | Sample garment image |
| `input/test_garment_facts.json` | Sample facts file |
| `ComfyUI/output/` | Generated images folder |

## 🔧 Customization

### Change Garment Facts
Edit `input/test_garment_facts.json`:

```json
{
  "garment": {
    "category": "t-shirt",
    "color_hex": "#FF0000",
    "color_name": "red",
    "fabric": "cotton"
  }
}
```

### Adjust Quality Settings
Edit `config/phase1_5_params.yaml`:

```yaml
generation:
  steps: 20        # More steps = better quality
  cfg: 7.0         # Higher = more prompt adherence
```

## 🚨 Troubleshooting

### ComfyUI Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Install missing dependencies
pip install -r ComfyUI/requirements.txt
```

### No Images Generated
- Check ComfyUI logs for errors
- Verify input files exist
- Ensure models are downloaded

### Poor Quality Results
- Increase generation steps (20 → 30)
- Adjust CFG scale (7.0 → 8.0)
- Check garment facts accuracy

## 📊 Quality Validation

After generation, validate your results:

```bash
python scripts/quality_validator_enhanced.py --input ComfyUI/output/ --facts input/ --report qa_report.json
```

**Good metrics:**
- Color ΔE < 3.0
- Edge SSIM > 0.75
- Background purity > 0.95

## 🎨 Advanced Features

### Batch Processing
```bash
python scripts/batch_ghost_processor.py --input_dir garments/ --output_dir results/
```

### Enhanced Pipeline
Load `workflows/phase1_5_enhanced.json` for:
- U²-Net segmentation
- IP-Adapter texture preservation
- ControlNet Inpaint polish

## 📚 Next Steps

1. **Read Full Documentation**: `README.md`
2. **Installation Guide**: `docs/INSTALLATION.md`
3. **Status Report**: `docs/PHASE_1_5_STATUS.md`
4. **Customize Pipeline**: Edit config files
5. **Scale Up**: Set up batch processing

## 🆘 Need Help?

- **Documentation**: Check `docs/` folder
- **Issues**: GitHub Issues page
- **Community**: GitHub Discussions

---

**Ready to create professional ghost mannequin photos!** 🎉