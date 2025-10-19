#!/usr/bin/env python3
"""
Test Ghost Mannequin Generation
Simple script to test the Phase 1.5 pipeline via ComfyUI API
"""

import requests
import json
import time
import os
from pathlib import Path

def test_ghost_mannequin():
    """Test the ghost mannequin generation pipeline"""
    
    # ComfyUI server URL
    comfyui_url = "http://localhost:8188"
    
    # Check if ComfyUI is running
    try:
        response = requests.get(f"{comfyui_url}/system_stats")
        if response.status_code == 200:
            print("✅ ComfyUI is running")
        else:
            print("❌ ComfyUI is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to ComfyUI: {e}")
        return False
    
    # Load the complete workflow
    workflow_path = Path("workflows/phase1_5_complete.json")
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {workflow_path}")
        return False
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    print("✅ Loaded Phase 1.5 complete workflow")
    
    # Modify workflow for test
    # Set input image
    if "1" in workflow["nodes"]:
        workflow["nodes"]["1"]["inputs"]["image"] = "test_garment.jpg"
    
    # Set facts file
    if "2" in workflow["nodes"]:
        workflow["nodes"]["2"]["inputs"]["facts_file_path"] = "input/test_garment_facts.json"
    
    print("✅ Configured workflow with test inputs")
    
    # Queue the workflow
    try:
        response = requests.post(
            f"{comfyui_url}/prompt",
            json={"prompt": workflow}
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"✅ Workflow queued successfully! Prompt ID: {prompt_id}")
            
            # Monitor progress
            print("\n🔄 Monitoring progress...")
            print("You can also watch progress in ComfyUI at: http://localhost:8188")
            
            # Check status periodically
            for i in range(30):  # Check for up to 5 minutes
                time.sleep(10)
                
                # Get queue status
                queue_response = requests.get(f"{comfyui_url}/queue")
                if queue_response.status_code == 200:
                    queue_data = queue_response.json()
                    
                    # Check if completed
                    running = queue_data.get("queue_running", [])
                    pending = queue_data.get("queue_pending", [])
                    
                    if not running and not pending:
                        print("✅ Processing completed!")
                        
                        # Get history
                        history_response = requests.get(f"{comfyui_url}/history/{prompt_id}")
                        if history_response.status_code == 200:
                            history = history_response.json()
                            if prompt_id in history:
                                status = history[prompt_id].get("status", {})
                                if status.get("status") == "success":
                                    print("🎉 Ghost mannequin generated successfully!")
                                    print("📁 Check the output directory for results")
                                    return True
                                else:
                                    print(f"❌ Generation failed: {status.get('message', 'Unknown error')}")
                                    return False
                        break
                    else:
                        print(f"⏳ Still processing... ({i+1}/30)")
            
            print("⏰ Processing is taking longer than expected")
            print("Check ComfyUI interface for detailed progress")
            return True
            
        else:
            print(f"❌ Failed to queue workflow: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during workflow execution: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Testing Phase 1.5 Ghost Mannequin Pipeline")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("ComfyUI").exists():
        print("❌ Please run this script from the project root directory")
        return
    
    # Run the test
    success = test_ghost_mannequin()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📖 Check QUICK_START.md for more usage instructions")
    else:
        print("\n❌ Test failed. Check the errors above.")
        print("💡 Try running the workflow manually in ComfyUI interface")

if __name__ == "__main__":
    main()
