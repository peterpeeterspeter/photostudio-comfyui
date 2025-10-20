#!/usr/bin/env python3
"""
Simple CLIP Model Test
Test if CLIP models are working correctly
"""

import requests
import json
import time
import os

def test_clip_models():
    """Test CLIP models with a simple workflow"""
    
    print("🧪 Simple CLIP Model Test")
    print("=" * 40)
    
    # Check if ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI is running")
        else:
            print("❌ ComfyUI not responding")
            return False
    except Exception as e:
        print(f"❌ ComfyUI not running: {e}")
        return False
    
    # Load the simple CLIP test workflow
    workflow_path = "workflows/test_clip_only.json"
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow not found: {workflow_path}")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    print(f"✅ Loaded workflow with {len(workflow)} nodes")
    
    # Check if test image exists
    test_image = "input/test_garment.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return False
    
    print(f"✅ Found: {test_image}")
    
    # Queue the workflow
    try:
        print("📤 Queuing CLIP test workflow...")
        response = requests.post("http://127.0.0.1:8188/prompt", 
                               json={"prompt": workflow}, 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"✅ Workflow queued with ID: {prompt_id}")
            
            # Monitor execution
            print("⏳ Monitoring execution...")
            start_time = time.time()
            
            while time.time() - start_time < 60:  # 1 minute timeout
                try:
                    response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=5)
                    if response.status_code == 200:
                        history = response.json()
                        if prompt_id in history:
                            status = history[prompt_id].get("status", {})
                            if status.get("status_str") == "success":
                                print("✅ CLIP test completed successfully!")
                                return True
                            elif status.get("status_str") == "error":
                                print(f"❌ CLIP test failed: {status.get('message', 'Unknown error')}")
                                return False
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️  Request error: {e}")
                    time.sleep(2)
            
            print("⏰ Timeout after 60 seconds")
            return False
            
        else:
            print(f"❌ Failed to queue workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_clip_models()
    if success:
        print("\n🎉 CLIP models are working correctly!")
    else:
        print("\n❌ CLIP test failed!")
        print("🔧 Check ComfyUI logs for details")
