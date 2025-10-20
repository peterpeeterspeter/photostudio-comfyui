#!/usr/bin/env python3
"""
Test Phase 2 SDXL Workflow
Tests the working Phase 2 pipeline with available components
"""

import sys
import os
import json
import requests
import time
from PIL import Image

# Add ComfyUI paths
sys.path.append('ComfyUI')

def test_phase2_workflow():
    """Test the Phase 2 SDXL workflow"""
    print("🚀 Testing Phase 2 SDXL Workflow...")
    
    # Check if ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code != 200:
            print("❌ ComfyUI not running. Start with: cd ComfyUI && python main.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ ComfyUI not running. Start with: cd ComfyUI && python main.py")
        return False
    
    print("✅ ComfyUI is running")
    
    # Load workflow
    workflow_path = "workflows/phase2_working_sdxl.json"
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow not found: {workflow_path}")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    print(f"✅ Loaded workflow with {len(workflow)} nodes")
    
    # Check required input files
    required_files = [
        "input/test_garment.jpg",
        "input/test_garment_facts.json"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    
    # Prepare workflow inputs
    workflow_inputs = {
        "1": {
            "image": "test_garment.jpg",
            "upload": "image"
        },
        "2": {
            "facts_file": "test_garment_facts.json"
        }
    }
    
    # Queue the workflow
    try:
        print("📤 Queuing workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json={
                "prompt": workflow,
                "client_id": "test_phase2_sdxl"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to queue workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        prompt_id = result.get("prompt_id")
        print(f"✅ Workflow queued with ID: {prompt_id}")
        
        # Monitor execution
        print("⏳ Monitoring execution...")
        start_time = time.time()
        max_wait = 300  # 5 minutes
        
        while time.time() - start_time < max_wait:
            try:
                # Check prompt status
                status_response = requests.get(
                    f"http://127.0.0.1:8188/prompt/{prompt_id}",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status", {})
                    
                    if status.get("status_str") == "success":
                        print("✅ Workflow completed successfully!")
                        
                        # Check for output images
                        history_response = requests.get(
                            f"http://127.0.0.1:8188/history/{prompt_id}",
                            timeout=10
                        )
                        
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            outputs = history_data.get("outputs", {})
                            
                            if "23" in outputs:  # SaveImage node
                                images = outputs["23"].get("images", [])
                                if images:
                                    print(f"✅ Generated {len(images)} images")
                                    for img in images:
                                        print(f"   - {img.get('filename', 'unknown')}")
                                    return True
                                else:
                                    print("⚠️  No images in output")
                            else:
                                print("⚠️  No SaveImage output found")
                        
                        return True
                    
                    elif status.get("status_str") == "error":
                        print("❌ Workflow failed!")
                        error = status.get("error", {})
                        print(f"Error: {error}")
                        return False
                    
                    else:
                        # Still running
                        progress = status.get("progress", 0)
                        print(f"⏳ Progress: {progress}%", end='\r')
                
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Request error: {e}")
                time.sleep(2)
        
        print(f"\n⏰ Timeout after {max_wait} seconds")
        return False
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_components():
    """Check if required components are available"""
    print("🔍 Checking Phase 2 Components...")
    
    components = {
        "SDXL Model": "ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors",
        "IP-Adapter Model": "ComfyUI/models/ipadapter/ip-adapter_sdxl_vit-h.safetensors",
        "SAM2 Model": "ComfyUI/models/sam2/sam2_hiera_base_plus.pt",
        "GroundingDINO Model": "ComfyUI/models/groundingdino/groundingdino_swint_ogc.pth",
        "Custom Nodes": "ComfyUI/custom_nodes/garment_part_segmentation.py"
    }
    
    all_available = True
    
    for name, path in components.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024*1024)  # MB
            print(f"✅ {name}: {size:.1f}MB")
        else:
            print(f"❌ {name}: Not found")
            all_available = False
    
    return all_available

def main():
    """Main test function"""
    print("🧪 Phase 2 SDXL Workflow Test")
    print("=" * 40)
    
    # Check components first
    if not check_components():
        print("\n⚠️  Some components missing, but continuing with available ones...")
    
    print("\n" + "=" * 40)
    
    # Test workflow
    success = test_phase2_workflow()
    
    if success:
        print("\n🎉 Phase 2 SDXL workflow test PASSED!")
        print("✅ Ready for production testing")
    else:
        print("\n❌ Phase 2 SDXL workflow test FAILED!")
        print("🔧 Check ComfyUI logs for details")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
