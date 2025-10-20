#!/usr/bin/env python3
"""
Test Real GroundingDINO Integration
Tests the actual GroundingDINO model with garment part detection
"""

import sys
import os
import json
from PIL import Image
import numpy as np

# Add ComfyUI paths
sys.path.append('ComfyUI')
sys.path.append('ComfyUI/custom_nodes')

def test_grounding_dino_integration():
    """Test real GroundingDINO integration"""
    print("🧪 Testing Real GroundingDINO Integration...")
    
    try:
        # Import our custom node
        from garment_part_segmentation import GarmentPartSegmentation
        
        # Create instance
        node = GarmentPartSegmentation()
        
        # Load test image
        test_image_path = "input/test_garment.jpg"
        if not os.path.exists(test_image_path):
            print(f"❌ Test image not found: {test_image_path}")
            return False
            
        image = Image.open(test_image_path)
        print(f"✅ Loaded test image: {image.size}")
        
        # Create a simple mask (full image for testing)
        mask = Image.new('L', image.size, 255)
        
        # Test parameters
        parts_list = ["collar", "sleeve", "placket", "pocket", "hem"]
        confidence_threshold = 0.3
        
        print(f"🔍 Testing part detection: {parts_list}")
        
        # Test the segmentation
        result = node.segment_parts(
            image=image,
            garment_mask=mask,
            segmentation_mode="dino_sam2",
            part_prompts=", ".join(parts_list),  # Convert list to comma-separated string
            min_parts_for_dino=2,
            confidence_threshold=confidence_threshold
        )
        
        parts_json, overlay_tensor = result
        
        # Parse results
        parts_data = json.loads(parts_json)
        
        print(f"✅ GroundingDINO Results:")
        print(f"   Method: {parts_data.get('segmentation_method', 'unknown')}")
        print(f"   Parts detected: {len(parts_data.get('parts', []))}")
        
        for part in parts_data.get('parts', []):
            print(f"   - {part.get('part_name', 'unknown')}: "
                  f"confidence={part.get('confidence', 0):.3f}, "
                  f"bbox={part.get('bbox', [])}")
        
        # Check if we got real results (not fallback)
        if parts_data.get('segmentation_method') == 'dino_sam2':
            print("✅ Real GroundingDINO integration working!")
            return True
        else:
            print(f"⚠️  Using fallback method: {parts_data.get('segmentation_method')}")
            return False
            
    except Exception as e:
        print(f"❌ GroundingDINO test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sam2_integration():
    """Test SAM2 model availability"""
    print("\n🧪 Testing SAM2 Integration...")
    
    try:
        # Check if SAM2 model exists
        sam2_path = "ComfyUI/models/sam2/sam2_hiera_base_plus.pt"
        if os.path.exists(sam2_path):
            size = os.path.getsize(sam2_path) / (1024*1024)  # MB
            print(f"✅ SAM2 model found: {size:.1f}MB")
            return True
        else:
            print(f"❌ SAM2 model not found: {sam2_path}")
            return False
            
    except Exception as e:
        print(f"❌ SAM2 test failed: {e}")
        return False

def test_ip_adapter_integration():
    """Test IP-Adapter model availability"""
    print("\n🧪 Testing IP-Adapter Integration...")
    
    try:
        # Check if IP-Adapter model exists
        ipadapter_path = "ComfyUI/models/ipadapter/ip-adapter_sdxl_vit-h.safetensors"
        if os.path.exists(ipadapter_path):
            size = os.path.getsize(ipadapter_path) / (1024*1024)  # MB
            print(f"✅ IP-Adapter model found: {size:.1f}MB")
            return True
        else:
            print(f"❌ IP-Adapter model not found: {ipadapter_path}")
            return False
            
    except Exception as e:
        print(f"❌ IP-Adapter test failed: {e}")
        return False

def test_sdxl_integration():
    """Test SDXL model availability"""
    print("\n🧪 Testing SDXL Integration...")
    
    try:
        # Check if SDXL model exists
        sdxl_path = "ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors"
        if os.path.exists(sdxl_path):
            size = os.path.getsize(sdxl_path) / (1024*1024*1024)  # GB
            print(f"✅ SDXL model found: {size:.1f}GB")
            return True
        else:
            print(f"❌ SDXL model not found: {sdxl_path}")
            return False
            
    except Exception as e:
        print(f"❌ SDXL test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Phase 2 Component Integration Tests")
    print("=" * 50)
    
    results = {}
    
    # Test each component
    results['grounding_dino'] = test_grounding_dino_integration()
    results['sam2'] = test_sam2_integration()
    results['ip_adapter'] = test_ip_adapter_integration()
    results['sdxl'] = test_sdxl_integration()
    
    # Summary
    print("\n📊 Integration Test Results:")
    print("=" * 30)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:15} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} components working")
    
    if passed_tests >= 3:  # At least 3 out of 4 working
        print("🎉 Ready for Phase 2 workflow testing!")
        return True
    else:
        print("⚠️  Some components need attention before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
