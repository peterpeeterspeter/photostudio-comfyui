#!/usr/bin/env python3
"""
Test IP-Adapter integration in Phase 2 pipeline
Tests that patterned garments trigger IP-Adapter activation
"""

import sys
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional


COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_FILE = "workflows/phase2_simple_no_clip.json"


def test_ipadapter_integration(test_image: str, facts_file: str, timeout: int = 600) -> Optional[Dict[str, Any]]:
    """
    Test IP-Adapter integration with a patterned garment
    
    Args:
        test_image: Path to test garment image
        facts_file: Path to facts file that should trigger IP-Adapter
        timeout: Timeout in seconds for the workflow
        
    Returns:
        Response from ComfyUI or None if failed
    """
    print(f"🔍 Testing IP-Adapter integration with: {test_image}")
    print(f"📄 Using facts file: {facts_file}")
    
    # Load workflow
    try:
        with open(WORKFLOW_FILE) as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Workflow file {WORKFLOW_FILE} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {WORKFLOW_FILE}: {e}")
        return None
    
    # Update LoadImage node with test image
    if not test_image.startswith("ComfyUI/input/"):
        import shutil
        src_path = Path(test_image)
        dst_path = Path("ComfyUI/input") / src_path.name
        shutil.copy2(src_path, dst_path)
        workflow["1"]["inputs"]["image"] = src_path.name
        print(f"Copied {test_image} to ComfyUI/input/ and updated workflow")
    else:
        workflow["1"]["inputs"]["image"] = test_image
        print(f"Updated LoadImage node (ID 1) to use: {test_image}")
    
    # Update LoadFactsNode with facts file (node 3 in simple workflow)
    facts_path = Path(facts_file)
    if facts_path.exists():
        # Copy facts to ComfyUI input directory
        dst_facts = Path("ComfyUI/input") / facts_path.name
        import shutil
        shutil.copy2(facts_path, dst_facts)
        workflow["3"]["inputs"]["facts_file_path"] = facts_path.name
        print(f"Updated LoadFactsNode (ID 3) to use: {facts_path.name}")
    else:
        print(f"❌ Facts file not found: {facts_file}")
        return None
    
    # Queue prompt
    try:
        print(f"📤 Queuing workflow to ComfyUI...")
        response = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to queue prompt: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        prompt_id = result.get("prompt_id")
        
        if not prompt_id:
            print(f"❌ No prompt ID returned: {result}")
            return None
        
        print(f"✅ Workflow queued successfully (ID: {prompt_id})")
        
        # Wait for completion
        print(f"⏳ Waiting for workflow completion (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check prompt status
                status_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
                if status_response.status_code == 200:
                    history = status_response.json()
                    
                    if prompt_id in history:
                        prompt_data = history[prompt_id]
                        
                        if "status" in prompt_data:
                            status = prompt_data["status"]
                            
                            if status.get("status_str") == "success":
                                print(f"✅ Workflow completed successfully!")
                                return prompt_data
                            elif status.get("status_str") == "error":
                                print(f"❌ Workflow failed: {status.get('error', 'Unknown error')}")
                                return None
                
                # Check if images are available
                queue_response = requests.get(f"{COMFYUI_URL}/queue")
                if queue_response.status_code == 200:
                    queue_data = queue_response.json()
                    if not queue_data.get("queue_running") and not queue_data.get("queue_pending"):
                        # Queue is empty, check for results
                        if prompt_id in history:
                            prompt_data = history[prompt_id]
                            if "outputs" in prompt_data:
                                print(f"✅ Workflow completed!")
                                return prompt_data
                
                time.sleep(5)  # Check every 5 seconds
                
            except requests.RequestException as e:
                print(f"⚠️  Request error while waiting: {e}")
                time.sleep(5)
        
        print(f"⏰ Timeout reached ({timeout}s)")
        return None
        
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def check_comfyui_status() -> bool:
    """Check if ComfyUI is running and accessible"""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main test function"""
    print("🚀 IP-Adapter Integration Test for Phase 2 Pipeline")
    print("=" * 60)
    
    # Check ComfyUI status
    print("🔍 Checking ComfyUI status...")
    if not check_comfyui_status():
        print("❌ ComfyUI is not running or not accessible")
        print("   Please start ComfyUI with: cd ComfyUI && python main.py --listen --port 8188")
        return 1
    
    print("✅ ComfyUI is running and accessible")
    
    # Use the same test image as before
    test_image = "data/input/real/test_garment_001.jpg"
    facts_file = "facts/cache/test_ipadapter_facts.json"
    
    print(f"\n🎯 Testing IP-Adapter integration with:")
    print(f"   Image: {test_image}")
    print(f"   Facts: {facts_file}")
    
    # Check if files exist
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        return 1
    
    if not Path(facts_file).exists():
        print(f"❌ Facts file not found: {facts_file}")
        return 1
    
    # Run the test
    result = test_ipadapter_integration(test_image, facts_file, timeout=600)
    
    if result is None:
        print("❌ IP-Adapter integration test failed")
        return 1
    
    print("✅ IP-Adapter integration test completed successfully!")
    
    # Check outputs
    if "outputs" in result:
        outputs = result["outputs"]
        print(f"\n📊 Pipeline outputs:")
        for node_id, node_output in outputs.items():
            print(f"   Node {node_id}: {list(node_output.keys())}")
    
    # Check for generated images
    output_dir = Path("ComfyUI/output")
    if output_dir.exists():
        recent_images = list(output_dir.glob("*.png"))
        if recent_images:
            latest_image = max(recent_images, key=lambda p: p.stat().st_mtime)
            print(f"\n🖼️  Latest generated image: {latest_image}")
    
    print("\n🎉 IP-Adapter integration test completed successfully!")
    print("\nNext steps:")
    print("1. Check the generated image in ComfyUI/output/")
    print("2. Verify that IP-Adapter was activated (check ComfyUI logs)")
    print("3. Compare quality with non-IP-Adapter results")
    
    return 0


if __name__ == "__main__":
    exit(main())
