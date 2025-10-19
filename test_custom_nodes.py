#!/usr/bin/env python3
"""
Test script to check if custom nodes can be imported without errors
"""

import sys
import os
sys.path.append('ComfyUI')
sys.path.append('ComfyUI/custom_nodes')

def test_import(module_name, class_name=None):
    """Test importing a module and optionally a class"""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} imported successfully")
            return True
        else:
            print(f"✅ {module_name} imported successfully")
            return True
    except Exception as e:
        print(f"❌ Failed to import {module_name}.{class_name if class_name else ''}: {e}")
        return False

def main():
    print("🔍 Testing Custom Node Imports...")
    print("=" * 50)
    
    # Test existing nodes
    print("\n📦 Testing Existing Nodes:")
    test_import("load_facts_node", "LoadFactsNode")
    test_import("light_facts_prompt", "PromptFromLightFacts")
    test_import("quality_gates.edge_gate", "QualityGateEdge")
    test_import("quality_gates.bg_gate", "QualityGateBackground")
    
    # Test new nodes
    print("\n🆕 Testing New Enhanced Nodes:")
    test_import("u2net_segmentation.u2net_node", "U2NetSegmentation")
    test_import("mask_ensemble", "MaskEnsemble")
    test_import("ip_adapter_conditional", "IPAdapterConditional")
    test_import("controlnet_inpaint_polish", "ControlNetInpaintPolish")
    
    print("\n🎯 Import testing complete!")

if __name__ == "__main__":
    main()
