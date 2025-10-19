#!/usr/bin/env python3
"""
Test script for Phase 1.5 Complete Workflow
Tests the integrated ghost mannequin pipeline with all custom nodes.
"""

import json
import requests
import time
import os
from pathlib import Path

# Configuration
COMFYUI_SERVER = "http://127.0.0.1:8188"
WORKFLOW_FILE = "workflows/phase1_5_mvp_working.json" # Back to working MVP
TEST_IMAGE = "input/test_garment.jpg"
TEST_FACTS = "input/test_garment_facts.json"

def load_workflow(workflow_path):
    """Load workflow from JSON file."""
    try:
        with open(workflow_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow file: {e}")
        return None

def queue_prompt(workflow):
    """Queue a prompt to ComfyUI."""
    try:
        response = requests.post(f"{COMFYUI_SERVER}/prompt", json={"prompt": workflow})
        if response.status_code == 200:
            result = response.json()
            return result.get("prompt_id")
        else:
            print(f"❌ Failed to queue prompt: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to ComfyUI server. Is it running on port 8188?")
        return None

def get_history(prompt_id):
    """Get execution history for a prompt."""
    try:
        response = requests.get(f"{COMFYUI_SERVER}/history/{prompt_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def check_comfyui_status():
    """Check if ComfyUI server is running."""
    try:
        response = requests.get(f"{COMFYUI_SERVER}/system_stats")
        return response.status_code == 200
    except:
        return False

def test_workflow_components():
    """Test individual workflow components."""
    print("🔍 Testing Phase 1.5 Workflow Components...")
    
    # Check if required files exist
    required_files = [
        "ComfyUI/custom_nodes/comfyui_rmbg/__init__.py",
        "ComfyUI/custom_nodes/load_facts_node.py",
        "ComfyUI/custom_nodes/light_facts_prompt.py",
        "ComfyUI/custom_nodes/quality_gates/__init__.py",
        "ComfyUI/custom_nodes/mask_utils_node.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required custom node files present")
    return True

def main():
    """Main test function."""
    print("🚀 Phase 1.5 Complete Workflow Test")
    print("=" * 50)
    
    # Check ComfyUI status
    if not check_comfyui_status():
        print("❌ ComfyUI server is not running or not accessible")
        print("   Please start ComfyUI with: cd ComfyUI && python main.py --listen --port 8188")
        return False
    
    print("✅ ComfyUI server is running")
    
    # Test workflow components
    if not test_workflow_components():
        return False
    
    # Load workflow
    workflow = load_workflow(WORKFLOW_FILE)
    if not workflow:
        return False
    
    print(f"✅ Loaded workflow: {WORKFLOW_FILE}")
    
    # Check if test files exist
    if not os.path.exists(TEST_IMAGE):
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return False
    
    if not os.path.exists(TEST_FACTS):
        print(f"❌ Test facts not found: {TEST_FACTS}")
        return False
    
    print("✅ Test input files present")
    
    # Queue the prompt
    print("📤 Queuing Phase 1.5 workflow...")
    prompt_id = queue_prompt(workflow)
    
    if not prompt_id:
        return False
    
    print(f"✅ Prompt queued with ID: {prompt_id}")
    print("⏳ Waiting for execution...")
    
    # Monitor execution
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        history = get_history(prompt_id)
        
        if history and prompt_id in history:
            prompt_data = history[prompt_id]
            
            if "status" in prompt_data:
                status = prompt_data["status"]
                if status.get("status_str") == "success":
                    print("✅ Workflow executed successfully!")
                    
                    # Check outputs
                    outputs = status.get("outputs", {})
                    if outputs:
                        print("📊 Generated outputs:")
                        for node_id, output_data in outputs.items():
                            if "images" in output_data:
                                for img_info in output_data["images"]:
                                    print(f"   - {img_info.get('filename', 'unknown')}")
                    
                    return True
                elif status.get("status_str") == "error":
                    print("❌ Workflow execution failed!")
                    if "error" in status:
                        print(f"   Error: {status['error']}")
                    return False
        
        time.sleep(2)
    
    print("⏰ Timeout waiting for workflow execution")
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Phase 1.5 workflow test completed successfully!")
        print("   Check the ComfyUI output folder for generated images.")
    else:
        print("\n💥 Phase 1.5 workflow test failed!")
        print("   Check the ComfyUI logs for error details.")
