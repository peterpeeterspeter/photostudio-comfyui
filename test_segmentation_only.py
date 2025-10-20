#!/usr/bin/env python3
"""
Test Phase 2 Segmentation Components Only
Tests the segmentation and analysis components without generation
"""

import sys
import os
import json
import requests
import time

def test_segmentation_workflow():
    """Test the segmentation workflow"""
    print("🚀 Testing Phase 2 Segmentation Components...")
    
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
    workflow_path = "workflows/phase2_segmentation_test.json"
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
    
    # Queue the workflow
    try:
        print("📤 Queuing segmentation workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json={
                "prompt": workflow,
                "client_id": "test_segmentation_only"
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
        max_wait = 180  # 3 minutes for segmentation only
        
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
                        print("✅ Segmentation workflow completed successfully!")
                        
                        # Check for output images
                        history_response = requests.get(
                            f"http://127.0.0.1:8188/history/{prompt_id}",
                            timeout=10
                        )
                        
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            outputs = history_data.get("outputs", {})
                            
                            # Check for segmentation outputs
                            if "6" in outputs:  # Garment segmentation
                                images = outputs["6"].get("images", [])
                                if images:
                                    print(f"✅ Generated {len(images)} segmentation images")
                                    for img in images:
                                        print(f"   - {img.get('filename', 'unknown')}")
                            
                            if "7" in outputs:  # Parts overlay
                                images = outputs["7"].get("images", [])
                                if images:
                                    print(f"✅ Generated {len(images)} parts overlay images")
                                    for img in images:
                                        print(f"   - {img.get('filename', 'unknown')}")
                            
                            return True
                        
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

def main():
    """Main test function"""
    print("🧪 Phase 2 Segmentation Test")
    print("=" * 40)
    
    # Test workflow
    success = test_segmentation_workflow()
    
    if success:
        print("\n🎉 Phase 2 segmentation test PASSED!")
        print("✅ Segmentation and analysis components working")
    else:
        print("\n❌ Phase 2 segmentation test FAILED!")
        print("🔧 Check ComfyUI logs for details")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
