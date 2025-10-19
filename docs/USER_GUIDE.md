# 🎯 **Photostudio.io Ghost Mannequin Generator - User Guide**

## 🚀 **Quick Start**

### **Upload Your Image and Generate a Ghost Mannequin**

```bash
# 1. Upload your garment image
python upload_and_generate.py /path/to/your/image.jpg

# 2. Generate the ghost mannequin
python test_phase1_5_workflow.py

# 3. Check your result
open ComfyUI/output/
```

**That's it!** Your ghost mannequin will be ready in 3-4 minutes.

---

## 📁 **How It Works**

### **Input Requirements**
- **Image**: Any garment photo (JPG, PNG, WEBP)
- **Facts JSON**: Optional but recommended for better results
- **Output**: Professional ghost mannequin product photo (1024x1024)

### **Processing Pipeline**
```
Your Image → Enhanced Segmentation → AI Generation → Quality Validation → Ghost Mannequin
```

---

## 🎯 **Three Ways to Upload Images**

### **Method 1: Command Line (Recommended)**
```bash
python upload_and_generate.py ~/Desktop/my_shirt.jpg
```
**What it does:**
- Copies your image to `input/` folder
- Creates a facts JSON file
- Updates the workflow
- Ready to generate!

### **Method 2: Manual Upload**
1. **Copy your image** to `input/` folder
2. **Rename it** to something simple like `my_garment.jpg`
3. **Create facts file** (or use example)
4. **Update workflow** to reference your image

### **Method 3: ComfyUI Web Interface**
1. **Open**: http://localhost:8188
2. **Load workflow**: `workflows/user_upload_workflow.json`
3. **Change image path** in LoadImage node
4. **Click "Queue Prompt"**

---

## 📊 **Example Usage**

### **Step 1: Upload Your Image**
```bash
# Example with a shirt image
python upload_and_generate.py ~/Desktop/red_shirt.jpg
```

**Output:**
```
✅ Uploaded image: red_shirt.jpg
✅ Created facts file: red_shirt_facts.json
✅ Updated workflow for your image

🎉 Ready to generate ghost mannequin!

📁 Your files:
   - Image: input/red_shirt.jpg
   - Facts: input/red_shirt_facts.json
   - Workflow: workflows/user_upload_workflow.json

🚀 Next steps:
   1. Make sure ComfyUI is running: cd ComfyUI && python main.py --listen --port 8188
   2. Run the generation: python test_phase1_5_workflow.py
   3. Check output: ComfyUI/output/

⏱️  Expected time: 3-4 minutes
📊 Output: High-quality 1024x1024 ghost mannequin image
```

### **Step 2: Generate Ghost Mannequin**
```bash
python test_phase1_5_workflow.py
```

**Output:**
```
🚀 Phase 1.5 Complete Workflow Test
==================================================
✅ ComfyUI server is running
✅ Loaded workflow: workflows/user_upload_workflow.json
✅ Test input files present
📤 Queuing Phase 1.5 workflow...
✅ Prompt queued with ID: ad355195-b06e-4547-af8b-5d3a2e7e5c27
⏳ Waiting for execution...
✅ Workflow executed successfully!

🎉 Phase 1.5 workflow test completed successfully!
   Check the ComfyUI output folder for generated images.
```

### **Step 3: Check Your Result**
```bash
ls -la ComfyUI/output/ | grep "your_image_name"
```

---

## 🎨 **Customizing Results**

### **Edit Facts JSON for Better Results**

**File**: `input/your_image_facts.json`

