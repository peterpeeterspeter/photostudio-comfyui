"""
Photostudio ComfyUI Custom Nodes

This package provides custom nodes for photostudio-specific workflows:
- LoadFactsNode: Parse FactsV3.json files and generate garment descriptions
- PromptBuilder: Build structured rendering prompts from facts + CCJ contract

Usage:
    These nodes integrate into ComfyUI's node graph system for 
    ghost mannequin generation workflows.
"""

from .load_facts_node import LoadFactsNode, NODE_CLASS_MAPPINGS as FACTS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as FACTS_DISPLAY_MAPPINGS
from .prompt_builder import PromptBuilder, NODE_CLASS_MAPPINGS as PROMPT_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as PROMPT_DISPLAY_MAPPINGS

# Combine all node mappings for ComfyUI registration
NODE_CLASS_MAPPINGS = {
    **FACTS_MAPPINGS,
    **PROMPT_MAPPINGS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FACTS_DISPLAY_MAPPINGS,
    **PROMPT_DISPLAY_MAPPINGS
}

# Export for ComfyUI
__all__ = [
    "LoadFactsNode",
    "PromptBuilder", 
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS"
]

# Metadata
WEB_DIRECTORY = "./web"
__version__ = "1.0.0"