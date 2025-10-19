import json
import os
from typing import Dict, Any, Tuple

class LoadFactsNode:
    """ComfyUI node for loading and parsing FactsV3.json files"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "facts_file_path": ("STRING", {
                    "default": "input/factsv3.json",
                    "multiline": False
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("garment_description", "facts_json")
    FUNCTION = "load_facts"
    CATEGORY = "photostudio"
    
    def load_facts(self, facts_file_path: str) -> Tuple[str, str]:
        """Load FactsV3.json and generate garment description"""
        try:
            # Handle relative paths from project root
            if not os.path.isabs(facts_file_path):
                facts_file_path = os.path.join(os.getcwd(), facts_file_path)
            
            if not os.path.exists(facts_file_path):
                return f"ERROR: File not found: {facts_file_path}", "{}"
            
            with open(facts_file_path, 'r', encoding='utf-8') as f:
                facts_data = json.load(f)
            
            # Generate concise garment description from key FactsV3 fields
            description = self._generate_garment_description(facts_data)
            
            # Return both description and full facts as JSON string
            return description, json.dumps(facts_data, ensure_ascii=False)
            
        except Exception as e:
            return f"ERROR: Failed to load facts: {str(e)}", "{}"
    
    def _generate_garment_description(self, facts: Dict[str, Any]) -> str:
        """Generate concise garment description from FactsV3 fields"""
        parts = []
        
        # Core garment info
        if facts.get('garment_type'):
            parts.append(facts['garment_type'])
        
        if facts.get('primary_color'):
            parts.append(f"{facts['primary_color']} color")
        
        if facts.get('primary_material'):
            parts.append(f"{facts['primary_material']} material")
        
        # Key features
        if facts.get('sleeve_length'):
            parts.append(f"{facts['sleeve_length']} sleeves")
        
        if facts.get('neckline'):
            parts.append(f"{facts['neckline']} neckline")
        
        if facts.get('fit_type'):
            parts.append(f"{facts['fit_type']} fit")
        
        # Special features
        if facts.get('has_patterns') and facts['has_patterns']:
            if facts.get('pattern_type'):
                parts.append(f"{facts['pattern_type']} pattern")
        
        if facts.get('has_embellishments') and facts['has_embellishments']:
            parts.append("with embellishments")
        
        # Brand/style context
        if facts.get('style_category'):
            parts.append(f"{facts['style_category']} style")
        
        # Construct description
        if parts:
            return ", ".join(parts[:8])  # Limit to 8 key features for brevity
        else:
            return "Generic garment"

# ComfyUI node mapping
NODE_CLASS_MAPPINGS = {
    "LoadFactsNode": LoadFactsNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadFactsNode": "Load Facts V3"
}