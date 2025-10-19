#!/usr/bin/env python3
"""
Simple script to upload an image and generate a ghost mannequin
Usage: python upload_and_generate.py path/to/your/image.jpg
"""

import sys
import shutil
import json
from pathlib import Path

def upload_and_generate(image_path):
    """Upload an image and generate a ghost mannequin"""
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file '{image_path}' not found")
        return False
    
    # Copy image to input folder
    image_name = Path(image_path).name
    input_path = Path("input") / image_name
    shutil.copy2(image_path, input_path)
    print(f"✅ Uploaded image: {image_name}")
    
    # Create basic facts file
    facts_name = f"{Path(image_name).stem}_facts.json"
    facts_path = Path("input") / facts_name
    
    basic_facts = {
        "analysis_mode": "light",
        "garment": {
            "category": "t-shirt",
            "color_hex": "#FF5733",
            "color_name": "orange",
            "fabric": "cotton",
            "silhouette": "relaxed",
            "finish": "matte",
            "pockets_count": 0,
            "pattern": "solid",
            "transparency_level": 0.0,
            "complexity_score": 0.3
        },
        "photography": {
            "bg": "pure_white",
            "lighting": "soft_even_high_key",
            "frame": "4:5",
            "coverage_pct": 85
        },
        "risk_score": 0.2
    }
    
    with open(facts_path, 'w') as f:
        json.dump(basic_facts, f, indent=2)
    print(f"✅ Created facts file: {facts_name}")
    
    # Update workflow with your image name
    workflow_path = Path("workflows/user_upload_workflow.json")
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Update image and facts references
    workflow["1"]["inputs"]["image"] = image_name
    workflow["2"]["inputs"]["facts_file_path"] = facts_name
    workflow["13"]["inputs"]["filename_prefix"] = f"{Path(image_name).stem}_ghost"
    
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"✅ Updated workflow for your image")
    
    print(f"""
🎉 Ready to generate ghost mannequin!

📁 Your files:
   - Image: input/{image_name}
   - Facts: input/{facts_name}
   - Workflow: workflows/user_upload_workflow.json

🚀 Next steps:
   1. Make sure ComfyUI is running: cd ComfyUI && python main.py --listen --port 8188
   2. Run the generation: python test_phase1_5_workflow.py
   3. Check output: ComfyUI/output/

⏱️  Expected time: 3-4 minutes
📊 Output: High-quality 1024x1024 ghost mannequin image
""")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_and_generate.py path/to/your/image.jpg")
        print("Example: python upload_and_generate.py ~/Desktop/my_shirt.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    upload_and_generate(image_path)