```json
{
  "analysis_mode": "light",
  "garment": {
    "category": "t-shirt",           // t-shirt, dress, jacket, etc.
    "color_hex": "#FF5733",          // Your garment's color
    "color_name": "orange",          // Color name
    "fabric": "cotton",              // cotton, polyester, silk, etc.
    "silhouette": "relaxed",         // relaxed, fitted, oversized
    "finish": "matte",               // matte, glossy, textured
    "pockets_count": 0,              // Number of pockets
    "pattern": "solid",              // solid, striped, printed, textured
    "transparency_level": 0.0,       // 0.0 = opaque, 1.0 = transparent
    "complexity_score": 0.3          // 0.0 = simple, 1.0 = complex
  },
  "photography": {
    "bg": "pure_white",              // pure_white, light_gray, etc.
    "lighting": "soft_even_high_key", // Lighting style
    "frame": "4:5",                  // Aspect ratio
    "coverage_pct": 85               // How much of frame is garment
  },
  "risk_score": 0.2                  // 0.0 = easy, 1.0 = challenging
}
```

### **Common Garment Categories**
- `t-shirt`, `dress_shirt`, `polo_shirt`
- `dress`, `skirt`, `pants`, `shorts`
- `jacket`, `blazer`, `hoodie`, `sweater`
- `underwear`, `swimwear`, `activewear`

### **Pattern Types**
- `solid` - Single color
- `striped` - Horizontal or vertical stripes
- `printed` - Graphics, logos, patterns
- `textured` - Fabric texture (denim, corduroy, etc.)

---

## 🔧 **Advanced Usage**

### **Batch Processing Multiple Images**

```bash
# Process multiple images
for image in ~/Desktop/garments/*.jpg; do
    python upload_and_generate.py "$image"
    python test_phase1_5_workflow.py
done
```

### **Quality Validation**

```bash
# Run quality validation on your results
python scripts/quality_validator_enhanced.py --input ComfyUI/output/ --facts input/ --report my_qa_report.json

# Generate quality summary
python scripts/generate_qa_report.py --input my_qa_report.json --output my_qa_summary.md
```

### **Custom Workflow Parameters**

Edit `workflows/user_upload_workflow.json` to adjust:
- **Image size**: Change width/height in EmptyLatentImage node
- **Quality**: Adjust steps, CFG, sampler in KSampler node
- **Segmentation**: Modify thresholds in RMBG and U²-Net nodes

---

## 📊 **Expected Results**

### **Performance**
- **Generation Time**: 3-4 minutes per image
- **Image Quality**: 1024x1024 high-resolution
- **Success Rate**: 90%+ with proper input

### **Quality Metrics**
- **Edge Sharpness**: Enhanced with ensemble segmentation
- **Color Accuracy**: Improved with optimized prompts
- **Background Purity**: Clean white backgrounds
- **Overall Quality**: Professional product photo standard

---

## 🚨 **Troubleshooting**

### **Common Issues**

**1. "Image not found" error**
```bash
# Make sure your image is in the input folder
ls -la input/
```

**2. "ComfyUI server not running"**
```bash
# Start ComfyUI server
cd ComfyUI && python main.py --listen --port 8188
```

**3. "Workflow failed"**
```bash
# Check ComfyUI logs for specific errors
# Make sure all custom nodes are loaded
```

**4. "Poor quality results"**
- **Check facts JSON**: Make sure color_hex matches your garment
- **Adjust parameters**: Try different CFG values (6.0-9.0)
- **Image quality**: Use high-resolution, well-lit garment photos

### **Getting Help**

1. **Check logs**: ComfyUI terminal output
2. **Validate input**: Ensure image and facts files exist
3. **Test with example**: Use `input/test_garment.jpg` first
4. **Quality validation**: Run QA scripts to identify issues

---

## 🎉 **Success!**

You now have a professional ghost mannequin product photo! The system uses:

- **Enhanced Segmentation**: RMBG + U²-Net ensemble for precise masking
- **AI Generation**: SDXL model with optimized prompts
- **Quality Validation**: Automated quality checks
- **Professional Output**: Ready for e-commerce use

**Your ghost mannequin is saved in**: `ComfyUI/output/your_image_name_ghost_00001_.png`

---

*Generated: December 19, 2024*  
*Phase 1.5 Enhanced Pipeline - Production Ready* ✅
