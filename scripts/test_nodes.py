#!/usr/bin/env python3
"""
Test Script for Photostudio ComfyUI Custom Nodes

This script validates that LoadFactsNode and PromptBuilder work correctly
in standalone mode before integrating into ComfyUI workflows.

Usage:
    python scripts/test_nodes.py
"""

import json
import os
import sys
from pathlib import Path

# Add custom_nodes to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_nodes"))

from load_facts_node import LoadFactsNode
from prompt_builder import PromptBuilder

def create_test_data():
    """Create sample test data for testing"""
    
    # Sample FactsV3 data
    test_facts = {
        "garment_type": "dress",
        "primary_color": "navy blue",
        "primary_material": "cotton",
        "sleeve_length": "long",
        "neckline": "crew",
        "fit_type": "relaxed",
        "has_patterns": True,
        "pattern_type": "floral",
        "has_embellishments": False,
        "style_category": "casual",
        "garment_length": "midi",
        "chest_width": "42cm",
        "fabric_weight": "medium",
        "color_accuracy": "high",
        "ghost_mannequin_requirements": {
            "interior_visibility_needed": True,
            "volume_preservation": "high",
            "drape_natural": True,
            "symmetry_critical": True,
            "edge_precision": "high"
        },
        "rendering_hints": {
            "fabric_behavior": "flowing",
            "critical_features": ["neckline", "sleeves", "drape"]
        }
    }
    
    # Sample CCJ ControlBlock data
    test_ccj = {
        "core_contract": {
            "mandatory_specs": {
                "background": {
                    "color": "#FFFFFF",
                    "type": "solid",
                    "edge_treatment": "clean alpha"
                },
                "silhouette": {
                    "garment_type": "dress",
                    "fit": "natural",
                    "symmetry": "bilateral"
                },
                "interior_rendering": {
                    "neckline_visible": True,
                    "cuff_visible": True,
                    "hem_visible": False
                },
                "color_accuracy": {
                    "primary_hex": "#1a237e",
                    "delta_e_max": 2.0
                },
                "resolution": {
                    "min_width": 2048,
                    "min_height": 2048
                }
            },
            "forbidden_elements": [
                "visible mannequin",
                "background patterns",
                "harsh shadows",
                "color distortion"
            ]
        },
        "rendering_hints": {
            "lighting": {
                "setup": "three-point studio",
                "key_light": "soft 45-degree",
                "shadows": "soft contact only"
            },
            "fabric_behavior": {
                "material_type": "cotton",
                "drape_weight": "natural",
                "texture_visibility": "clear"
            },
            "critical_details": {
                "preserve": ["fabric texture", "natural drape", "color accuracy"],
                "enhance": ["garment structure", "interior visibility"],
                "avoid": ["artificial stiffness", "color shift", "harsh edges"]
            }
        }
    }
    
    return test_facts, test_ccj

def setup_test_files():
    """Create test input files"""
    
    # Create input directory if it doesn't exist
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)
    
    test_facts, test_ccj = create_test_data()
    
    # Write test FactsV3 file
    facts_path = input_dir / "test_factsv3.json"
    with open(facts_path, 'w', encoding='utf-8') as f:
        json.dump(test_facts, f, indent=2, ensure_ascii=False)
    
    # Write test CCJ file
    ccj_path = input_dir / "test_ccj_controlblock.json"
    with open(ccj_path, 'w', encoding='utf-8') as f:
        json.dump(test_ccj, f, indent=2, ensure_ascii=False)
    
    return str(facts_path), str(ccj_path)

def test_load_facts_node(facts_path):
    """Test LoadFactsNode functionality"""
    print("🧪 Testing LoadFactsNode...")
    
    # Create node instance
    loader = LoadFactsNode()
    
    # Test loading facts
    description, facts_json = loader.load_facts(facts_path)
    
    # Validate results
    assert not description.startswith("ERROR"), f"LoadFactsNode failed: {description}"
    assert facts_json != "{}", "Facts JSON should not be empty"
    
    # Parse facts back to verify
    facts_dict = json.loads(facts_json)
    assert "garment_type" in facts_dict, "Missing garment_type in facts"
    
    print(f"✅ LoadFactsNode passed!")
    print(f"   Generated description: {description}")
    print(f"   Facts loaded: {len(facts_dict)} fields")
    
    return description, facts_dict

def test_prompt_builder(facts_description, facts_dict, ccj_path):
    """Test PromptBuilder functionality"""
    print("\n🧪 Testing PromptBuilder...")
    
    # Create node instance
    builder = PromptBuilder()
    
    # Test building prompt
    final_prompt, core_contract, rendering_hints = builder.build_prompt(
        facts_description=facts_description,
        facts_dict=facts_dict,
        ccj_path=ccj_path,
        custom_additions="Test custom addition",
        include_chinese=True
    )
    
    # Validate results
    assert "ERROR" not in final_prompt, f"PromptBuilder failed: {final_prompt}"
    assert "SYSTEM" in final_prompt, "Missing system section"
    assert "GARMENT" in final_prompt, "Missing garment section"
    assert "隐形人台效果" in final_prompt, "Missing Chinese terms"
    assert "CORE CONTRACT" in core_contract, "Missing core contract header"
    assert "RENDERING HINTS" in rendering_hints, "Missing rendering hints header"
    
    print(f"✅ PromptBuilder passed!")
    print(f"   Final prompt length: {len(final_prompt)} characters")
    print(f"   Includes Chinese terms: {'隐形人台效果' in final_prompt}")
    print(f"   Custom additions included: {'Test custom addition' in final_prompt}")
    
    return final_prompt, core_contract, rendering_hints

def test_integration():
    """Test full integration workflow"""
    print("\n🧪 Testing Full Integration Workflow...")
    
    # Setup test files
    facts_path, ccj_path = setup_test_files()
    
    # Test LoadFactsNode
    description, facts_dict = test_load_facts_node(facts_path)
    
    # Test PromptBuilder with LoadFactsNode output
    final_prompt, core_contract, rendering_hints = test_prompt_builder(
        description, facts_dict, ccj_path
    )
    
    print(f"\n✅ Full Integration Test PASSED!")
    print(f"   Pipeline: FactsV3 → LoadFactsNode → PromptBuilder → Final Prompt")
    print(f"   Output ready for ComfyUI workflow")
    
    return final_prompt

def print_sample_output(final_prompt):
    """Print a sample of the generated prompt"""
    print(f"\n" + "="*60)
    print("📝 SAMPLE GENERATED PROMPT:")
    print("="*60)
    
    # Show first 500 characters
    sample = final_prompt[:500]
    print(sample)
    if len(final_prompt) > 500:
        print(f"\n... [truncated - full length: {len(final_prompt)} characters]")
    
    print("="*60)

def main():
    """Run all tests"""
    print("🚀 Starting Phase B: Custom Nodes Testing")
    print("="*50)
    
    try:
        # Run integration test
        final_prompt = test_integration()
        
        # Show sample output
        print_sample_output(final_prompt)
        
        print(f"\n🎉 PHASE B: COMPLETE! All Tests Passed!")
        print(f"✅ LoadFactsNode - working")
        print(f"✅ PromptBuilder - working") 
        print(f"✅ Integration - working")
        print(f"✅ Ready for Phase A: ComfyUI Workflow JSON")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)