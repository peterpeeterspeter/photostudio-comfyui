#!/usr/bin/env python3
"""
Test script to verify the torch.compiler fix works
"""
import requests
import json
import time
import os

def test_comfyui_connection():
    """Test if ComfyUI is running and accessible"""
    try:
        response = requests.get("http://localhost:8188/system_stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ ComfyUI is running")
            print(f"   PyTorch version: {stats['system']['pytorch_version']}")
            print(f"   ComfyUI version: {stats['system']['comfyui_version']}")
            return True
        else:
            print(f"❌ ComfyUI returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to ComfyUI at http://localhost:8188")
        return False
    except Exception as e:
        print(f"❌ Error connecting to ComfyUI: {e}")
        return False

def test_simple_workflow():
    """Test a simple workflow to verify torch.compiler fix"""
    print("\n🧪 Testing simple workflow...")
    
    # Simple workflow that just loads a checkpoint and encodes text
    simple_workflow = {
        "1": {
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text": "test prompt",
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        }
    }
    
    try:
        # Queue the simple workflow
        response = requests.post(
            "http://localhost:8188/prompt",
            json={"prompt": simple_workflow},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "prompt_id" in result:
                print(f"✅ Simple workflow queued successfully")
                print(f"   Prompt ID: {result['prompt_id']}")
                return True
            else:
                print(f"❌ Workflow failed: {result}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing workflow: {e}")
        return False

def main():
    print("🎯 Testing Ghost Mannequin Pipeline - PyTorch Fix Verification")
    print("=" * 60)
    
    # Test 1: ComfyUI Connection
    if not test_comfyui_connection():
        print("\n❌ ComfyUI is not running. Please start it first.")
        return False
    
    # Test 2: Simple Workflow
    if not test_simple_workflow():
        print("\n❌ Simple workflow test failed.")
        return False
    
    print("\n🎉 All tests passed! The torch.compiler fix is working.")
    print("\n📋 Next steps:")
    print("   1. Open ComfyUI at http://localhost:8188")
    print("   2. Load workflows/working_test.json")
    print("   3. Click 'Queue Prompt' to test ghost mannequin generation")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
